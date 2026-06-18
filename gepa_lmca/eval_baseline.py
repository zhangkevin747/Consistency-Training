"""Score the seed production rubric on a split -> weighted pairwise ranking error
+ bootstrap CI. This is the number GEPA must beat.

Usage: python eval_baseline.py [split=test] [--limit N]
Caches per-critique predictions to data/lmca/preds_<model>.jsonl (gitignored).
"""
import json
import os
import sys
import threading
import random
import statistics as st
from concurrent.futures import ThreadPoolExecutor

import hashlib
from data import load_lmca, split, ec_scoreable
from judge import load_openrouter_key, run_judge, TASK_MODEL, DIMS
from prompt import build_prompt, SEED_GUIDANCE
from metric import dataset_error, inter_rater_ceiling

# cache must be invalidated when the model OR the prompt (guidance/rubric) changes
PROMPT_HASH = hashlib.md5((TASK_MODEL + SEED_GUIDANCE
                           + build_prompt("", "", "")).encode()).hexdigest()[:10]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONCURRENCY = int(os.environ.get("CONCURRENCY", "12"))
CACHE = os.path.join(ROOT, "data", "lmca",
                     f"preds_{TASK_MODEL.replace('/', '_')}.jsonl")
_lock = threading.Lock()


def load_cache():
    d = {}
    if os.path.exists(CACHE):
        for line in open(CACHE):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            d[r["key"]] = r["scores"]
    return d


def append_cache(key, scores):
    with _lock:
        with open(CACHE, "a") as f:
            f.write(json.dumps({"key": key, "scores": scores}) + "\n")


def bootstrap_ci(items, model_scores, n=1000, seed=0):
    rnd = random.Random(seed)
    errs = []
    idx = list(range(len(items)))
    for _ in range(n):
        samp = [rnd.choice(idx) for _ in idx]
        e = dataset_error([items[i] for i in samp], [model_scores[i] for i in samp])
        if e is not None:
            errs.append(e)
    errs.sort()
    return errs[int(0.025 * len(errs))], errs[int(0.975 * len(errs))]


def main():
    which = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "test"
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    key = load_openrouter_key()  # seed = production rubric with SEED_GUIDANCE injected

    items = ec_scoreable(load_lmca())   # same population GEPA optimizes/evaluates on
    tr, va, te = split(items)
    data = {"train": tr, "val": va, "test": te, "all": items}[which]
    if limit:
        data = data[:limit]

    # global stable key per (argument, critique) so cache survives re-splits
    gidx = {id(it): i for i, it in enumerate(items)}
    cache = load_cache()
    tasks = []
    for it in data:
        ai = gidx[id(it)]
        for ci, c in enumerate(it["critiques"]):
            k = f"{PROMPT_HASH}:{ai}:{ci}"
            if k not in cache:
                tasks.append((k, it["argument"], c["text"]))
    print(f"model={TASK_MODEL}  split={which}  args={len(data)}  "
          f"to-judge={len(tasks)} (cached {sum(len(it['critiques']) for it in data)-len(tasks)})")

    def run(t):
        k, arg, crit = t
        sc, _ = run_judge(key, build_prompt(SEED_GUIDANCE, arg, crit))
        sc = sc or {}
        append_cache(k, sc)
        return k, sc
    if tasks:
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
            for i, (k, sc) in enumerate(ex.map(run, tasks), 1):
                cache[k] = sc
                if i % 25 == 0:
                    print(f"  {i}/{len(tasks)}", flush=True)

    # assemble model scores aligned to data; missing/parse-fail -> 0.5 (neutral)
    model_scores = []
    nfail = 0
    for it in data:
        ai = gidx[id(it)]
        row = []
        for ci in range(len(it["critiques"])):
            sc = cache.get(f"{PROMPT_HASH}:{ai}:{ci}", {})
            if "overall" not in sc:
                nfail += 1
            row.append(sc.get("overall", 0.5))
        model_scores.append(row)

    err = dataset_error(data, model_scores)
    lo, hi = bootstrap_ci(data, model_scores)
    ceiling = inter_rater_ceiling(data)
    print(f"\n=== SEED RUBRIC on {which} ===")
    print(f"weighted pairwise ranking error = {err:.3f}   95% CI [{lo:.3f}, {hi:.3f}]")
    print(f"human inter-rater ceiling (this split) = {ceiling:.3f}")
    print(f"random ~0.162 (paper 0.173) ; frontier ~0.08 ; parse-fails: {nfail}")
    print(f"addressable gap seed->ceiling = {err-ceiling:.3f}  "
          f"(a 'very significant' GEPA win ≈ -{(err-ceiling)/3:.3f} to -{(err-ceiling)/2:.3f})")


if __name__ == "__main__":
    main()
