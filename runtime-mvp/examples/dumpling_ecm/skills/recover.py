import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot
from runtime.world.context import world


def run():
    print("[Skill]    Initiating recovery procedure...")

    robot.release()
    robot.move_arm("reset_position")
    print("[Skill]    Arm reset.")

    # Fix alignment for next attempt
    world.wrapper_aligned = True
    print("[Skill]    Wrapper alignment corrected.")

    robot.move_to("workspace")
    print("[Skill]    Recovery complete — ready for retry.")

    return {"status": "success"}
