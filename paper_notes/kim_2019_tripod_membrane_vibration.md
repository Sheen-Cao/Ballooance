# Kim et al. 2019 — A Simple Tripod Mobile Robot Using Soft Membrane Vibration Actuators

**Type:** Research letter, *IEEE Robotics and Automation Letters* (2019)
**Authors:** DongWook Kim, Jae In Kim, Yong-Lae Park (Seoul National University)
**Citation key:** `kimSimpleTripodMobile2019`

## Core Claim

A self-vibrating soft pneumatic actuator that converts a *constant* input pressure into mechanical oscillation through an integrated valve-membrane mechanism — no active inflation/deflation control needed. Three of these arranged in an equilateral triangle make a tripod mobile robot capable of translation and rotation by differential pressure.

## Critical Correction to Initial §2.1 Draft

My §2.1 v1 said: *"an inflatable membrane is driven at its resonant frequency, and the resulting periodic deformation propels the robot."*

**This is wrong.** The mechanism is **not** resonant excitation — it's a *relaxation oscillator* built from an integrated valve. Mechanism per the paper:

1. Constant input pressure inflates the membrane.
2. Membrane expansion physically pushes a valve shaft downward.
3. At a release threshold (L* = 7 mm), the shaft opens an exhaust port.
4. Air escapes → membrane deflates → shaft retracts → exhaust closes.
5. Cycle repeats. Frequency is set by the constant input pressure.

This is even **more** in line with the §2.1 argument than I originally claimed: not a controller specifying a frequency, but a controller specifying *only a constant pressure*, with the body itself producing the periodic timing.

## Key Quotes

> "The advantage of this mechanism is that the actuator does not require active control of inflation and deflation of the chamber for the motion of the membrane, which is necessary in conventional closed-chamber pneumatic actuators, such as McKibben muscles and PneuNet actuators." (Introduction, p. 2289)

> "By repeating this motion, the actuator creates vibration, and its frequency can be controlled by the input air pressure." (Introduction, p. 2289)

> "This is the first attempt to create a soft actuator which can create vibration only using soft and rigid materials without any commercial motors." (Introduction, p. 2289)

## Other Useful Details

- **Payload**: robot can carry 5× its own weight.
- **Control approach**: model-free, Gaussian process-based — the input-output mapping is *learned*, not modeled, because the dynamics are too nonlinear for analytical control. (Supports the §2.1 claim that *modeling is harder* even when *control inputs are simpler*.)
- **Material**: silicone rubber Ecoflex-0030 membrane in 3D-printed housing; valve shaft is rigid plastic.
- **Trajectory tracking**: the robot follows polygon trajectories using differential pressure across the three actuators — the geometric arrangement (equilateral triangle) is what enables omni-directional motion.

## Relevance Per Section

### §2.1 (Soft + Pneumatic) — *primary citation here*
- Strongest example of *"controller specifies a steady input; gait emerges from material self-actuation."*
- Use as the **first** specific system in §2.1's "specific systems" paragraph because the input-output simplification is the cleanest of the three.
- Specifically cite: "no active control of inflation/deflation needed" → directly supports the user's "control interface更粗粒" point from the Consensus discussion.

### §2.2 (Morphological Computation) — *NOT primary*
- Could be cited as an example of "morphological computation" but the paper itself doesn't use that term — it positions itself as a control simplification, not a body-as-computer claim. Don't lean on it for §2.2's conceptual argument.

### §2.4 (Emergence) — *NOT relevant*
- Single body, no emergent collective behavior. Skip.

## Distinction from the Thesis Work

| | Kim 2019 | This thesis |
|---|---|---|
| Body type | Single rigid housing + soft membrane | Multiple inflated modules in polyhedral arrangement |
| Pneumatic input | Constant pressure → vibration | Discrete D/I/H states across modules |
| Locomotion | Vibration-driven sliding | Inflation-driven CoM shift / tip-over |
| Body computation | Membrane-valve self-oscillation | Inter-module passive coupling |

Use the contrast to position your work: Kim shows that a *single soft body* can absorb timing into its material. Your thesis asks: what about *coupling between bodies*?

## Watch out for / Nuances

1. Don't claim "resonant frequency" — the mechanism is a relaxation oscillator (valve switching), not resonance.
2. The paper says control is *simpler* (constant pressure input) but also explicitly notes that *modeling is harder* — they use a Gaussian process for closed-loop trajectory control. This nuance directly supports the user's Consensus discussion point: *"actuator简化, 控制建模更难"*.
3. The robot's omni-directional capability comes from **geometric arrangement** of three actuators in a triangle — a small but useful illustration that "configuration matters" even at this single-body scale.
