import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot
from runtime.world.context import world


def run():
    print("[Skill]    Boiling dumpling...")

    if not world.dumpling_wrapped:
        return {"status": "failure", "reason": "no_wrapped_dumpling"}

    robot.move_arm("dumpling")
    robot.grasp()
    robot.move_to("pot")
    robot.release()
    print("[Skill]    Dumpling in pot. Boiling...")
    time.sleep(0.3)

    world.dumpling_cooked = True
    print("[Skill]    Dumpling cooked and ready to serve.")

    return {"status": "success"}
