import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot


def run():
    print("[Skill]    Preparing dough and filling...")

    robot.move_arm("dough_station")
    robot.grasp()
    print("[Skill]    Picked up dough.")

    robot.move_arm("workspace")
    robot.release()
    print("[Skill]    Dough placed on workspace.")

    robot.move_arm("filling_station")
    robot.grasp()
    print("[Skill]    Picked up filling.")

    robot.move_arm("workspace")
    robot.release()
    print("[Skill]    Filling placed. Ready to wrap.")

    return {"status": "success"}
