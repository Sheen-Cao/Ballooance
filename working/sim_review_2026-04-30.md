# MuJoCo 仿真诊断报告

**日期：** 2026-04-30
**审查范围：** `simulation/models/ballooance.xml`、`simulation/envs/ballooance_env.py`、`simulation/train.py`、`simulation/test.py`、`simulation/scripts/{interactive,replay,send_command}.py`
**目标：** 验证现有 MuJoCo 工程是否能支撑 MEMORY 里定义的四个仿真角色（design-space filter / CA rule search / material-free baseline / parametric design record）以及 sim-real 对齐方法。

---

## TL;DR

整体框架已经搭起来了 —— MJCF 模型、Gym env、PPO 训练、可视化交互、串口接入都有。但里面有几个**会让目前训练/测试结果不可用**的硬伤需要先修，再谈写论文里的方法学。最严重的三个是：

1. **`BallooanceEnv` 训练时气球半径永远不变** —— `test.py` 里手动改 `model.geom_size` 来模拟充气，但 env 没做这件事。RL agent 学到的是"球往外伸但不变大"的假机器人。
2. **MJCF 里 plate_6 / plate_7 多了 `ball joint`，其他六个没有** —— 这破坏了 cospherical 模型的对称性，导致两个角能转而六个角不能转，物理上是脏的。
3. **`HOLD` 状态实际上不 hold** —— env 里收到 HOLD 时只是 `ctrl` 不变，但位置执行器还在驱动到上一次的目标。语义和真实硬件的"关电磁阀保压"不一致。

下面按文件逐项展开。

---

## 1. MJCF 模型审查 (`simulation/models/ballooance.xml`)

### 1.1 几何参数与文档自洽性 ✓

注释里声明的 cospherical 几何全部对得上：
- 内接球 R = 45mm，立方体 edge = 51.96mm，half-size = 25.98mm ≈ 0.026m ✓
- 角点位置 (±0.026, ±0.026, ±0.026) ✓
- 气球初始偏移 d_min = 20mm，沿外向法向投影 = 0.020/√3 ≈ 0.01155m ✓
- slide joint 行程 d_max − d_min = 58mm = 0.058m ✓

这部分干净。

### 1.2 [严重] 不对称的 ball joint（lines 168, 178）

```xml
<body name="plate_6" ...>
  <joint name="joint_6" type="ball" range="0 0.52" damping="0.2"/>   <!-- 只有 6 和 7 有！-->
  ...
</body>
```

只有 plate_6 和 plate_7 加了 ball joint，其他六个 plate 都是刚接到 core 上的。注释写"ball joint 暂时移除，plate 刚性固定到 core"，看起来是调试残留，没清理干净。

**影响：** 八个角的力学响应不对称，立方体的 O_h 对称性被破坏；任何基于"对称配对"（pair across cube diagonal）的策略在仿真里都会失真。

**修复：** 要么全部移除（保持当前的"刚性 plate"假设），要么全部加上（如果想模拟实物里 plate-balloon 的少量柔性）。从你 MEMORY 里描述"balloon-to-balloon contact creates implicit mechanical coupling"看，**当前阶段保留刚性 plate 更合适**，把 ball joint 留给后期建模柔性环节。

### 1.3 [严重] 气球的碰撞体半径在 MJCF 里是固定的（lines 117, 127, 135 …）

```xml
<geom name="balloon_0_geom" type="sphere" size="0.029" mass="0.04" .../>
```

`size="0.029"` 是 deflate 状态的半径。`test.py` 在每个仿真步里手动调用 `model.geom_size[gid, 0] = d_to_R(d)` 来模拟充气；但 `BallooanceEnv` **完全没做这件事**。详见 §2.1。

**修复方向：** 把"d → balloon_radius"的更新逻辑封装成一个独立函数，env 和 test.py 都调用。

### 1.4 接触参数 [可商榷]

```xml
<default><geom condim="6" friction="6.0 0.3 0.1"
              solimp="0.9 0.95 0.005" solref="0.02 1"/></default>
```

