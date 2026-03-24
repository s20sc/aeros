from agent.planner import plan
from eap.registry import get_skill, make_stub_skill
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

            skill = get_skill(skill_name)

            if not skill:
                # Skill not installed — create stub so runtime can still check policy
                skill = make_stub_skill(skill_name)

            success = execute_with_policy(skill_name, skill)

            if not success:
                print("[Agent]    Task blocked by policy.")
                return

        print("[Agent]    Task complete.")
