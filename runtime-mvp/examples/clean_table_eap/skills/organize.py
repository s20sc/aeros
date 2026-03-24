import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot
from runtime.world.context import world


def run():
    print("[Skill]    Organizing items on table...")

    robot.move_arm("plate")
    robot.grasp()
    robot.move_to("shelf")
    robot.release()
    print("[Skill]    Plate shelved.")

    robot.move_arm("cup")
    robot.grasp()
    robot.move_to("rack")
    robot.release()
    print("[Skill]    Cup racked.")

    world.table_organized = True
    print("[Skill]    Table organized.")

    return {"status": "success"}
