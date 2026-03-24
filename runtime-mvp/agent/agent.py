from agent.planner import plan, DIRECT_CHAINS
from eap.registry import get_skill
from runtime.runtime import execute_with_policy
from runtime.trace import start_trace, add_step, finish_trace
from runtime.world.context import world

MAX_REPLAN_CYCLES = 10


class Agent:

    def run(self, instruction):
        print(f'[Agent]    Received: "{instruction}"')
        print("[Agent]    Planning task...")

        root_skill_name = plan(instruction)

        if not root_skill_name:
            print("[Agent]    No matching skill found.")
            return

        # Direct chain (no plan skill)
        if root_skill_name in DIRECT_CHAINS:
            chain = DIRECT_CHAINS[root_skill_name]
            start_trace(root_skill_name)
            steps = [{"skill": s} for s in chain]
            self._execute_graph(steps)
            return

        # Plan-based: re-planning loop
        self._replan_loop(root_skill_name)

    def _replan_loop(self, plan_skill_name):
        """Execute with re-planning: plan -> execute one step -> re-plan."""
        start_trace("unknown")
        step_counter = 0

        for cycle in range(MAX_REPLAN_CYCLES):
            # Run the plan skill
            print(f"\n[Agent]    === Re-plan cycle {cycle + 1} ===")

            skill_entry = get_skill(plan_skill_name)
            if not skill_entry:
                print(f"[Agent]    Plan skill not found: {plan_skill_name}")
                finish_trace("aborted")
                return

            result = execute_with_policy(plan_skill_name, skill_entry)

            if result.get("status") != "success":
                print(f"[Agent]    Plan failed: {result.get('reason')}")
                finish_trace("aborted")
                return

            task_graph = result.get("task_graph")
            if not task_graph or not task_graph.get("steps"):
                print("[Agent]    Planner returned no steps — task complete.")
                finish_trace("completed")
                return

            # Update trace task name from first plan
            from runtime.trace import _current_trace
            if _current_trace and _current_trace["task"] == "unknown":
                _current_trace["task"] = task_graph.get("task", "unknown")

            steps = task_graph["steps"]
            next_step = steps[0]
            remaining = len(steps)
            print(f"[Agent]    Plan has {remaining} step(s), executing next: {next_step['skill']}")

            # Execute just the first step
            step_counter += 1
            success = self._execute_one_step(next_step, step_counter)

            if not success:
                # Step failed and no recovery succeeded — abort
                print("[Agent]    Step failed — task aborted.")
                finish_trace("aborted")
                return

            # After executing, loop back to re-plan with updated world state

        print("[Agent]    Max re-plan cycles reached — task aborted.")
        finish_trace("aborted")

    def _execute_step(self, skill_name):
        skill_entry = get_skill(skill_name)
        if not skill_entry:
            print(f"[Agent]    Skill not found: {skill_name}")
            return {"status": "failure", "reason": "skill_not_found"}
        return execute_with_policy(skill_name, skill_entry)

    def _execute_one_step(self, step, step_num):
        """Execute a single step with retry + fallback. Returns True if step succeeded."""
        skill_name = step["skill"] if isinstance(step, dict) else step
        retries = step.get("retry", 0) if isinstance(step, dict) else 0
        fallback = step.get("on_failure") if isinstance(step, dict) else None
        continue_on_recovery = step.get("continue_on_recovery", False) if isinstance(step, dict) else False
        step_id = f"step_{step_num}"

        print(f"[Agent]    Executing: {skill_name}")

        # Try with retries
        add_step(step_id, skill_name, "running", attempt=1)
        result = self._execute_step(skill_name)
        attempt = 1

        while result.get("status") != "success" and attempt <= retries:
            add_step(step_id, skill_name, "failed", reason=result.get("reason"), attempt=attempt)
            attempt += 1
            reason = result.get("reason", "unknown")
            print(f"[Agent]    Failed: {reason} — retrying ({attempt}/{retries + 1})")
            add_step(step_id, skill_name, "running", attempt=attempt)
            result = self._execute_step(skill_name)

        if result.get("status") == "success":
            add_step(step_id, skill_name, "success", attempt=attempt, world_state=world.snapshot())
            return True

        # Failed after all retries
        add_step(step_id, skill_name, "failed", reason=result.get("reason"), attempt=attempt, world_state=world.snapshot())
        reason = result.get("reason", "unknown")
        print(f"[Agent]    Failed after {attempt} attempt(s): {reason}")

        if fallback:
            print(f"[Agent]    Triggering fallback: {fallback}")
            recovery_id = f"{step_id}_recovery"
            add_step(recovery_id, fallback, "running", attempt=1)
            fb_result = self._execute_step(fallback)

            if fb_result.get("status") == "success":
                add_step(recovery_id, fallback, "success", attempt=1, world_state=world.snapshot())
                print(f"[Agent]    Recovery succeeded — will re-plan.")
                return True  # Recovery fixed world state, re-plan will adapt
            else:
                add_step(recovery_id, fallback, "failed", reason=fb_result.get("reason"), attempt=1)
                print(f"[Agent]    Recovery failed.")
                return False

        return False

    def _execute_graph(self, steps):
        """Execute a fixed chain of steps (for direct chains without re-planning)."""
        total = len(steps)

        for i, step in enumerate(steps, 1):
            skill_name = step["skill"] if isinstance(step, dict) else step
            step_id = f"step_{i}"

            print(f"[Agent]    Step {i}/{total}: {skill_name}")
            add_step(step_id, skill_name, "running", attempt=1)
            result = self._execute_step(skill_name)

            if result.get("status") == "success":
                add_step(step_id, skill_name, "success", attempt=1, world_state=world.snapshot())
                continue

            add_step(step_id, skill_name, "failed", reason=result.get("reason"), attempt=1, world_state=world.snapshot())
            print(f"[Agent]    Step {i} failed — task graph halted.")
            finish_trace("aborted")
            return

        print("[Agent]    All steps complete. Task done.")
        finish_trace("completed")
