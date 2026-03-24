class WorldState:
    """Observable world state shared across the system."""

    def __init__(self):
        # Robot
        self.robot_position = "home"
        self.gripper_holding = None

        # Dumpling task
        self.dough_on_workspace = False
        self.filling_on_workspace = False
        self.wrapper_aligned = False
        self.dumpling_wrapped = False
        self.dumpling_cooked = False

        # Clean table task
        self.table_wiped = False
        self.table_organized = False

    def snapshot(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def __repr__(self):
        items = ", ".join(f"{k}={v}" for k, v in self.snapshot().items())
        return f"WorldState({items})"
