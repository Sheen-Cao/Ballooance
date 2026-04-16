"""
replay.py - 用训练好的模型跑可视化回放
运行：python scripts/replay.py
"""

import os
import sys
import mujoco
import mujoco.viewer
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from envs.ballooance_env import BallooanceEnv

TRAINED_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "../models/trained/best/best_model.zip"
)


def replay():
    try:
        from stable_baselines3 import PPO
        model = PPO.load(TRAINED_MODEL_PATH)
        print(f"已加载训练模型: {TRAINED_MODEL_PATH}")
    except FileNotFoundError:
        print("未找到训练好的模型，使用随机动作演示...")
        model = None

    env = BallooanceEnv(render_mode="human")
    obs, _ = env.reset()

    print("开始回放，关闭窗口退出...")
    total_reward = 0
    steps = 0

    while True:
        if model is not None:
            action, _ = model.predict(obs, deterministic=True)
        else:
            action = env.action_space.sample()

        obs, reward, terminated, truncated, _ = env.step(action)
        total_reward += reward
        steps += 1

        if terminated or truncated:
            print(f"Episode结束 | 步数: {steps} | 总奖励: {total_reward:.3f}")
            obs, _ = env.reset()
            total_reward = 0
            steps = 0

    env.close()


if __name__ == "__main__":
    replay()
