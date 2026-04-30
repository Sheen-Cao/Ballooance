# Mousa et al. 2025 — Multifunctional Fluidic Units for Emergent, Responsive Robotic Behaviors

**Type:** Research article, *Advanced Materials* (2025)
**Authors:** Mostafa Mousa, Alberto Comoretto, Johannes T.B. Overvelde, Antonio E. Forte
**Affiliation:** Oxford, King's College London, AMOLF, Eindhoven
**Citation key:** `mousaMultifunctionalFluidicUnits`
**Note:** Year may be off by one in some Zotero records — DOI is 10.1002/adma.202510298, published 2025 in Adv. Materials.

## Core Claim

A *single multifunctional fluidic unit* can be configured as valve, sensor, or actuator — or all three at once (self-sensing oscillating actuator). Multiple such units, mechanically coupled via a shared body, exhibit **emergent passive self-synchronization**, modeled with Kuramoto coupled oscillators.

## Three Demonstrations Built from the Same Unit

1. **Controlled shaker** — a periodic actuator driven by constant pressure
2. **Multimodal hopper** — different gaits from the same hardware by re-tuning the unit
3. **Crawler with environmental boundary sensing** — sensor + actuator integrated into one limb

## Self-Synchronization (the part that matters most for the thesis)

> "When these units are mechanically coupled via a shared body, [they] exhibit emergent passive behaviors, such as self-synchronization—a behavior that is elucidated with a Kuramoto model of networks of oscillators." (abstract)

Mechanism: each oscillating limb has its own fluidic dynamics, but mechanical coupling through a shared body causes phase-locking without any centralized timing controller.

**Why this matters for thesis:**
This is the **single most direct existing-systems evidence for the thesis's "passive material coupling produces emergent coordination"** argument. The user's claim that *neighboring inflated bodies couple through their shared substrate to produce coordinated behavior without explicit control* is, at the level of mechanism, the same phenomenon Mousa demonstrates in 2D fluidic networks — extended to 3D polyhedral arrangements.

## Their Preferred Terminology

- The paper uses **"embodied intelligence"** as its umbrella term, not "morphological computation" directly.
- They cite the principle as: *"leveraging the robot body compliance and harnessing the dynamics of its interaction with the environment is known as embodied intelligence."*
- "Embedded control" — valves incorporated into robot body, configured into oscillator circuits driving locomotion.
- Their framing: fluidic circuits enable behaviors "without reliance on electronics or software"

## Quotable Passages

> "Fluidic circuits have shown significant promise in enabling complex functionality in soft robots with a minimal number of input signals." (abstract, p. 1)

> "Strategic combinations of these components enable embedding sophisticated control schemes directly into robotic structures, facilitating complex behaviors like automatic gripping, actuator sequencing, and coordinated locomotion, all without reliance on electronics or software." (introduction, p. 1)

> "When these units are mechanically coupled via a shared body, [they] exhibit emergent passive behaviors, such as self-synchronization." (abstract)

## Relevance Per Section

### §2.1 (Soft + Pneumatic) — *primary citation here*
- Strongest evidence for the §2.1 argument: minimal pneumatic inputs → complex behaviors.
- Specifically: a *single constant pressure input* drives the self-oscillating limb (no time-varying control signal).
- Use this paper as the closing example in §2.1's "specific systems" paragraph: it pushes the *"actuator network as its own coordinator"* argument the furthest of the three §2.1 cases.

### §2.4 (Emergence — secondary citation, complementary angle)
- Self-synchronization via Kuramoto is a clean local-rules → global-behavior example *grounded in physics*, not in CA simulation.
- Cite alongside Cademartiri & Bishop 2015 / Rubenstein 2014 to show emergence works in physical fluidic systems as well as digital agents.

### **NOT** §2.3 (Modularity)
Although Mousa's units are technically "modular" in the assembly sense, the paper is not a *modular reconfigurable robotics* contribution — it does not study how different topological arrangements of units yield different robot capabilities. Don't cite it as MRR.

## Distinction from the Thesis Work

| | Mousa 2025 | This thesis |
|---|---|---|
| Coupling | 2D fluidic network coupled through shared pressure circuit | 3D polyhedral coupling through inflated-membrane contact |
| Topology as variable? | No — single design demonstrated | Yes — comparative across tetra/octa/cube |
| Locomotion driver | Periodic oscillation (Kuramoto-style sync) | Discrete inflation states (D/I/H) producing tip-over gaits |

Use this contrast to position your work: Mousa establishes that *passive coupling produces emergent coordination*. Your thesis asks: *what happens when you make the coupling topology a design variable*?

## Watch out for / Nuances

1. The paper uses **"embodied intelligence"** rather than "morphological computation" — be careful if grouping it with Pfeifer-style MC literature.
2. Self-synchronization is *physics-based* (Kuramoto), not algorithm-based (CA / boids). When citing in §2.4, frame as a different *mode* of emergence (continuous-time oscillator coupling) than the discrete-state cellular models.
3. Mousa et al. emphasize their unit is **reconfigurable** but the reconfiguration is *functional* (sensor↔actuator↔valve), not *topological* (changing the arrangement of multiple units).
