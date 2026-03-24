import time


def run():
    print("[Skill]    Generating task graph...")
    time.sleep(0.3)

    graph = {
        "task": "make_dumplings",
        "steps": [
            {"skill": "dumpling.prepare"},
            {"skill": "dumpling.wrap", "on_failure": "dumpling.recover"},
            {"skill": "dumpling.boil"},
        ]
    }

    print("[Skill]    Task graph:")
    for step in graph["steps"]:
        fallback = f" [fallback: {step['on_failure']}]" if "on_failure" in step else ""
        print(f"[Skill]      -> {step['skill']}{fallback}")

    return {"status": "success", "task_graph": graph}
