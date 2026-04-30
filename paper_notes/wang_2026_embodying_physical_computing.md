# Wang et al. 2026 — Embodying Physical Computing into Soft Robots

**Type:** Perspective paper, *Nature Communications* (2026)
**Authors:** Jun Wang, Ziyang Zhou, Ardalan Kahak, Suyi Li (Virginia Tech)
**Citation key:** `wangEmbodyingPhysicalComputing2026`

## Core Claim

The "final frontier" for soft robotics is *softening and onboarding computers and controllers themselves*. The paper proposes a formal framework for **physical computing** in soft robots and distinguishes three strategies: analog oscillators, physical reservoir computing (PRC), and physical algorithmic computing (mechanical logic gates).

## Important Conceptual Distinction (be careful when citing)

Wang et al. **deliberately distinguish** physical computing from morphological computation:
- *Morphological computation* = soft body's compliance simplifies control (e.g., a tentacle wrapping an object with one global pressure input). They acknowledge this is "intelligence by mechanics" but say it does NOT meet their definition of physical computing because it lacks the encoding–kernel–decoding architecture and is not reprogrammable.
- *Physical computing* (their framework) = explicit input encoding into a mechanical kernel, internal interactions evolve to produce output, output decoded — and the evolution can be re-programmed.

> "Some non-conventional and innovative computing paradigms in the robotics field, such as the aforementioned 'morphological computation,' are physically computing in this paper because they do not have the 'encoding-kernel evolution-decoding' architecture, and they are not reprogrammable." (p. 2)

**Implication for citation:** If we cite Wang 2026 as evidence for "the body computes," we should cite it for the *broader phenomenon* of softness-facilitated control, **not** as direct support for "morphological computation = physical computing." Better yet, cite it as evidence that "the field is actively trying to push computational work into soft material structures."

## Quotable Passages

> "The dream of creating entirely soft, versatile, and capable robots—akin to the octopus—has long inspired scientists and engineers... Yet, softening and onboarding computers and controllers remain a major challenge and present one of the final frontiers towards robust and intelligent soft robots." (p. 1)

> "Soft and rotating legs can naturally accommodate uneven surfaces and large obstacles, allowing the robot to traverse challenging terrains without complex controls like in the quadrupeds. Soft curling tentacles can wrap and entangle themselves around objects with widely different shapes, thus manipulating them with a simple global pressure input. Such softness-facilitated control is sometimes referred to as 'intelligence by mechanics' or 'morphological computation.'" (p. 1)

> "Roboticists have long recognized that the inherent material softness can facilitate and simplify control" (p. 1)

## Relevance to §2.1 (Soft + Pneumatic)

The paragraph quoted above (p. 1, "Soft and rotating legs...") is the **strongest single passage in the paper for §2.1's argument**. It compactly demonstrates:
1. Soft material → less explicit control needed (terrain compliance, object wrapping)
2. "Simple global pressure input" → complex behavior — directly supports the user's pneumatic-as-coarse-actuator argument
3. The field has a name for this: "intelligence by mechanics" / "morphological computation"

Use this for: the §2.1 paragraph that argues *"a property the controller would otherwise need to specify is instead absorbed by the material's own response to a small pneumatic input."*

## Relevance to Other Sections

- **§2.2 (Morphological computation):** Wang 2026's distinction between morphological computation and physical computing is **directly relevant**. §2.2 should cite this paper to acknowledge that "morphological computation" is the loose label for what soft bodies do, even if rigorous reformulations (like Wang's framework) push toward stricter definitions.
- **§2.4 (Emergence/control):** The paper's discussion of "less control input → richer behavior" connects to bottom-up/local-rule arguments. PRC and analog oscillator examples are particularly relevant.

## Watch out for / Nuances

1. This is a **Perspective paper, not a primary research paper** — cite as a framing/positioning reference, not as experimental evidence.
2. Don't claim Wang 2026 "demonstrates morphological computation" — the paper specifically argues for a sharper distinction that *excludes* MC from the strict physical-computing category.
3. The 2026 publication year means it's contemporary with this thesis — useful for showing the field is still actively defining its boundaries.
