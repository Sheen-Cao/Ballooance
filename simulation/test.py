"""
test.py - 可视化测试脚本
气球尺寸动态变化版本：
  - 半径从 ~29mm (deflated) 连续变化到 ~81mm (inflated)
  - 充/放气速度约 25 秒完成全程
  - 三种状态：INFLATE / HOLD / DEFLATE
运行：python test.py
"""

import mujoco
import mujoco.viewer
import math
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models/ballooance.xml")

# ── 气球物理参数（对应 Grasshopper 模型，单位 m）──────────────────
R_BASE = 0.0211       # 底面圆半径（固定）
D_MIN  = 0.020        # deflate 状态的 d 值
D_MAX  = 0.078        # inflate 状态的 d 值
INFLATE_SECONDS = 60  # 从最小尺寸充气到最大尺寸的时间（秒）
INFLATE_RATE = (D_MAX - D_MIN) / INFLATE_SECONDS  # m/s

def d_to_R(d):
    """根据 d 值计算球半径 R = √(r² + d²)"""
    return math.sqrt(R_BASE**2 + d**2)

# ── 状态常量 ──────────────────────────────────────────────────────
DEFLATE = 0
HOLD    = 1
INFLATE = 2

# ── 步态序列 ──────────────────────────────────────────────────────
# 格式：(持续秒数, [balloon_0~7 的状态])
# Corner mapping:
#   0:(+,+,+)  1:(+,+,-)  2:(+,-,+)  3:(+,-,-)
#   4:(-,+,+)  5:(-,+,-)  6:(-,-,+)  7:(-,-,-)
# 每个阶段：只有2个气球在 INFLATE/DEFLATE，其余全部 HOLD
# 这样可以清楚观察三种状态的区别
# H=HOLD, I=INFLATE, D=DEFLATE
H, I, D = HOLD, INFLATE, DEFLATE
#
# 底部气球 index（含 -z 分量）：
#   1:(+,+,-)   3:(+,-,-)   5:(-,+,-)   7:(-,-,-)
#
# 翻滚策略：充气同侧两个底部气球 → 撑地 → 反作用力推动翻滚
#
GAIT_SEQUENCE = [
    #           0  1  2  3  4  5  6  7
    (80, [H, I, H, H, H, I, H, H]),  # balloon 1 和 3 充气（+x 底部）→ 向 -x 翻滚
    (80, [H, H, H, H, H, H, H, H]),  # 全部 HOLD，观察静止
    (80, [H, D, H, H, H, D, H, H]),  # balloon 1 和 3 放气
]


def run_test():
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data  = mujoco.MjData(model)

    # 获取 8 个气球 geom 和 expand 关节的 ID（用于读取真实 qpos）
    balloon_geom_ids = [
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, f"balloon_{i}_geom")
        for i in range(8)
    ]
    expand_joint_ids = [
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"expand_{i}")
        for i in range(8)
    ]
    qpos_addrs = [model.jnt_qposadr[jid] for jid in expand_joint_ids]

    # 命令侧的"目标"气球量（仅用于驱动 ctrl，不直接驱动 geom）
    balloon_d     = [D_MIN] * 8
    balloon_state = [HOLD]  * 8

    # 初始化 geom 尺寸
    for i, gid in enumerate(balloon_geom_ids):
        model.geom_size[gid, 0] = d_to_R(balloon_d[i])

    print("=" * 55)
    print("Ballooance MuJoCo Viewer")
    print(f"气球半径范围：{d_to_R(D_MIN)*1000:.1f}mm → {d_to_R(D_MAX)*1000:.1f}mm")
    print(f"充/放气速率：{INFLATE_RATE*1000:.2f} mm/s（全程 {INFLATE_SECONDS}s）")
    print("关闭窗口退出")
    print("=" * 55)

    sequence_idx   = 0
    sequence_start = 0.0
    _, init_states = GAIT_SEQUENCE[0]
    balloon_state  = list(init_states)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.azimuth   = 45
        viewer.cam.elevation = -20
        viewer.cam.distance  = 0.8

        step = 0
        while viewer.is_running():
            sim_time = data.time
            dt       = model.opt.timestep

            # ── 切换步态阶段 ────────────────────────────────────
            phase_dur, _ = GAIT_SEQUENCE[sequence_idx]
            if sim_time - sequence_start >= phase_dur:
                sequence_idx   = (sequence_idx + 1) % len(GAIT_SEQUENCE)
                sequence_start = sim_time
                _, new_states  = GAIT_SEQUENCE[sequence_idx]
                balloon_state  = list(new_states)
                print(f"t={sim_time:.1f}s | 切换到阶段 {sequence_idx}")

            # ── 更新命令端 balloon_d，并 ramp 写到 ctrl ──────────
            #   balloon_d 是"目标气量"，ctrl 跟随它移动。
            #   geom_size 不再这里改 —— 改完 mj_step 后再读真实 qpos
            for i in range(8):
                if balloon_state[i] == INFLATE:
                    balloon_d[i] = min(D_MAX, balloon_d[i] + INFLATE_RATE * dt)
                elif balloon_state[i] == DEFLATE:
                    balloon_d[i] = max(D_MIN, balloon_d[i] - INFLATE_RATE * dt)
                # HOLD：不变

                # ctrl 是 slide joint 目标位移（[0, 0.058]）
                data.ctrl[i] = balloon_d[i] - D_MIN

            # ── 推进仿真 ─────────────────────────────────────────
            mujoco.mj_step(model, data)

            # ── 关键修复：用真实 qpos 同步 geom_size ──────────────
            #   如果 slide joint 被地面/邻球顶住没动，geom 也不会鼓出来
            for i in range(8):
                actual_d = data.qpos[qpos_addrs[i]] + D_MIN
                model.geom_size[balloon_geom_ids[i], 0] = d_to_R(actual_d)

            viewer.sync()

            # ── 定时打印状态 ─────────────────────────────────────
            if step % 500 == 0:
                core_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "core")
                pos = data.xpos[core_id]
                radii = [f"{d_to_R(d)*1000:.0f}" for d in balloon_d]
                print(f"t={sim_time:6.1f}s | "
                      f"pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}) | "
                      f"R(mm)={radii}")

            step += 1


if __name__ == "__main__":
    run_test()