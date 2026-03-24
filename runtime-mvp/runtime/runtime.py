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
        return {"status": "denied", "reason": reason}

    print("[Runtime]  Permission — OK")
    record(skill_name, eap_id, "allow")
    print(f"[Runtime]  Executing: {skill_name}")

    start = time.time()

    result = None
    if hasattr(skill, "run"):
        result = skill.run()

    elapsed = time.time() - start

    # Normalize result
    if result is None:
        result = {"status": "success"}
    elif not isinstance(result, dict):
        result = {"status": "success"}

    if result.get("status") == "success":
        print(f"[Skill]    {skill_name} — completed ({elapsed:.1f}s)")
    else:
        print(f"[Skill]    {skill_name} — FAILED ({elapsed:.1f}s): {result.get('reason', 'unknown')}")
        record(skill_name, eap_id, "skill_failure", result.get("reason"))

    return result
