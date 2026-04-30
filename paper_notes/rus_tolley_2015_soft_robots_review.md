# Rus & Tolley 2015 — Design, Fabrication and Control of Soft Robots

**Type:** Review article, *Nature* (vol. 521, 2015)
**Authors:** Daniela Rus (MIT CSAIL), Michael T. Tolley (UC San Diego)
**Citation key:** `rusDesignFabricationControl2015`
**Importance:** **Canonical soft robotics review**, widely cited as the field-defining reference.

## Core Definition Provided by the Paper

> "We define soft robots as systems that are capable of autonomous behaviour, and that are primarily composed of materials with moduli in the range of that of soft biological materials." (p. 467)

Soft biological materials: Young's modulus ~10⁴–10⁹ Pa. Conventional robotics materials: ~10⁹–10¹² Pa. Three orders of magnitude separation.

## Three Load-Bearing Claims for §2.1

### Claim 1: Soft bodies are not "rigid members connected at discrete joints"

> "Conventionally, engineers have employed rigid materials to fabricate precise, predictable robotic systems, which are easily modelled as rigid members connected at discrete joints... Conventional approaches to robot control assume rigidity in the linkage structure of the robot and are a poor fit for controlling soft bodies, thus soft materials require new algorithms." (p. 467)

This is the *modeling-is-harder* side of the trade-off (matches the user's Consensus discussion point: *"软执行器…强非线性、耦合,往往需要数据驱动、reservoir computing 等新控制方式"*).

### Claim 2: Body and brain are coupled — "mechanical intelligence"

> "This tight coupling between body and brain allows us to think about soft-bodied systems as machines with **mechanical intelligence**, in which the body can be viewed as augmenting the brain with **morphological computation**. **This ability of the body to perform computation simplifies the control algorithms in many situations, blurring the line between the body and the brain.**" (p. 467, emphasis mine)

This is the *control-is-simpler* side of the trade-off (matches *"形体和被动顺应在帮你干活...intelligence by mechanics"*). It is **also** the strongest single quotable sentence from the paper for the thesis's overall argument that *configuration is part of computation*.

### Claim 3: Continuous deformability → high (effectively infinite) DOF

> "[Soft robots] have a continuously deformable structure with muscle-like actuation that emulates biological systems and results in a relatively large number of degrees of freedom compared with their hard-bodied counterparts." (p. 467)

This grounds the modeling-difficulty argument: rigid robots have 6 (or N×6) discrete DOFs; soft robots have continuum DOFs that classical kinematics cannot represent.

## Pneumatic-Specific Material in the Paper

- Discusses **fluidic elastomer actuators (FEAs)** and **pneu-nets** as primary soft actuation strategies.
- Notes the 1992 paper (Suzumori et al.) as the founding pneumatic-soft-actuator demonstration.
- Identifies the engineering trade-off: "high strains required for actuation can lead to slow actuation rates and rupture failures" — a useful caveat to mention if anyone asks why your thesis uses inflation-state primitives (D/I/H) rather than continuous pressure modulation.

## Quotable Passages

> "Soft robots have bodies made out of intrinsically soft and/or extensible materials (for example, silicone rubbers) that can deform and absorb much of the energy arising from a collision." (p. 467)

> "The key challenge for creating soft machines that achieve their full potential is the development of controllable soft bodies using materials that integrate sensors, actuators and computation, and that together enable the body to deliver the desired behaviour." (p. 467)

> "[The body augments] the brain with morphological computation. This ability of the body to perform computation simplifies the control algorithms in many situations, blurring the line between the body and the brain." (p. 467)

## Relevance Per Section

### §2.1 (Soft + Pneumatic) — *primary citation here*
- Use as the **definitional reference**: "Soft robots are robots whose bodies are composed of materials with moduli closer to biological tissue than to engineering materials" — citing Rus & Tolley.
- The "mechanical intelligence / morphological computation simplifies control" passage is the **central conceptual support** for the §2.1 argument that compliant material distributes computational work to the body.

### §2.2 (Morphological computation) — *secondary citation*
- The passage about "augmenting the brain with morphological computation" is also relevant in §2.2, but be careful not to double-cite Rus & Tolley as the *primary* MC reference — Pfeifer et al. is the proper primary. Rus & Tolley cite Pfeifer (refs 15, 16 in their text); use them as the soft-robotics-side endorsement of MC.

### §2.4 (Emergence) — *not relevant*
- The review is not about emergence or coordination — it is about a single-body field overview.

## Distinction from the Thesis Work

- Rus & Tolley survey the field as it stood in 2015 — primarily *monolithic single-body* soft robots (caterpillar, octopus arm, fish, etc.).
- The review explicitly notes "modular bodies consisting of soft rubber segments, which can be composed serially or in parallel to create complex morphologies" — but this is the **exception**, not the field's main thrust.
- The thesis works in the underexplored intersection: *modular* soft robots where modules are *comparable units* in a *topologically variable* configuration. This is largely outside Rus & Tolley's 2015 scope.

## Watch out for / Nuances

1. The review is now **10+ years old** at thesis time (2026). Field has moved on, especially toward learning-based control (cite Wang 2026 for the more recent state).
2. The paper does **not** itself argue for "configuration as design variable" — it argues for "soft material as design substrate." Don't over-claim it.
3. The "morphological computation" framing in this paper is *adopted from* Pfeifer et al. — when you want the *primary source* on MC, cite Pfeifer & Bongard 2007 / Pfeifer & Iida 2005 (in §2.2), not Rus & Tolley.
