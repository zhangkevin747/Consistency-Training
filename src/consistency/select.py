"""Screen rolled-out candidates down to the questions worth judging.

We over-generate candidates, roll them all out (cheap), and here keep only the ones that carry
real signal -- WITHOUT ever leading the model:

  Type 1: keep questions whose NEUTRAL phrasings genuinely disagree. spread = range of the
          per-phrasing mean probabilities; keep if spread >= SPREAD_MIN. This is the model's
          own unforced inconsistency -- exactly what the consistency reward is meant to catch.
  Type 2: keep questions that actually VIOLATE the conjunction on average,
          V = max(0, mean P(A and B) - mean P(A)) >= VIOLATION_MIN. Non-violating questions
          have no reward signal (V=0) and are dropped before any (expensive) judging.

Among the questions that pass, we keep the top N_KEEP_* by signal strength (spread / V). The
result is written to a selection CSV that the judge stage reads to decide what to compare.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from statistics import mean

import pandas as pd

from . import config as C
from .utils import read_jsonl


def _valid(rs: list[dict]) -> list[dict]:
    return [r for r in rs if r.get("parse_ok") and r.get("probability") is not None]


def screen(rollouts: list[dict], pilot: bool = False) -> pd.DataFrame:
    """One row per candidate question with its signal metric, threshold pass, and kept flag."""
    rows: list[dict] = []

    # ---- Type 1: natural phrasing spread ----
    t1 = [r for r in rollouts if r.get("type") == 1]
    by_q: dict[str, list[dict]] = defaultdict(list)
    for r in t1:
        by_q[r["question_id"]].append(r)
    for qid, rs in by_q.items():
        valid = _valid(rs)
        by_phrasing: dict[str, list[float]] = defaultdict(list)
        for r in valid:
            by_phrasing[r["group_kind"]].append(r["probability"])
        phrasing_means = [mean(v) for v in by_phrasing.values() if v]
        spread = (max(phrasing_means) - min(phrasing_means)) if len(phrasing_means) >= 2 else 0.0
        enough = len(valid) >= 2 * C.NEAR_FAR_Q
        passed = enough and spread >= C.SPREAD_MIN
        reason = ("ok" if passed else
                  "too few parses" if not enough else
                  f"spread {spread:.3f} < {C.SPREAD_MIN}")
        rows.append({"question_id": qid, "type": 1, "n_parse": len(valid),
                     "metric_name": "spread", "metric": round(spread, 4),
                     "passed": passed, "reason": reason})

    # ---- Type 2: average conjunction violation ----
    t2 = [r for r in rollouts if r.get("type") == 2]
    by_q2: dict[str, list[dict]] = defaultdict(list)
    for r in t2:
        by_q2[r["question_id"]].append(r)
    for qid, rs in by_q2.items():
        a = _valid([r for r in rs if r["group_kind"] == "A"])
        ab = _valid([r for r in rs if r["group_kind"] == "AandB"])
        V = (max(0.0, mean(r["probability"] for r in ab) - mean(r["probability"] for r in a))
             if a and ab else 0.0)
        # we judge the AandB group, so it must have enough parses to form near/far pairs
        enough = len(ab) >= 2 * C.TYPE2_Q and len(a) >= 1
        passed = enough and V >= C.VIOLATION_MIN
        reason = ("ok" if passed else
                  "too few parses" if not enough else
                  f"V {V:.3f} < {C.VIOLATION_MIN}")
        rows.append({"question_id": qid, "type": 2, "n_parse": len(a) + len(ab),
                     "metric_name": "V", "metric": round(V, 4),
                     "passed": passed, "reason": reason})

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # rank passing questions by signal strength within each type; keep the top N_KEEP_*
    keep_n = ({1: C.PILOT_KEEP_TYPE1, 2: C.PILOT_KEEP_TYPE2} if pilot
              else {1: C.N_KEEP_TYPE1, 2: C.N_KEEP_TYPE2})
    df["kept"] = False
    df["rank"] = pd.NA
    for t, grp in df.groupby("type"):
        order = grp[grp["passed"]].sort_values("metric", ascending=False)
        keep_ids = list(order["question_id"].head(keep_n[t]))
        df.loc[df["question_id"].isin(keep_ids), "kept"] = True
        for rk, qid in enumerate(keep_ids):
            df.loc[df["question_id"] == qid, "rank"] = rk
    return df


def select(pilot: bool = False) -> pd.DataFrame:
    rollouts = read_jsonl(C.rollouts_file(pilot))
    if not rollouts:
        raise SystemExit(f"no rollouts at {C.rollouts_file(pilot)} -- run sample_rollouts first")
    df = screen(rollouts, pilot=pilot)
    out = C.selection_file(pilot)
    df.to_csv(out, index=False)

    for t, label in ((1, "Type-1 (phrasing spread)"), (2, "Type-2 (conjunction V)")):
        g = df[df["type"] == t]
        if len(g):
            kept = g[g["kept"]]
            mvals = kept["metric"]
            rng = f"{mvals.min():.3f}-{mvals.max():.3f}" if len(kept) else "n/a"
            print(f"  {label}: kept {len(kept)}/{len(g)} candidates "
                  f"({int(g['passed'].sum())} passed threshold); kept metric range {rng}")
    print(f"Wrote selection -> {out}")
    return df


def load_selection(pilot: bool = False) -> tuple[set[str], set[str]]:
    """Return (kept Type-1 question ids, kept Type-2 question ids)."""
    path = C.selection_file(pilot)
    if not path.exists():
        raise SystemExit(f"no selection at {path} -- run the 'select' stage first")
    df = pd.read_csv(path)
    kept = df[df["kept"]]
    t1 = set(kept[kept["type"] == 1]["question_id"])
    t2 = set(kept[kept["type"] == 2]["question_id"])
    return t1, t2


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    args = ap.parse_args()
    select(pilot=args.pilot)


if __name__ == "__main__":
    main()
