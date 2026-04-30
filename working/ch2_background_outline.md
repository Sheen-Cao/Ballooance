# Chapter 2: Background Review — Detailed Outline

**Chapter arc:** *control paradigm (emergence)* → *embodiment principle (matter)* → *existing systems (robots)*
Each section narrows scope; the third closes with the gap statement that bridges to Ch.3.

---

## 2.0 Chapter Introduction (1 short paragraph)

**Role:** Tell the reader what the chapter does and how it maps to Ch.1.

**Points to make:**
- This chapter situates the thesis within three converging literatures: (1) emergence as a control paradigm, (2) embodiment / morphological computation, and (3) soft and modular robotics as existing systems.
- The arc moves from broad concept to specific system; the gap identified at the end of 2.3 motivates the design framework introduced in Ch.3.
- Briefly acknowledge: an early thread on second-order cybernetics and HRI shaped the author's initial framing but is not pursued in the experimental work; mentioned for completeness, treated in the reflection chapter.

**Length:** ~5–7 sentences.

---

## 2.1 Elegance of Emergence

**Role:** Establish the bottom-up control paradigm — that complex global behavior can arise from simple local rules. This grounds the dialectic from §1.1 (Bottom-up vs. Top-down) and motivates the CA-based control direction in Ch.6.

### Argument structure (4 sub-arguments)

**A1 — Emergence as a precise relationship, not a metaphor.**
Emergence is often used loosely. In computational practice, it means: global properties that are predictable from but not reducible to the local rules — the global state cannot be obtained by linear superposition of agent states. This is the technical sense the chapter uses.

*Citations:* Anderson 1972 ("More is different"); Wolfram 2002 (cellular automata, qualitative classes); possibly Holland 1998 (Emergence); Mitchell 2009 (Complexity: A Guided Tour).

**A2 — Three computational practices that operationalize emergence.**

(a) *Cellular automata* — local update rules over discrete lattices producing global pattern (Conway's Game of Life; Wolfram's Class III/IV behavior). Foundational because it shows minimal rule sets producing universal computation.

(b) *Boids and flocking* — Reynolds 1987 — three simple rules (separation, alignment, cohesion) producing coherent flocks. Shows emergence works on continuous spatial agents.

(c) *Swarm robotics and programmable matter* — Rubenstein et al. 2014 (Kilobots: 1024 robots assembling shapes via local sensing); Li et al. 2019 *Nature* (particle robots: collective locomotion from minimal local rules). These move emergence from simulation into hardware.

*Citations:* Reynolds 1987; Wolfram 2002; Rubenstein et al. 2014 *Science*; Li et al. 2019 *Nature*; Cademartiri & Bishop 2015 (programmable self-assembly review).

**A3 — Self-organization and reducibility.**
Self-organization is the broader umbrella: structure arising without external direction. Connection to Turing's 1952 reaction–diffusion (morphogenesis), *Physarum* foraging networks, and ant colony optimization. Key conceptual point — these systems are not "non-linear" in the colloquial sense; they are *not reducible to compositional sums of agent states*. (Avoid the "linear vs. non-linear" framing — too easily misread as "Lyapunov-style" non-linearity.)

*Citations:* Turing 1952; Bonabeau et al. 1999 (Swarm Intelligence); maybe Camazine et al. 2001 (Self-Organization in Biological Systems).

**A4 — What emergence offers robotics, and where it has stalled.**
The promise: control specifications can be local, allowing robust, scalable, and graceful-degradation systems. The limit: most emergence-based robotics has been built on **rigid agents in free space** — kilobots, M-Blocks, particle robots — where coupling between agents is communicated rather than mechanical. The emergence available to a soft, physically coupled body is comparatively underexplored. This sets up §2.2.

*Citations:* Romanishin et al. 2013 (M-Blocks); Rubenstein et al. 2014; possibly Wang et al. 2024 (Robo-Matter, *Nat Comm*) as a recent attempt to bridge.