- `friction=6.0`：橡胶气球-地面 µ 实测一般 1.5–4.0，6.0 偏高。这个数值估计是为了补偿"刚性球替代柔性气球"造成的接触面积损失（真实气球压地是面接触，sim 是点接触），把摩擦调高让翻滚不打滑。**这是一个合理的工程取舍，但要在论文里明确说明这是 calibration 而非物理常数。**
- `condim=6` 包含 torsional friction，对球-平面接触是必要的，否则旋转无阻尼。
- `solimp / solref` 偏软（0.9, 0.95, 0.005 / 0.02, 1）—— 球-球互压时可能进入轻微穿透。如果你想强调 balloon-balloon coupling 是 morphological computation 的一部分，这里需要更硬的接触（solimp=0.95 0.99 0.001）才能让"互推"传力清晰。

### 1.5 没有 IMU sensor block ⚠️

当前 `<sensor>` 只有 framepos / framelinvel / frameangvel / framequat，没有 `<accelerometer>` 和 `<gyro>`。

按 MEMORY 里 sim-real 对齐的指标（attitude RMSE、ang vel FFT、accel DTW），需要的是**和实物 IMU 同源的信号**。线加速度在 MuJoCo 里要从速度数值微分得出，会引入数值噪声并和真机 IMU 的物理噪声对不上量级。

**建议补一个 `site` 装在 core 上，挂上 accelerometer 和 gyro：**

```xml
<sensor>
  <accelerometer name="imu_accel" site="core_site"/>
  <gyro          name="imu_gyro"  site="core_site"/>
  <framequat     name="imu_quat"  objtype="site" objname="core_site"/>
</sensor>
```

`core_site` 已经在 line 101 定义了，直接用就好。

### 1.6 缺少 tracking 摄像头（影响 `render`）

`BallooanceEnv.render()` 调用 `update_scene(camera="track_core")`，但 MJCF 里没有这个 camera。直接调 render 会报错。

**补一段：**

```xml
<worldbody>
  <camera name="track_core" mode="trackcom" pos="0 -0.6 0.3" xyaxes="1 0 0 0 0 1"/>
  ...
</worldbody>
```

### 1.7 Mass 数字需要校核

core 0.2kg + 8×0.04kg(balloon) + 8×0.015kg(plate) ≈ 0.64kg。

如果你称过实物，对一下；不一致会让 sim-real gait timing 系统性偏移。

---

## 2. Env 审查 (`simulation/envs/ballooance_env.py`)

### 2.1 [严重] 训练时气球不会变大（呼应 §1.3）

`step()` 里只做了 `data.ctrl[actuator] = target`，没有更新 `model.geom_size`。所以 RL 看到的是"slide joint 把刚性小球往外移，但小球本身一直只有 29mm"。

**后果：**
- balloon-balloon 互压几乎不会发生（小球之间间距远）
- 翻滚需要的接触面拓扑根本不成立
- 训练得到的策略到了 `test.py` 那种"会变大"的环境立刻失效

**修复：** 在 `step()` 里加入和 `test.py` 一致的更新逻辑（建议拆成 helper）：

```python
def _update_balloon_geoms(self):
    for i in range(self.n_balloons):
        d = self.data.ctrl[self.actuator_ids[i]] + D_MIN
        self.model.geom_size[self.balloon_geom_ids[i], 0] = math.sqrt(R_BASE**2 + d**2)
```

注意：`mj_forward` 之后再 `mj_step`，否则 contact pair 用的还是旧 size。

### 2.2 [严重] HOLD 语义错误

```python
for i, a in enumerate(action):
    target = STATE_TARGETS[int(a)]
    if target is not None:
        self.data.ctrl[self.actuator_ids[i]] = target
    # HOLD: leave ctrl unchanged
```

HOLD 时 `ctrl` 不变，但位置执行器仍在驱动到上一次的 target —— 上一次如果是 INFLATE，HOLD 期间还在继续充气直到顶到 ctrlrange 上限。这和实物"关电磁阀，气体留在球里"的语义对不上。

**修复：** HOLD 时把 ctrl 锁到当前关节位置：

```python
if a == HOLD:
    qpos_addr = self.model.jnt_qposadr[self.expand_joint_ids[i]]
    self.data.ctrl[self.actuator_ids[i]] = self.data.qpos[qpos_addr]
```

### 2.3 [中等] 充气速率比真实快 100×

