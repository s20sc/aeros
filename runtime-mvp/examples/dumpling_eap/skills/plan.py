import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from runtime.world.context import world


def run():
    print("[Planner]  Assessing world state...")
    time.sleep(0.2)

    steps = []

    # Need materials on workspace?
    if not world.dough_on_workspace or not world.filling_on_workspace:
        steps.append({"skill": "dumpling.prepare"})
        print("[Planner]  -> dumpling.prepare (materials needed)")

    # Alignment issue?
    if not world.wrapper_aligned and not world.dumpling_wrapped:
        steps.append({"skill": "dumpling.recover"})
        print("[Planner]  -> dumpling.recover (alignment fix needed)")

    # Need to wrap?
    if not world.dumpling_wrapped:
        steps.append({
            "skill": "dumpling.wrap",
            "retry": 2,
            "on_failure": "dumpling.recover",
            "continue_on_recovery": True,
        })
        print("[Planner]  -> dumpling.wrap (wrapping needed)")

    # Need to cook?
    if not world.dumpling_cooked:
        steps.append({"skill": "dumpling.boil"})
        print("[Planner]  -> dumpling.boil (cooking needed)")

    if not steps:
        print("[Planner]  Nothing to do — task already complete.")
        return {"status": "success", "task_graph": {"task": "make_dumplings", "steps": []}}

    print(f"[Planner]  Dynamic plan: {len(steps)} step(s)")

    return {
        "status": "success",
        "task_graph": {
            "task": "make_dumplings",
            "steps": steps,
        }
    }