### Key transition sentences

**Section opener:**
> "If the dialectical framing of Chapter 1 distinguished bottom-up from top-down control, this section examines what bottom-up actually delivers as a computational practice — and what it has, so far, left aside."

**Section closer (transition into 2.2):**
> "Emergence shows that complex behavior need not be specified from the top. But every example surveyed here treats agents as mechanically independent units exchanging information. The next section examines a related but distinct claim: that even within a single body, intelligence can be distributed across material and form rather than concentrated in a controller."

### Watch out for
- Don't get lost in CA / Wolfram metaphysics — keep the section grounded in *what this means for robot control*.
- Don't promise more than the experiments deliver. The thesis pilots CA-style control; it does not prove emergence at scale.

---

## 2.2 Matter Does Matter

**Role:** Establish the embodiment / morphological computation paradigm — that the body is a computational participant, not a passive platform. This grounds the dialectic from §1.1 (Soft vs. Rigid) and motivates the configuration-as-computation argument central to Ch.5.

### Argument structure (4 sub-arguments)

**B1 — The classical separation of body and controller.**
Industrial robotics treats the body as a mechanical platform: the controller specifies torques, the body executes. This separation has been productive but has a quiet cost — it makes any computation done by the body invisible, and treats compliance, friction, and material variability as noise.

*Citations:* Brief reference to classical control (no need to cite extensively); maybe Brooks 1991 (Intelligence without representation) as the early dissent.

**B2 — Morphological computation: the body as computational participant.**
Pfeifer & Bongard 2007 and Pfeifer & Iida 2005 articulate the central claim: a well-designed body offloads computation that would otherwise need to be specified by the controller. Examples — passive dynamic walking (McGeer 1990): a leg's mass distribution alone produces stable walking on a slope, no controller required; the universal soft gripper (Brown et al. 2010, "jamming"): grasps irregular objects through passive deformation, no feedback loops; and physical reservoir computing in compliant bodies and tensegrity (Hauser et al. 2011; Caluwaerts et al. 2014) — using body dynamics as a substrate for computation itself.

*Citations:* Pfeifer & Bongard 2007 (*How the Body Shapes the Way We Think*); Pfeifer & Iida 2005 (*New Robotics*); McGeer 1990 (passive dynamic walker); Brown et al. 2010 (jamming gripper); Hauser et al. 2011; possibly Müller & Hoffmann 2017 (review of morphological computation definitions).

**B3 — Morphing matter and programmable self-assembly.**
A complementary line of work treats matter not as fixed but as reconfigurable in response to stimuli. Tibbits's *Self-Assembly Lab* and CMU's *Morphing Matter Lab* (Lining Yao et al.) demonstrate materials whose form changes are programmed at fabrication time. This pushes morphological computation in a constructive direction — instead of designing around what compliance does, you design *what compliance is*.

*Citations:* Tibbits 2014 ("4D Printing"); Yao et al. (Morphing Matter Lab work — pick representative paper); Cademartiri & Bishop 2015 (programmable self-assembly, *Nat Materials*); Wang et al. 2024 (Robo-Matter).

**B4 — Implication: the design question changes.**
If the body computes, the design question changes from *"what controller do we need?"* to *"what body would make the controller's task smaller, or unnecessary?"* This reframing is the conceptual lens this thesis adopts. But — important caveat — most demonstrations of morphological computation are on *single-body, monolithic* systems. The question of how morphological computation operates in *modular* bodies, where the modules are coupled through their material rather than rigidly attached, has received less attention. This sets up §2.3.

*Citations:* Pfeifer & Bongard 2007 (return citation); maybe Müller & Hoffmann 2017 for the design-question reframing.

### Key transition sentences

**Section opener:**
> "If emergence relocates intelligence from a central controller to a population of agents, morphological computation relocates it once more — from the controller to the body itself."

