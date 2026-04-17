# Ballooance — Project Memory
> This file is Claude's persistent memory for the Ballooance project.
> **How to use:** At the start of a new session, say "Read my memory file." When important decisions are made or progress happens, say "Update my memory file."

---

## Project Overview
- **Project name:** Ballooance
- **Type:** Master's thesis — Computational Design, CMU
- **Owner:** Sheen (sheencao.0824@gmail.com)
- **Repo/workspace:** `D:\Share\CMU\Thesis\Ballooance`

**One-line thesis:** A design framework for modular inflatable robots based on cospherical polyhedral primitives, asking how discrete topological configuration shapes locomotive capacity and what minimum structural complexity is required for controllable mobility.

**Intellectual core (as of 2026-04-17):** Inspired by emergence theory — how do simple local behaviors (balloon inflate/deflate) coordinated within a geometric configuration produce effective global locomotion? The thesis frames configuration not as a container for control, but as part of the computation itself (morphological computation).

---

## Current Stage
- [x] Robot design — complete
- [x] Physical prototyping (multiple rounds) — complete
- [x] Thesis framing & research questions — defined
- [ ] Configuration comparison experiments — in progress (tetra & cube done; bipyramid & octa need systematic data)
- [ ] Sim-to-real alignment — in progress (MuJoCo model built, metrics defined, ArUco camera not yet set up)
- [ ] Control policy (CA rules) — in progress (pairing strategy established, formal rule set not yet written)
- [ ] Learned policy / RL — not started

---

## Thesis Framing

### Central Research Question
> How does the discrete topological configuration of a modular inflatable robot shape its locomotive capacity, and what is the minimum structural complexity required for controllable mobility under a cost–mobility trade-off?

### Three Contributions
1. **Cospherical polyhedral design framework** — a geometrically principled design space for comparing modular inflatable robot topologies under a shared cospherical constraint (all vertices inscribed in a sphere of uniform radius)
2. **Empirical lower bound on topological complexity** — tetrahedron physically cannot locomote via inflation even at 1.5× module expansion; establishes minimum complexity threshold
3. **Symmetry-grounded actuation reduction** — pairing strategy derived from dual-polyhedral symmetry, reduces actuator count without sacrificing gait reachability

### Three Intellectual Pillars (from 2026-04-17 session)
1. **Emergence**: simple inflate/deflate rules + polyhedral geometry → global locomotion emerges. Links to cellular automata, boids, particle robots (Li et al. Nature 2019)
2. **Passive material compliance**: balloon-to-balloon physical contact creates implicit mechanical coupling — balloon A inflating pushes neighbour B, changing B's effective support direction. This is morphological computation. Distinct from rigid modular robots (AuxBot) which block this coupling.
3. **Bottom-up control**: CA/boid-inspired local rules (each balloon responds to gravity + neighbour state) rather than top-down explicit gait planning

### Thesis Structure (Funnel Arc)
- **Part I — Design Space (breadth):** Ch.1 Intro, Ch.2 Background, Ch.3 Cospherical framework, Ch.4 Manual prototyping & config comparison
- **Part II — Deep Dive (depth):** Ch.5 Pairing strategy & symmetry, Ch.6 Digital twin & sim-real, Ch.7 Control policy (CA rules + RL benchmark)
- **Part III — Reflection:** Ch.8 Material as implicit computation, Ch.9 Conclusion

### Thesis Statement / Punchline
*"In soft modular systems, configuration is not just a container for control but part of it."*

---

## Design Framework — Four Configurations

All candidates share the **cospherical constraint**: inflatable modules placed at vertices of a polyhedron inscribed in a sphere of uniform radius.

| Config | #Modules | Symmetry | Tip-over capable? | Notes |
|--------|----------|----------|-------------------|-------|
| Tetrahedron | 4 | T_d | **No** — lower bound | Cannot reach unbalanced state even at 1.5× inflation |
| Bipyramid | 5 | D_3h | ? | Not yet systematically tested — critical to test |
| Octahedron | 6 | O_h | Likely yes | Expected marginal/critical regime — thesis protagonist candidate |
| Cube | 8 | O_h | Yes | Gait "relatively obvious" — upper bound of control redundancy |

**Key insight:** Choose the *boundary* configuration (likely octahedron/6-unit) as the thesis focus — not the easiest (cube) nor the impossible (tetra), but the one where intelligent control is actually *necessary*.

### Actuator Setup
- 8 solenoids + 1 pump
- 3 states per balloon: **D** (deflate), **I** (inflate), **H** (hold)
- Pairing strategy: connect opposite pairs → reduces effective actuator count (e.g., 8 → 4 pairs for cube)

---

