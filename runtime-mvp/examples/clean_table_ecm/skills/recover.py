import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot
from runtime.world.context import world


def run():
    print("[Skill]    Recovery: re-wetting sponge and repositioning...")
    robot.move_arm("sponge_station")
    time.sleep(0.1)
    robot.move_arm("table_surface")
    time.sleep(0.1)
    # Reset wipe state so re-plan will attempt wipe again
    world.table_wiped = False
    print("[Skill]    Recovery complete — ready for re-wipe attempt.")
    return {"status": "success"}
