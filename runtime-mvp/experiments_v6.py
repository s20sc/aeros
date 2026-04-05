#!/usr/bin/env python3
"""
AEROS V6 Experiments — Ablation Study & Failure Boundary
=========================================================
Addresses V5 reviewer feedback:
  Required 1: Ablation study decomposing AEROS's advantage
  Required 2: Failure boundary exploration (p_fail > 50%)

Experiment 4b (Ablation): AEROS-full vs AEROS-no-policy vs
  AEROS-static-plan vs AEROS-no-recovery, same conditions as Exp 4.
Experiment 7: Failure boundary sweep (p_fail = 10% to 90%)
  for all 4 architectures + AEROS ablation variants.
"""

import sys, os, time, random, json, copy, math, io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(__file__))

from experiments import reset_all, load_ecms, count_steps, _patch_sleep, _unpatch_sleep
from experiments_v3 import (
    wilson_ci, fisher_exact_p, TASK_CONFIGS, patch_failure,
    run_flat_pipeline, run_bt_style, run_progprompt_style, run_aeros_full,
)


# ===========================================================================
# AEROS Ablation Variants
# ===========================================================================

def run_aeros_no_policy(seed, task_name):
    """AEROS without policy enforcement — skills bypass permission checks."""
    cfg = TASK_CONFIGS[task_name]
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from runtime.trace import get_trace

    cleanup = patch_failure(task_name, cfg["fail_rate"])

    # Patch policy to always allow
    import runtime.policy as policy_mod
    original_check = policy_mod.check_permission
    policy_mod.check_permission = lambda skill, ecm: (True, "bypassed")

    # Patch runtime to use bypassed policy
    import runtime.runtime as runtime_mod
    original_exec = runtime_mod.execute_with_policy
    def exec_no_policy(skill_name, skill_entry):
        skill = skill_entry["module"]
        result = None
        try:
            if hasattr(skill, "run"):
                result = skill.run()
        except Exception as e:
            return {"status": "failure", "reason": f"skill_exception: {str(e)}"}
        if result is None:
            result = {"status": "success"}
        elif not isinstance(result, dict):
            result = {"status": "success"}
        return result
    runtime_mod.execute_with_policy = exec_no_policy

    # Also need plan cleanup for clean_table
    plan_cleanup = None
    if task_name == "clean_table":
        from ecm.registry import get_skill
        plan_skill = get_skill("clean.plan")
        if plan_skill:
            original_plan_run = plan_skill["module"].run
            def patched_plan_run():
                result = original_plan_run()
                if result.get("task_graph") and result["task_graph"].get("steps"):
                    for step in result["task_graph"]["steps"]:
                        if step.get("skill") == "clean.wipe":
                            step["retry"] = 1
                            step["on_failure"] = "clean.recover"
                return result
            plan_skill["module"].run = patched_plan_run
            plan_cleanup = lambda: setattr(plan_skill["module"], 'run', original_plan_run)

    from agent.agent import Agent
    agent = Agent()
    agent.run(cfg["instruction"])

    trace = get_trace()
    success = cfg["success_check"](world)
    total_steps = count_steps(trace)
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}

    cleanup()
    if plan_cleanup:
        plan_cleanup()
    policy_mod.check_permission = original_check
    runtime_mod.execute_with_policy = original_exec

    return {"success": success, "steps": total_steps,
            "robot_actions": robot_metrics.get("total_actions", 0)}


def run_aeros_static_plan(seed, task_name):
    """AEROS without dynamic re-planning — plan once, execute all steps sequentially.
    Keeps retry, recovery, and policy enforcement."""
    cfg = TASK_CONFIGS[task_name]
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from ecm.registry import get_skill
    from runtime.runtime import execute_with_policy
    from runtime.trace import start_trace, add_step, finish_trace

    cleanup = patch_failure(task_name, cfg["fail_rate"])

    plan_map = {
        "make_dumplings": "dumpling.plan",
        "clean_table": "clean.plan",
        "fetch_object": "fetch.plan",
    }
    plan_skill_name = plan_map[task_name]

    # Patch clean_table plan to add retry/recovery
    plan_cleanup = None
    if task_name == "clean_table":
        plan_skill = get_skill("clean.plan")
        if plan_skill:
            original_plan_run = plan_skill["module"].run
            def patched_plan_run():
                result = original_plan_run()
                if result.get("task_graph") and result["task_graph"].get("steps"):
                    for step in result["task_graph"]["steps"]:
                        if step.get("skill") == "clean.wipe":
                            step["retry"] = 1
                            step["on_failure"] = "clean.recover"
                return result
            plan_skill["module"].run = patched_plan_run
            plan_cleanup = lambda: setattr(plan_skill["module"], 'run', original_plan_run)

    start_trace(task_name)

    # Plan ONCE
    skill_entry = get_skill(plan_skill_name)
    result = execute_with_policy(plan_skill_name, skill_entry)

    steps_executed = 1

    if result.get("status") != "success" or not result.get("task_graph"):
        finish_trace("aborted")
        cleanup()
        if plan_cleanup:
            plan_cleanup()
        return {"success": False, "steps": steps_executed, "robot_actions": 0}

    plan_steps = result["task_graph"]["steps"]

    # Execute ALL steps sequentially (no re-planning)
    for i, step in enumerate(plan_steps):
        skill_name = step["skill"]
        retries = step.get("retry", 0)
        fallback = step.get("on_failure")
        s_entry = get_skill(skill_name)
        if not s_entry:
            break

        # Try with retries
        step_result = execute_with_policy(skill_name, s_entry)
        steps_executed += 1
        attempt = 1

        while step_result.get("status") != "success" and attempt <= retries:
            attempt += 1
            step_result = execute_with_policy(skill_name, s_entry)
            steps_executed += 1

        if step_result.get("status") != "success" and fallback:
            fb_entry = get_skill(fallback)
            if fb_entry:
                fb_result = execute_with_policy(fallback, fb_entry)
                steps_executed += 1

        if step_result.get("status") != "success" and not fallback:
            break

    success = cfg["success_check"](world)
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}
    finish_trace("completed" if success else "aborted")

    cleanup()
    if plan_cleanup:
        plan_cleanup()

    return {"success": success, "steps": steps_executed,
            "robot_actions": robot_metrics.get("total_actions", 0)}


