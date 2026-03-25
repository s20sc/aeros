import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot
from runtime.world.context import world


def run():
    print("[Skill]    Wiping table surface...")

    robot.move_arm("sponge")
    robot.grasp()
    robot.move_arm("table_surface")
    print("[Skill]    Scrubbing...")
    robot.move_arm("table_edge")
    robot.release()

    world.table_wiped = True
    print("[Skill]    Table surface clean.")

    return {"status": "success"}
