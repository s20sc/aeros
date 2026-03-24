class WorldState:
    """Observable world state shared across the system."""

    def __init__(self):
        self.robot_position = "home"
        self.gripper_holding = None
        self.dough_on_workspace = False
        self.filling_on_workspace = False
        self.wrapper_aligned = False
        self.dumpling_wrapped = False
        self.dumpling_cooked = False

    def snapshot(self):
        return {
            "robot_position": self.robot_position,
            "gripper_holding": self.gripper_holding,
            "dough_on_workspace": self.dough_on_workspace,
            "filling_on_workspace": self.filling_on_workspace,
            "wrapper_aligned": self.wrapper_aligned,
            "dumpling_wrapped": self.dumpling_wrapped,
            "dumpling_cooked": self.dumpling_cooked,
        }

    def __repr__(self):
        items = ", ".join(f"{k}={v}" for k, v in self.snapshot().items())
        return f"WorldState({items})"