def run_aeros_no_recovery(seed, task_name):
    """AEROS without recovery actions — keeps re-planning, retry, and policy,
    but removes fallback/on_failure from all plan steps."""
    cfg = TASK_CONFIGS[task_name]
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from runtime.trace import get_trace

    cleanup = patch_failure(task_name, cfg["fail_rate"])

    # For clean_table, patch plan but WITHOUT recovery
    plan_cleanup = None
    if task_name == "clean_table":
        from ecm.registry import get_skill
        plan_skill = get_skill("clean.plan")
        if plan_skill:
            original_plan_run = plan_skill["module"].run
            def patched_plan_run():
                result = original_plan_run()
                if result.get("task_graph") and result["task_graph"].get("steps"):
                    for step in result["task_graph"]["steps"]:
                        if step.get("skill") == "clean.wipe":
                            step["retry"] = 1
                            # NO on_failure — this is the ablation
                            step.pop("on_failure", None)
                return result
            plan_skill["module"].run = patched_plan_run
            plan_cleanup = lambda: setattr(plan_skill["module"], 'run', original_plan_run)

    # Patch Agent to strip on_failure from all steps
    from agent import agent as agent_mod
    OrigAgent = agent_mod.Agent
    original_execute_one = OrigAgent._execute_one_step

    def patched_execute_one(self, step, step_num):
        if isinstance(step, dict):
            step = dict(step)
            step.pop("on_failure", None)
        return original_execute_one(self, step, step_num)

    OrigAgent._execute_one_step = patched_execute_one

    agent = OrigAgent()
    agent.run(cfg["instruction"])

    trace = get_trace()
    success = cfg["success_check"](world)
    total_steps = count_steps(trace)
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}

    cleanup()
    if plan_cleanup:
        plan_cleanup()
    OrigAgent._execute_one_step = original_execute_one

    return {"success": success, "steps": total_steps,
            "robot_actions": robot_metrics.get("total_actions", 0)}


# ===========================================================================
# Experiment Ablation: AEROS variants (4 variants × 3 tasks)
# ===========================================================================

def experiment_ablation(n_trials=100):
    """Ablation: decompose AEROS's advantage by disabling one component at a time."""
    variants = [
        ("AEROS (full)",        run_aeros_full),
        ("AEROS-no-policy",     run_aeros_no_policy),
        ("AEROS-static-plan",   run_aeros_static_plan),
        ("AEROS-no-recovery",   run_aeros_no_recovery),
    ]

    tasks = ["make_dumplings", "clean_table", "fetch_object"]
    results = {}

    for var_name, run_fn in variants:
        results[var_name] = {}
        for task_name in tasks:
            trial_results = []
            for i in range(n_trials):
                seed = 9000 + hash(task_name) % 1000 + i
                trial_results.append(run_fn(seed, task_name))

            successes = sum(1 for r in trial_results if r["success"])
            avg_steps = sum(r["steps"] for r in trial_results) / len(trial_results)
            ci = wilson_ci(successes, n_trials)

            results[var_name][task_name] = {
                "success_rate": round(successes / n_trials * 100, 1),
                "successes": successes,
                "ci_lower": ci[0],
                "ci_upper": ci[1],
                "avg_steps": round(avg_steps, 1),
            }

    return results


# ===========================================================================
# Experiment Failure Boundary: sweep p_fail from 10% to 90%
# ===========================================================================

