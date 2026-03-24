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

        # Check if this is a direct chain (no plan skill)
        if root_skill_name in DIRECT_CHAINS:
            self._execute_chain(DIRECT_CHAINS[root_skill_name])
            return

        # Otherwise: execute the plan skill, expect a task graph back
        print(f"[Agent]    Dispatching plan skill: {root_skill_name}")

        skill_entry = get_skill(root_skill_name)
        if not skill_entry:
            print(f"[Agent]    Skill not found: {root_skill_name}")
            return

        result = execute_with_policy(root_skill_name, skill_entry)

        if result is None:
            print("[Agent]    Task blocked by policy.")
            return

        # If plan returned a task graph, execute it
        if isinstance(result, dict) and "steps" in result:
            steps = [s["skill"] for s in result["steps"]]
            print(f"[Agent]    Task graph received: {len(steps)} steps")
            self._execute_chain(steps)
        else:
            print("[Agent]    Task complete.")

    def _execute_chain(self, skill_names):
        for i, skill_name in enumerate(skill_names, 1):
            print(f"[Agent]    Step {i}/{len(skill_names)}: {skill_name}")

            skill_entry = get_skill(skill_name)

            if not skill_entry:
                print(f"[Agent]    Skill not found: {skill_name}")
                print("[Agent]    Task graph halted.")
                return

            result = execute_with_policy(skill_name, skill_entry)

            if result is None:
                print(f"[Agent]    Step {i} blocked by policy — task graph halted.")
                return

        print("[Agent]    All steps complete. Task done.")
