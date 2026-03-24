import time
from runtime.policy import check_permission
from runtime.audit import record


def execute_with_policy(skill_name, skill_entry):
    eap_id = skill_entry["eap_id"]
    skill = skill_entry["module"]

    print(f"[Runtime]  Permission check: {skill_name} (from {eap_id})")

    allowed, reason = check_permission(skill_name, eap_id)

    if not allowed:
        print(f"[Runtime]  DENIED: {skill_name} — {reason}")
        record(skill_name, eap_id, "deny", reason)
        return None

    print("[Runtime]  Permission — OK")
    record(skill_name, eap_id, "allow")
    print(f"[Runtime]  Executing: {skill_name}")

    start = time.time()

    result = None
    if hasattr(skill, "run"):
        result = skill.run()

    elapsed = time.time() - start
    print(f"[Skill]    {skill_name} — completed ({elapsed:.1f}s)")
    return result if result is not None else True
