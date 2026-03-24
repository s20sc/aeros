import time
import random


def run():
    print("[Skill]    Placing filling on dough...")
    time.sleep(0.2)

    # Simulate occasional failure (30% chance)
    if random.random() < 0.3:
        print("[Skill]    ERROR: filling leaked during fold")
        return {"status": "failure", "reason": "wrap_integrity_check_failed"}

    print("[Skill]    Folding and sealing...")
    time.sleep(0.2)
    print("[Skill]    Dumpling wrapped.")
    return {"status": "success"}
