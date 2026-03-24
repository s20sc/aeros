#!/usr/bin/env python3
"""
EAPOS Evaluation Experiments
=============================
Three experiments to validate the EAPOS architecture:
  1. Dynamic Re-planning vs Static Planning
  2. Retry / Recovery robustness
  3. Policy Enforcement effectiveness

All results are printed as tables and saved to experiments_results.json.
"""

import sys, os, time, random, json, copy

sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Helpers: reset all global state between trials
# ---------------------------------------------------------------------------

def reset_all():
    """Reset world, robot, audit, trace, and registries for a clean trial."""
    from runtime.world.context import world
    from runtime.robot.context import robot as _robot
    import runtime.audit as audit_mod
    import runtime.trace as trace_mod
    import runtime.policy as policy_mod
    import eap.registry as reg_mod

    world.reset()
    _robot.__init__()
    audit_mod._log.clear()
    trace_mod._current_trace = None
    trace_mod._live_path = None
    policy_mod._blocked_skills.clear()

    reg_mod._skill_registry.clear()
    reg_mod._eap_registry.clear()


def _patch_sleep():
    """Replace time.sleep with a no-op to speed up experiments.
    Robot actions simulate delay; for measurement we record logical time."""
    import time as _time
    _time._original_sleep = _time.sleep
    _time.sleep = lambda s: None

def _unpatch_sleep():
    import time as _time
    if hasattr(_time, "_original_sleep"):
        _time.sleep = _time._original_sleep


def load_eaps():
    """Load all example EAPs."""
    from eap.loader import load_eap
    base = os.path.dirname(__file__)
    examples_dir = os.path.join(base, "examples")
    for name in sorted(os.listdir(examples_dir)):
        eap_path = os.path.join(examples_dir, name)
        if os.path.isdir(eap_path) and os.path.exists(os.path.join(eap_path, "eap.yaml")):
            load_eap(eap_path)


# ---------------------------------------------------------------------------
# Experiment 1: Dynamic Re-planning vs Static Planning
# ---------------------------------------------------------------------------

def count_steps(trace):
    """Count total executed skill steps (excluding plan calls) as a proxy for execution cost."""
    if not trace:
        return 0
    return sum(1 for s in trace["steps"] if s["status"] in ("success", "failed"))


def run_dynamic_replan_trial(seed):
    """Run one trial with dynamic re-planning (normal agent behavior)."""
    random.seed(seed)
    reset_all()
    load_eaps()

    from agent.agent import Agent
    from runtime.world.context import world
    from runtime.trace import get_trace

    agent = Agent()
    agent.run("make dumplings")

    trace = get_trace()
    success = world.dumpling_cooked
    total_steps = count_steps(trace)

    # Count replan cycles from audit log (plan calls go through execute_with_policy)
    import runtime.audit as audit_mod
    replan_count = sum(1 for e in audit_mod._log if e["skill"] == "dumpling.plan" and e["decision"] == "allow")

    return {
        "success": success,
        "steps": total_steps,
        "replan_count": replan_count,
    }


def run_static_plan_trial(seed):
    """Run one trial with static planning: generate plan once, execute all steps in order."""
    random.seed(seed)
    reset_all()
    load_eaps()

    from eap.registry import get_skill
    from runtime.runtime import execute_with_policy
    from runtime.world.context import world
    from runtime.trace import start_trace, add_step, finish_trace, get_trace

    # Step 1: call the planner ONCE to get the full plan
    plan_entry = get_skill("dumpling.plan")
    plan_result = execute_with_policy("dumpling.plan", plan_entry)

    if plan_result.get("status") != "success" or not plan_result.get("task_graph"):
        return {"success": False, "steps": 1, "replan_count": 1}

    steps = plan_result["task_graph"]["steps"]
    start_trace("make_dumplings_static")

    # Step 2: execute ALL steps in order, no re-planning, no retry, no recovery
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

    success = world.dumpling_cooked and not task_failed
    finish_trace("completed" if success else "aborted")
    total_steps = count_steps(get_trace())

    return {
        "success": success,
        "steps": total_steps,
        "replan_count": 1,
    }