`test.py` 用 60 秒走完全行程；env 直接 `ctrl = target`，position actuator 在 kp=80 / damping=0.8 下大概 0.1–0.5s 走完。

如果你的 RL 目标是"控制策略学时序协同"，这种 instant-fill 完全 OK；但如果想用 sim 当 CA rule 的 search engine 然后部署到真机，时间尺度不匹配会让 rule 的 timing 直接对不上。

**建议加 ramp limiter：**

```python
INFLATE_RATE = (D_MAX - D_MIN) / 60.0  # m/s, matches real
ctrl_step = INFLATE_RATE * substep_dt * n_substeps
new_ctrl = np.clip(target, current_ctrl - ctrl_step, current_ctrl + ctrl_step)
```

### 2.4 [中等] Observation 用 `data.ctrl` 而不是真实 joint 状态

```python
balloon_states = np.array([self.data.ctrl[self.actuator_ids[i]] / BALLOON_MAX ...])
```

`data.ctrl` 是命令，不是当前状态。Agent 看到的是自己刚发的 action，不是机器人现在长什么样。在有时间延迟（ramp limiter）的设定下这两者会差很远。

**改：** 用 `data.qpos[jnt_qposadr[expand_joint_id]]`。

### 2.5 [中等] Episode 太短

`max_episode_steps=1000`，每步 10×0.001s = 10ms，整 episode 才 10 秒。真机充气一次要 60 秒。10 秒里气球都没充完，agent 学不到一个完整翻滚周期。

**建议：**
- 如果用 instant-fill：保持 1000 步 OK
- 如果用真实 ramp：改到 ≥6000 步（60s）或更长

### 2.6 [轻] Reward 可商榷

```python
forward_reward = (core_x - prev_x) / dt / 10  # = m/s
height_penalty = -5.0 if core_z < 0.05 else 0.0
```

- forward_reward 是 m/s，量级合理。但只奖励 +x 方向，没考虑 -x、±y。如果实验目标是"任意方向位移"，应改为 `np.linalg.norm(planar_velocity)`。
- height_penalty 阈值 0.05 太敏感 —— 翻滚瞬间核心低点就会触发，反而抑制翻滚学习。建议改为基于 episode 平均高度或仅在长时间过低时罚。
- 缺少**翻滚奖励**：你 MEMORY 里的指标是"tip-over likelihood"和"displacement per cycle"，应直接奖励朝向变化（quaternion 角度差）+ 净位移，而非瞬时速度。

### 2.7 [轻] 初始扰动只加在 xy，不加在朝向

```python
self.data.qpos[:3] += self.np_random.uniform(-0.005, 0.005, 3)
```

这是平移扰动；要做 robust policy，应同时加小角度的初始姿态扰动（quaternion 部分）。

---

## 3. 训练脚本 (`train.py`)

整体没有大问题，PPO 默认超参合理。两点观察：

- `device="cpu"` 默认，模型很小，CPU 训练 500k 步大概要几小时；如果有 GPU 切 cuda 会更快
- `n_envs=4` 对于这个观察/动作空间偏少，可以拉到 8–16 加速

但在修复 §2.1（geom 不更新）之前训练出来的模型基本是无效的，所以这些不是当前优先级。

---

## 4. Sim-real 对齐方法学 —— 当前状态

### 4.1 已经具备的能力

| MEMORY 指标 | 当前 sim 能否计算 | 备注 |
|---|---|---|
| Attitude RMSE (geodesic on SO(3)) | ✓ 有 framequat sensor | 需要在 env 里加 trajectory recorder |
| Angular velocity FFT | ✓ 有 frameangvel | 同上 |
| Acceleration DTW | △ 需数值微分 cvel | **建议加 accelerometer sensor，§1.5** |
| Heading drift rate | ✓ 从 quat 推 | |
| Displacement per cycle | ✓ 有 framepos | 需 ArUco 在实物侧 |
| Fréchet distance on 2D traj | ✓ | 库：`similaritymeasures.frechet_dist` |
| Heading stability SD | ✓ | |

### 4.2 缺的基础设施

