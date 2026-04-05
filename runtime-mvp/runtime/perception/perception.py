import random
from runtime.world.context import world


def detect_wrapper_alignment():
    """Simulate vision-based wrapper alignment detection."""
    aligned = random.random() > 0.3  # 70% success
    world.wrapper_aligned = aligned
    print(f"[Percept]  Wrapper alignment check: {'aligned' if aligned else 'NOT aligned'}")
    return aligned


def detect_workspace_ready():
    """Check if workspace has required materials."""
    ready = world.dough_on_workspace and world.filling_on_workspace
    print(f"[Percept]  Workspace ready: {ready} (dough={world.dough_on_workspace}, filling={world.filling_on_workspace})")
    return ready


def detect_grasp_alignment():
    """Simulate vision-based grasp pose estimation for fetch task."""
    aligned = random.random() > 0.35  # 65% success
    print(f"[Percept]  Grasp alignment check: {'aligned' if aligned else 'NOT aligned'}")
    return aligned
