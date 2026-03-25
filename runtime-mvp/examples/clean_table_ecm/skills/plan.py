import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.world.context import world


def run():
    print("[Planner]  Assessing table state...")
    time.sleep(0.2)

    steps = []

    if not getattr(world, "table_wiped", False):
        steps.append({"skill": "clean.wipe"})
        print("[Planner]  -> clean.wipe (table needs wiping)")

    if not getattr(world, "table_organized", False):
        steps.append({"skill": "clean.organize"})
        print("[Planner]  -> clean.organize (items need organizing)")

    if not steps:
        print("[Planner]  Table is already clean.")

    return {
        "status": "success",
        "task_graph": {
            "task": "clean_table",
            "steps": steps,
        }
    }
