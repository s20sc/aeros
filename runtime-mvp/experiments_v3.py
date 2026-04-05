#!/usr/bin/env python3
"""
AEROS V3 Experiments — Revised Baseline & Cross-Task Evaluation
================================================================
Addresses reviewer feedback on:
  (1) Weak baselines — now compares AEROS against BehaviorTree.CPP-style
      and ProgPrompt-style execution semantics.
  (2) Narrow task scope — evaluates across 3 structurally different tasks:
      make_dumplings (manipulation), clean_table (manipulation),
      fetch_object (navigation + manipulation).

Experiment 4b: Published-Baseline Comparison (3 architectures × 3 tasks)
Experiment 5b: Cross-Task Generalization (AEROS across 3 tasks)

Uses the same infrastructure as experiments.py.
"""

import sys, os, time, random, json, copy, math, io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(__file__))

from experiments import reset_all, load_ecms, count_steps, _patch_sleep, _unpatch_sleep


# ---------------------------------------------------------------------------
# Wilson score interval
# ---------------------------------------------------------------------------

def wilson_ci(successes, n, z=1.96):
    """95% Wilson score confidence interval for binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denom
    lo = max(0.0, center - margin)
    hi = min(1.0, center + margin)
    return (round(lo * 100, 1), round(hi * 100, 1))


def fisher_exact_p(a, b, c, d):
    """One-sided Fisher's exact test p-value (a+b vs c+d success counts).
    Uses logarithmic computation to avoid overflow."""
    n = a + b + c + d
    def log_factorial(x):
        return sum(math.log(i) for i in range(1, x + 1))

    log_p_cutoff = (log_factorial(a + b) + log_factorial(c + d) +
                    log_factorial(a + c) + log_factorial(b + d) - log_factorial(n))

    p_value = 0.0
    for i in range(a, min(a + b, a + c) + 1):
        j = a + b - i
        k = a + c - i
        l = n - i - j - k
        if j < 0 or k < 0 or l < 0:
            continue
        log_p = (log_factorial(i + j) + log_factorial(k + l) +
                 log_factorial(i + k) + log_factorial(j + l) - log_factorial(n) -
                 log_factorial(i) - log_factorial(j) - log_factorial(k) - log_factorial(l))
        p_value += math.exp(log_p)
    return round(p_value, 6)


# ===========================================================================
# Task Definitions — failure injection configuration
# ===========================================================================

TASK_CONFIGS = {
    "make_dumplings": {
        "instruction": "make dumplings",
        "fail_skill": "dumpling.wrap",
        "fail_rate": 0.30,
        "success_check": lambda w: w.dumpling_cooked,
        "patch_target": "wrapper_alignment",  # perception function to patch
        "flat_sequence": ["dumpling.prepare", "dumpling.wrap", "dumpling.boil"],
    },
    "clean_table": {
        "instruction": "clean table",
        "fail_skill": "clean.wipe",
        "fail_rate": 0.40,
        "success_check": lambda w: w.table_wiped and w.table_organized,
        "patch_target": "wipe_skill",
        "flat_sequence": ["clean.wipe", "clean.organize"],
    },
    "fetch_object": {
        "instruction": "fetch the object",
        "fail_skill": "fetch.grasp",
        "fail_rate": 0.35,
        "success_check": lambda w: w.object_delivered,
        "patch_target": "grasp_alignment",
        "flat_sequence": ["fetch.navigate", "fetch.detect", "fetch.grasp", "fetch.deliver"],
    },
}


# ===========================================================================
# Failure injection helpers
# ===========================================================================

def patch_failure(task_name, fail_rate):
    """Inject stochastic failure for the failable skill. Returns cleanup fn."""
    cfg = TASK_CONFIGS[task_name]
    from ecm.registry import get_skill
    from runtime.world.context import world
    import runtime.perception.perception as percept_mod

    if task_name == "make_dumplings":
        original = percept_mod.detect_wrapper_alignment
        def patched():
            aligned = random.random() > fail_rate
            world.wrapper_aligned = aligned
            return aligned
        percept_mod.detect_wrapper_alignment = patched
        skill = get_skill("dumpling.wrap")
        if skill:
            skill["module"].detect_wrapper_alignment = patched
        def cleanup():
            percept_mod.detect_wrapper_alignment = original
            if skill:
                skill["module"].detect_wrapper_alignment = original
        return cleanup

    elif task_name == "clean_table":
        skill = get_skill("clean.wipe")
        original_run = skill["module"].run
        def patched_run():
            if random.random() < fail_rate:
                return {"status": "failure", "reason": "wipe_incomplete"}
            return original_run()
        skill["module"].run = patched_run
        def cleanup():
            skill["module"].run = original_run
        return cleanup

    elif task_name == "fetch_object":
        original = percept_mod.detect_grasp_alignment
        def patched():
            aligned = random.random() > fail_rate
            return aligned
        percept_mod.detect_grasp_alignment = patched
        skill = get_skill("fetch.grasp")
        if skill:
            skill["module"].detect_grasp_alignment = patched
            # Also patch the perception import inside the module
            skill["module"].perception.detect_grasp_alignment = patched
        def cleanup():
            percept_mod.detect_grasp_alignment = original
            if skill:
                skill["module"].detect_grasp_alignment = original
                skill["module"].perception.detect_grasp_alignment = original
        return cleanup


# ===========================================================================
# Architecture 1: Flat Pipeline (no retry, no re-plan, no policy)
# ===========================================================================

def run_flat_pipeline(seed, task_name):
    """Execute skills in fixed order. Any failure aborts."""
    cfg = TASK_CONFIGS[task_name]
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from ecm.registry import get_skill

    cleanup = patch_failure(task_name, cfg["fail_rate"])

    steps_executed = 0
    for skill_name in cfg["flat_sequence"]:
        skill_entry = get_skill(skill_name)
        if not skill_entry:
            break
        result = skill_entry["module"].run()
        steps_executed += 1
        if result is None:
            result = {"status": "success"}
        if result.get("status") != "success":
            break

    success = cfg["success_check"](world)
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}
    cleanup()

    return {"success": success, "steps": steps_executed,
            "robot_actions": robot_metrics.get("total_actions", 0)}


# ===========================================================================
# Architecture 2: BehaviorTree.CPP-style execution
# ===========================================================================

def run_bt_style(seed, task_name, max_retries=3):
    """BehaviorTree.CPP semantics: Sequence + Retry decorator on failable node.
    Fixed tree structure — no dynamic re-planning, no recovery action.
    Retry count is statically defined in the tree (max_retries)."""
    cfg = TASK_CONFIGS[task_name]
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from ecm.registry import get_skill

    cleanup = patch_failure(task_name, cfg["fail_rate"])

    steps_executed = 0
    fail_skill = cfg["fail_skill"]

    for skill_name in cfg["flat_sequence"]:
        skill_entry = get_skill(skill_name)
        if not skill_entry:
            break

        if skill_name == fail_skill:
            # Retry decorator node: retry up to max_retries
            succeeded = False
            for attempt in range(max_retries):
                result = skill_entry["module"].run()
                steps_executed += 1
                if result is None:
                    result = {"status": "success"}
                if result.get("status") == "success":
                    succeeded = True
                    break
            if not succeeded:
                break
        else:
            result = skill_entry["module"].run()
            steps_executed += 1
            if result is None:
                result = {"status": "success"}
            if result.get("status") != "success":
                break

    success = cfg["success_check"](world)
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}
    cleanup()

    return {"success": success, "steps": steps_executed,
            "robot_actions": robot_metrics.get("total_actions", 0)}


# ===========================================================================
# Architecture 3: ProgPrompt-style execution
# ===========================================================================

def run_progprompt_style(seed, task_name, max_replans=3):
    """ProgPrompt semantics: generate full plan, execute all steps sequentially.
    On failure, regenerate the ENTIRE plan from scratch (no partial re-plan).
    No recovery action, no per-step retry. Limited re-generation budget."""
    cfg = TASK_CONFIGS[task_name]
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from ecm.registry import get_skill
    from runtime.runtime import execute_with_policy

    cleanup = patch_failure(task_name, cfg["fail_rate"])

    steps_executed = 0
    plan_skill_name = cfg["instruction"].split()[0]
    # Derive plan skill from task
    plan_map = {
        "make_dumplings": "dumpling.plan",
        "clean_table": "clean.plan",
        "fetch_object": "fetch.plan",
    }
    plan_skill = plan_map[task_name]

    for replan in range(max_replans):
        # Generate full plan
        skill_entry = get_skill(plan_skill)
        if not skill_entry:
            break
        plan_result = execute_with_policy(plan_skill, skill_entry)
        steps_executed += 1

        if plan_result.get("status") != "success" or not plan_result.get("task_graph"):
            break

        plan_steps = plan_result["task_graph"]["steps"]
        if not plan_steps:
            # No steps means task complete
            break

        # Execute ALL steps in sequence (no partial re-plan)
        plan_failed = False
        for step in plan_steps:
            s_name = step["skill"]
            s_entry = get_skill(s_name)
            if not s_entry:
                plan_failed = True
                break
            result = execute_with_policy(s_name, s_entry)
            steps_executed += 1
            if result.get("status") != "success":
                plan_failed = True
                break

        if not plan_failed:
            break  # Success
        # Otherwise loop back for full re-plan

    success = cfg["success_check"](world)
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}
    cleanup()

    return {"success": success, "steps": steps_executed,
            "robot_actions": robot_metrics.get("total_actions", 0)}


# ===========================================================================
# Architecture 4: AEROS full (re-plan + retry + recovery + policy)
# ===========================================================================

def run_aeros_full(seed, task_name):
    """AEROS architecture: dynamic re-planning, per-step retry, recovery
    actions, and policy enforcement."""
    cfg = TASK_CONFIGS[task_name]
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from runtime.trace import get_trace
    from ecm.registry import get_skill

    cleanup = patch_failure(task_name, cfg["fail_rate"])

    # For clean_table, patch plan to add retry for wipe
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
            def plan_cleanup_fn():
                plan_skill["module"].run = original_plan_run
            plan_cleanup = plan_cleanup_fn

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

    return {"success": success, "steps": total_steps,
            "robot_actions": robot_metrics.get("total_actions", 0)}


# ===========================================================================
# Experiment 4b: Published-Baseline Comparison (4 arch × 3 tasks)
# ===========================================================================

def experiment_4b(n_trials=100):
    """Baseline comparison: Flat Pipeline, BT.CPP-style, ProgPrompt-style, AEROS."""
    architectures = [
        ("Flat Pipeline",   run_flat_pipeline),
        ("BT.CPP (retry=3)", lambda s, t: run_bt_style(s, t, max_retries=3)),
        ("ProgPrompt (replan=3)", lambda s, t: run_progprompt_style(s, t, max_replans=3)),
        ("AEROS (full)",    run_aeros_full),
    ]

    tasks = ["make_dumplings", "clean_table", "fetch_object"]
    results = {}

    for arch_name, run_fn in architectures:
        results[arch_name] = {}
        for task_name in tasks:
            trial_results = []
            for i in range(n_trials):
                seed = 7000 + hash(task_name) % 1000 + i
                trial_results.append(run_fn(seed, task_name))

            successes = sum(1 for r in trial_results if r["success"])
            avg_steps = sum(r["steps"] for r in trial_results) / len(trial_results)
            ci = wilson_ci(successes, n_trials)

            results[arch_name][task_name] = {
                "success_rate": round(successes / n_trials * 100, 1),
                "successes": successes,
                "ci_lower": ci[0],
                "ci_upper": ci[1],
                "avg_steps": round(avg_steps, 1),
            }

    return results


# ===========================================================================
# Experiment 5b: Cross-Task Generalization
# ===========================================================================

def experiment_5b(n_trials=100):
    """Cross-task: AEROS dynamic vs static across 3 tasks."""
    tasks = ["make_dumplings", "clean_table", "fetch_object"]
    results = {}

    for task_name in tasks:
        # Static: plan once, execute all
        static_results = []
        dynamic_results = []

        for i in range(n_trials):
            seed = 8000 + hash(task_name) % 1000 + i

            # Static
            static_results.append(
                run_progprompt_style(seed, task_name, max_replans=1)
            )
            # Dynamic (AEROS)
            dynamic_results.append(
                run_aeros_full(seed, task_name)
            )

        def summarize(trial_list):
            s = sum(1 for r in trial_list if r["success"])
            ci = wilson_ci(s, n_trials)
            return {
                "success_rate": round(s / n_trials * 100, 1),
                "successes": s,
                "ci_lower": ci[0],
                "ci_upper": ci[1],
                "avg_steps": round(sum(r["steps"] for r in trial_list) / n_trials, 1),
            }

        results[task_name] = {
            "static": summarize(static_results),
            "dynamic": summarize(dynamic_results),
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

    # --- Experiment 4b ---
    print(f"Running Experiment 4b: Baseline Comparison (4 arch × 3 tasks, n={N})...")
    with redirect_stdout(f_null):
        r4 = experiment_4b(N)
    all_output["experiment_4b_baseline"] = r4

    print("\n" + "=" * 80)
    print("EXPERIMENT 4b: Published-Baseline Comparison")
    print("=" * 80)

    tasks = ["make_dumplings", "clean_table", "fetch_object"]
    task_short = {"make_dumplings": "Dumpling", "clean_table": "CleanTbl", "fetch_object": "FetchObj"}

    print(f"\n{'Architecture':<26}", end="")
    for t in tasks:
        print(f"  {task_short[t]:>10}", end="")
    print(f"  {'Mean':>8}")
    print("-" * 72)

    for arch_name, task_data in r4.items():
        print(f"{arch_name:<26}", end="")
        rates = []
        for t in tasks:
            rate = task_data[t]["success_rate"]
            rates.append(rate)
            print(f"  {rate:>9}%", end="")
        mean_rate = round(sum(rates) / len(rates), 1)
        print(f"  {mean_rate:>7}%")

    # Print CIs
    print(f"\n{'Architecture':<26}", end="")
    for t in tasks:
        print(f"  {'95% CI':>18}", end="")
    print()
    print("-" * 86)
    for arch_name, task_data in r4.items():
        print(f"{arch_name:<26}", end="")
        for t in tasks:
            d = task_data[t]
            print(f"  [{d['ci_lower']:>5},{d['ci_upper']:>5}]", end="")
        print()

    # Fisher's exact: AEROS vs BT.CPP per task
    print("\nFisher's exact test (AEROS vs BT.CPP):")
    for t in tasks:
        aeros_s = r4["AEROS (full)"][t]["successes"]
        aeros_f = N - aeros_s
        bt_s = r4["BT.CPP (retry=3)"][t]["successes"]
        bt_f = N - bt_s
        p = fisher_exact_p(aeros_s, aeros_f, bt_s, bt_f)
        print(f"  {task_short[t]}: p = {p}")

    # --- Experiment 5b ---
    print(f"\nRunning Experiment 5b: Cross-Task Generalization (n={N})...")
    with redirect_stdout(f_null):
        r5 = experiment_5b(N)
    all_output["experiment_5b_cross_task"] = r5

    print("\n" + "=" * 80)
    print("EXPERIMENT 5b: Cross-Task Generalization (Static vs AEROS Dynamic)")
    print("=" * 80)

    print(f"\n{'Task':<18} {'Static%':>9} {'Static CI':>16} {'Dynamic%':>10} {'Dynamic CI':>16}")
    print("-" * 72)
    for t in tasks:
        s = r5[t]["static"]
        d = r5[t]["dynamic"]
        print(f"{task_short[t]:<18} {s['success_rate']:>8}% [{s['ci_lower']:>5},{s['ci_upper']:>5}]"
              f" {d['success_rate']:>9}% [{d['ci_lower']:>5},{d['ci_upper']:>5}]")

    _unpatch_sleep()

    # Save
    out_path = os.path.join(os.path.dirname(__file__), "experiment_results_v3.json")
    with open(out_path, "w") as f:
        json.dump(all_output, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
