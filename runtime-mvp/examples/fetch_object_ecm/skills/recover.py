import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.world.context import world
from runtime.robot.context import robot


def run():
    print("[Skill]    Recovery: repositioning arm for re-grasp...")
    robot.move_arm("home")
    time.sleep(0.1)
    robot.move_arm("target_object")
    time.sleep(0.1)
    # Reset grasp state so re-plan will try grasp again
    world.object_grasped = False
    print("[Skill]    Recovery complete — ready for re-grasp attempt.")
    return {"status": "success"}
