"""
interactive.py - 实时串口/键盘控制仿真

支持两种输入方式：
  1. 键盘输入（默认）：在终端输入命令，回车发送
  2. 串口输入：连接 Arduino 等设备，自动接收命令

命令格式：8个字符，每个字符对应一个 balloon
  I = INFLATE   （充气）
  D = DEFLATE   （放气）
  H = HOLD      （保持）

示例命令：
  HIHHHHHH   → 只有 balloon_1 充气
  IDIDIDIDID → 奇偶交替充放气
  DDDDDDDD   → 全部放气
  HHHHHHHH   → 全部保持

Corner mapping：
  0:(+,+,+)  1:(+,+,-)  2:(+,-,+)  3:(+,-,-)
  4:(-,+,+)  5:(-,+,-)  6:(-,-,+)  7:(-,-,-)

底部（含-z）：1, 3, 5, 7
顶部（含+z）：0, 2, 4, 6

运行方式：
  键盘模式：python scripts/interactive.py
  串口模式：python scripts/interactive.py --port COM3 --baud 9600
"""

import mujoco
import mujoco.viewer
import math
import os
import sys
import threading
import argparse
import time

# ── 路径 ────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/ballooance.xml")

# ── 气球物理参数 ─────────────────────────────────────────────────────
R_BASE         = 0.0211
D_MIN          = 0.020
D_MAX          = 0.078
INFLATE_SECONDS = 60
INFLATE_RATE   = (D_MAX - D_MIN) / INFLATE_SECONDS

def d_to_R(d):
    return math.sqrt(R_BASE**2 + d**2)

DEFLATE, HOLD, INFLATE = 0, 1, 2
CHAR_MAP = {'I': INFLATE, 'D': DEFLATE, 'H': HOLD,
            'i': INFLATE, 'd': DEFLATE, 'h': HOLD}

# ── 共享状态（线程间通信） ─────────────────────────────────────────
balloon_state = [HOLD] * 8
state_lock    = threading.Lock()


def parse_command(cmd: str) -> list | None:
    """
    解析命令字符串，返回 8 个状态值，或 None（命令无效）
    """
    cmd = cmd.strip().upper()
    if len(cmd) != 8:
        return None
    states = []
    for c in cmd:
        if c not in ('I', 'D', 'H'):
            return None
        states.append(CHAR_MAP[c])
    return states


# ────────────────────────────────────────────────────────────────────
# 输入线程：键盘
# ────────────────────────────────────────────────────────────────────
def keyboard_thread():
    print("\n[控制台] 键盘模式启动")
    print("[控制台] 输入8字符命令（I=充气 D=放气 H=保持），回车发送")
    print("[控制台] 示例：HIHHHHHH  DDDDDDDD  IIIIDDDD\n")

    # 预设快捷命令
    shortcuts = {
        'HOLD': 'HHHHHHHH',
        'ALL_IN': 'IIIIIIII',
        'ALL_DE': 'DDDDDDDD',
        'ROLL_X': 'HHIIHHII',   # +x侧底部充气
        'ROLL_Y': 'HIHHIHHI',   # +y侧充气
        'BOT_IN': 'HIHIHIHI',   # 底部4个充气
        'TOP_IN': 'IHIHIHIH',   # 顶部4个充气
    }

    print("[控制台] 快捷指令：", list(shortcuts.keys()), "\n")

    while True:
        try:
            raw = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not raw:
            continue

        # 快捷指令
        cmd = shortcuts.get(raw.upper(), raw)

        states = parse_command(cmd)
        if states is None:
            print(f"  ✗ 无效命令「{raw}」，需要8个字符，每个为 I/D/H")
            continue

        with state_lock:
            for i, s in enumerate(states):
                balloon_state[i] = s

        labels = {INFLATE: 'I', DEFLATE: 'D', HOLD: 'H'}
        print(f"  ✓ 已应用：{''.join(labels[s] for s in states)}")


# ────────────────────────────────────────────────────────────────────
# 输入线程：串口
# ────────────────────────────────────────────────────────────────────
def serial_thread(port: str, baud: int):
    try:
        import serial
    except ImportError:
        print("[串口] 未安装 pyserial，请运行：pip install pyserial")
        return

    print(f"[串口] 连接 {port} @ {baud} baud ...")
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"[串口] 已连接，等待命令...")
    except Exception as e:
        print(f"[串口] 连接失败：{e}")
        return

    while True:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            states = parse_command(line)
            if states is None:
                print(f"[串口] 无效命令：{line!r}")
                continue

            with state_lock:
                for i, s in enumerate(states):
                    balloon_state[i] = s

            labels = {INFLATE: 'I', DEFLATE: 'D', HOLD: 'H'}
            print(f"[串口] 收到：{''.join(labels[s] for s in states)}")

        except Exception as e:
            print(f"[串口] 读取错误：{e}")
            time.sleep(0.5)


# ────────────────────────────────────────────────────────────────────
# 主仿真循环
# ────────────────────────────────────────────────────────────────────
def run_simulation():
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data  = mujoco.MjData(model)

    balloon_geom_ids = [
        mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, f"balloon_{i}_geom")
        for i in range(8)
    ]
    balloon_d = [D_MIN] * 8

    # 初始化 geom 尺寸
    for i, gid in enumerate(balloon_geom_ids):
        model.geom_size[gid, 0] = d_to_R(balloon_d[i])

    print("\n[仿真] MuJoCo Viewer 启动中...")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.azimuth   = 45
        viewer.cam.elevation = -20
        viewer.cam.distance  = 0.8

        step = 0
        while viewer.is_running():
            dt = model.opt.timestep

            # 读取当前状态（线程安全）
            with state_lock:
                current_state = list(balloon_state)

            # 更新每个气球
            for i in range(8):
                if current_state[i] == INFLATE:
                    balloon_d[i] = min(D_MAX, balloon_d[i] + INFLATE_RATE * dt)
                elif current_state[i] == DEFLATE:
                    balloon_d[i] = max(D_MIN, balloon_d[i] - INFLATE_RATE * dt)

                model.geom_size[balloon_geom_ids[i], 0] = d_to_R(balloon_d[i])
                data.ctrl[i] = balloon_d[i] - D_MIN

            mujoco.mj_forward(model, data)
            mujoco.mj_step(model, data)
            viewer.sync()

            if step % 1000 == 0:
                core_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "core")
                pos    = data.xpos[core_id]
                labels = {INFLATE: 'I', DEFLATE: 'D', HOLD: 'H'}
                state_str = ''.join(labels[s] for s in current_state)
                radii = [f"{d_to_R(d)*1000:.0f}" for d in balloon_d]
                print(f"[t={data.time:6.1f}s] pos=({pos[0]:.3f},{pos[1]:.3f},{pos[2]:.3f})"
                      f"  state={state_str}  R(mm)={radii}")
            step += 1


# ────────────────────────────────────────────────────────────────────
# 入口
# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ballooance Interactive Controller")
    parser.add_argument("--port", type=str, default=None,
                        help="串口端口，例如 COM3 或 /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=9600,
                        help="波特率（默认 9600）")
    args = parser.parse_args()

    # 启动输入线程
    if args.port:
        t = threading.Thread(target=serial_thread, args=(args.port, args.baud), daemon=True)
    else:
        t = threading.Thread(target=keyboard_thread, daemon=True)
    t.start()

    # 主线程运行仿真
    run_simulation()