## Control Policy Direction

### Primary Approach: Bottom-up CA Rules
Formalise the existing pairing strategy as a cellular automaton rule set. Each balloon's state is a function of its own position relative to gravity + neighbour states:

- **Rule 1 (gravity sensing):** Inflate if you are on the current ground-contact side
- **Rule 2 (symmetry breaking):** Inflate when your opposite is in Hold; deflate when opposite inflates
- **Rule 3 (neighbour avoidance):** Delay inflate when neighbour is already inflated

Same rule set applied across all configurations → different emergent behaviour per topology = the experiment.

### RL Role: Benchmark, not primary
Train RL in MuJoCo sim → use as optimal policy benchmark. Research question: "How close does the CA rule approach RL-optimal, and where does the gap come from?"

### NOT recommended: Sim-trained RL directly deployed to real
MuJoCo rigid-body sim doesn't capture: balloon-to-balloon contact coupling, material hysteresis, asymmetric expansion. Direct sim→real RL transfer will likely fail.

---

## Simulation Roles (defined 2026-04-17)

Sim in this project is NOT a precise physics predictor. It plays four distinct roles:

1. **Design-space filter:** Quickly check whether a configuration can geometrically shift CoM enough to tip over (rigid-body approximation is sufficient for this geometric question)
2. **CA rule search engine:** Rapidly sweep candidate CA rule combinations to find promising ones before physical testing (much faster than physical iteration)
3. **Material-free baseline:** Sim captures geometry + rules only; real adds material passive coupling. Gap = material's contribution to locomotion. This gap is *evidence for the emergence/morphological computation argument*, not an error to apologize for.
4. **Parametric design record:** MJCF model makes the research reproducible; geometry parameters are version-controlled

### MuJoCo Model (built 2026-04-16)
- Core: cube inscribed in R=45mm sphere, edge L=51.96mm
- Balloon: trimmed sphere, d from 20mm (deflate) → 78mm (inflate)
- 8 ball joints + 8 slide joints
- Env: obs=18-dim, action=MultiDiscrete([3]×8), reward=forward progress + height penalty

---

## Sim-to-Real Methodology

### Metrics (IMU-only track)
- Attitude RMSE: geodesic distance on SO(3), `θ_err = 2·acos(|<q_sim, q_real>|)`
- Angular velocity spectrum: FFT comparison, Bhattacharyya distance on power spectrum
- Acceleration DTW: dynamic time warping on |a(t)| signal
- Heading drift rate: deg/s

### Metrics (IMU + ArUco track — recommended)
- All IMU metrics above, plus:
- Displacement per cycle (cm/cycle)
- Fréchet distance on 2D trajectory
- Heading stability SD across trials
- Terminal position error as % of path length

### Setup needed
- Overhead camera (phone on tripod is fine) + ArUco/AprilTag on robot top
- NTP time sync between camera and IMU
- **ArUco NOT yet set up — needed before displacement claims can be made**

### Key framing
Sim-real gap is NOT uniform — it's configuration-dependent. Tetra (if it moved at all) would be geometry-dominated; cube behaviour in high-symmetry regime would average out material effects. The marginal regime (octa) shows highest material sensitivity. This is both a finding and a research design choice.

---

## Literature Positioning