1. **轨迹记录器** —— 没有把 sim 跑出的 (t, pos, quat, ang_vel, accel, action) 写到 csv/parquet 的代码
2. **命令重放器** —— 实物记录一段 (t, action_sequence)，sim 端能否 replay 同样的序列？目前 `test.py` 的 GAIT_SEQUENCE 是硬编码的，不能从外部文件读
3. **指标计算脚本** —— attitude RMSE / FFT / DTW / Fréchet 这些需要一个独立的 `analysis/compare.py`，吃两份 csv（sim & real）输出指标
4. **噪声模型** —— 真实 IMU 有 ~0.01 g 的 accel noise 和 ~0.5 deg/s 的 gyro bias drift，sim 是干净的。要么 sim 加噪声、要么 real 端做滤波后再比较

### 4.3 仿真四角色当前覆盖度

回到 MEMORY 里的四个 sim role：

| 角色 | 当前覆盖度 | 缺什么 |
|---|---|---|
| Design-space filter | ❌ 30% | 只有 cube；需要参数化生成 tetra/bipyramid/octa 的 MJCF |
| CA rule search engine | ❌ 20% | 没有 CA rule executor；只有硬编码 GAIT_SEQUENCE |
| Material-free baseline | ⚠️ 60% | 框架在但前述 bug（geom 不更新、HOLD 语义）让 baseline 不可信 |
| Parametric design record | ⚠️ 40% | XML 是手写的，几何参数没有从单一 source of truth 派生 |

---

## 5. 优先级建议

### P0 —— 必须先修，否则现有结果不可信
- [ ] §1.2 移除 plate_6 / plate_7 上残留的 ball joint
- [ ] §2.1 在 env.step() 里同步更新 `model.geom_size`
- [ ] §2.2 修 HOLD 语义
- [ ] §2.4 obs 改用 qpos 而非 ctrl

### P1 —— 影响 sim-real 对齐
- [ ] §1.5 加 IMU sensor (accelerometer + gyro)
- [ ] §1.6 加 tracking camera
- [ ] §2.5 episode 长度对齐充气时间尺度
- [ ] §4.2 写一个 `TrajectoryRecorder` 把仿真信号存 csv
- [ ] §4.2 写一个 `replay_command_log.py`，吃实物记录的 (t, 8-char cmd) 序列在 sim 里跑

### P2 —— 扩展四角色
- [ ] 写参数化生成器：`scripts/generate_config.py {tetra|bipyramid|octa|cube} → ballooance_<config>.xml`
- [ ] 实现 CA rule executor（你 MEMORY 里那 3 条规则的状态机）
- [ ] 写指标对比脚本 `analysis/compare_sim_real.py`

### P3 —— 训练侧改进
- [ ] §2.6 reward 改为多方向位移 + 翻滚朝向变化奖励
- [ ] §2.3 ramp limiter（如果走 sim2real 路线）
- [ ] §1.4 接触参数针对 balloon-balloon coupling 做敏感性分析

---

## 6. 论文里 "sim-real alignment methodology" 章节怎么写

等你 P0/P1 修完之后再动笔比较稳。届时章节结构建议：

> **6.x Sim-Real Alignment Methodology**
>
> 6.x.1 *Why MuJoCo, why rigid-body* —— 解释为什么选 MuJoCo（速度 / RL 生态 / MJCF 参数化）以及为什么接受 rigid-body 近似（gap 本身是论据，不是 bug）
>
> 6.x.2 *Sensor parity* —— sim 端的 IMU sensor 和实物 IMU 数据通道一一对应；time sync 用 NTP；记录格式统一为 csv
>
> 6.x.3 *Command replay protocol* —— 用同一段 (t, action) 序列驱动 sim 和实物，对比响应而非自由策略
>
> 6.x.4 *Metrics* —— 你 MEMORY 里那六个指标，每个写定义、用途、何时失效
>
> 6.x.5 *Configuration-dependent gap* —— 你那个核心论点：gap 在 tetra（几何主导）和 cube（高对称平均化）下小，在 octa（marginal regime）下大。这是 finding，不是 error。

我可以等你 P0 修完后再写这部分初稿 —— 那时候你能给我一个"sim 和实物在 cube 配置下、同一 command sequence 下的对比图/数据"，章节会有真实素材撑着。

---

**生成文件：** `working/sim_review_2026-04-30.md`
