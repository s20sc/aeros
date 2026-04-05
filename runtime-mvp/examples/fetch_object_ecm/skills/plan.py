import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.world.context import world


def run():
    print("[Planner]  Assessing fetch task state...")
    time.sleep(0.2)

    steps = []

    if not getattr(world, "robot_at_target", False):
        steps.append({"skill": "fetch.navigate"})
        print("[Planner]  -> fetch.navigate (robot needs to reach target)")

    if not getattr(world, "object_detected", False):
        steps.append({"skill": "fetch.detect"})
        print("[Planner]  -> fetch.detect (object not yet located)")

    if not getattr(world, "object_grasped", False):
        steps.append({
            "skill": "fetch.grasp",
            "retry": 1,
            "on_failure": "fetch.recover",
        })
        print("[Planner]  -> fetch.grasp (object not yet picked up)")

    if not getattr(world, "object_delivered", False):
        steps.append({"skill": "fetch.deliver"})
        print("[Planner]  -> fetch.deliver (object not yet at goal)")

    if not steps:
        print("[Planner]  Fetch task already complete.")

    return {
        "status": "success",
        "task_graph": {
            "task": "fetch_object",
            "steps": steps,
        }
    }
