import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot
from runtime.world.context import world


def run():
    print("[Skill]    Preparing dough and filling...")

    robot.move_arm("dough_station")
    robot.grasp()
    robot.move_arm("workspace")
    robot.release()
    world.dough_on_workspace = True
    print("[Skill]    Dough placed on workspace.")

    robot.move_arm("filling_station")
    robot.grasp()
    robot.move_arm("workspace")
    robot.release()
    world.filling_on_workspace = True
    print("[Skill]    Filling placed. Ready to wrap.")

    return {"status": "success"}
