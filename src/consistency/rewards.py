"""Per-rollout consistency rewards, exactly as in control-room/ExperimentDesign.md.

Type 1 (phrasing consistency): for a question, let T = mean probability over ALL phrasings
and rollouts (the joint target). Each rollout with value v gets
    R = -|v - T|.

Type 2 (conjunction P(A and B) <= P(A)): per question let mean_A, mean_AandB be the group
means and V = max(0, mean_AandB - mean_A). If V = 0 the constraint holds and R = 0 for all.
Otherwise push the groups apart:
    A group:      R = +V * (v - mean_A)        (reward higher v)
    A-and-B group: R = -V * (v - mean_AandB)    (reward lower v)
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from statistics import mean

import pandas as pd

from . import config as C
from .utils import read_jsonl


def _valid(rollouts: list[dict]) -> list[dict]:
    return [r for r in rollouts if r.get("parse_ok") and r.get("probability") is not None]


def compute_rewards(rollouts: list[dict]) -> list[dict]:
    rows: list[dict] = []

    # ---- Type 1: target T is the joint mean across all phrasings of a question ----
    t1 = [r for r in rollouts if r.get("type") == 1]
    by_q: dict[str, list[dict]] = defaultdict(list)
    for r in t1:
        by_q[r["question_id"]].append(r)
    for qid, rs in by_q.items():
        valid = _valid(rs)
        T = mean(r["probability"] for r in valid) if valid else None
        for r in rs:
            v = r.get("probability")
            reward = (-abs(v - T)) if (r.get("parse_ok") and v is not None and T is not None) else None
            rows.append({
                "rollout_id": r["rollout_id"], "question_id": qid, "type": 1,
                "group_id": r["group_id"], "group_kind": r["group_kind"],
                "probability": v, "parse_ok": bool(r.get("parse_ok")),
                "group_target_T": T, "violation_V": None,
                "reward": reward,
            })

    # ---- Type 2: violation-scaled push between P(A) and P(A and B) ----
    t2 = [r for r in rollouts if r.get("type") == 2]
    by_q2: dict[str, list[dict]] = defaultdict(list)
    for r in t2:
        by_q2[r["question_id"]].append(r)
    for qid, rs in by_q2.items():
        a = _valid([r for r in rs if r["group_kind"] == "A"])
        ab = _valid([r for r in rs if r["group_kind"] == "AandB"])
        mean_a = mean(r["probability"] for r in a) if a else None
        mean_ab = mean(r["probability"] for r in ab) if ab else None
        V = max(0.0, mean_ab - mean_a) if (mean_a is not None and mean_ab is not None) else None
        for r in rs:
            v = r.get("probability")
            kind = r["group_kind"]
            gmean = mean_a if kind == "A" else mean_ab
            if not (r.get("parse_ok") and v is not None and V is not None):
                reward = None
            elif V == 0.0:
                reward = 0.0  # constraint satisfied -> no update
            elif kind == "A":
                reward = +V * (v - mean_a)
            else:  # AandB
                reward = -V * (v - mean_ab)
            rows.append({
                "rollout_id": r["rollout_id"], "question_id": qid, "type": 2,
                "group_id": r["group_id"], "group_kind": kind,
                "probability": v, "parse_ok": bool(r.get("parse_ok")),
                "group_target_T": gmean, "violation_V": V,
                "reward": reward,
            })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    args = ap.parse_args()

    rollouts = read_jsonl(C.rollouts_file(args.pilot))
    if not rollouts:
        raise SystemExit(f"no rollouts at {C.rollouts_file(args.pilot)} -- run sample_rollouts first")
    rows = compute_rewards(rollouts)
    df = pd.DataFrame(rows)
    out = C.rewards_file(args.pilot)
    df.to_csv(out, index=False)

    scored = df[df["reward"].notna()]
    n_viol = df[(df["type"] == 2)].groupby("question_id")["violation_V"].first()
    print(f"Wrote {len(df)} reward rows ({len(scored)} scored) -> {out}")
    if len(n_viol):
        print(f"Type-2 conjunction violations: {(n_viol > 0).sum()}/{len(n_viol)} questions (V>0)")


if __name__ == "__main__":
    main()
