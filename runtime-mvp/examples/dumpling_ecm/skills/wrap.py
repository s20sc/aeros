import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.robot.context import robot
from runtime.world.context import world
from runtime.perception.perception import detect_wrapper_alignment, detect_workspace_ready


def run():
    print("[Skill]    Wrapping dumpling...")

    # Perception: check workspace
    if not detect_workspace_ready():
        return {"status": "failure", "reason": "workspace_not_ready"}

    # Perception: check alignment
    if not detect_wrapper_alignment():
        return {"status": "failure", "reason": "wrapper_not_aligned"}

    # Execute wrap
    robot.move_arm("dough")
    robot.grasp()
    robot.move_arm("fold_position")
    print("[Skill]    Folding and sealing...")
    robot.release()

    world.dumpling_wrapped = True
    print("[Skill]    Dumpling wrapped.")

    return {"status": "success"}
