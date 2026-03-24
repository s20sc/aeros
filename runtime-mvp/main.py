import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import Agent
from eap.loader import load_eap
from eap.registry import list_skills, list_eaps, activate_eap, deactivate_eap, uninstall_eap
from runtime.policy import block_skill, unblock_skill
from runtime.audit import get_log
from runtime.trace import print_trace, export_trace_json, save_trace, generate_mermaid


STATE_ICONS = {
    "installed": "[ ]",
    "activated": "[*]",
    "deactivated": "[-]",
    "uninstalled": "[x]",
}


def print_help():
    print("""
EAPOS Commands:
  <instruction>          Run a task (e.g. "make a dumpling", "pick up the cup")
  install <path>         Install and activate an EAP
  uninstall <eap_id>     Uninstall an EAP
  activate <eap_id>      Activate a deactivated EAP
  deactivate <eap_id>    Deactivate an EAP (skills unregistered)
  list                   List all EAPs with state, skills, and permissions
  block <skill>          Block a skill (operator override)
  unblock <skill>        Unblock a skill
  audit                  Show policy audit log
  trace                  Show last execution trace
  trace json             Export trace as JSON
  trace save             Save trace to JSON file
  trace mermaid          Generate Mermaid flowchart
  help                   Show this message
  exit                   Quit
""")


def print_list():
    eaps = list_eaps()
    if not eaps:
        print("No EAPs installed.\n")
        return

    print("\n=== LOADED EAPS ===\n")
    for eap_id, meta in eaps.items():
        config = meta["config"]
        state = meta["state"]
        icon = STATE_ICONS.get(state, "[?]")
        print(f"{icon} EAP: {eap_id}")
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

    # Auto-load example EAPs
    for name in sorted(os.listdir(examples_dir)):
        eap_path = os.path.join(examples_dir, name)
        if os.path.isdir(eap_path) and os.path.exists(os.path.join(eap_path, "eap.yaml")):
            load_eap(eap_path)

    print("\nEAPOS Runtime v1.0")
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
            load_eap(path)
        elif line.startswith("uninstall "):
            eap_id = line[10:].strip()
            ok, err = uninstall_eap(eap_id)
            if ok:
                print(f"[EAP]      Uninstalled: {eap_id}")
            else:
                print(f"[Error]    {err}")
        elif line.startswith("activate "):
            eap_id = line[9:].strip()
            ok, err = activate_eap(eap_id)
            if ok:
                print(f"[EAP]      Activated: {eap_id}")
            else:
                print(f"[Error]    {err}")
        elif line.startswith("deactivate "):
            eap_id = line[11:].strip()
            ok, err = deactivate_eap(eap_id)
            if ok:
                print(f"[EAP]      Deactivated: {eap_id}")
            else:
                print(f"[Error]    {err}")
        elif line == "audit":
            log = get_log()
            if log:
                print("\nAudit Log:")
                for i, entry in enumerate(log, 1):
                    reason_str = f" reason={entry['reason']}" if entry['reason'] else ""
                    print(f"  {i}. [{entry['time']}] skill={entry['skill']} eap={entry['eap']} decision={entry['decision']}{reason_str}")
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
