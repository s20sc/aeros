def plan(instruction):
    """Rule-based planner. Maps instructions to skill sequences."""
    instruction = instruction.lower()

    if "dumpling" in instruction:
        return ["dumpling.plan", "dumpling.exec"]
    elif "pick" in instruction or "place" in instruction:
        return ["pick.place"]
    else:
        return []
