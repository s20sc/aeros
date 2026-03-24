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

            skill = get_skill(skill_name)

            if not skill:
                print(f"[Agent]    Skill not found: {skill_name}")
                continue

            execute_with_policy(skill_name, skill)

        print("[Agent]    Task complete.")
