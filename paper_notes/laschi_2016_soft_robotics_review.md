# Laschi, Mazzolai, Cianchetti 2016 — Soft Robotics: Technologies and Systems Pushing the Boundaries of Robot Abilities

**Type:** Review article, *Science Robotics* (vol. 1, eaah3690, December 2016)
**Authors:** Cecilia Laschi (Scuola Superiore Sant'Anna), Barbara Mazzolai (IIT), Matteo Cianchetti
**Citation key:** `laschi_soft_2016`
**Importance:** Field-state review focused on *what abilities* soft robotics enables, complementing Rus & Tolley 2015 (which is more about *materials and methods*).

## Definition Adopted

The paper deliberately adopts the **RoboSoft community definition**, distinct from Rus & Tolley's modulus-based definition:

> "Soft robots/devices that can actively interact with the environment and can undergo 'large' deformations relying on inherent or structural compliance." (p. 1, citing RoboSoft)

This is a **functional** rather than **material** definition. Useful when arguing that soft robotics is about *how the robot interacts with its environment*, not just what it's made of.

## The "Spectrum" Framing

A major contribution of this review is **Figure 1: a pictorial spectrum** from "mostly stiff with a few selectively compliant elements" → "entirely soft." Concrete systems on the spectrum:

- iSprawl, X-RHex (mostly stiff, locally compliant)
- Soft fish, OCTOPUS (rigid frame + soft arms)
- PoseiDRONE, soft grippers, origami robots
- Tuft Softworm, rehab glove, **inflatable robots**, Octobot (entirely soft)

For the thesis, this spectrum is useful: your modular inflatable robot sits toward the *entirely soft* end on each module, but with discrete connections — the spectrum isn't a clean axis for your work.

## Direct Mention of Inflatable Robots

> "Inflatable robots are based on multiple inflatable chambers whose shape determines the robot motion." (Fig. 1 caption, citing ref [52])

This is the **most direct prior framing** of inflatable robots in a major review — and crucially, Laschi et al. say *"shape determines the robot motion"*. The thesis's claim *"configuration is part of computation"* is essentially a sharper version of this 2016 statement.

## Three Load-Bearing Claims for §2.1

### Claim 1: Compliance enables embodied intelligence

> "One of the main benefits of the compliance possessed by soft robots is that they can implement embodied intelligence principles (for example, preflexes). They can also conform to surfaces or objects, absorb energy to maintain stability, and exhibit physical robustness and human-safe operation at potentially low cost." (p. 1)

(Note: "preflexes" = passive mechanical responses that play the role of reflexes without neural control — a useful term that's specific enough to be quotable.)

### Claim 2: Soft abilities are *qualitatively new*

> "Abilities such as squeezing, stretching, climbing, growing, and morphing would not be possible with an approach based only on rigid links." (Abstract)

### Claim 3: Future challenge is morphological adaptation

> "The challenge ahead for soft robotics is to further develop the abilities for robots to grow, evolve, self-heal, develop, and biodegrade, which are the ways that robots can adapt their morphology to the environment." (Abstract)

This grounds the *"morphology adapts to environment"* angle of morphological computation — useful for §2.2.

## Quotable Passages

> "The use of soft matter for building robots has been recognized as the current challenge for pushing the boundaries of robotics technologies." (p. 1)

> "The compliance and the elasticity of soft body parts allow reactions with interaction forces without control and support the bioinspired approach." (p. 1)

> "Inflatable robots are based on multiple inflatable chambers whose shape determines the robot motion." (Fig. 1 caption)

## Relevance Per Section

### §2.1 (Soft + Pneumatic) — *primary citation here*
- Pair with Rus & Tolley 2015 as the **two foundational soft robotics reviews**.
- Use Laschi et al. specifically when emphasizing **abilities** (squeezing, stretching, morphing) rather than **materials** (Rus & Tolley territory).
- The "inflatable robots: shape determines motion" line is a one-sentence precursor to the user's thesis statement — worth quoting in §2.1's opener or §2.2's bridge.

### §2.2 (Morphological computation) — *secondary*
- The "morphology adapts to environment" claim and "preflexes" framing connect to MC.
- But Laschi et al. is **not** a primary MC source — they cite the concept rather than develop it. Use Pfeifer for primary MC, Laschi as field-side endorsement.

### §2.3 / §2.4 — *not relevant*
- This review is about single-body soft robotics; doesn't cover modularity or emergence as primary topics.

## Strategic Note: Pairing Rus & Tolley with Laschi

These two reviews are usually cited together because they take complementary angles:

| | Rus & Tolley 2015 | Laschi et al. 2016 |
|---|---|---|
| Venue | *Nature* | *Science Robotics* |
| Focus | Design, fabrication, control (process) | Abilities, application spectrum (outcomes) |
| Definition basis | Material modulus | Functional behavior |
| Use as citation | "What soft robotics is" | "What soft robotics can do" |

In §2.1, citing both signals comprehensive grounding in the field's foundational literature.

## Watch out for / Nuances

1. **Definitional inconsistency**: Laschi et al. and Rus & Tolley adopt different definitions of "soft robot." The thesis should pick one (probably Rus & Tolley's modulus-based, since it's more rigorous) and acknowledge the existence of the other.
2. **"Preflexes"** is a term worth using sparingly — it's specific and academic, signals deeper familiarity, but unfamiliar readers may need a parenthetical gloss.
3. The paper is **2016** — the rapidly-growing soft robotics field has changed; for *current* state-of-the-field framing, pair with Wang 2026 (which is the 2026 perspective on where the field needs to go next).
