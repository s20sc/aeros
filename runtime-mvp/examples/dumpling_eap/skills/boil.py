import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot


def run():
    print("[Skill]    Boiling dumpling...")

    robot.move_arm("dumpling")
    robot.grasp()
    print("[Skill]    Picked up dumpling.")

    robot.move_to("pot")
    robot.release()
    print("[Skill]    Dumpling placed in pot. Boiling...")

    import time
    time.sleep(0.3)
    print("[Skill]    Dumpling cooked and ready to serve.")

    return {"status": "success"}
