"""Turn pairwise judgments into a per-rollout quality score, within each unit.

A "unit" is the correlation group: the QUESTION for Type 1 (pooled across phrasings) and the
(A and B) GROUP for Type 2. It is carried on each judgment as `unit_id`.

- win_rate: wins / games (a tie counts as half a win to each side). Simple, robust sanity check.
- bt_strength: Bradley-Terry log-strength fit per unit via a regularized MM (minorization-
  maximization) iteration, centered to mean 0 within the unit. Primary score: it pools the
  whole comparison graph, so it's less noisy than raw win-rate.

A unit's scores are comparable only within that unit, which is exactly what we correlate
against the (also within-unit) consistency reward.
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np
import pandas as pd

from . import config as C
from .utils import read_jsonl


def _bt_group(items: list[str], wins: dict, games: dict, lam: float = 1.0,
              iters: int = 500, tol: float = 1e-10) -> dict[str, float]:
    """Regularized Bradley-Terry via MM. wins[(i,j)] = fractional wins of i over j;
    games[(i,j)] = total games between i and j. Returns centered log-strengths."""
    idx = {it: k for k, it in enumerate(items)}
    n = len(items)
    W = np.zeros(n)                      # total (regularized) wins per item
    M = np.zeros((n, n))                 # games matrix
    for (i, j), g in games.items():
        a, b = idx[i], idx[j]
        M[a, b] += g
        M[b, a] += g
    for (i, j), w in wins.items():
        W[idx[i]] += w
    # symmetric prior: lam games split 0.5/0.5 vs a reference of strength 1 (log 0)
    W_reg = W + lam * 0.5
    p = np.ones(n)
    for _ in range(iters):
        denom = np.zeros(n)
        for a in range(n):
            s = 0.0
            for b in range(n):
                if a != b and M[a, b] > 0:
                    s += M[a, b] / (p[a] + p[b])
            s += lam / (p[a] + 1.0)      # prior term vs reference strength 1
            denom[a] = s
        p_new = W_reg / np.where(denom > 0, denom, 1e-12)
        p_new *= n / p_new.sum()         # normalize to keep scale stable
        if np.max(np.abs(np.log(p_new) - np.log(p))) < tol:
            p = p_new
            break
        p = p_new
    logp = np.log(p)
    logp -= logp.mean()                  # center within group
    return {it: float(logp[idx[it]]) for it in items}


def compute_quality(judgments: list[dict]) -> list[dict]:
    by_group: dict[str, list[dict]] = defaultdict(list)
    for j in judgments:
        if j.get("ok") and j.get("winner") is not None:
            by_group[j["unit_id"]].append(j)

    rows: list[dict] = []
    for gid, js in by_group.items():
        items = sorted({r for j in js for r in (j["rollout_a"], j["rollout_b"])})
        wins: dict[tuple[str, str], float] = defaultdict(float)
        games: dict[tuple[str, str], float] = defaultdict(float)
        win_count: dict[str, float] = defaultdict(float)
        game_count: dict[str, float] = defaultdict(float)
        for j in js:
            a, b = j["rollout_a"], j["rollout_b"]
            key = (a, b)
            games[key] += 1
            game_count[a] += 1
            game_count[b] += 1
            if j["winner"] == "a":
                wins[key] += 1; win_count[a] += 1
            elif j["winner"] == "b":
                wins[(b, a)] += 1; win_count[b] += 1
            else:  # tie -> half each
                wins[key] += 0.5; wins[(b, a)] += 0.5
                win_count[a] += 0.5; win_count[b] += 0.5

        bt = _bt_group(items, wins, games) if len(items) >= 2 else {it: 0.0 for it in items}
        gtype = js[0]["type"]
        for it in items:
            g = game_count[it]
            rows.append({
                "rollout_id": it, "unit_id": gid, "type": gtype,
                "n_games": g, "wins": win_count[it],
                "win_rate": (win_count[it] / g) if g > 0 else np.nan,
                "bt_strength": bt[it],
            })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    args = ap.parse_args()

    judgments = read_jsonl(C.judgments_file(args.pilot))
    if not judgments:
        raise SystemExit(f"no judgments at {C.judgments_file(args.pilot)} -- run judge first")
    rows = compute_quality(judgments)
    df = pd.DataFrame(rows)
    out = C.quality_file(args.pilot)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} per-rollout quality scores across "
          f"{df['unit_id'].nunique()} units -> {out}")


if __name__ == "__main__":
    main()
