# 仿真稳定性修复 — Change Log

**日期：** 2026-04-30
**目标：** 解决"气球穿地" + "气球互相重叠穿模"
**修改的文件：**
- `simulation/models/ballooance.xml`
- `simulation/test.py`
- `simulation/scripts/interactive.py`

---

## 根因（一句话）

`geom_size` 被 Python 立即更新到目标半径，但 slide joint 的 qpos 是带物理延迟的。结果是球的"半径"已经长到 81mm，但球心还没移到外面 —— **球在原地"鼓"出来**，要么穿地、要么穿邻球。再叠加上接触参数偏软（5mm 容差）和 actuator kp 偏硬（80），软接触挡不住硬位置控制，自然就穿了。

---

## MJCF 改了什么 (`simulation/models/ballooance.xml`)

| 位置 | 旧 | 新 | 原因 |
|------|------|------|------|
| `<option timestep>` | 0.001 | **0.0005** | 接触刚化后需要更小步长稳定 |
| `<option iterations>` | 200 | **500** | 8 球互压 + 地面 = 多接触体，多迭代才收敛 |
| `<option>` 新增 | — | `cone="elliptic"` `jacobian="dense"` `impratio="3"` | 椭圆摩擦锥比金字塔在球-平面接触上更稳；模型小，dense 比稀疏快；impratio>1 让法向接触优先收敛 |
| 默认 `<geom solimp>` | 0.9 0.95 0.005 | **0.99 0.999 0.0001 0.5 2** | 容差 5mm → 0.1mm，几乎无穿透 |
| 默认 `<geom solref>` | 0.02 1 | **0.005 1** | 时间常数 20ms → 5ms，硬接触 |
| 默认 `<geom friction>` | 6.0 0.3 0.1 | **3.0 0.05 0.05** | 6.0 太极端会触发数值抖动；3.0 已远超 µ_rubber-rubber ≈ 1.5 |
| 地面 `<geom>` | 用默认 | **显式覆盖** solimp/solref/friction | 地面参数和气球同步刚化 |
| `<body name="core" pos>` | 0 0 0.09 | **0 0 0.13** | 抬高 4cm，给底部气球留充气空间，避免初始就贴地 |
| plate_6 / plate_7 内的 `<joint type="ball">` | 存在（仅这两个角） | **删除** | 对称性 bug，调试残留 |
| slide joint `damping` | 0.8 | **3.0** | 给 actuator 加机械阻尼，避免位置控制振荡 |
| `<position kp>` | 80 | **25** | 80 N/m × 0.058m = 4.64N 直接顶穿软接触；25 配合现在的硬接触刚好能顶住 |
| 新增 `<camera name="track_core">` | — | trackcom 跟随 | 之前 env.render() 调用却没定义会报错 |
| `<sensor>` 新增 | — | accelerometer + gyro on core_site | sim-real 对齐需要 IMU 同源信号 |

---

## Python 脚本改了什么

### `simulation/test.py` 和 `simulation/scripts/interactive.py`（同一处修复）

**之前：**
```python
# 在 mj_step 之前更新 geom_size 到目标
balloon_d[i] += INFLATE_RATE * dt        # 命令端目标
model.geom_size[gid] = d_to_R(balloon_d[i])   # ← 立即长到目标，不管物理！
data.ctrl[i] = balloon_d[i] - D_MIN

mj_forward(...)
mj_step(...)
```

**之后：**
```python
# 1) 命令端：balloon_d 是"目标气量"，写到 ctrl
balloon_d[i] += INFLATE_RATE * dt
data.ctrl[i] = balloon_d[i] - D_MIN

# 2) 推进物理
mj_step(model, data)

# 3) 物理回读：geom_size 同步到 slide joint 的真实 qpos
#    被地面/邻球顶住没动 → geom 也不会鼓出来
for i in range(8):
    actual_d = data.qpos[qpos_addrs[i]] + D_MIN
    model.geom_size[ball_gids[i], 0] = d_to_R(actual_d)
```

**关键变化：geom_size 从"命令"驱动改为"物理状态"驱动。** 这就闭环了。

---

## 还可能要调的几个旋钮

如果运行后还有问题，按下面顺序调：

1. **如果还有微小穿模**：
   `solref="0.005 1"` → `solref="0.003 1"`（更硬）
   `iterations="500"` → `iterations="1000"`

2. **如果机器人抖、不稳**：
   `timestep="0.0005"` → `timestep="0.0002"`（更小）
   slide joint `damping="3.0"` → `damping="5.0"`

3. **如果气球不能把核心顶起来 / 翻不过去**：
   actuator `kp="25"` → `kp="40"`（适度加力，但别回到 80）

4. **如果气球贴地后弹起**：减小 `friction` 第二项（torsional），或把 condim 从 6 改回 3（去掉扭转摩擦，球-平面接触更稳）

5. **如果走到 ramp 太慢、看一个翻滚要等几分钟**：`test.py` 里把 `INFLATE_SECONDS = 60` 改成 `30` 或 `15`，但注意这会偏离实物时间尺度，做 sim-real 比较时再调回来

---

## 没改但建议下一步处理的

- `BallooanceEnv` 里同样的 geom_size sync 逻辑还没加 —— 等你想训练 RL 时再统一进 env
- env 的 HOLD 语义、obs 用 ctrl 而非 qpos 的 bug —— 见 `sim_review_2026-04-30.md`
- 命令日志记录器（trajectory recorder）用于 sim-real 对比 —— 还没写

---

## 怎么验证修复有效

```bash
cd D:\Share\CMU\Thesis\Ballooance\simulation
python test.py
```

预期：
- 启动后机器人在空中悬停约 1cm 落到地面（初始 z=0.13），稳定不抖
- 进入 GAIT_SEQUENCE 阶段 1：balloon 1、3 充气，应该看到气球往外/往下伸，被地面顶住，**核心被推起来**而不是球穿地
- 任意两球之间不应再有可见的视觉重叠；如果还有，调 §"还可能要调的旋钮"

---

**生成文件：** `working/sim_fix_changelog_2026-04-30.md`
