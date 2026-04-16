"""
BallooanceEnv - Gymnasium environment for the Ballooance inflatable robot.

Each of the 8 balloons has 3 discrete states:
    0 = DEFLATE  (target position = 0.0)
    1 = HOLD     (target position = current position, no change)
    2 = INFLATE  (target position = 0.04 m)

Observation space (18 dims):
    [0:3]   core position (x, y, z)
    [3:6]   core linear velocity (vx, vy, vz)
    [6:10]  core orientation quaternion (w, x, y, z)
    [10:13] core angular velocity
    [13:21] balloon expansion states (0.0 ~ 1.0 normalized)

Action space:
    MultiDiscrete([3, 3, 3, 3, 3, 3, 3, 3])
    Each element: 0=deflate, 1=hold, 2=inflate
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco
import os


# Balloon expansion limits (must match MJCF ctrlrange)
BALLOON_MIN = 0.0
BALLOON_MAX = 0.058

# State target positions
STATE_TARGETS = {
    0: BALLOON_MIN,   # DEFLATE
    1: None,          # HOLD (no change)
    2: BALLOON_MAX,   # INFLATE
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/ballooance.xml")


class BallooanceEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(self, render_mode=None, max_episode_steps=1000):
        super().__init__()
        self.render_mode = render_mode
        self.max_episode_steps = max_episode_steps
        self._step_count = 0

        # Load MuJoCo model
        self.model = mujoco.MjModel.from_xml_path(MODEL_PATH)
        self.data  = mujoco.MjData(self.model)

        # Identify actuator indices (act_0 ~ act_7)
        self.n_balloons = 8
        self.actuator_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"act_{i}")
            for i in range(self.n_balloons)
        ]

        # Identify body id for core (used for reward)
        self.core_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "core")

        # ---- Spaces ----
        # Actions: 8 balloons × 3 discrete states
        self.action_space = spaces.MultiDiscrete([3] * self.n_balloons)

        # Observations: pos(3) + vel(3) + quat(4) + angvel(3) + balloon_states(8)
        obs_dim = 3 + 3 + 4 + 3 + self.n_balloons
        self.observation_space = spaces.Box(
            low  = -np.inf,
            high =  np.inf,
            shape = (obs_dim,),
            dtype = np.float32,
        )

        # Renderer (lazy init)
        self._renderer = None

    # ------------------------------------------------------------------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        # Small random perturbation to initial state for robustness
        self.data.qpos[:3] += self.np_random.uniform(-0.005, 0.005, 3)

        mujoco.mj_forward(self.model, self.data)
        self._step_count = 0
        self._prev_x = self.data.xpos[self.core_id, 0]

        return self._get_obs(), {}

    # ------------------------------------------------------------------
    def step(self, action):
        # Apply balloon actions
        for i, a in enumerate(action):
            target = STATE_TARGETS[int(a)]
            if target is not None:
                self.data.ctrl[self.actuator_ids[i]] = target
            # HOLD: leave ctrl unchanged

        # Step physics (multiple substeps per control step for stability)
        for _ in range(10):
            mujoco.mj_step(self.model, self.data)

        obs = self._get_obs()
        reward = self._compute_reward()
        terminated = self._is_terminated()
        truncated  = self._step_count >= self.max_episode_steps

        self._step_count += 1
        self._prev_x = self.data.xpos[self.core_id, 0]

        if self.render_mode == "human":
            self.render()

        return obs, reward, terminated, truncated, {}

    # ------------------------------------------------------------------
    def _get_obs(self):
        core_pos    = self.data.xpos[self.core_id].copy()               # (3,)
        core_vel    = self.data.cvel[self.core_id, 3:6].copy()          # linear vel (3,)
        core_angvel = self.data.cvel[self.core_id, 0:3].copy()          # angular vel (3,)
        core_quat   = self.data.xquat[self.core_id].copy()              # (4,)

        # Balloon expansion: read joint positions, normalize to [0,1]
        balloon_states = np.array([
            self.data.ctrl[self.actuator_ids[i]] / BALLOON_MAX
            for i in range(self.n_balloons)
        ], dtype=np.float32)

        obs = np.concatenate([
            core_pos.astype(np.float32),
            core_vel.astype(np.float32),
            core_quat.astype(np.float32),
            core_angvel.astype(np.float32),
            balloon_states,
        ])
        return obs

    # ------------------------------------------------------------------
    def _compute_reward(self):
        core_x = self.data.xpos[self.core_id, 0]
        core_z = self.data.xpos[self.core_id, 2]

        # Forward progress reward
        forward_reward = (core_x - self._prev_x) / self.model.opt.timestep / 10

        # Penalty for falling over (z too low)
        height_penalty = -5.0 if core_z < 0.05 else 0.0

        # Small energy penalty to encourage efficiency
        energy_penalty = -0.001 * np.sum(np.abs(self.data.ctrl))

        return float(forward_reward + height_penalty + energy_penalty)

    # ------------------------------------------------------------------
    def _is_terminated(self):
        core_z = self.data.xpos[self.core_id, 2]
        return bool(core_z < 0.03)  # Robot has collapsed to ground

    # ------------------------------------------------------------------
    def render(self):
        if self._renderer is None:
            self._renderer = mujoco.Renderer(self.model, height=480, width=640)

        self._renderer.update_scene(self.data, camera="track_core")
        frame = self._renderer.render()

        if self.render_mode == "human":
            import cv2
            cv2.imshow("Ballooance", frame[:, :, ::-1])
            cv2.waitKey(1)
        elif self.render_mode == "rgb_array":
            return frame

    # ------------------------------------------------------------------
    def close(self):
        if self._renderer is not None:
            self._renderer.close()