**Section closer (transition into 2.3):**
> "The principle of matter-as-computation is well established in monolithic soft systems and in compliant single-body machines. What kinds of robots, then, instantiate this principle in *modular* form — where the body is composed of comparable units, and where the configuration of those units is itself a design variable? Two robotic traditions have approached this question from different directions."

### Watch out for
- Risk of overlap with §2.3 — keep §2.2 *conceptual*: the principle, the examples, the design-question reframing. Save specific comparable systems (Wait, Chin, Nozaki, Yu, Usevitch) for §2.3.
- Cite Tibbits explicitly when borrowing the *"Robot unlike robot"* / *"Robot without robot"* framing for §2.3 title.

---

## 2.3 Robot Unlike Robot

**Role:** *Position* the thesis against existing robotic systems. This is the section where the literature delivers the gap. Borrows title from Tibbits (cite explicitly).

### Sub-section structure (three sub-sections, each ~½ page)

#### 2.3.1 Soft Robotics — Compliance Without Comparability

**Argument:** Soft robotics has demonstrated remarkable compliance and material intelligence, but its design language is largely *monolithic* — a single continuous body whose behavior is hard to compare across designs because there is no shared structural primitive.

*Systems to cite:*
- Rus & Tolley 2015 *Nature* — review, foundational reference for the field
- Wait et al. 2010 — pneumatic spherical rolling robot (single body, no modularity)
- Usevitch et al. 2020 *Science Robotics* — untethered isoperimetric soft robot in octahedral configuration (closest to your geometric framing, but not modular and only one shape)
- Mousa, Comoretto, Overvelde, Forte — fluidic units, self-synchronization (relevant to soft control)
- Brief mention: octopus-inspired manipulators, soft grippers as the broader family.

*Closing point:* These systems show what compliance can do. They do not provide a way to compare configurations under shared geometric constraints.

#### 2.3.2 Modular Reconfigurable Robotics — Comparability Without Compliance

**Argument:** MRR offers exactly what soft robotics lacks — comparable units, design spaces that can be enumerated and studied. But almost all MRR is *rigid*; reconfigurability lives in mechanical re-attachment or joint angles, not in the body's material behavior.

*Systems to cite:*
- Yim et al. 2007 *IEEE RAM* — modular self-reconfigurable robots review (must cite per advisor expectation)
- Ahmadzadeh & Masehian 2015 — review
- Romanishin et al. 2013 — M-Blocks (rigid cube tumbling via internal flywheel)
- Rubenstein et al. 2014 — Kilobots (rigid swarm)
- Chin et al. 2023 *RA-L* — AuxBots (rigid auxetic shells, modular flipper-style locomotion)
- Yu et al. 2026 — agile legged locomotion in reconfigurable MRR (RL, bottom-up but rigid)

*Closing point:* These systems show what comparable design spaces look like. They block exactly the passive material coupling that makes soft systems interesting.

#### 2.3.3 At the Boundary — Soft + Modular + Reconfigurable

**Argument:** A few systems sit at or near the intersection. Each pays a different price; none asks the question this thesis asks.

*Systems to discuss (positioning, not exhaustive):*
- Nozaki et al. 2018 — Mochibot (32-leg radial skeleton, rhombic triacontahedron, continuous shape-changing). *Polyhedral structure as design primitive — closest to your framing — but rigid, top-down gait planning, maximizes DOF.*
- NASA SUPERball / tensegrity icosahedral robots (Sunspiral et al.). *Polyhedral and compliant via tensegrity — but uses cables and rigid struts, not pneumatic modules; not modular in the sense of swappable units.*
- Li et al. 2019 *Nature* — particle robots. *Soft-edged collective locomotion from minimal local rules — but agents do not maintain topological configuration; the "configuration" is dynamic and emergent rather than designed.*
- Tibbits self-assembly lab — programmable matter. *Configuration is the output of the matter, but not a controlled design variable for studying locomotion.*
- Wang et al. 2024 — Robo-Matter, *Nat Comm*. *Reconfigurable smart materials, but small scale, no locomotion focus.*

