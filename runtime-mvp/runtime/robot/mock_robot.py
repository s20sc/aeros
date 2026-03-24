import time
from runtime.robot.robot import Robot
from runtime.world.context import world


class MockRobot(Robot):
    """Simulated robot for development and demo."""

    def __init__(self):
        self.position = "home"
        self.gripper = "open"
        self.holding = None

    def move_arm(self, target):
        print(f"[Robot]    Moving arm to '{target}'...")
        time.sleep(0.3)
        self.position = target
        world.robot_position = target

    def grasp(self):
        print("[Robot]    Grasping...")
        time.sleep(0.2)
        self.gripper = "closed"
        self.holding = self.position
        world.gripper_holding = self.position

    def release(self):
        print("[Robot]    Releasing...")
        time.sleep(0.2)
        self.gripper = "open"
        self.holding = None
        world.gripper_holding = None

    def move_to(self, location):
        print(f"[Robot]    Moving to '{location}'...")
        time.sleep(0.4)
        self.position = location
        world.robot_position = location

    def get_state(self):
        return {
            "position": self.position,
            "gripper": self.gripper,
            "holding": self.holding,
        }
