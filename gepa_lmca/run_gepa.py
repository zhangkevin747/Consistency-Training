"""5-fold cross-validated GEPA on LMCA (self-reflection).

For each fold: hold out the test fold; split the rest into feedback (minibatch
reflection) + pareto (selection); run GEPA to evolve only the {guidance} block;
evaluate the seed AND the evolved guidance on the held-out fold. Aggregate across
folds = a held-out estimate over the whole dataset, on the paper's metric (weighted
pairwise ranking error vs Emery Cooper).

task = reflection = gpt-5.4-mini (no external teacher -> no distillation).

Env: K=5  BUDGET=300 (max_metric_calls/fold)  FEEDBACK=50  CONCURRENCY=12
     TASK_MODEL=openai/gpt-5.4-mini  REFLECT_MODEL=openai/gpt-5.4-mini
Usage: python run_gepa.py            (real run — costs API; see cost_estimate.py first)
       python run_gepa.py --smoke    (1 fold, tiny budget, for a wiring check)
"""
import json
import os
import sys
import random
import statistics as st

import gepa

from data import load_lmca, ec_scoreable, kfold
from prompt import SEED_GUIDANCE, COMPONENT
from judge import load_openrouter_key, make_reflection_lm, TASK_MODEL, REFLECT_MODEL
from adapter import LMCAAdapter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Custom reflection prompt: the default tells the LM to write a COMPLETE instruction
# (task description, domain facts, OUTPUT FORMAT) — but our component is only the small
# reasoning-guidance slot inside a frozen rubric. This constrains it to stay in scope.
REFLECTION_TEMPLATE = """The text below is ONLY the "reasoning guidance" block of a larger, FIXED critique-judging prompt:
```
<curr_param>
```
CRITICAL: the rest of the judging prompt is FIXED and supplied elsewhere. You must NOT restate, redefine, contradict, or re-specify any of:
- the seven scoring dimensions (centrality, strength, correctness, clarity, dead weight, single issue, overall) or their definitions;
- the 0.0-1.0 scale or the few-shot examples;
- the REQUIRED OUTPUT FORMAT (a single ```json object with those seven keys per critique). Never mention or change the output format.
Doing any of the above breaks the judge (unparseable output) and is strongly penalized.

Below are positions the judge scored, with feedback on its ranking errors and its own reasoning:
```
<side_info>
```
Write improved REASONING GUIDANCE: concise instructions on HOW the judge should think when applying the fixed rubric — what to attend to, common mistakes to avoid, how to handle conditional reasoning / analogy / causation / overclaiming — informed by the errors above. Do NOT output a rubric, list dimensions, or specify any output format. Provide only the new guidance text within ``` blocks."""

K = int(os.environ.get("K", "5"))
FOLDS = int(os.environ.get("FOLDS", str(K)))      # how many folds to actually run
BUDGET = int(os.environ.get("BUDGET", "300"))     # max_metric_calls per fold
FEEDBACK = int(os.environ.get("FEEDBACK", "50"))  # feedback (minibatch) set size
VAL = int(os.environ.get("VAL", "0"))             # cap on pareto/valset size (0 = no cap)
CONCURRENCY = int(os.environ.get("CONCURRENCY", "12"))
MINIBATCH = int(os.environ.get("MINIBATCH", "3"))
OUTDIR = os.path.join(ROOT, "data", "lmca", "gepa_runs")


def err(adapter, items, candidate):
    """Held-out weighted ranking error = 1 - mean(position scores)."""
    eb = adapter.evaluate(items, candidate, capture_traces=False)
    return 1.0 - st.mean(eb.scores)


def main():
    smoke = "--smoke" in sys.argv
    key = load_openrouter_key()
    os.makedirs(OUTDIR, exist_ok=True)
    items = ec_scoreable(load_lmca())
    print(f"{len(items)} EC-scoreable positions | task={TASK_MODEL} reflect={REFLECT_MODEL}")
    adapter = LMCAAdapter(key, concurrency=CONCURRENCY)
    reflection_lm = make_reflection_lm(key)
    seed_candidate = {COMPONENT: SEED_GUIDANCE}

    k = 1 if smoke else K
    budget = 30 if smoke else BUDGET
    fold_results = []
    for f, train_pool, test in kfold(items, k=K, seed=0):
        if smoke:
            train_pool, test = train_pool[:8], test[:6]
        random.Random(100 + f).shuffle(train_pool)
        feedback = train_pool[:(4 if smoke else FEEDBACK)]
        pareto = train_pool[(4 if smoke else FEEDBACK):]
        if VAL:
            pareto = pareto[:VAL]
        print(f"\n=== FOLD {f} ===  feedback={len(feedback)} pareto={len(pareto)} test={len(test)}")

        result = gepa.optimize(
            seed_candidate=seed_candidate,
            trainset=feedback,
            valset=pareto,
            adapter=adapter,
            reflection_lm=reflection_lm,
            reflection_prompt_template=REFLECTION_TEMPLATE,
            reflection_minibatch_size=MINIBATCH,
            max_metric_calls=budget,
            candidate_selection_strategy="pareto",
            display_progress_bar=True,
            run_dir=os.path.join(OUTDIR, f"fold{f}"),
            seed=0,
        )
        best = result.best_candidate
        seed_err = err(adapter, test, seed_candidate)
        gepa_err = err(adapter, test, best)
        print(f"FOLD {f}: seed test err={seed_err:.3f}  ->  GEPA test err={gepa_err:.3f}  "
              f"(Δ={gepa_err-seed_err:+.3f})")
        fold_results.append({"fold": f, "seed_err": seed_err, "gepa_err": gepa_err,
                             "best_guidance": best[COMPONENT]})
        with open(os.path.join(OUTDIR, f"fold{f}_result.json"), "w") as fh:
            json.dump(fold_results[-1], fh, indent=2)
        if smoke or len(fold_results) >= FOLDS:
            break

    print("\n=== CV SUMMARY ===")
    se = st.mean(r["seed_err"] for r in fold_results)
    ge = st.mean(r["gepa_err"] for r in fold_results)
    print(f"folds={len(fold_results)}  seed CV err={se:.3f}  GEPA CV err={ge:.3f}  "
          f"improvement={se-ge:+.3f}")
    with open(os.path.join(OUTDIR, "cv_summary.json"), "w") as fh:
        json.dump({"seed_cv_err": se, "gepa_cv_err": ge, "folds": fold_results}, fh, indent=2)


if __name__ == "__main__":
    main()
