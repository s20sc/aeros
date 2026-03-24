import time
from runtime.policy import check_permission


def execute_with_policy(skill_name, skill):
    print(f"[Runtime]  Permission check: {skill_name}")

    if not check_permission(skill_name):
        print(f"[Runtime]  DENIED: {skill_name}")
        return

    print("[Runtime]  Permission — OK")
    print(f"[Runtime]  Executing: {skill_name}")

    start = time.time()

    if hasattr(skill, "run"):
        skill.run()

    elapsed = time.time() - start
    print(f"[Skill]    {skill_name} — completed ({elapsed:.1f}s)")
