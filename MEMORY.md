# Ballooance — Project Memory
> This file is Claude's persistent memory for the Ballooance project.
> **How to use:** At the start of a new session, say "Read my memory file." When important decisions are made or progress happens, say "Update my memory file."

---

## Project Overview
- **Project name:** Ballooance
- **Type:** Master's thesis — Computational Design, CMU
- **Owner:** Sheen (sheencao.0824@gmail.com)
- **Repo/workspace:** `D:\Share\CMU\Thesis\Ballooance`

**Summary:** A modular inflatable robot system. The robot is made up of inflatable units that can be assembled in different configurations. The design and physical prototyping phases are complete; the current focus is developing a **control policy** for effective locomotion/movement.

---

## Current Stage
- [x] Robot design — complete
- [x] Physical prototyping (multiple rounds) — complete
- [ ] Control policy development — **in progress**

---

## Design & Prototyping Notes

### Unit Configurations (from Pics folder)
- 4-unit, 5-unit, 6-unit, 8-unit configurations have been tested/modeled
- Images show structural views (`_str`) and core views (`_core`)
- Unit types documented in `types.png` / `types-1.png`

### Files
| File | Description |
|------|-------------|
| `3d_models/thesis_models.3dm` | Main Rhino 3D model |
| `3d_models/generator.gh` – `generator_5.gh` | Grasshopper generative scripts (5 iterations) |
| `gh_generator.py` | Python script related to Grasshopper generation |
| `Pics/` | Prototype photos and renders |

---

## Control Policy — Goals & Progress
- **Goal:** Develop a control policy so the robot can move effectively
- **Status:** Just starting — no implementation yet
- **Approach (TBD):** _To be filled in as decisions are made_
- **Open questions:**
  - What locomotion strategy? (crawling, rolling, peristaltic, etc.)
  - Simulation environment? (MuJoCo, PyBullet, Isaac Gym, custom?)
  - Learning-based (RL) vs. model-based control?
  - How are individual units actuated? (pneumatic pressure, valves?)

---

## Key Decisions Log
_Append entries here as decisions are made._

| Date | Decision | Rationale |
|------|----------|-----------|
| — | — | — |

---

## References & Resources
_Add papers, links, or tools that are relevant._

---

## Session Notes
_Brief notes from past sessions._

| Date | Summary |
|------|---------|
| 2026-04-14 | Set up MEMORY.md. Project at transition point: design done, starting control policy development. |

