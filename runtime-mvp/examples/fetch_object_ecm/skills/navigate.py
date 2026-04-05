import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.world.context import world
from runtime.robot.context import robot


def run():
    print("[Skill]    Navigating to target location...")
    robot.move_to("target_location")
    time.sleep(0.2)
    world.robot_at_target = True
    print("[Skill]    Arrived at target location.")
    return {"status": "success"}
