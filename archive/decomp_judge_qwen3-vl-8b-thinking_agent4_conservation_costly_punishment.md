# Decomposition component rollouts — Opus judge scores

**Question:** `agent4_conservation_costly_punishment.yaml`
**Model:** qwen/qwen3-vl-8b-thinking (N=32/component, temp 1.0)  ·  **Judge:** Opus 4.8

**H:** The capacity for costly punishment is the primary mechanism that allowed large-scale human cooperation to evolve beyond what kin selection and direct reciprocity could sustain.

**E:** In evolutionary game-theoretic models of large groups, costly punishment can stabilize any individually costly behavior — not just cooperation. A population in which the prevailing norm is an arbitrary individually costly behavior, and in which individuals punish deviations from that norm, can resist invasion by non-punishing mutants just as effectively as a population whose norm is cooperation.

Each cell is mean±sd of the Opus rubric score across 32 rollouts of that component.

| component | acceptability | relevance | sufficiency | reasonableness | calibration | overall | credSD |
|---|---|---|---|---|---|---|---|
| a_P(H) | 0.76±0.11 | 0.82±0.09 | 0.52±0.07 | 0.57±0.09 | 0.55±0.20 | 0.56±0.08 | 0.18 |
| e_P(E) | 0.27±0.23 | 0.33±0.27 | 0.18±0.15 | 0.18±0.16 | 0.30±0.23 | 0.20±0.16 | 0.35 |
| p1_P(H|E) | 0.23±0.28 | 0.26±0.33 | 0.13±0.18 | 0.13±0.19 | 0.15±0.21 | 0.13±0.18 | 0.17 |
| p0_P(H|~E) | 0.23±0.31 | 0.22±0.30 | 0.11±0.16 | 0.12±0.18 | 0.21±0.23 | 0.13±0.17 | 0.22 |

**Agreement check:** variance probe flagged P(E) as least stable and P(H|E) as
sign-inverted (P(H|E) > P(H|¬E) on an undercutting evidence). Does the judge
independently score P(H|E) / P(E) reasoning worst?
