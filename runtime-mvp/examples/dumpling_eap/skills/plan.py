import time


def run():
    print("[Skill]    Generating task graph...")
    time.sleep(0.3)

    graph = {
        "task": "make_dumplings",
        "steps": [
            {"skill": "dumpling.prepare", "depends_on": None},
            {"skill": "dumpling.wrap", "depends_on": "dumpling.prepare"},
            {"skill": "dumpling.boil", "depends_on": "dumpling.wrap"},
        ]
    }

    print(f"[Skill]    Task graph:")
    for step in graph["steps"]:
        dep = f" (after {step['depends_on']})" if step["depends_on"] else ""
        print(f"[Skill]      -> {step['skill']}{dep}")

    return graph
