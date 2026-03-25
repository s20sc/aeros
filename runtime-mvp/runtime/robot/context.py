import os

ROBOT_BACKEND = os.environ.get("AEROS_ROBOT", "mock")

if ROBOT_BACKEND == "pybullet":
    from runtime.robot.pybullet_robot import PyBulletRobot
    robot = PyBulletRobot(gui=False)
else:
    from runtime.robot.mock_robot import MockRobot
    robot = MockRobot()
