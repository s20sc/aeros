import time


def run():
    print("[Skill]    Generating task graph...")
    time.sleep(0.3)

    graph = {
        "task": "make_dumplings",
        "steps": [
            {"skill": "dumpling.prepare"},
            {
                "skill": "dumpling.wrap",
                "retry": 2,
                "on_failure": "dumpling.recover",
                "continue_on_recovery": True,
            },
            {"skill": "dumpling.boil"},
        ]
    }

    print("[Skill]    Task graph:")
    for step in graph["steps"]:
        extras = []
        if step.get("retry"):
            extras.append(f"retry={step['retry']}")
        if step.get("on_failure"):
            extras.append(f"fallback={step['on_failure']}")
        if step.get("continue_on_recovery"):
            extras.append("continue_on_recovery")
        suffix = f" [{', '.join(extras)}]" if extras else ""
        print(f"[Skill]      -> {step['skill']}{suffix}")

    return {"status": "success", "task_graph": graph}
