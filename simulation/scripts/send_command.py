"""
send_command.py - 独立命令发送终端
在第二个终端窗口里运行，把命令写入共享文件，interactive.py 读取执行

终端1：python scripts/interactive.py
终端2：python scripts/send_command.py
"""

import os

CMD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".balloon_cmd")

shortcuts = {
    'HOLD'  : 'HHHHHHHH',
    'ALL_IN': 'IIIIIIII',
    'ALL_DE': 'DDDDDDDD',
    'ROLL_X': 'HHIIHHII',
    'ROLL_Y': 'HIHHIHHI',
    'BOT_IN': 'HIHIHIHI',
    'TOP_IN': 'IHIHIHIH',
}

print("=" * 45)
print("Ballooance 命令发送器")
print("格式：8字符  I=充气 D=放气 H=保持")
print("快捷：", list(shortcuts.keys()))
print("=" * 45)

while True:
    try:
        raw = input(">>> ").strip()
    except (EOFError, KeyboardInterrupt):
        break

    if not raw:
        continue

    cmd = shortcuts.get(raw.upper(), raw).upper()

    if len(cmd) != 8 or not all(c in 'IDH' for c in cmd):
        print(f"  ✗ 无效命令，需要8个 I/D/H 字符")
        continue

    with open(CMD_FILE, 'w') as f:
        f.write(cmd)
    print(f"  ✓ 已发送：{cmd}")