def experiment_1_replanning(n_trials=50):
    """Experiment 1: Dynamic re-planning vs static planning."""
    print("=" * 60)
    print("EXPERIMENT 1: Dynamic Re-planning vs Static Planning")
    print(f"  Trials per condition: {n_trials}")
    print("=" * 60)

    static_results = []
    dynamic_results = []

    for i in range(n_trials):
        seed = 1000 + i
        static_results.append(run_static_plan_trial(seed))
        dynamic_results.append(run_dynamic_replan_trial(seed))

    def summarize(results):
        successes = sum(1 for r in results if r["success"])
        avg_steps = sum(r["steps"] for r in results) / len(results)
        avg_replan = sum(r["replan_count"] for r in results) / len(results)
        return {
            "success_rate": round(successes / len(results) * 100, 1),
            "avg_steps": round(avg_steps, 1),
            "avg_replan_count": round(avg_replan, 1),
        }

    static_summary = summarize(static_results)
    dynamic_summary = summarize(dynamic_results)

    print(f"\n{'Method':<25} {'Success%':>10} {'Avg Steps':>12} {'Replan Count':>14}")
    print("-" * 63)
    print(f"{'Static Plan':<25} {static_summary['success_rate']:>9}% {static_summary['avg_steps']:>11} {static_summary['avg_replan_count']:>13}")
    print(f"{'Dynamic Re-planning':<25} {dynamic_summary['success_rate']:>9}% {dynamic_summary['avg_steps']:>11} {dynamic_summary['avg_replan_count']:>13}")
    print()

    return {"static": static_summary, "dynamic": dynamic_summary}


# ---------------------------------------------------------------------------
# Experiment 2: Retry / Recovery
# ---------------------------------------------------------------------------

def run_retry_recovery_trial(seed, enable_retry, enable_recovery, fail_rate=0.5):
    """Run one dumpling trial with configurable retry/recovery and failure rate."""
    random.seed(seed)
    reset_all()
    load_eaps()

    from runtime.world.context import world
    from runtime.trace import get_trace
    import runtime.perception.perception as percept_mod

    from eap.registry import get_skill

    # Monkey-patch alignment detection to use custom fail_rate
    # Must patch both the module AND the wrap skill's local reference
    original_detect = percept_mod.detect_wrapper_alignment

    def patched_detect():
        aligned = random.random() > fail_rate
        world.wrapper_aligned = aligned
        return aligned

    percept_mod.detect_wrapper_alignment = patched_detect
    # Also patch in the wrap skill module (it imported at load time)
    wrap_skill = get_skill("dumpling.wrap")
    if wrap_skill:
        wrap_skill["module"].detect_wrapper_alignment = patched_detect

    # Monkey-patch the plan skill to control retry/recovery per condition
    original_plan_skill = get_skill("dumpling.plan")
    original_plan_run = original_plan_skill["module"].run

    def patched_plan_run():
        result = original_plan_run()
        if result.get("task_graph") and result["task_graph"].get("steps"):
            for step in result["task_graph"]["steps"]:
                if step.get("skill") == "dumpling.wrap":
                    step["retry"] = 1 if enable_retry else 0
                    if not enable_recovery:
                        step.pop("on_failure", None)
                        step.pop("continue_on_recovery", None)
        return result

    original_plan_skill["module"].run = patched_plan_run

    from agent.agent import Agent

    agent = Agent()
    agent.run("make dumplings")

    trace = get_trace()
    success = world.dumpling_cooked
    total_steps = count_steps(trace)

    recovery_count = 0
    retry_count = 0
    if trace:
        for s in trace["steps"]:
            if "recovery" in s["id"] and s["status"] == "success":
                recovery_count += 1
            if s["status"] == "failed" and "recovery" not in s["id"]:
                retry_count += 1

    # Restore originals
    original_plan_skill["module"].run = original_plan_run
    percept_mod.detect_wrapper_alignment = original_detect
    if wrap_skill:
        wrap_skill["module"].detect_wrapper_alignment = original_detect

    return {
        "success": success,
        "steps": total_steps,
        "recovery_count": recovery_count,
        "retry_count": retry_count,
    }


def experiment_2_retry_recovery(n_trials=50):
    """Experiment 2: Impact of retry and recovery mechanisms."""
    print("=" * 60)
    print("EXPERIMENT 2: Retry and Recovery Mechanisms")
    print(f"  Trials per condition: {n_trials}")
    FAIL_RATE = 0.5
    print(f"  Wrap skill failure rate: {FAIL_RATE*100:.0f}%")
    print(f"  Retry attempts (when enabled): 1")
    print("=" * 60)

    configs = [
        ("No Retry / No Recovery", False, False),
        ("Retry Only",             True,  False),
        ("Retry + Recovery",       True,  True),
    ]

    all_results = {}
    for label, retry, recovery in configs:
        results = []
        for i in range(n_trials):
            seed = 2000 + i
            results.append(run_retry_recovery_trial(seed, retry, recovery, FAIL_RATE))

        successes = sum(1 for r in results if r["success"])
        avg_steps = sum(r["steps"] for r in results) / len(results)
        avg_recovery = sum(r["recovery_count"] for r in results) / len(results)

        summary = {
            "success_rate": round(successes / len(results) * 100, 1),
            "avg_steps": round(avg_steps, 1),
            "avg_recovery_count": round(avg_recovery, 1),
        }
        all_results[label] = summary

    print(f"\n{'Strategy':<25} {'Success%':>10} {'Avg Steps':>12} {'Avg Recovery':>14}")
    print("-" * 63)
    for label, summary in all_results.items():
        print(f"{label:<25} {summary['success_rate']:>9}% {summary['avg_steps']:>11} {summary['avg_recovery_count']:>13}")
    print()

    return all_results


