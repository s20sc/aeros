from agent.planner import plan, DIRECT_CHAINS
from eap.registry import get_skill
from runtime.runtime import execute_with_policy
from runtime.trace import start_trace, add_step, finish_trace


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

        # Execute plan skill
        print(f"[Agent]    Dispatching plan skill: {root_skill_name}")

        skill_entry = get_skill(root_skill_name)
        if not skill_entry:
            print(f"[Agent]    Skill not found: {root_skill_name}")
            return

        result = execute_with_policy(root_skill_name, skill_entry)

        if result.get("status") != "success":
            print(f"[Agent]    Plan failed: {result.get('reason')}")
            print("[Agent]    Task aborted.")
            return

        # Execute task graph
        task_graph = result.get("task_graph")
        if task_graph and "steps" in task_graph:
            task_name = task_graph.get("task", "unknown")
            start_trace(task_name)
            print(f"[Agent]    Task graph received: {len(task_graph['steps'])} steps")
            self._execute_graph(task_graph["steps"])
        else:
            print("[Agent]    Task complete.")

    def _execute_step(self, skill_name):
        skill_entry = get_skill(skill_name)
        if not skill_entry:
            print(f"[Agent]    Skill not found: {skill_name}")
            return {"status": "failure", "reason": "skill_not_found"}
        return execute_with_policy(skill_name, skill_entry)

    def _execute_graph(self, steps):
        total = len(steps)

        for i, step in enumerate(steps, 1):
            skill_name = step["skill"] if isinstance(step, dict) else step
            retries = step.get("retry", 0) if isinstance(step, dict) else 0
            fallback = step.get("on_failure") if isinstance(step, dict) else None
            continue_on_recovery = step.get("continue_on_recovery", False) if isinstance(step, dict) else False
            step_id = f"step_{i}"

            print(f"[Agent]    Step {i}/{total}: {skill_name}")

            # Try with retries
            add_step(step_id, skill_name, "running", attempt=1)
            result = self._execute_step(skill_name)
            attempt = 1

            while result.get("status") != "success" and attempt <= retries:
                add_step(step_id, skill_name, "failed", reason=result.get("reason"), attempt=attempt)
                attempt += 1
                reason = result.get("reason", "unknown")
                print(f"[Agent]    Step {i} failed: {reason} — retrying ({attempt}/{retries + 1})")
                add_step(step_id, skill_name, "running", attempt=attempt)
                result = self._execute_step(skill_name)

            # Step succeeded
            if result.get("status") == "success":
                add_step(step_id, skill_name, "success", attempt=attempt)
                continue

            # Step failed after all retries
            add_step(step_id, skill_name, "failed", reason=result.get("reason"), attempt=attempt)
            reason = result.get("reason", "unknown")
            print(f"[Agent]    Step {i} failed after {attempt} attempt(s): {reason}")

            if fallback:
                print(f"[Agent]    Triggering fallback: {fallback}")
                recovery_id = f"{step_id}_recovery"
                add_step(recovery_id, fallback, "running", attempt=1)
                fb_result = self._execute_step(fallback)

                if fb_result.get("status") == "success":
                    add_step(recovery_id, fallback, "success", attempt=1)
                    if continue_on_recovery:
                        print(f"[Agent]    Recovery succeeded — continuing execution.")
                        continue
                    else:
                        print(f"[Agent]    Recovery succeeded — task graph halted (safe stop).")
                        finish_trace("recovered")
                        return
                else:
                    add_step(recovery_id, fallback, "failed", reason=fb_result.get("reason"), attempt=1)
                    print(f"[Agent]    Recovery failed — task graph halted.")
                    finish_trace("aborted")
                    return

            print(f"[Agent]    No fallback defined — task graph halted.")
            finish_trace("aborted")
            return

        print("[Agent]    All steps complete. Task done.")
        finish_trace("completed")
