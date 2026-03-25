#!/usr/bin/env python3
"""
AEROS Extended Experiments
===========================
Two additional experiments to address peer-review feedback:
  4. External Baseline Comparison (Flat Pipeline / BT Fallback / AEROS)
  5. Cross-Task Validation (clean_table with perturbation)

Uses the same infrastructure as experiments.py.
"""

import sys, os, time, random, json, copy, math

sys.path.insert(0, os.path.dirname(__file__))

from experiments import reset_all, load_ecms, count_steps, _patch_sleep, _unpatch_sleep


# ---------------------------------------------------------------------------
# Helpers: Wilson score interval for binomial proportion
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


# ---------------------------------------------------------------------------
# Experiment 4: External Baseline Comparison
# ---------------------------------------------------------------------------

def run_flat_pipeline_trial(seed, fail_rate=0.3):
    """Flat pipeline: call skills in fixed order, no policy check, no retry, no re-plan."""
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from ecm.registry import get_skill
    import runtime.perception.perception as percept_mod

    # Patch failure
    original_detect = percept_mod.detect_wrapper_alignment
    def patched_detect():
        aligned = random.random() > fail_rate
        world.wrapper_aligned = aligned
        return aligned
    percept_mod.detect_wrapper_alignment = patched_detect
    wrap_skill = get_skill("dumpling.wrap")
    if wrap_skill:
        wrap_skill["module"].detect_wrapper_alignment = patched_detect

    # Fixed skill sequence — no planner, just execute in order
    skill_sequence = ["dumpling.prepare", "dumpling.wrap", "dumpling.boil"]

    steps_executed = 0
    for skill_name in skill_sequence:
        skill_entry = get_skill(skill_name)
        if not skill_entry:
            break
        # Direct execution — NO policy check
        result = skill_entry["module"].run()
        steps_executed += 1
        if result is None:
            result = {"status": "success"}
        if result.get("status") != "success":
            break

    success = world.dumpling_cooked
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}

    # Restore
    percept_mod.detect_wrapper_alignment = original_detect
    if wrap_skill:
        wrap_skill["module"].detect_wrapper_alignment = original_detect

    return {
        "success": success,
        "steps": steps_executed,
        "robot_actions": robot_metrics.get("total_actions", 0),
    }


def run_bt_fallback_trial(seed, fail_rate=0.3, max_retries=2):
    """Behavior tree baseline: fixed sequence with fallback (retry) node.
    No re-planning, no recovery action, no policy check."""
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from ecm.registry import get_skill
    import runtime.perception.perception as percept_mod

    # Patch failure
    original_detect = percept_mod.detect_wrapper_alignment
    def patched_detect():
        aligned = random.random() > fail_rate
        world.wrapper_aligned = aligned
        return aligned
    percept_mod.detect_wrapper_alignment = patched_detect
    wrap_skill = get_skill("dumpling.wrap")
    if wrap_skill:
        wrap_skill["module"].detect_wrapper_alignment = patched_detect

    # BT-style: Sequence[ prepare, Fallback[ wrap x max_retries ], boil ]
    skill_sequence = ["dumpling.prepare", "dumpling.wrap", "dumpling.boil"]

    steps_executed = 0
    for skill_name in skill_sequence:
        skill_entry = get_skill(skill_name)
        if not skill_entry:
            break

        if skill_name == "dumpling.wrap":
            # Fallback node: retry up to max_retries
            succeeded = False
            for attempt in range(1, max_retries + 1):
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

    success = world.dumpling_cooked
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}

    # Restore
    percept_mod.detect_wrapper_alignment = original_detect
    if wrap_skill:
        wrap_skill["module"].detect_wrapper_alignment = original_detect

    return {
        "success": success,
        "steps": steps_executed,
        "robot_actions": robot_metrics.get("total_actions", 0),
    }


def run_aeros_full_trial(seed, fail_rate=0.3):
    """AEROS full architecture: re-planning + retry(1) + recovery + policy."""
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from runtime.trace import get_trace
    from ecm.registry import get_skill
    import runtime.perception.perception as percept_mod

    # Patch failure
    original_detect = percept_mod.detect_wrapper_alignment
    def patched_detect():
        aligned = random.random() > fail_rate
        world.wrapper_aligned = aligned
        return aligned
    percept_mod.detect_wrapper_alignment = patched_detect
    wrap_skill = get_skill("dumpling.wrap")
    if wrap_skill:
        wrap_skill["module"].detect_wrapper_alignment = patched_detect

    from agent.agent import Agent
    agent = Agent()
    agent.run("make dumplings")

    trace = get_trace()
    success = world.dumpling_cooked
    total_steps = count_steps(trace)
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}

    # Restore
    percept_mod.detect_wrapper_alignment = original_detect
    if wrap_skill:
        wrap_skill["module"].detect_wrapper_alignment = original_detect

    return {
        "success": success,
        "steps": total_steps,
        "robot_actions": robot_metrics.get("total_actions", 0),
    }