# ---------------------------------------------------------------------------
# Experiment 3: Policy Enforcement
# ---------------------------------------------------------------------------

def experiment_3_policy(n_trials=50):
    """Experiment 3: Policy enforcement effectiveness."""
    print("=" * 60)
    print("EXPERIMENT 3: Policy Enforcement")
    print(f"  Trials per condition: {n_trials}")
    print("=" * 60)

    # Define test cases: (skill_name, eap_id, should_be_blocked)
    # We test with a mix of valid and invalid requests
    reset_all()
    load_eaps()

    from eap.registry import get_skill, get_eap_permissions, _skill_registry, _eap_registry
    from runtime.policy import check_permission
    from runtime.system_policy import SYSTEM_POLICY

    # Collect all registered skills and their expected validity
    test_cases = []

    # Valid skills (should be allowed)
    valid_skills = [
        ("dumpling.plan", "com.eapos.dumpling"),
        ("dumpling.prepare", "com.eapos.dumpling"),
        ("dumpling.wrap", "com.eapos.dumpling"),
        ("dumpling.boil", "com.eapos.dumpling"),
        ("dumpling.recover", "com.eapos.dumpling"),
        ("clean.plan", "com.eapos.clean_table"),
        ("clean.wipe", "com.eapos.clean_table"),
        ("clean.organize", "com.eapos.clean_table"),
        ("pick_place.detect", "com.eapos.pick_place"),
        ("pick_place.grasp", "com.eapos.pick_place"),
        ("pick_place.place", "com.eapos.pick_place"),
    ]

    # Invalid skills — blocked by policy (high risk, forbidden actuator)
    invalid_skills = [
        ("unsafe.cut", "com.eapos.unsafe"),  # high risk + knife actuator
    ]

    # Cross-EAP violations: skill from wrong EAP (not in allowed_skills)
    cross_eap_violations = [
        ("dumpling.wrap", "com.eapos.clean_table"),
        ("clean.wipe", "com.eapos.dumpling"),
        ("pick_place.grasp", "com.eapos.dumpling"),
        ("dumpling.boil", "com.eapos.pick_place"),
    ]

    # Nonexistent skill requests
    nonexistent_skills = [
        ("fake.skill", "com.eapos.dumpling"),
        ("dumpling.fly", "com.eapos.dumpling"),
    ]

    results_enabled = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "total_time_ms": 0, "checks": 0}
    results_disabled = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "total_time_ms": 0, "checks": 0}

    for trial in range(n_trials):
        random.seed(3000 + trial)

        # Shuffle test cases for each trial
        all_cases = []
        for skill, eap in valid_skills:
            all_cases.append((skill, eap, False))  # should NOT be blocked
        for skill, eap in invalid_skills:
            all_cases.append((skill, eap, True))  # should be blocked
        for skill, eap in cross_eap_violations:
            all_cases.append((skill, eap, True))  # should be blocked
        for skill, eap in nonexistent_skills:
            all_cases.append((skill, eap, True))  # should be blocked

        random.shuffle(all_cases)

        for skill_name, eap_id, should_block in all_cases:
            # --- Policy ENABLED ---
            t0 = time.perf_counter()
            allowed, reason = check_permission(skill_name, eap_id)
            t1 = time.perf_counter()
            elapsed_ms = (t1 - t0) * 1000
            results_enabled["total_time_ms"] += elapsed_ms
            results_enabled["checks"] += 1

            blocked = not allowed
            if should_block and blocked:
                results_enabled["tn"] += 1  # correctly blocked
            elif should_block and not blocked:
                results_enabled["fn"] += 1  # should have blocked but didn't (false acceptance)
            elif not should_block and not blocked:
                results_enabled["tp"] += 1  # correctly allowed
            elif not should_block and blocked:
                results_enabled["fp"] += 1  # incorrectly blocked valid action

            # --- Policy DISABLED (everything allowed) ---
            t0 = time.perf_counter()
            # Simulate: no policy check, just pass through
            t1 = time.perf_counter()
            disabled_elapsed_ms = (t1 - t0) * 1000
            results_disabled["total_time_ms"] += disabled_elapsed_ms
            results_disabled["checks"] += 1

            if should_block:
                results_disabled["fn"] += 1  # false acceptance (no blocking at all)
            else:
                results_disabled["tp"] += 1  # valid action passes

    def compute_metrics(res):
        total_should_block = res["tn"] + res["fn"]
        total_valid = res["tp"] + res["fp"]
        blocking_rate = round(res["tn"] / total_should_block * 100, 1) if total_should_block > 0 else 0
        false_accept = round(res["fn"] / total_should_block * 100, 1) if total_should_block > 0 else 0
        false_reject = round(res["fp"] / total_valid * 100, 1) if total_valid > 0 else 0
        avg_overhead = round(res["total_time_ms"] / res["checks"], 3) if res["checks"] > 0 else 0
        return {
            "blocking_rate": blocking_rate,
            "false_acceptance_rate": false_accept,
            "false_rejection_rate": false_reject,
            "avg_overhead_ms": avg_overhead,
            "total_checks": res["checks"],
        }

    enabled_metrics = compute_metrics(results_enabled)
    disabled_metrics = compute_metrics(results_disabled)

    print(f"\n{'Setting':<20} {'Block%':>8} {'FalseAccept%':>14} {'FalseReject%':>14} {'Overhead(ms)':>14}")
    print("-" * 72)
    print(f"{'Policy Disabled':<20} {disabled_metrics['blocking_rate']:>7}% {disabled_metrics['false_acceptance_rate']:>13}% {disabled_metrics['false_rejection_rate']:>13}% {disabled_metrics['avg_overhead_ms']:>13}")
    print(f"{'Policy Enabled':<20} {enabled_metrics['blocking_rate']:>7}% {enabled_metrics['false_acceptance_rate']:>13}% {enabled_metrics['false_rejection_rate']:>13}% {enabled_metrics['avg_overhead_ms']:>13}")
    print()

    return {"disabled": disabled_metrics, "enabled": enabled_metrics}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import io
    from contextlib import redirect_stdout

    N_TRIALS = 100
    all_results = {}

    # Disable sleep for speed
    _patch_sleep()

    # Suppress verbose per-trial output, only show summaries
    print("Running experiments (suppressing per-trial output)...\n")

    f_null = io.StringIO()

    with redirect_stdout(f_null):
        r1 = experiment_1_replanning(N_TRIALS)
    all_results["experiment_1_replanning"] = r1
    # Print summary
    print("=" * 60)
    print("EXPERIMENT 1: Dynamic Re-planning vs Static Planning")
    print(f"  Trials per condition: {N_TRIALS}")
    print("=" * 60)
    print(f"\n{'Method':<25} {'Success%':>10} {'Avg Steps':>12} {'Replan Count':>14}")
    print("-" * 63)
    print(f"{'Static Plan':<25} {r1['static']['success_rate']:>9}% {r1['static']['avg_steps']:>11} {r1['static']['avg_replan_count']:>13}")
    print(f"{'Dynamic Re-planning':<25} {r1['dynamic']['success_rate']:>9}% {r1['dynamic']['avg_steps']:>11} {r1['dynamic']['avg_replan_count']:>13}")
    print()

    with redirect_stdout(f_null):
        r2 = experiment_2_retry_recovery(N_TRIALS)
    all_results["experiment_2_retry_recovery"] = r2
    print("=" * 60)
    print("EXPERIMENT 2: Retry and Recovery Mechanisms")
    print(f"  Trials per condition: {N_TRIALS}")
    print("=" * 60)
    print(f"\n{'Strategy':<25} {'Success%':>10} {'Avg Steps':>12} {'Avg Recovery':>14}")
    print("-" * 63)
    for label, summary in r2.items():
        print(f"{label:<25} {summary['success_rate']:>9}% {summary['avg_steps']:>11} {summary['avg_recovery_count']:>13}")
    print()

    with redirect_stdout(f_null):
        r3 = experiment_3_policy(N_TRIALS)
    all_results["experiment_3_policy"] = r3
    print("=" * 60)
    print("EXPERIMENT 3: Policy Enforcement")
    print(f"  Trials per condition: {N_TRIALS}")
    print("=" * 60)
    print(f"\n{'Setting':<20} {'Block%':>8} {'FalseAccept%':>14} {'FalseReject%':>14} {'Overhead(ms)':>14}")
    print("-" * 72)
    print(f"{'Policy Disabled':<20} {r3['disabled']['blocking_rate']:>7}% {r3['disabled']['false_acceptance_rate']:>13}% {r3['disabled']['false_rejection_rate']:>13}% {r3['disabled']['avg_overhead_ms']:>13}")
    print(f"{'Policy Enabled':<20} {r3['enabled']['blocking_rate']:>7}% {r3['enabled']['false_acceptance_rate']:>13}% {r3['enabled']['false_rejection_rate']:>13}% {r3['enabled']['avg_overhead_ms']:>13}")
    print()

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "experiment_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
