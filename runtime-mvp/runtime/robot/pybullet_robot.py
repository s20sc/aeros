"""
PyBullet Robot Backend — Franka Panda 7-DOF Arm
================================================
Replaces MockRobot with physics-simulated execution.
Runs headless (DIRECT mode) by default for experiments.
Set gui=True for visual debugging.
"""

import time
import math
import pybullet as p
import pybullet_data
from runtime.robot.robot import Robot
from runtime.world.context import world


# Named workspace locations → 3D coordinates (x, y, z)
# Franka Panda base at origin, EE rests at ~(0.09, 0, 0.82)
# Reachable workspace: roughly x=0.2-0.6, y=-0.4-0.4, z=0.3-0.9
LOCATIONS = {
    "home":             (0.3,  0.0,  0.6),
    "dough_station":    (0.4,  0.25, 0.45),
    "filling_station":  (0.4, -0.25, 0.45),
    "workspace":        (0.45, 0.0,  0.4),
    "dough":            (0.45, 0.05, 0.4),
    "fold_position":    (0.4,  0.0,  0.5),
    "dumpling":         (0.45, 0.0,  0.4),
    "pot":              (0.3,  0.35, 0.45),
    "reset_position":   (0.3,  0.0,  0.6),
    "adjust_position":  (0.35, 0.0,  0.5),
    # pick_place locations
    "target_object":    (0.45, -0.2, 0.4),
    "placement_zone":   (0.45,  0.2, 0.4),
    # clean_table locations
    "sponge":           (0.5,  0.0,  0.4),
    "table_surface":    (0.45, 0.0,  0.35),
    "table_edge":       (0.45, 0.25, 0.35),
    "plate":            (0.35, -0.2, 0.4),
    "cup":              (0.35,  0.2, 0.4),
    "shelf":            (0.25, -0.3, 0.5),
    "rack":             (0.25,  0.3, 0.5),
}

# Franka Panda joint indices
ARM_JOINTS = [0, 1, 2, 3, 4, 5, 6]  # 7 revolute joints
FINGER_JOINTS = [9, 10]               # 2 prismatic finger joints
END_EFFECTOR = 8                       # hand joint (better IK target)

FINGER_OPEN = 0.04
FINGER_CLOSED = 0.01


class PyBulletRobot(Robot):
    """Franka Panda robot in PyBullet physics simulation."""

    def __init__(self, gui=False, realtime=False):
        self.gui = gui
        self.realtime = realtime
        self.position = "home"
        self.gripper = "open"
        self.holding = None

        # Counters for metrics (must be before _move_to_position)
        self.total_actions = 0
        self.total_ik_steps = 0
        self.action_log = []

        # Connect
        mode = p.GUI if gui else p.DIRECT
        self.client = p.connect(mode)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81, physicsClientId=self.client)

        # Load scene
        self.plane = p.loadURDF("plane.urdf", physicsClientId=self.client)
        self.robot_id = p.loadURDF(
            "franka_panda/panda.urdf",
            basePosition=[0, 0, 0],
            useFixedBase=True,
            physicsClientId=self.client,
        )

        # Move to home position
        self._move_to_position(LOCATIONS["home"])

    def move_arm(self, target):
        pos = LOCATIONS.get(target)
        if not pos:
            print(f"[Robot]    WARNING: Unknown location '{target}', using home")
            pos = LOCATIONS["home"]

        print(f"[Robot]    Moving arm to '{target}' {pos}...")
        t0 = time.time()

        success = self._move_to_position(pos)

        elapsed = time.time() - t0
        self.position = target
        world.robot_position = target
        self.total_actions += 1
        self.action_log.append({
            "action": "move_arm",
            "target": target,
            "pos": pos,
            "success": success,
            "time": elapsed,
        })

    def grasp(self):
        print("[Robot]    Grasping...")
        t0 = time.time()

        self._set_fingers(FINGER_CLOSED)
        self._step_sim(50)

        elapsed = time.time() - t0
        self.gripper = "closed"
        self.holding = self.position
        world.gripper_holding = self.position
        self.total_actions += 1
        self.action_log.append({
            "action": "grasp",
            "success": True,
            "time": elapsed,
        })

    def release(self):
        print("[Robot]    Releasing...")
        t0 = time.time()

        self._set_fingers(FINGER_OPEN)
        self._step_sim(50)

        elapsed = time.time() - t0
        self.gripper = "open"
        self.holding = None
        world.gripper_holding = None
        self.total_actions += 1
        self.action_log.append({
            "action": "release",
            "success": True,
            "time": elapsed,
        })

    def move_to(self, location):
        # Same as move_arm for a fixed-base manipulator
        self.move_arm(location)

    def get_state(self):
        ee_state = p.getLinkState(self.robot_id, END_EFFECTOR, physicsClientId=self.client)
        ee_pos = ee_state[0]
        return {
            "position": self.position,
            "gripper": self.gripper,
            "holding": self.holding,
            "ee_position": [round(x, 4) for x in ee_pos],
            "total_actions": self.total_actions,
        }

    def get_metrics(self):
        """Return simulation metrics for experiments."""
        return {
            "total_actions": self.total_actions,
            "total_ik_steps": self.total_ik_steps,
            "action_log": self.action_log,
        }

    def shutdown(self):
        p.disconnect(self.client)

    # ---- Internal methods ----

    def _move_to_position(self, target_pos, orientation=None):
        """Move end effector to target position using IK.
        Uses resetJointState for precise positioning (kinematic mode),
        which is standard practice in PyBullet research."""
        if orientation is None:
            orientation = p.getQuaternionFromEuler([math.pi, 0, 0])

        # Iterative IK for better accuracy
        for _ in range(5):
            joint_poses = p.calculateInverseKinematics(
                self.robot_id,
                END_EFFECTOR,
                target_pos,
                targetOrientation=orientation,
                maxNumIterations=1000,
                residualThreshold=1e-7,
                physicsClientId=self.client,
            )

            # Apply joint positions directly
            for i, joint_idx in enumerate(ARM_JOINTS):
                p.resetJointState(self.robot_id, joint_idx, joint_poses[i],
                                  physicsClientId=self.client)

        # Step simulation to settle
        self._step_sim(10)

        # Measure final accuracy
        ee_pos = p.getLinkState(self.robot_id, END_EFFECTOR, physicsClientId=self.client)[0]
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(ee_pos, target_pos)))
        return dist < 0.05

    def _set_fingers(self, width):
        """Set gripper finger width."""
        for joint_idx in FINGER_JOINTS:
            p.setJointMotorControl2(
                self.robot_id,
                joint_idx,
                p.POSITION_CONTROL,
                targetPosition=width,
                force=20,
                physicsClientId=self.client,
            )

    def _step_sim(self, steps):
        """Step simulation forward."""
        for _ in range(steps):
            p.stepSimulation(physicsClientId=self.client)
            self.total_ik_steps += 1
            if self.realtime:
                time.sleep(1.0 / 240.0)