*Comparison table* (recommended — matches your existing positioning data):

| System | Modular? | Soft? | Topological comparison? | Locomotion via inflation? |
|--------|----------|-------|------------------------|---------------------------|
| Wait et al. 2010 | No | Yes (pneumatic) | No | Yes |
| Usevitch et al. 2020 | No | Yes | Single config | Partial |
| Chin et al. 2023 (AuxBot) | Yes | No (rigid auxetic) | Limited | No |
| Nozaki et al. 2018 (Mochibot) | No (monolithic) | Partially | No (single shape) | No |
| Yu et al. 2026 (MRR) | Yes | No | Yes (rigid) | No |
| Li et al. 2019 (particles) | Yes (collective) | Partial | Emergent only | No |
| **This thesis** | **Yes (vertex modules)** | **Yes (pneumatic)** | **Yes (cospherical family)** | **Yes** |

#### 2.3.4 The Gap — Closing the Chapter

**Argument:** Combining the readings of §2.1 and §2.2 with the systems surveyed here, a precise gap emerges.

*Synthesis sentences (these are draft transitions you can use verbatim):*

> "Existing soft robots demonstrate that matter performs computational work, but their monolithic form makes it difficult to ask how the *arrangement* of compliant elements shapes that work. Existing modular robots demonstrate that arrangement can be studied as a design variable, but their rigid construction blocks the passive material coupling that makes the question of arrangement interesting in the first place. Between these two traditions lies a thinly populated region: systems that are simultaneously soft, modular, and reconfigurable, in which both compliance and configuration can be varied and compared on shared terms."

> "It is in this region that the thesis is sited. The chapters that follow develop a geometric design framework — the *cospherical polyhedral primitive* — that operationalizes this region, allowing different topological configurations of identical inflatable modules to be designed, fabricated, simulated, and tested under one comparative language."

### Key transition sentences

**Section opener:**
> "Two robotic traditions have engaged with the dialectics of Chapter 1, each from a different side. Soft robotics has taken matter seriously but design comparability lightly; modular reconfigurable robotics has taken comparability seriously but compliance lightly. This section reads each in turn, then identifies the region they leave open."

**Section closer (transition to Ch.3):**
> "What this region requires is a design framework that holds compliance and configuration together — that lets the geometric arrangement of soft modules be specified and varied without losing comparability across designs. Such a framework is the subject of the next chapter."

### Watch out for
- Don't enumerate every soft robot or every MRR. Pick ~5 per category — enough to support the argument, not a survey.
- The comparison table is your strongest asset here. Lead with it visually and let the prose support it, rather than the other way around.
- Tibbits *"Robot without robot"* — explicit citation needed early in the section, ideally in the first paragraph that uses the title's framing.

---

## Cross-section reminders

- **Avoid double-citing the same paper for the same argument across sections.** Pfeifer & Bongard 2007 belongs in §2.2; if cited again in §2.1 or §2.3, only for a different argument.
- **Section length budget:** §2.1 ≈ 3–4 pages, §2.2 ≈ 3–4 pages, §2.3 ≈ 5–7 pages (the longest, since it carries the gap). Total chapter ≈ 12–15 pages.
- **Transition discipline:** every section ends by naming what the next section addresses. The chapter as a whole ends by naming what Ch.3 does.

---

## Open questions to resolve before drafting

1. **Citations you want to use that aren't on this list?** I built from your memory's Stage 2 reference list and the DryRun positioning data. If you've added papers since (especially anything from Pangaro's cybernetic side that you still want to keep, even minimally), tell me where it lands.
2. **Comparison table placement.** I put it in §2.3.3. You could also put it earlier (as the section's anchor) or in §2.3.4 (as part of the gap statement). Your call.
3. **Sub-section numbering vs. continuous prose.** §2.3 has four sub-sections (2.3.1–2.3.4) in this outline. Some thesis conventions keep §2.3 as continuous prose without numbered sub-sections. Which does your committee prefer?
