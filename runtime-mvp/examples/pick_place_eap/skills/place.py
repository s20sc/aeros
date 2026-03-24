import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot


def run():
    robot.move_to("placement_zone")
    robot.release()
    print("[Skill]    Object placed.")

    return {"status": "success"}
