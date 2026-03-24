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

    def _execute_graph(self, steps):
        total = len(steps)

        for i, step in enumerate(steps, 1):
            skill_name = step["skill"] if isinstance(step, dict) else step
            fallback = step.get("on_failure") if isinstance(step, dict) else None

            print(f"[Agent]    Step {i}/{total}: {skill_name}")

            skill_entry = get_skill(skill_name)
            if not skill_entry:
                print(f"[Agent]    Skill not found: {skill_name}")
                print("[Agent]    Task graph halted.")
                return

            result = execute_with_policy(skill_name, skill_entry)
            status = result.get("status", "success")

            # Step succeeded — continue
            if status == "success":
                continue

            # Step failed — try fallback if available
            if fallback:
                reason = result.get("reason", "unknown")
                print(f"[Agent]    Step {i} failed: {reason}")
                print(f"[Agent]    Triggering fallback: {fallback}")

                fb_entry = get_skill(fallback)
                if not fb_entry:
                    print(f"[Agent]    Fallback skill not found: {fallback}")
                    print("[Agent]    Task graph halted.")
                    return

                fb_result = execute_with_policy(fallback, fb_entry)

                if fb_result.get("status") == "success":
                    print(f"[Agent]    Fallback succeeded — task graph halted (needs replanning).")
                else:
                    print(f"[Agent]    Fallback also failed — task graph halted.")
                return

            # Step failed, no fallback — halt
            reason = result.get("reason", "unknown")
            print(f"[Agent]    Step {i} failed: {reason} — task graph halted.")
            return

        print("[Agent]    All steps complete. Task done.")
