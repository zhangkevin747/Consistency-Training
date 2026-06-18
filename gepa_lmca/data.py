"""Load + split the LMCA dataset (private; lives in gitignored data/lmca/)."""
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "data", "lmca", "shared_dataset_v2-0.jsonl")


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def load_lmca(path=DEFAULT_PATH, min_crits=2):
    """Each item: {argument, tags, critiques:[{text, human_overall, n_raters,
    rater_overall:{rater->overall}, ratings}]}. Keeps args with >=min_crits rated."""
    rows = [json.loads(l) for l in open(path)]
    out = []
    for r in rows:
        crits = []
        for c in r.get("critiques", []):
            rater_overall = {}
            for rater, lst in c.get("ratings", {}).items():
                ovs = [float(it["overall"]) for it in lst
                       if isinstance(it.get("overall"), (int, float))]
                if ovs:
                    rater_overall[rater] = _mean(ovs)
            if not rater_overall:
                continue
            crits.append({
                "text": c["text"],
                "human_overall": _mean(list(rater_overall.values())),
                "n_raters": len(rater_overall),
                "rater_overall": rater_overall,
                "ratings": c.get("ratings", {}),
            })
        if len(crits) >= min_crits:
            out.append({"argument": r["argument"], "tags": r.get("tags", []),
                        "critiques": crits})
    return out


def split(items, seed=0, fracs=(0.5, 0.3, 0.2)):
    """train (feedback) / val (pareto) / test."""
    idx = list(range(len(items)))
    random.Random(seed).shuffle(idx)
    n = len(items)
    a = int(n * fracs[0])
    b = a + int(n * fracs[1])
    pick = lambda I: [items[i] for i in I]
    return pick(idx[:a]), pick(idx[a:b]), pick(idx[b:])


def ec_scoreable(items, gold="Emery Cooper", min_crits=2):
    """Keep positions with >= min_crits critiques rated by the gold rater."""
    out = []
    for it in items:
        n = sum(1 for c in it["critiques"] if c["rater_overall"].get(gold) is not None)
        if n >= min_crits:
            out.append(it)
    return out


def kfold(items, k=5, seed=0):
    """Yield (fold_index, train_pool, test_fold). train_pool = all other folds."""
    idx = list(range(len(items)))
    random.Random(seed).shuffle(idx)
    folds = [[] for _ in range(k)]
    for pos, i in enumerate(idx):
        folds[pos % k].append(items[i])
    for f in range(k):
        test = folds[f]
        train_pool = [it for g in range(k) if g != f for it in folds[g]]
        yield f, train_pool, test


if __name__ == "__main__":
    items = load_lmca()
    npairs = sum(len(it["critiques"]) * (len(it["critiques"]) - 1) // 2 for it in items)
    print(f"{len(items)} args with >=2 rated critiques; "
          f"{sum(len(it['critiques']) for it in items)} critiques; "
          f"{npairs} within-arg critique pairs")
    tr, va, te = split(items)
    print(f"split: train {len(tr)}  val {len(va)}  test {len(te)}")
