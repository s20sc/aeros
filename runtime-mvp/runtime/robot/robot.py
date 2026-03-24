class Robot:
    """Abstract robot interface. All robot backends must implement this."""

    def move_arm(self, target):
        raise NotImplementedError

    def grasp(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError

    def move_to(self, location):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError
