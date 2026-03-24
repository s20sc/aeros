import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot


def run():
    print("[Skill]    Computing grasp pose...")

    robot.move_arm("target_object")
    robot.grasp()
    print("[Skill]    Object secured.")

    return {"status": "success"}
