"""Correlate the consistency reward with the strong model's blind quality judgment.

Unit of analysis: per rollout. Reward and quality are both only comparable WITHIN a unit (the
QUESTION for Type 1, the A-and-B GROUP for Type 2), so we (a) compute a pooled within-unit-
centered correlation (subtract each unit's mean from both reward and quality, then correlate the
pooled residuals -- the headline number) and (b) the mean of per-unit correlations. Both are
reported with Pearson, Spearman, and Kendall, overall and split by Type 1 / Type 2.

A positive correlation is the result of interest: it means the consistency reward prefers the
same rollouts a much stronger model prefers on reasoning quality -- i.e. consistency training
behaves like training against a stronger reward model.
"""
from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from . import config as C

EPS = 1e-9
QUALITY_METRICS = ["bt_strength", "win_rate"]
COEFFS = {
    "pearson": lambda x, y: stats.pearsonr(x, y),
    "spearman": lambda x, y: stats.spearmanr(x, y),
    "kendall": lambda x, y: stats.kendalltau(x, y),
}


def _load_merged(pilot: bool) -> pd.DataFrame:
    rewards = pd.read_csv(C.rewards_file(pilot))
    quality = pd.read_csv(C.quality_file(pilot))
    # unit_id (the correlation group) comes from quality, since pairs define the units.
    df = rewards.drop(columns=[c for c in ("unit_id",) if c in rewards.columns]).merge(
        quality[["rollout_id", "unit_id", "win_rate", "bt_strength"]],
        on="rollout_id", how="inner",
    )
    df = df[df["reward"].notna()].copy()
    return df


def _nondegenerate(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Keep only units where both reward and the metric vary (else correlation is undefined)."""
    keep = []
    for gid, g in df.groupby("unit_id"):
        if g[metric].notna().sum() >= 2 and g["reward"].std(ddof=0) > EPS and g[metric].std(ddof=0) > EPS:
            keep.append(g[g[metric].notna()])
    return pd.concat(keep) if keep else df.iloc[0:0]


def _center_within_group(df: pd.DataFrame, metric: str) -> tuple[np.ndarray, np.ndarray]:
    x = df["reward"] - df.groupby("unit_id")["reward"].transform("mean")
    y = df[metric] - df.groupby("unit_id")[metric].transform("mean")
    return x.to_numpy(), y.to_numpy()


def _pergroup_mean(df: pd.DataFrame, metric: str, coeff) -> tuple[float, int]:
    rs = []
    for _, g in df.groupby("unit_id"):
        if len(g) >= 3:
            r = coeff(g["reward"].to_numpy(), g[metric].to_numpy())[0]
            if np.isfinite(r):
                rs.append(r)
    return (float(np.mean(rs)) if rs else np.nan, len(rs))


def _rows_for_scope(df: pd.DataFrame, scope: str) -> list[dict]:
    out = []
    for metric in QUALITY_METRICS:
        nd = _nondegenerate(df, metric)
        if len(nd) < 3:
            continue
        xc, yc = _center_within_group(nd, metric)
        keep = (~np.isnan(xc)) & (~np.isnan(yc))
        xc, yc = xc[keep], yc[keep]
        for cname, cfn in COEFFS.items():
            if len(xc) >= 3 and np.std(xc) > EPS and np.std(yc) > EPS:
                pooled_r, pooled_p = cfn(xc, yc)
            else:
                pooled_r, pooled_p = (np.nan, np.nan)
            pg_r, n_units = _pergroup_mean(nd, metric, cfn)
            out.append({
                "scope": scope, "metric": metric, "coefficient": cname,
                "pooled_r": round(float(pooled_r), 4), "pooled_p": float(f"{pooled_p:.3g}") if np.isfinite(pooled_p) else np.nan,
                "pooled_n": int(len(xc)),
                "perunit_mean_r": round(pg_r, 4) if np.isfinite(pg_r) else np.nan,
                "n_units": n_units,
            })
    return out


def _plot(df: pd.DataFrame, pilot: bool) -> None:
    metric = "bt_strength"
    nd = _nondegenerate(df, metric)
    if len(nd) < 3:
        return
    xc, yc = _center_within_group(nd, metric)
    types = nd["type"].to_numpy()
    keep = (~np.isnan(xc)) & (~np.isnan(yc))
    xc, yc, types = xc[keep], yc[keep], types[keep]
    r = stats.pearsonr(xc, yc)[0] if np.std(xc) > EPS and np.std(yc) > EPS else np.nan

    plt.figure(figsize=(6.5, 5.5))
    for t, color, lab in [(1, "#2b6cb0", "Type 1 (phrasing)"), (2, "#c05621", "Type 2 (conjunction)")]:
        m = types == t
        if m.any():
            plt.scatter(xc[m], yc[m], s=22, alpha=0.6, c=color, label=lab, edgecolors="none")
    if np.isfinite(r) and len(xc) >= 2:
        b, a = np.polyfit(xc, yc, 1)
        xs = np.linspace(xc.min(), xc.max(), 50)
        plt.plot(xs, a + b * xs, "k--", lw=1)
    plt.axhline(0, color="gray", lw=0.5); plt.axvline(0, color="gray", lw=0.5)
    plt.xlabel("consistency reward (within-unit centered)")
    plt.ylabel("strong-model quality: BT strength (within-unit centered)")
    ttl = "pilot" if pilot else "full"
    plt.title(f"Consistency reward vs strong-model quality ({ttl})\npooled Pearson r = {r:.3f}, n = {len(xc)}")
    plt.legend(); plt.tight_layout()
    plt.savefig(C.plot_file(pilot), dpi=140)
    plt.close()


def correlate(pilot: bool = False) -> pd.DataFrame:
    df = _load_merged(pilot)
    if len(df) < 3:
        raise SystemExit("not enough scored rollouts to correlate")
    rows = _rows_for_scope(df, "all")
    rows += _rows_for_scope(df[df["type"] == 1], "type1")
    rows += _rows_for_scope(df[df["type"] == 2], "type2")
    res = pd.DataFrame(rows)
    out = C.correlation_file(pilot)
    res.to_csv(out, index=False)
    _plot(df, pilot)
    print(f"\n=== Correlation: consistency reward vs strong-model quality ===")
    print(res.to_string(index=False))
    print(f"\nWrote {out}")
    print(f"Wrote {C.plot_file(pilot)}")
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    args = ap.parse_args()
    correlate(pilot=args.pilot)


if __name__ == "__main__":
    main()
