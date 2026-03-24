def plan(instruction):
    """Rule-based planner. Returns the root skill name (plan skill or direct skill)."""
    instruction = instruction.lower()

    if "dumpling" in instruction:
        return "dumpling.plan"  # returns a task graph
    elif "pick" in instruction:
        return "pick_place.detect"  # first in a direct chain
    elif "place" in instruction:
        return "pick_place.place"
    elif "cut" in instruction or "knife" in instruction:
        return "unsafe.cut"
    else:
        return None


# Direct skill chains (for EAPs without a plan skill)
DIRECT_CHAINS = {
    "pick_place.detect": ["pick_place.detect", "pick_place.grasp", "pick_place.place"],
    "pick_place.place": ["pick_place.place"],
    "unsafe.cut": ["unsafe.cut"],
}
