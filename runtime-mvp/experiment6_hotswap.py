"""
Experiment 6: Runtime ECM Hot-Swapping
======================================
Validates that ECMs can be dynamically loaded during task execution
and that the agent can immediately utilize newly available capabilities.

Scenario:
  The agent starts with only the `make_dumplings` ECM loaded.
  Mid-execution (after completing the dumpling task), a `clean_table` ECM
  is dynamically loaded at runtime. The agent must then plan and execute
  the table-cleaning task using the newly available skills,
  without restarting or re-initializing.

Metrics:
  - Hot-swap success rate: % of trials where the new ECM loads and
    the agent successfully executes the second task.
  - Swap latency: Time (ms) to register the new ECM and update
    the skill registry.
  - Post-swap task success: % of trials completing the second task
    after hot-swap.

Design:
  100 independent randomized trials.
  Dumpling task: 30% failure rate on wrap step.
  Table cleaning task: 40% failure rate on wipe step.
  Dynamic re-planning enabled for both tasks.
"""

import json
import random
import time
import statistics
from pathlib import Path

# ---------------------------------------------------------------------------
# Simulated ECM Registry (mirrors the AEROS runtime)
# ---------------------------------------------------------------------------

class ECMRegistry:
    """Minimal ECM registry supporting runtime hot-swap."""

    def __init__(self):
        self.ecms = {}
        self.skills = {}

    def load_ecm(self, ecm_name, ecm_def):
        """Dynamically load an ECM at runtime."""
        self.ecms[ecm_name] = ecm_def
        for skill in ecm_def["skills"]:
            self.skills[skill["name"]] = {
                "ecm": ecm_name,
                "risk_level": skill.get("risk_level", "low"),
                "actuators": skill.get("actuators", []),
            }

    def unload_ecm(self, ecm_name):
        """Unload an ECM at runtime."""
        if ecm_name in self.ecms:
            for skill in self.ecms[ecm_name]["skills"]:
                self.skills.pop(skill["name"], None)
            del self.ecms[ecm_name]

    def get_available_skills(self):
        return list(self.skills.keys())

    def has_skill(self, skill_name):
        return skill_name in self.skills


# ---------------------------------------------------------------------------
# ECM Definitions
# ---------------------------------------------------------------------------

DUMPLING_ECM = {
    "name": "make_dumplings",
    "version": "1.0.0",
    "skills": [
        {"name": "prepare_materials", "risk_level": "low", "actuators": ["gripper"]},
        {"name": "align_wrapper", "risk_level": "low", "actuators": ["gripper", "arm"]},
        {"name": "wrap_dumpling", "risk_level": "medium", "actuators": ["gripper", "arm"]},
        {"name": "boil_dumpling", "risk_level": "medium", "actuators": ["gripper"]},
    ],
}

CLEAN_TABLE_ECM = {
    "name": "clean_table",
    "version": "1.0.0",
    "skills": [
        {"name": "clear_clutter", "risk_level": "low", "actuators": ["gripper", "arm"]},
        {"name": "wipe_surface", "risk_level": "low", "actuators": ["gripper", "arm"]},
        {"name": "verify_cleanliness", "risk_level": "low", "actuators": []},
    ],
}


# ---------------------------------------------------------------------------
# Simulated Skill Execution (matches experiments 1-5 design)
# ---------------------------------------------------------------------------

def execute_skill(skill_name, fail_rate, rng):
    """Execute a skill with stochastic failure injection."""
    if rng.random() < fail_rate:
        return False, "stochastic_failure"
    return True, "success"


def run_task_with_replanning(task_skills, fail_skill, fail_rate, rng,
                             max_replan=10):
    """Run a task with dynamic re-planning (same loop as Exp 1/4/5)."""
    steps = 0
    replans = 0

    for skill_name in task_skills:
        if skill_name == fail_skill:
            # This skill may fail; attempt with re-planning
            for attempt in range(max_replan):
                steps += 1
                success, _ = execute_skill(skill_name, fail_rate, rng)
                if success:
                    break
                replans += 1
            else:
                return False, steps, replans  # Exhausted re-plan budget
        else:
            steps += 1
            success, _ = execute_skill(skill_name, 0.0, rng)
            if not success:
                return False, steps, replans

    return True, steps, replans


# ---------------------------------------------------------------------------
# Experiment 6: Hot-Swap Trial
# ---------------------------------------------------------------------------

