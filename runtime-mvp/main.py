import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import Agent
from eap.loader import load_eap
from eap.registry import list_skills, list_eaps
from runtime.policy import block_skill, unblock_skill
from runtime.audit import get_log


def print_help():
    print("""
EAPOS Commands:
  <instruction>        Run a task (e.g. "make a dumpling", "pick up the cup")
  install <path>       Install an EAP from path
  list                 List installed EAPs and skills
  block <skill>        Block a skill (policy deny)
  unblock <skill>      Unblock a skill
  audit                Show policy audit log
  help                 Show this message
  exit                 Quit
""")


def main():
    agent = Agent()
    base = os.path.dirname(__file__)

    # Auto-load example EAPs
    examples_dir = os.path.join(base, "examples")
    for name in sorted(os.listdir(examples_dir)):
        eap_path = os.path.join(examples_dir, name)
        if os.path.isdir(eap_path) and os.path.exists(os.path.join(eap_path, "eap.yaml")):
            load_eap(eap_path)

    print("\nEAPOS Runtime v0.4")
    print('Type "help" for commands\n')

    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        elif line == "exit":
            break
        elif line == "help":
            print_help()
        elif line == "list":
            eaps = list_eaps()
            if eaps:
                print("\nInstalled EAPs:")
                for eap_id, config in eaps.items():
                    print(f"  {eap_id} v{config['version']} — {config.get('description', '')}")
                print(f"\nRegistered skills:")
                for s in list_skills():
                    print(f"  {s}")
                print()
            else:
                print("No EAPs installed.\n")
        elif line.startswith("install "):
            path = line[8:].strip()
            if os.path.isdir(path):
                load_eap(path)
            else:
                full = os.path.join(examples_dir, path)
                if os.path.isdir(full):
                    load_eap(full)
                else:
                    print(f"[Error] Path not found: {path}")
        elif line == "audit":
            log = get_log()
            if log:
                print("\nAudit Log:")
                for entry in log:
                    reason_str = f" reason={entry['reason']}" if entry['reason'] else ""
                    print(f"  [{entry['time']}] skill={entry['skill']} eap={entry['eap']} decision={entry['decision']}{reason_str}")
                print()
            else:
                print("No audit entries yet.\n")
        elif line.startswith("block "):
            skill = line[6:].strip()
            block_skill(skill)
            print(f"[Runtime]  Blocked: {skill}")
        elif line.startswith("unblock "):
            skill = line[8:].strip()
            unblock_skill(skill)
            print(f"[Runtime]  Unblocked: {skill}")
        else:
            agent.run(line)


if __name__ == "__main__":
    main()