def experiment_4_baseline_comparison(n_trials=100):
    """Experiment 4: External baseline comparison."""
    print("=" * 60)
    print("EXPERIMENT 4: External Baseline Comparison")
    print(f"  Trials per condition: {n_trials}")
    print(f"  Wrap skill failure rate: 30%")
    print("=" * 60)

    FAIL_RATE = 0.3

    configs = [
        ("Flat Pipeline", lambda s: run_flat_pipeline_trial(s, FAIL_RATE)),
        ("BT Fallback (2 retries)", lambda s: run_bt_fallback_trial(s, FAIL_RATE, 2)),
        ("AEROS (full)", lambda s: run_aeros_full_trial(s, FAIL_RATE)),
    ]

    all_results = {}
    for label, run_fn in configs:
        results = []
        for i in range(n_trials):
            seed = 4000 + i
            results.append(run_fn(seed))

        successes = sum(1 for r in results if r["success"])
        avg_steps = sum(r["steps"] for r in results) / len(results)
        avg_actions = sum(r.get("robot_actions", 0) for r in results) / len(results)
        ci = wilson_ci(successes, n_trials)

        summary = {
            "success_rate": round(successes / len(results) * 100, 1),
            "ci_lower": ci[0],
            "ci_upper": ci[1],
            "avg_steps": round(avg_steps, 1),
            "avg_robot_actions": round(avg_actions, 1),
        }
        all_results[label] = summary

    print(f"\n{'Architecture':<25} {'Succ%':>7} {'95% CI':>16} {'Steps':>7} {'Actions':>9}")
    print("-" * 66)
    for label, s in all_results.items():
        print(f"{label:<25} {s['success_rate']:>6}% [{s['ci_lower']:>5},{s['ci_upper']:>5}] {s['avg_steps']:>6} {s['avg_robot_actions']:>8}")
    print()

    return all_results


# ---------------------------------------------------------------------------
# Experiment 5: Cross-Task Validation (clean_table)
# ---------------------------------------------------------------------------

def run_clean_table_static_trial(seed, fail_rate=0.4):
    """Static plan for clean_table: plan once, execute all steps, no retry."""
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from ecm.registry import get_skill
    from runtime.runtime import execute_with_policy
    from runtime.trace import start_trace, add_step, finish_trace, get_trace

    # Patch wipe skill to randomly fail
    wipe_skill = get_skill("clean.wipe")
    original_wipe_run = wipe_skill["module"].run

    def patched_wipe_run():
        if random.random() < fail_rate:
            print("[Skill]    Wipe failed — surface still dirty.")
            return {"status": "failure", "reason": "wipe_incomplete"}
        return original_wipe_run()

    wipe_skill["module"].run = patched_wipe_run

    # Plan once
    plan_entry = get_skill("clean.plan")
    plan_result = execute_with_policy("clean.plan", plan_entry)

    if plan_result.get("status") != "success" or not plan_result.get("task_graph"):
        wipe_skill["module"].run = original_wipe_run
        return {"success": False, "steps": 1, "replan_count": 1}

    steps = plan_result["task_graph"]["steps"]
    start_trace("clean_table_static")

    step_num = 0
    task_failed = False
    for step in steps:
        step_num += 1
        skill_name = step["skill"]
        skill_entry = get_skill(skill_name)
        if not skill_entry:
            task_failed = True
            break

        add_step(f"step_{step_num}", skill_name, "running", attempt=1)
        result = execute_with_policy(skill_name, skill_entry)

        if result.get("status") != "success":
            add_step(f"step_{step_num}", skill_name, "failed",
                     reason=result.get("reason"), attempt=1)
            task_failed = True
            break
        else:
            add_step(f"step_{step_num}", skill_name, "success", attempt=1)

    success = world.table_wiped and world.table_organized and not task_failed
    finish_trace("completed" if success else "aborted")
    total_steps = count_steps(get_trace())
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}

    # Restore
    wipe_skill["module"].run = original_wipe_run

    return {
        "success": success,
        "steps": total_steps,
        "replan_count": 1,
        "robot_actions": robot_metrics.get("total_actions", 0),
    }


def run_clean_table_dynamic_trial(seed, fail_rate=0.4):
    """Dynamic re-planning for clean_table: plan->execute one step->re-plan.
    Uses retry(1) + on_failure for wipe."""
    random.seed(seed)
    reset_all()
    load_ecms()

    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    from runtime.trace import get_trace
    from ecm.registry import get_skill
    import runtime.audit as audit_mod

    # Patch wipe skill to randomly fail
    wipe_skill = get_skill("clean.wipe")
    original_wipe_run = wipe_skill["module"].run

    def patched_wipe_run():
        if random.random() < fail_rate:
            print("[Skill]    Wipe failed — surface still dirty.")
            return {"status": "failure", "reason": "wipe_incomplete"}
        return original_wipe_run()

    wipe_skill["module"].run = patched_wipe_run

    # Patch clean.plan to add retry for wipe step
    plan_skill = get_skill("clean.plan")
    original_plan_run = plan_skill["module"].run

    def patched_plan_run():
        result = original_plan_run()
        if result.get("task_graph") and result["task_graph"].get("steps"):
            for step in result["task_graph"]["steps"]:
                if step.get("skill") == "clean.wipe":
                    step["retry"] = 1
        return result

    plan_skill["module"].run = patched_plan_run

    from agent.agent import Agent
    agent = Agent()
    agent.run("clean table")

    trace = get_trace()
    success = world.table_wiped and world.table_organized
    total_steps = count_steps(trace)
    replan_count = sum(1 for e in audit_mod._log
                       if e["skill"] == "clean.plan" and e["decision"] == "allow")
    robot_metrics = _robot.get_metrics() if hasattr(_robot, 'get_metrics') else {}

    # Restore
    wipe_skill["module"].run = original_wipe_run
    plan_skill["module"].run = original_plan_run

    return {
        "success": success,
        "steps": total_steps,
        "replan_count": replan_count,
        "robot_actions": robot_metrics.get("total_actions", 0),
    }