def run_with_custom_fail_rate(run_fn, seed, task_name, fail_rate):
    """Run any architecture function with a custom failure rate override."""
    # Temporarily override the task config's fail rate
    original_rate = TASK_CONFIGS[task_name]["fail_rate"]
    TASK_CONFIGS[task_name]["fail_rate"] = fail_rate
    try:
        result = run_fn(seed, task_name)
    finally:
        TASK_CONFIGS[task_name]["fail_rate"] = original_rate
    return result


def experiment_failure_boundary(n_trials=100):
    """Sweep p_fail from 10% to 90% for key architectures."""
    fail_rates = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]

    architectures = [
        ("Flat Pipeline",       run_flat_pipeline),
        ("BT.CPP (retry=3)",    lambda s, t: run_bt_style(s, t, max_retries=3)),
        ("ProgPrompt (replan=3)", lambda s, t: run_progprompt_style(s, t, max_replans=3)),
        ("AEROS (full)",        run_aeros_full),
    ]

    # Run on all 3 tasks, average the results
    tasks = ["make_dumplings", "clean_table", "fetch_object"]
    results = {}

    for arch_name, run_fn in architectures:
        results[arch_name] = {}
        for fr in fail_rates:
            fr_key = f"{int(fr*100)}%"
            task_successes = []
            for task_name in tasks:
                successes = 0
                for i in range(n_trials):
                    seed = 10000 + int(fr * 1000) + hash(task_name) % 1000 + i
                    r = run_with_custom_fail_rate(run_fn, seed, task_name, fr)
                    if r["success"]:
                        successes += 1
                task_successes.append(successes)

            total_s = sum(task_successes)
            total_n = n_trials * len(tasks)
            mean_rate = round(total_s / total_n * 100, 1)
            ci = wilson_ci(total_s, total_n)

            results[arch_name][fr_key] = {
                "mean_success_rate": mean_rate,
                "per_task": {
                    tasks[j]: round(task_successes[j] / n_trials * 100, 1)
                    for j in range(len(tasks))
                },
                "ci_lower": ci[0],
                "ci_upper": ci[1],
            }

    return results


# ===========================================================================
# Main
# ===========================================================================

def main():
    N = 100
    _patch_sleep()
    f_null = io.StringIO()

    all_output = {
        "metadata": {
            "n_trials": N,
            "robot_backend": os.environ.get("AEROS_ROBOT", "mock"),
        }
    }

    tasks = ["make_dumplings", "clean_table", "fetch_object"]
    task_short = {"make_dumplings": "Dumpling", "clean_table": "CleanTbl", "fetch_object": "FetchObj"}

    # --- Ablation Study ---
    print(f"Running Ablation Study (4 AEROS variants × 3 tasks, n={N})...")
    with redirect_stdout(f_null):
        r_abl = experiment_ablation(N)
    all_output["experiment_ablation"] = r_abl

    print("\n" + "=" * 80)
    print("ABLATION STUDY: AEROS Component Decomposition")
    print("=" * 80)

    print(f"\n{'Variant':<24}", end="")
    for t in tasks:
        print(f"  {task_short[t]:>10}", end="")
    print(f"  {'Mean':>8}")
    print("-" * 72)

    for var_name, task_data in r_abl.items():
        print(f"{var_name:<24}", end="")
        rates = []
        for t in tasks:
            rate = task_data[t]["success_rate"]
            rates.append(rate)
            print(f"  {rate:>9}%", end="")
        mean_rate = round(sum(rates) / len(rates), 1)
        print(f"  {mean_rate:>7}%")

    # CIs
    print(f"\n{'Variant':<24}", end="")
    for t in tasks:
        print(f"  {'95% CI':>18}", end="")
    print()
    print("-" * 86)
    for var_name, task_data in r_abl.items():
        print(f"{var_name:<24}", end="")
        for t in tasks:
            d = task_data[t]
            print(f"  [{d['ci_lower']:>5},{d['ci_upper']:>5}]", end="")
        print()

    # --- Failure Boundary ---
    print(f"\n\nRunning Failure Boundary Sweep (4 arch × 9 fail rates × 3 tasks, n={N})...")
    with redirect_stdout(f_null):
        r_fb = experiment_failure_boundary(N)
    all_output["experiment_failure_boundary"] = r_fb

    print("\n" + "=" * 80)
    print("FAILURE BOUNDARY: Mean Success Rate vs Failure Probability")
    print("=" * 80)

    fail_rates_str = ["10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%"]
    print(f"\n{'Architecture':<26}", end="")
    for fr in fail_rates_str:
        print(f"  {fr:>5}", end="")
    print()
    print("-" * 80)

    for arch_name, fr_data in r_fb.items():
        print(f"{arch_name:<26}", end="")
        for fr in fail_rates_str:
            rate = fr_data[fr]["mean_success_rate"]
            print(f"  {rate:>4}%", end="")
        print()

    _unpatch_sleep()

    # Save
    out_path = os.path.join(os.path.dirname(__file__), "experiment_results_v6.json")
    with open(out_path, "w") as f:
        json.dump(all_output, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
