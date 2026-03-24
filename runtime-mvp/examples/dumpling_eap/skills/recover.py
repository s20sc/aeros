import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot


def run():
    print("[Skill]    Initiating recovery procedure...")

    robot.release()
    print("[Skill]    Discarding failed dumpling.")

    robot.move_arm("reset_position")
    print("[Skill]    Arm reset to home position.")

    robot.move_to("workspace")
    print("[Skill]    Recovery complete — ready for retry.")

    return {"status": "success"}
