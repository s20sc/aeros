import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.world.context import world
from runtime.robot.context import robot


def run():
    print("[Skill]    Navigating to delivery zone...")
    robot.move_to("delivery_zone")
    time.sleep(0.2)
    robot.release()
    world.object_delivered = True
    print("[Skill]    Object delivered successfully.")
    return {"status": "success"}