### Three Key Papers
| Paper | Mechanism | Most similar to Sheen's work in... | Key difference |
|-------|-----------|-----------------------------------|----------------|
| Wait et al. (ICRA 2010) | Pneumatic bladder sphere, 32 segments, truncated icosahedron | Mechanism: inflation → CoM shift → rolling | Single monolithic body, no modularity, no topology comparison |
| Chin et al. (RA-L 2023) | AuxBots: rigid auxetic jitterbug shell, motor+leadscrew, 4–7 units, flipper gait | Modularity + volume-changing locomotion | Rigid not soft, no polyhedral topology comparison |
| Nozaki et al. (IROS 2018) | Mochibot: 32-leg radial skeleton, rhombic triacontahedron, continuous free-form crawling | Polyhedral structure as design primitive | 32 DOF rigid, top-down gait planning, maximises DOF (inverse of Sheen's min-DOF question) |

### Positioning Statement
None of the three papers ask: *"which polyhedral topology achieves minimum-complexity locomotion via soft pneumatic inflation?"* This is the research niche.

### Other relevant literature to know
- **Mark Yim et al. (2007 IEEE RAM):** Modular self-reconfigurable robots review, discusses cost-mobility trade-off — must cite
- **NASA SUPERball (Sunspiral et al.):** Tensegrity icosahedral robot, tumbling locomotion — structurally similar, cite for context
- **M-Blocks (Romanishin, Rus, MIT 2013):** Rigid cube tumbling via internal flywheel — same tumbling mechanism, different execution
- **Karl Sims (1994):** Evolutionary virtual creatures — computational design of robot morphology, foundational
- **Li et al. (Nature 2019):** Particle robots — collective locomotion from simple local rules, directly relevant to emergence framing
- **Pfeifer & Iida:** Morphological computation — theoretical grounding for material-as-computation argument

---

## Key Metrics & Success States

### Configuration comparison (primary)
- **Mobility threshold (binary):** Can configuration achieve tip-over at max inflation? N=5 trials
- **Tip-over likelihood:** % of trials with successful forward motion
- **Min actuator count:** Smallest number of solenoids needed for mobility (from pairing strategy)
- **Symmetry reduction ratio:** full DOF / paired DOF

### Locomotion quality (selected config)
- Displacement per cycle (cm) — **requires ArUco camera**
- Heading stability SD (degrees) across trials
- Trial-to-trial variance (reflects material unpredictability contribution)

### Sim-to-real
- Attitude RMSE, angular velocity spectrum alignment, tip-over timing error
- **Success state:** Sim correctly predicts which configs can/cannot move (topology-level), even if it misses exact kinematics

---

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-16 | Simulation stack: MuJoCo + Python + Gymnasium + SB3 | Speed, RL ecosystem, enough for rigid-body approximation |
| 2026-04-17 | Primary thesis focus: **Configuration Design** (not control policy, not sim-to-real) | Computational design dept expects design frameworks; tetra failure + cube success is the core finding |
| 2026-04-17 | Choose **marginal/boundary config** (likely octa/6-unit) as thesis protagonist | Cube is trivially controllable; tetra is impossible; marginal regime is where intelligent control matters |
| 2026-04-17 | Control approach: **bottom-up CA rules** as primary, RL as benchmark | Philosophically consistent with emergence framing; feasible without full RL deployment |
| 2026-04-17 | Sim-real gap = **evidence, not error** | Gap measures material's contribution to locomotion, supports morphological computation argument |
| 2026-04-17 | Add **overhead camera + ArUco** for position ground truth | IMU double-integration drift makes displacement claims unreliable; camera is low-cost fix |

---

## Abstract (current best version, 2026-04-17)

> Soft robots gain their abilities as much from their shape as from their control, yet the choice of shape is rarely systematic. Modular robots, by contrast, offer design spaces that can be compared and studied — but most modular robots today are rigid, leaving the combination of modularity and soft inflation largely unexplored.
>
> This thesis works in that gap. It asks how the arrangement of modules in an inflatable robot shapes its ability to move, and how few modules are enough to support controllable motion under a cost–mobility trade-off. This question comes from a common trade-off in soft robot design: adding more modules increases what a robot can do but also raises its cost and control complexity, while simpler setups may lose the ability to move at all.
>
> To study this trade-off, I propose a family of robots built from identical spherical inflatable modules placed on the vertices of cospherical polyhedra — tetrahedron, bipyramid, octahedron, and cube — so that different configurations share one geometric language and can be compared on equal terms. The thesis argues that, in soft modular systems, configuration is not just a container for control but part of it.

---

## Open Questions / Next Steps

### Urgent (needed for experiments)
- [ ] Test Bipyramid (5-unit) physically — critical for establishing whether lower bound is 4 or 5
- [ ] Set up overhead camera + ArUco for position ground truth
- [ ] Formalise CA rule set in writing (3–5 rules as a state machine per balloon)
- [ ] Build configuration comparison table with actual data (tetra/bipyramid/octa/cube)

### For thesis writing
- [ ] Draft Ch.2 Literature Review (position against 3 papers above)
- [ ] Write 1–2 page thesis proposal for advisor
- [ ] Measure balloon-to-balloon passive coupling (single balloon vs. neighbour-occupied inflation)
- [ ] Decide on exact configuration to use as thesis protagonist (pending bipyramid test)

### Longer term
- [ ] Implement CA rule set in hardware
- [ ] Run RL training in MuJoCo for benchmark comparison
- [ ] Systematic sim-real comparison across selected configuration

---

## Session Notes

| Date | Summary |
|------|---------|
| 2026-04-14 | Set up MEMORY.md. Project at transition point: design done, starting control policy development. |
| 2026-04-16 | Built MuJoCo simulation: MJCF model, Gymnasium env, PPO training script. Tuned physics params. |
| 2026-04-17 | Major thesis framing session. Defined RQ, 3 contributions, emergence framing, 4-config comparison arc, control policy direction (CA rules), sim roles, literature positioning (3 papers), abstract draft, metrics. Key shift: sim-real gap reframed as evidence for material computation argument. |
