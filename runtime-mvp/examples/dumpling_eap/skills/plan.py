import time
import json


def run():
    print("[Skill]    Analyzing instruction...")
    time.sleep(0.3)

    task_graph = {
        "task": "make_dumpling",
        "steps": [
            {"id": 1, "action": "prepare_dough", "status": "pending"},
            {"id": 2, "action": "add_filling", "depends_on": 1, "status": "pending"},
            {"id": 3, "action": "wrap", "depends_on": 2, "status": "pending"},
            {"id": 4, "action": "steam", "depends_on": 3, "status": "pending"},
        ]
    }

    print(f"[Skill]    Task graph generated:")
    for step in task_graph["steps"]:
        dep = f" (after step {step['depends_on']})" if "depends_on" in step else ""
        print(f"[Skill]      step {step['id']}: {step['action']}{dep}")