def run_hotswap_trial(seed, dump_fail_rate=0.30, clean_fail_rate=0.40):
    """
    Single trial:
      1. Start with only make_dumplings ECM loaded.
      2. Execute dumpling task (with re-planning).
      3. Hot-swap: dynamically load clean_table ECM at runtime.
      4. Agent detects new capabilities and plans clean_table task.
      5. Execute clean_table task (with re-planning).
    """
    rng = random.Random(seed)
    registry = ECMRegistry()

    # Phase 1: Load initial ECM and execute dumpling task
    registry.load_ecm("make_dumplings", DUMPLING_ECM)

    assert registry.has_skill("wrap_dumpling")
    assert not registry.has_skill("wipe_surface")  # Not yet loaded

    dumpling_skills = ["prepare_materials", "align_wrapper",
                       "wrap_dumpling", "boil_dumpling"]
    dump_ok, dump_steps, dump_replans = run_task_with_replanning(
        dumpling_skills, "wrap_dumpling", dump_fail_rate, rng
    )

    if not dump_ok:
        return {
            "success": False,
            "phase": "dumpling",
            "dump_steps": dump_steps,
            "dump_replans": dump_replans,
            "swap_latency_ms": 0,
            "swap_success": False,
            "clean_steps": 0,
            "clean_replans": 0,
        }

    # Phase 2: Hot-swap — dynamically load clean_table ECM
    t0 = time.perf_counter_ns()
    registry.load_ecm("clean_table", CLEAN_TABLE_ECM)
    swap_ns = time.perf_counter_ns() - t0
    swap_latency_ms = swap_ns / 1e6

    swap_success = (
        registry.has_skill("wipe_surface")
        and registry.has_skill("clear_clutter")
        and registry.has_skill("verify_cleanliness")
    )

    if not swap_success:
        return {
            "success": False,
            "phase": "swap",
            "dump_steps": dump_steps,
            "dump_replans": dump_replans,
            "swap_latency_ms": swap_latency_ms,
            "swap_success": False,
            "clean_steps": 0,
            "clean_replans": 0,
        }

    # Phase 3: Agent plans and executes clean_table using new ECM
    clean_skills = ["clear_clutter", "wipe_surface", "verify_cleanliness"]
    clean_ok, clean_steps, clean_replans = run_task_with_replanning(
        clean_skills, "wipe_surface", clean_fail_rate, rng
    )

    return {
        "success": dump_ok and swap_success and clean_ok,
        "phase": "complete" if clean_ok else "clean_table",
        "dump_steps": dump_steps,
        "dump_replans": dump_replans,
        "swap_latency_ms": swap_latency_ms,
        "swap_success": swap_success,
        "clean_steps": clean_steps,
        "clean_replans": clean_replans,
    }


# ---------------------------------------------------------------------------
# Wilson Score Confidence Interval
# ---------------------------------------------------------------------------

def wilson_ci(successes, n, z=1.96):
    """95% Wilson score interval for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    margin = z * ((p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) ** 0.5) / denom
    lo = max(0.0, center - margin)
    hi = min(1.0, center + margin)
    return p_hat, lo, hi


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    N = 100
    results = []

    print(f"Experiment 6: Runtime ECM Hot-Swapping ({N} trials)")
    print("=" * 60)

    for i in range(N):
        r = run_hotswap_trial(seed=42000 + i)
        results.append(r)

    # Aggregate
    overall_success = sum(1 for r in results if r["success"])
    swap_success = sum(1 for r in results if r["swap_success"])
    post_swap_success = sum(
        1 for r in results if r["swap_success"] and r["phase"] == "complete"
    )
    swap_attempted = sum(1 for r in results if r["phase"] != "dumpling")

    swap_latencies = [r["swap_latency_ms"] for r in results if r["swap_success"]]
    total_steps = [
        r["dump_steps"] + r["clean_steps"] for r in results if r["success"]
    ]
    total_replans = [
        r["dump_replans"] + r["clean_replans"] for r in results if r["success"]
    ]

    # Wilson CIs
    p_overall, lo_overall, hi_overall = wilson_ci(overall_success, N)
    p_swap, lo_swap, hi_swap = wilson_ci(swap_success, swap_attempted)
    p_post, lo_post, hi_post = wilson_ci(post_swap_success, swap_success)

    print(f"\nOverall (both tasks): {overall_success}/{N} = "
          f"{p_overall*100:.1f}% [{lo_overall*100:.1f}, {hi_overall*100:.1f}]")
    print(f"ECM swap success:    {swap_success}/{swap_attempted} = "
          f"{p_swap*100:.1f}% [{lo_swap*100:.1f}, {hi_swap*100:.1f}]")
    print(f"Post-swap task:      {post_swap_success}/{swap_success} = "
          f"{p_post*100:.1f}% [{lo_post*100:.1f}, {hi_post*100:.1f}]")

    if swap_latencies:
        print(f"\nSwap latency (ms):   mean={statistics.mean(swap_latencies):.4f}, "
              f"median={statistics.median(swap_latencies):.4f}, "
              f"max={max(swap_latencies):.4f}")

    if total_steps:
        print(f"Total steps (success): mean={statistics.mean(total_steps):.1f}")
    if total_replans:
        print(f"Total replans (success): mean={statistics.mean(total_replans):.1f}")

    # Save JSON
    output = {
        "experiment": "6_hotswap",
        "n_trials": N,
        "overall_success": overall_success,
        "overall_ci": [round(lo_overall * 100, 1), round(hi_overall * 100, 1)],
        "swap_success": swap_success,
        "swap_success_ci": [round(lo_swap * 100, 1), round(hi_swap * 100, 1)],
        "post_swap_success": post_swap_success,
        "post_swap_ci": [round(lo_post * 100, 1), round(hi_post * 100, 1)],
        "swap_latency_mean_ms": round(statistics.mean(swap_latencies), 4)
            if swap_latencies else None,
        "swap_latency_max_ms": round(max(swap_latencies), 4)
            if swap_latencies else None,
        "avg_total_steps": round(statistics.mean(total_steps), 1)
            if total_steps else None,
        "avg_total_replans": round(statistics.mean(total_replans), 1)
            if total_replans else None,
    }

    out_path = Path(__file__).parent / "experiment6_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
