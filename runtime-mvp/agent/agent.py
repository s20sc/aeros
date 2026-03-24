from agent.planner import plan
from eap.registry import get_skill
from runtime.runtime import execute_with_policy


class Agent:

    def run(self, instruction):
        print(f'[Agent]    Received: "{instruction}"')
        print("[Agent]    Planning task...")

        skill_names = plan(instruction)

        if not skill_names:
            print("[Agent]    No matching skill found.")
            return

        for skill_name in skill_names:
            print(f"[Agent]    Dispatching skill: {skill_name}")

            skill_entry = get_skill(skill_name)

            if not skill_entry:
                print(f"[Agent]    Skill not found: {skill_name}")
                print("[Agent]    Task blocked — skill not installed.")
                return

            success = execute_with_policy(skill_name, skill_entry)

            if not success:
                print("[Agent]    Task blocked by policy.")
                return

        print("[Agent]    Task complete.")
