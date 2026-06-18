# GEPA → LMCA: implementation plan (for review)

**Goal.** Use GEPA (reflective prompt evolution) to optimize the *judge rubric prompt* so the
model's critique ratings better match human ratings on LMCA — i.e. lower the weighted pairwise
ranking error. Primary strategy: optimize the real metric directly. Secondary: wire in the
**consistency** signal as an alternate optimization target to test the north-star question
(does pushing consistency pull competence?).

---

## 1. What GEPA is (the parts that matter here)

- Maintains a **pool of candidate prompts**; each iteration: pick a candidate (Pareto-based),
  run it on a small **minibatch** (≈3), collect **execution traces + textual feedback**, and ask a
  **reflection LLM** to *rewrite* the prompt to fix the diagnosed failures. If the new prompt beats
  the old on the minibatch, evaluate it on a **Pareto validation set** and add it to the pool.
- **Selection is Genetic-Pareto**: keep candidates that are best on *some* instance (not just the
  global best), sample ∝ how many instances they win → preserves diverse "winning strategies."
- **Key difference from GRPO**: the learning signal is *natural-language feedback* (which pair was
  misranked and why), not a scalar. GEPA reports ~10–20% over GRPO at up to **35× fewer rollouts**.
- Library: [`gepa-ai/gepa`](https://github.com/gepa-ai/gepa) — `gepa.optimize(seed_candidate,
  trainset, valset, task_lm, reflection_lm, max_metric_calls)` + a custom **`GEPAAdapter`** whose
  `evaluate(candidate) -> (score, feedback_text)` is where we plug LMCA. Paper: arXiv:2507.19457.

## 2. The LMCA data (already extracted to `data/lmca/`, gitignored, private)

- `shared_dataset_v2-0.jsonl`: **311 arguments**, **716 critiques**, **1187 ratings** from 6 raters
  (Cooper, Kastner, Nguyen, Oesterheld, Finnveden, Gloor).
- Each critique → `text` + `ratings[rater] = [{overall, correctness, centrality, strength, clarity,
  dead weight, single issue}]`, all floats in [0,1]. `overall` mean 0.33.
- critiques/argument ranges 0–13 (drop args with <2 rated critiques — can't form a pair).
- **Human gold = Emery Cooper's `overall`** (the primary rater, 946 ratings) — this matches the
  paper's Table 5 benchmark, which scores models vs Emery Cooper. (We do NOT use mean-over-raters;
  the paper benchmarks against the single primary rater, so EC is the comparable target.)
- Seed judge prompt: `Judge prompts/…rubric_v3….json` → `instructions` field (**62,713 chars**).

## 3. The metric (μ) and feedback (μf)

**Metric — weighted pairwise ranking error** (matches Caspar's "weighted pairwise ranking error
rate", range-compression-immune). For each argument, over all critique pairs (A,B) whose *human*
overall differs:
- model is correct on the pair if it orders A,B the same way humans do;
- weight each pair by `|human_overall(A) − human_overall(B)|` (big-gap pairs matter more);
- `error = Σ weight·[misordered] / Σ weight`; GEPA **score = 1 − error**.
- ⚠️ Confirm against their exact App B.1 definition (within-argument vs global pairs, tie handling).

**Feedback (μf) — the GEPA payload.** For misranked pairs in the minibatch, emit text like:
> Argument: «…». Critique A (human 0.80) vs B (human 0.20): your rubric scored A=0.40, B=0.55 →
> **misordered**. Your stated reasoning for A emphasized «…»; for B «…». The higher-rated critique
> here was more «…». Consider what your rubric is under/over-weighting.

This per-pair disagreement diagnostic is what the reflection LM mutates the rubric from — far
richer than the scalar. Include the model's own explanation (rubric has `include_explanation`).

## 4. GEPA wiring

| GEPA component | LMCA choice |
|---|---|
| seed_candidate | `{"rubric": <production instructions>}` (single module to start) |
| task_lm | the judge model under optimization — **decide**: mid-tier (gpt-4.1-mini / Qwen) leaves headroom for the prompt to help; frontier = stronger baseline, less headroom |
| reflection_lm | strong model (GPT-5 / Opus 4.8) to rewrite the rubric |
| trainset (𝒟_feedback) | ~150 args for minibatches |
| valset (𝒟_pareto) | ~100 args, full-eval ranking score per candidate |
| held-out test | ~61 args (+ optional by-`tags` split for transfer) never seen during search |
| max_metric_calls | start 150–300 (each call = judge one argument's critiques) |

## 5. Code structure (`gepa_lmca/`)

- `data.py` — load jsonl, aggregate human gold, filter ≥2 critiques, make train/val/test splits
  (seeded; optional tag-stratified for transfer).
- `judge.py` — run a rubric prompt on (argument, critique) via API → parsed `{overall,…}` +
  explanation. Allowed paid endpoints only (LMCA must stay off free OpenRouter).
- `metric.py` — `weighted_pairwise_error(arg, model_scores)` → (score, per-pair feedback text).
- `adapter.py` — `LMCAAdapter(GEPAAdapter)`: `evaluate(candidate, batch)` runs judge over a batch,
  returns (mean score, concatenated feedback); `make_reflective_dataset()`.
- `run_gepa.py` — calls `gepa.optimize(...)`; logs candidate lineage; saves best rubric + test score.
- `eval_baseline.py` — score the seed rubric on test (the number to beat).

## 6. Secondary: the consistency arms (the research question)

Reuse the *same* harness, swap μf:
- **Arm A (this plan's core):** μ = LMCA ranking error. Distills humans; ceiling = human agreement.
- **Arm B:** μ = variance-normalized paraphrase **consistency** (Caspar's unbiased
  `(E[X]−E[Y])²` estimator, normalized by dataset variance). Optimize consistency, **eval on LMCA**.
  Tests: does pushing consistency pull competence? (Our within-model results predict it may not —
  watch for the range-compression degenerate, which the normalization is meant to block.)
- **Arm C:** optimize consistency on domain X, eval LMCA on held-out domain Y (label-free transfer —
  the scalable-oversight payoff).

## 7. Risks / decisions to confirm before coding

1. **62k-char seed rubric** is large to reflect over. Options: let GEPA edit it whole, modularize
   into sections, or seed from a distilled rubric. — recommend modularize after a whole-prompt run.
2. **Exact weighted-pairwise-ranking-error** definition (need their writeup App B.1).
3. **task_lm choice** (headroom vs baseline strength).
4. **Rater aggregation** under uneven coverage / disagreement (mean vs rater-weighted).
5. **Cost/endpoints**: paid API only for LMCA; estimate ≈ max_metric_calls × |critiques| judge calls.

## 8. Milestones

1. `data.py` + `eval_baseline.py` → reproduce a sane seed-rubric ranking score (sanity vs Caspar).
2. `judge.py` + `metric.py` with feedback text (unit-test the metric on a toy ordering).
3. `adapter.py` + `run_gepa.py`, small run (max_metric_calls=50) end-to-end.
4. Full Arm A run; report test ranking score vs seed; inspect the evolved rubric.
5. Arms B/C using the same harness.
