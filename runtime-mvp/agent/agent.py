from agent.planner import plan, DIRECT_CHAINS
from eap.registry import get_skill
from runtime.runtime import execute_with_policy


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
            steps = [{"skill": s} for s in DIRECT_CHAINS[root_skill_name]]
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
            print(f"[Agent]    Task graph received: {len(task_graph['steps'])} steps")
            self._execute_graph(task_graph["steps"])
        else:
            print("[Agent]    Task complete.")

    def _execute_step(self, skill_name):
        """Execute a single skill. Returns result dict."""
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

            print(f"[Agent]    Step {i}/{total}: {skill_name}")

            # Try execution with retries
            result = self._execute_step(skill_name)
            attempt = 1

            while result.get("status") != "success" and attempt <= retries:
                attempt += 1
                reason = result.get("reason", "unknown")
                print(f"[Agent]    Step {i} failed: {reason} — retrying ({attempt}/{retries + 1})")
                result = self._execute_step(skill_name)

            # Step succeeded
            if result.get("status") == "success":
                continue

            # Step failed after all retries — try fallback
            reason = result.get("reason", "unknown")
            print(f"[Agent]    Step {i} failed after {attempt} attempt(s): {reason}")

            if fallback:
                print(f"[Agent]    Triggering fallback: {fallback}")
                fb_result = self._execute_step(fallback)

                if fb_result.get("status") == "success":
                    if continue_on_recovery:
                        print(f"[Agent]    Recovery succeeded — continuing execution.")
                        continue
                    else:
                        print(f"[Agent]    Recovery succeeded — task graph halted (safe stop).")
                        return
                else:
                    print(f"[Agent]    Recovery failed — task graph halted.")
                    return

            # No fallback — halt
            print(f"[Agent]    No fallback defined — task graph halted.")
            return

        print("[Agent]    All steps complete. Task done.")
