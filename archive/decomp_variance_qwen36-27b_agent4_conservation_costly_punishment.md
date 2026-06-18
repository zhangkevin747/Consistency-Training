# Decomposition component-variance probe

**Question:** `agent4_conservation_costly_punishment.yaml`
**Model:** qwen/qwen3.6-27b  ·  N=32 per component  ·  temp 1.0

**Hypothesis (H):** The capacity for costly punishment is the primary mechanism that allowed large-scale human cooperation to evolve beyond what kin selection and direct reciprocity could sustain.

**Evidence (E):** In evolutionary game-theoretic models of large groups, costly punishment can stabilize any individually costly behavior — not just cooperation. A population in which the prevailing norm is an arbitrary individually costly behavior, and in which individuals punish deviations from that norm, can resist invasion by non-punishing mutants just as effectively as a population whose norm is cooperation.

## Component variance
| component | n | mean | sd | min | max |
|---|---|---|---|---|---|
| a_P(H) | 32 | 0.534 | **0.142** | 0.30 | 0.80 |
| e_P(E) | 32 | 0.787 | **0.228** | 0.10 | 0.95 |
| p1_P(H|E) | 32 | 0.308 | **0.168** | 0.10 | 0.75 |
| p0_P(H|~E) | 31 | 0.705 | **0.199** | 0.20 | 0.90 |

LTP on means: P(H) 0.534 vs implied 0.393 (residual +0.142)

### per-component sorted samples
- a_P(H): [0.3, 0.35, 0.35, 0.35, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.45, 0.45, 0.45, 0.45, 0.5, 0.5, 0.5, 0.55, 0.6, 0.6, 0.6, 0.62, 0.65, 0.65, 0.65, 0.65, 0.7, 0.7, 0.72, 0.75, 0.8, 0.8]
- e_P(E): [0.1, 0.2, 0.2, 0.3, 0.7, 0.75, 0.8, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.92, 0.95]
- p1_P(H|E): [0.1, 0.1, 0.1, 0.15, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.25, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.4, 0.4, 0.5, 0.6, 0.7, 0.7, 0.75]
- p0_P(H|~E): [0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.6, 0.7, 0.75, 0.75, 0.75, 0.75, 0.75, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.9, 0.9]
