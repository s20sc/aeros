import time
from runtime.policy import check_permission


def execute_with_policy(skill_name, skill_entry):
    eap_id = skill_entry["eap_id"]
    skill = skill_entry["module"]

    print(f"[Runtime]  Permission check: {skill_name} (from {eap_id})")

    allowed, reason = check_permission(skill_name, eap_id)

    if not allowed:
        print(f"[Runtime]  DENIED: {skill_name} — {reason}")
        return False

    print("[Runtime]  Permission — OK")
    print(f"[Runtime]  Executing: {skill_name}")

    start = time.time()

    if hasattr(skill, "run"):
        skill.run()

    elapsed = time.time() - start
    print(f"[Skill]    {skill_name} — completed ({elapsed:.1f}s)")
    return True
