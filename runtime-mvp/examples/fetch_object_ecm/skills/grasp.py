import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.world.context import world
from runtime.robot.context import robot
import runtime.perception.perception as perception


def run():
    print("[Skill]    Computing grasp pose for detected object...")
    time.sleep(0.1)

    # Check grasp alignment (uses perception — can fail stochastically)
    aligned = perception.detect_grasp_alignment()

    if not aligned:
        print("[Skill]    Grasp alignment failed — object slipped.")
        return {"status": "failure", "reason": "grasp_alignment_failed"}

    robot.move_arm("target_object")
    robot.grasp()
    world.object_grasped = True
    print("[Skill]    Object grasped successfully.")
    return {"status": "success"}
