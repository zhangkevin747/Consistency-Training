# Consistency Training — Experiment Log

Succinct summary of every small experiment, with sample sizes and effect sizes.
Through-line: **the model is better holistically than componentially.** Every reward built on
the *number* or the *componential structure* fails; the only thing that lit up is *holistic
self-verification*, and only at scale (27B).

Models: Gemma-3-4B and Qwen3-VL-8B-Thinking (early), Qwen3.6-27B (scale work). Judge: Opus 4.8 xhigh.

---

## 1. Judge validation (instrument check)
**Verdict: judge is real, the nulls are not its fault.**
- Sensitivity on gold pairs: injected self-contradiction 100% (5/5), off-topic 100% (5/5), vs no-reasoning stub 60% (3/5); overall 87%.
- Stability across swapped A/B order: 85% (n=20).
- **Qualification:** on *contested close* pairs the forced-binary verdict reproduces only ~50% (8/16 on t1_002). Perception validated; forced-choice protocol is noise-limited on incomparable pairs → all pairwise-measured nulls are attenuated toward 50%.

## 2. Type-1 consistency reward  R = −|v − T|  (consensus distance)
**Verdict: NULL — consensus T is the centroid of the model's errors, not the truth.**
- Self-gen questions, Gemma-4B: 192 pairs / 12 questions → near-consensus win **48%** (r≈0.08, p≈0.44).
- Qwen-8B reasoning model (rules out decoupling): win **48.6%**, r≈−0.12 (n.s.).
- Out-of-sample replication: **nothing replicated** — in-sample −0.27 came back +0.03; a promising calibration heuristic +0.28 (p=0.01) → +0.06 (p=0.65). Small-sample noise.
- Acorn (collaborators' own claims): 112 pairs → near-consensus win **42.9%**; all 6 pooled r slightly negative, n.s.
- **Caveat (deduction-rubric audit):** against per-rollout cited-error counts (not binary verdicts), the SAME reward DID track quality: Spearman(reward, deductions) = **−0.366 (p=0.0055, n=56)**; NEAR 14.2 vs FAR 17.0 errors (MW p=0.027). In-sample only.
- **Pre-registered OOS (2026-06-13):** 112 unselected rollouts, range-restricted (reward SD 0.069 vs 0.180). Predict support>0, correctness~0. **Result pending.**

## 3. Type-2 conjunction reward  (P(A∧B) ≤ P(A))
**Verdict: DEAD — no fallacy to exploit with valid phrasing.**
- Gemma-4B, explicit "BOTH A AND B" framing: 9/10 questions V = exactly 0 (1 had 0.032). Explicit framing debiases away the fallacy.
- Qwen-8B (thinking model) with valid transparent-entailment items: **0/12 violated.** Thinking model notices the nesting and respects the rule. To get violations you need a weaker model whose number is then decoupled from its reasoning.

## 4. T* reconciliation-as-target
**Verdict: NULL — bottleneck is reconciler capability (8B has a skeptic-flip bias).**
- Acorn, 5 questions w/ ≥2 camps, 80 pairs: T* = **51.3%** vs T = 46.3% (both coin flip, p=0.91).
- Failure is specific: reconciler flipped to the skeptical/low camp 5/5 questions (vs judge ~2/5). Worked spectacularly where the minority was right (t1_002: 0.25 → 0.75); hurt where majority was right. Quantifier slips ("some" → "most"). Reconciliation samples themselves bimodal.

## 5. Self-verification gap sweep (8B)  — 11+ self-derived signals
**Verdict: NULL at 8B — generator-verifier gap is zero to negative.**
Scored against 112 Opus pairwise judgments (chance = 50%):
- consensus-T 46% · reconciled-T* 51% · length/extremity/hedging 52–53% · self-judge plain 47% (71% of pairs flip with order) · self-judge+rubric 53% · critique-then-decide 39% · cross-variant composite 45% · reasoning-readback coupling 46% · constraint-web coherence 41% · crux-resolution 47.8%.
- Mechanism: (1) no stable self-preference (verdicts flip with position 71%); (2) readback coupling tight (mean |implied−stated| 0.025) — quality variance is in argument *selection*, not verbalization; (3) coherence-web partner beliefs are draws from the same unstable lottery → propagation compounds instability.

## 6. Scale diagnostic (27B) — the pivot
**Verdict: the gap is an 8B property, not a method property. Consensus reward INVERTS; self-verification SWITCHES ON.**
- 168 rollouts (24/q × 7 q), ~$40. 27B much better calibrated to Opus than 8B (|p−Opus| 0.276 vs 0.430).
- **Part A — consensus reward → quality goes NEGATIVE at scale:** within-Q Spearman(−|v−T|, rubric) support **−0.239**, mean5 −0.248 (8B was +0.398 in-sample). Tight confident attractor; better rollouts deviate from it. Strongest evidence to abandon the consensus reward.
- **Part B — self-verification:** 27B judging its own rollouts pairwise agrees with Opus winner **94.9% (37/39 decided, p=3e-9)**. Length confound checked: on 7 length-discordant pairs still chose quality 6/7. Genuine.

## 7. Logical coherence sweep (27B)  — does enforcing coherence move bias?
**Verdict: real violations exist, but enforcing them moves the WRONG way.**
- Violation magnitudes (0 = coherent): negation 0.033 (satisfied) · foolproof-prob 0.031 (satisfied) · **total-probability 0.244** (two cases ~0.60) · **entailment 0.55** (n=1). Real fuel where a marginal links to a conditional decomposition.
- **Direction check kills it:** direct marginal vs coherence-implied value vs Opus own-answers — **direct belief closer to Opus 3/4** (t1_013 direct 0.92 / implied 0.33 / Opus 0.91). The conditionals are the unreliable part; enforcing coherence corrupts a decent holistic answer. (n=4, Opus anchor.)

## 8. Decomposition-as-reward — three variants (law of total probability)
**Verdict: ALL THREE NULL under proper testing. Closes the decomposition line.**
Decompose P(H)=P(H|E)P(E)+P(H|¬E)(1−P(E)) in separate rollouts, turn implied v into a reward for direct rollouts. 18 questions (6 acorn + **12 fresh contested claims authored by the Opus 4.8 CLI**, removes hand-authoring bias). 27B: 280 directs + 216 decomps ($1.7); Opus judged all 280 ($58.6); decompositions clean (0/12 degenerate, gaps 0.40–0.90).
- **#1 point-selector** R = −|v − v_implied|: +0.27 at n=4 — but same artifact subset (t1_000/002/013).
- **#3 cloud/density** R = KDE density of v under implied distribution: mean ρ **+0.05**, worse than point; spread is inversion-instability junk (t1_013 multimodal fragmentation).
- **#2 direction/compass** R = (v−T)·sign(v_implied−T): contributes one bit/question. Stable-gradient hit rate **6/11 (p=0.50, chance)**; mean dir-ρ **−0.017**; best FIXED rule (humility prior) **+0.155** → decomposition LOSES to a constant rule by 0.173.
  - Mechanism = the artifact we guarded against: true within-Q quality gradient points DOWN 13/18 (hedged/lower answers score higher — a humility prior). The n=4 +0.247 came entirely from the subset where decomposition coincidentally aligned with that prior. On 12 fresh questions where they diverge, compass is at chance.
  - **Right-yardstick confirmation** (Opus own-answers as truth proxy, not the probability-blind rubric): compass points toward truth **8/18 (p=0.76)**; fresh 12 are 4/12 (below chance). v_implied is a WORSE point estimate than mode T (mean |v_imp−Opus| 0.214 vs |T−Opus| 0.174; decomp better only 5/18). Direct/mode beats decomposed 13/18.

---

## Bottom line
| Family | Result |
|---|---|
| Consensus reward −\|v−T\| | NULL at 8B, INVERTS at 27B |
| Conjunction (Type-2) | DEAD (no fallacy with valid phrasing) |
| T* reconciliation | NULL (reconciler capability bottleneck) |
| Self-verification (8B) | NULL (gap is zero/negative) |
| Logical coherence | Real violations, but enforcing moves wrong way |
| Decomposition reward (×3) | ALL NULL — componential layer doesn't rank rollouts |
| **Holistic self-verification (27B)** | **94.9% vs Opus — the only surviving lead** |