def experiment_5_cross_task(n_trials=100):
    """Experiment 5: Cross-task validation on clean_table."""
    print("=" * 60)
    print("EXPERIMENT 5: Cross-Task Validation (clean_table)")
    print(f"  Trials per condition: {n_trials}")
    print(f"  Wipe skill failure rate: 40%")
    print("=" * 60)

    static_results = []
    dynamic_results = []

    for i in range(n_trials):
        seed = 5000 + i
        static_results.append(run_clean_table_static_trial(seed))
        dynamic_results.append(run_clean_table_dynamic_trial(seed))

    def summarize(results):
        successes = sum(1 for r in results if r["success"])
        avg_steps = sum(r["steps"] for r in results) / len(results)
        avg_replan = sum(r["replan_count"] for r in results) / len(results)
        avg_actions = sum(r.get("robot_actions", 0) for r in results) / len(results)
        ci = wilson_ci(successes, n_trials)
        return {
            "success_rate": round(successes / len(results) * 100, 1),
            "ci_lower": ci[0],
            "ci_upper": ci[1],
            "avg_steps": round(avg_steps, 1),
            "avg_replan_count": round(avg_replan, 1),
            "avg_robot_actions": round(avg_actions, 1),
        }

    static_summary = summarize(static_results)
    dynamic_summary = summarize(dynamic_results)

    print(f"\n{'Method':<25} {'Succ%':>7} {'95% CI':>16} {'Steps':>7} {'Replan':>8}")
    print("-" * 65)
    print(f"{'Static Plan':<25} {static_summary['success_rate']:>6}% [{static_summary['ci_lower']:>5},{static_summary['ci_upper']:>5}] {static_summary['avg_steps']:>6} {static_summary['avg_replan_count']:>7}")
    print(f"{'Dynamic Re-planning':<25} {dynamic_summary['success_rate']:>6}% [{dynamic_summary['ci_lower']:>5},{dynamic_summary['ci_upper']:>5}] {dynamic_summary['avg_steps']:>6} {dynamic_summary['avg_replan_count']:>7}")
    print()

    return {"static": static_summary, "dynamic": dynamic_summary}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import io
    from contextlib import redirect_stdout

    N_TRIALS = 100
    all_results = {}

    backend = os.environ.get("AEROS_ROBOT", "mock")
    all_results["metadata"] = {
        "robot_backend": backend,
        "n_trials": N_TRIALS,
        "robot_model": "Franka Panda 7-DOF" if backend == "pybullet" else "MockRobot",
        "simulation": "PyBullet" if backend == "pybullet" else "None (mock)",
    }

    _patch_sleep()

    print(f"Running extended experiments (backend={backend}, n={N_TRIALS})...\n")

    f_null = io.StringIO()

    # Experiment 4
    with redirect_stdout(f_null):
        r4 = experiment_4_baseline_comparison(N_TRIALS)
    all_results["experiment_4_baseline"] = r4
    print("=" * 60)
    print("EXPERIMENT 4: External Baseline Comparison")
    print(f"  Trials per condition: {N_TRIALS}, failure rate: 30%")
    print("=" * 60)
    print(f"\n{'Architecture':<25} {'Succ%':>7} {'95% CI':>16} {'Steps':>7} {'Actions':>9}")
    print("-" * 66)
    for label, s in r4.items():
        print(f"{label:<25} {s['success_rate']:>6}% [{s['ci_lower']:>5},{s['ci_upper']:>5}] {s['avg_steps']:>6} {s['avg_robot_actions']:>8}")
    print()

    # Experiment 5
    with redirect_stdout(f_null):
        r5 = experiment_5_cross_task(N_TRIALS)
    all_results["experiment_5_cross_task"] = r5
    print("=" * 60)
    print("EXPERIMENT 5: Cross-Task Validation (clean_table)")
    print(f"  Trials per condition: {N_TRIALS}, wipe failure rate: 40%")
    print("=" * 60)
    print(f"\n{'Method':<25} {'Succ%':>7} {'95% CI':>16} {'Steps':>7} {'Replan':>8}")
    print("-" * 65)
    for label, s in r5.items():
        print(f"{label:<25} {s['success_rate']:>6}% [{s['ci_lower']:>5},{s['ci_upper']:>5}] {s['avg_steps']:>6} {s['avg_replan_count']:>7}")
    print()

    _unpatch_sleep()

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "experiment_results_extended.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
