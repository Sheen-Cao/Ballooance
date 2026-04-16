"""
train.py - 强化学习训练入口
算法：PPO (Proximal Policy Optimization)
库：Stable-Baselines3

运行：python train.py
训练结果保存到 ./logs/ 和 ./models/trained/
用 tensorboard --logdir logs 查看训练曲线
"""

import os
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import (
    EvalCallback,
    CheckpointCallback,
    BaseCallback,
)
from stable_baselines3.common.monitor import Monitor
import sys

sys.path.insert(0, os.path.dirname(__file__))
from envs.ballooance_env import BallooanceEnv

# ── 路径配置 ──────────────────────────────────────────────
LOG_DIR        = os.path.join(os.path.dirname(__file__), "logs")
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "models/trained")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# ── 训练超参数 ─────────────────────────────────────────────
N_ENVS        = 4        # 并行环境数量（根据CPU核心数调整）
TOTAL_STEPS   = 500_000  # 总训练步数（初次测试可改小，如50_000）
EVAL_FREQ     = 10_000   # 每隔多少步评估一次
SAVE_FREQ     = 50_000   # 每隔多少步保存一次checkpoint


class ProgressCallback(BaseCallback):
    """打印训练进度"""
    def __init__(self, print_freq=10000):
        super().__init__()
        self.print_freq = print_freq

    def _on_step(self):
        if self.n_calls % self.print_freq == 0:
            print(f"[Step {self.n_calls:>7}] "
                  f"episodes={self.model.ep_info_buffer.__len__()}")
        return True


def make_env():
    env = BallooanceEnv(render_mode=None)
    env = Monitor(env)
    return env


def train():
    print("=" * 60)
    print("Ballooance RL Training — PPO")
    print(f"并行环境: {N_ENVS} | 总步数: {TOTAL_STEPS:,}")
    print("=" * 60)

    # 创建向量化训练环境
    train_env = make_vec_env(make_env, n_envs=N_ENVS)

    # 创建单独的评估环境
    eval_env = make_vec_env(make_env, n_envs=1)

    # PPO 模型
    model = PPO(
        policy         = "MlpPolicy",
        env            = train_env,
        learning_rate  = 3e-4,
        n_steps        = 2048,       # 每次更新收集的步数
        batch_size     = 256,
        n_epochs       = 10,
        gamma          = 0.99,
        gae_lambda     = 0.95,
        clip_range     = 0.2,
        ent_coef       = 0.01,       # 熵奖励，鼓励探索
        verbose        = 1,
        tensorboard_log = LOG_DIR,
        device         = "cpu",      # 换成 "cuda" 如果有GPU
    )

    # 回调函数
    callbacks = [
        EvalCallback(
            eval_env,
            best_model_save_path = os.path.join(CHECKPOINT_DIR, "best"),
            log_path             = LOG_DIR,
            eval_freq            = EVAL_FREQ,
            deterministic        = True,
            render               = False,
        ),
        CheckpointCallback(
            save_freq  = SAVE_FREQ,
            save_path  = CHECKPOINT_DIR,
            name_prefix = "ballooance_ppo",
        ),
        ProgressCallback(print_freq=10000),
    ]

    # 开始训练
    model.learn(
        total_timesteps = TOTAL_STEPS,
        callback        = callbacks,
        tb_log_name     = "PPO_ballooance",
        progress_bar    = True,
    )

    # 保存最终模型
    final_path = os.path.join(CHECKPOINT_DIR, "ballooance_final")
    model.save(final_path)
    print(f"\n训练完成。模型已保存到: {final_path}")
    print(f"查看训练曲线: tensorboard --logdir {LOG_DIR}")


if __name__ == "__main__":
    train()
