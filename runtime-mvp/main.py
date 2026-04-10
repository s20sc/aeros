import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import Agent
from ecm.loader import load_ecm
from ecm.registry import list_skills, list_ecms, activate_ecm, deactivate_ecm, uninstall_ecm
from runtime.policy import block_skill, unblock_skill
from runtime.audit import get_log
from runtime.trace import print_trace, export_trace_json, save_trace, generate_mermaid, visualize, set_live_path
from runtime.world.context import world


STATE_ICONS = {
    "installed": "[ ]",
    "activated": "[*]",
    "deactivated": "[-]",
    "uninstalled": "[x]",
}


def print_help():
    print("""
AEROS Commands:
  <instruction>          Run a task (e.g. "make a dumpling", "pick up the cup")
  install <path>         Install and activate an ECM
  uninstall <ecm_id>     Uninstall an ECM
  activate <ecm_id>      Activate a deactivated ECM
  deactivate <ecm_id>    Deactivate an ECM (skills unregistered)
  list                   List all ECMs with state, skills, and permissions
  block <skill>          Block a skill (operator override)
  unblock <skill>        Unblock a skill
  audit                  Show policy audit log
  trace                  Show last execution trace
  trace json             Export trace as JSON
  trace save             Save trace to JSON file
  trace mermaid          Generate Mermaid flowchart
  trace viz              Compact one-line execution graph
  world                  Show current world state
  reset                  Reset world state for fresh demo
  help                   Show this message
  exit                   Quit
""")


def print_list():
    ecms = list_ecms()
    if not ecms:
        print("No ECMs installed.\n")
        return

    print("\n=== LOADED ECMS ===\n")
    for ecm_id, meta in ecms.items():
        config = meta["config"]
        state = meta["state"]
        icon = STATE_ICONS.get(state, "[?]")
        print(f"{icon} ECM: {ecm_id}")
        print(f"    version: {config['version']}")
        print(f"    state:   {state}")
        print(f"    description: {config.get('description', '')}")

        print(f"    skills:")
        for skill in config.get("skills", []):
            active = skill in list_skills()
            status = "(active)" if active else "(inactive)"
            print(f"      - {skill} {status}")

        permissions = meta.get("permissions", {})
        skill_perms = permissions.get("skill_permissions", {})
        if skill_perms:
            print(f"    permissions:")
            for sk, sp in skill_perms.items():
                risk = sp.get("risk_level", "low")
                acts = sp.get("actuators", [])
                print(f"      {sk}: risk={risk}, actuators={acts}")
        print()


def main():
    agent = Agent()
    base = os.path.dirname(__file__)
    examples_dir = os.path.join(base, "examples")

    # Enable live trace for UI
    ui_dir = os.path.join(base, "..", "ui")
    if os.path.isdir(ui_dir):
        set_live_path(os.path.join(ui_dir, "latest_trace.json"))

    # Auto-load example ECMs
    for name in sorted(os.listdir(examples_dir)):
        ecm_path = os.path.join(examples_dir, name)
        if os.path.isdir(ecm_path) and os.path.exists(os.path.join(ecm_path, "ecm.yaml")):
            load_ecm(ecm_path)

    print("\nAEROS Runtime v1.0")
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
            print_list()
        elif line.startswith("install "):
            path = line[8:].strip()
            if not os.path.isdir(path):
                full = os.path.join(examples_dir, path)
                if os.path.isdir(full):
                    path = full
                else:
                    print(f"[Error]    Path not found: {path}")
                    continue
            load_ecm(path)
        elif line.startswith("uninstall "):
            ecm_id = line[10:].strip()
            ok, err = uninstall_ecm(ecm_id)
            if ok:
                print(f"[ECM]      Uninstalled: {ecm_id}")
            else:
                print(f"[Error]    {err}")
        elif line.startswith("activate "):
            ecm_id = line[9:].strip()
            ok, err = activate_ecm(ecm_id)
            if ok:
                print(f"[ECM]      Activated: {ecm_id}")
            else:
                print(f"[Error]    {err}")
        elif line.startswith("deactivate "):
            ecm_id = line[11:].strip()
            ok, err = deactivate_ecm(ecm_id)
            if ok:
                print(f"[ECM]      Deactivated: {ecm_id}")
            else:
                print(f"[Error]    {err}")
        elif line == "audit":
            log = get_log()
            if log:
                print("\nAudit Log:")
                for i, entry in enumerate(log, 1):
                    reason_str = f" reason={entry['reason']}" if entry['reason'] else ""
                    print(f"  {i}. [{entry['time']}] skill={entry['skill']} ecm={entry['ecm']} decision={entry['decision']}{reason_str}")
                print()
            else:
                print("No audit entries yet.\n")
        elif line == "trace":
            print_trace()
        elif line == "trace json":
            j = export_trace_json()
            if j:
                print(j)
        elif line == "trace save":
            save_trace()
        elif line == "trace mermaid":
            m = generate_mermaid()
            if m:
                print(f"\n{m}\n")
        elif line == "trace viz":
            visualize()
        elif line == "world":
            print(f"\n=== WORLD STATE ===")
            for k, v in world.snapshot().items():
                print(f"  {k}: {v}")
            print()
        elif line == "reset":
            world.reset()
            from runtime.robot.context import robot as _robot
            _robot.__init__()
            print("[System]   World state and robot reset.\n")
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
