import sys
import os
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot


def run():
    print("[Skill]    Wrapping dumpling...")

    robot.move_arm("dough")
    robot.grasp()

    # Simulate occasional failure (30% chance)
    if random.random() < 0.3:
        robot.release()
        print("[Skill]    ERROR: filling leaked during fold")
        return {"status": "failure", "reason": "wrap_integrity_check_failed"}

    robot.move_arm("fold_position")
    print("[Skill]    Folding and sealing...")
    robot.release()
    print("[Skill]    Dumpling wrapped.")

    return {"status": "success"}
