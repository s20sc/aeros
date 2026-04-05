import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.world.context import world


def run():
    print("[Skill]    Scanning workspace with RGB-D camera...")
    time.sleep(0.2)
    world.object_detected = True
    print("[Skill]    Object detected at (0.42, -0.15, 0.05).")
    return {"status": "success"}
