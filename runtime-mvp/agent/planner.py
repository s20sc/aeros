from eap.registry import get_skill


def plan(instruction):
    """Rule-based planner. Maps instructions to skill sequences."""
    instruction = instruction.lower()

    if "dumpling" in instruction:
        return ["dumpling.plan", "dumpling.exec"]
    elif "pick" in instruction:
        return ["pick_place.detect", "pick_place.grasp", "pick_place.place"]
    elif "place" in instruction:
        return ["pick_place.place"]
    elif "cut" in instruction or "knife" in instruction:
        # Dangerous operation — skill exists but should be blocked by policy
        return ["unsafe.cut"]
    elif "sort" in instruction:
        return ["sorting.classify", "sorting.arrange"]
    else:
        return []
