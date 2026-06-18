#!/usr/bin/env python3
"""Plot probability vs judge-overall for the cross-phrasing run, faceted by question."""
import json, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = [json.loads(l) for l in open("data/cross_phrasing_8b.jsonl")]
ok = [r for r in rows if r["ok"] and r["probability"] is not None
      and r["scores"].get("overall") is not None]
qs = sorted(set(r["qid"] for r in ok))
REPS = ["R1", "R2", "R3", "R4"]
RCOL = {"R1": "#1f77b4", "R2": "#ff7f0e", "R3": "#2ca02c", "R4": "#d62728"}

def spearman(x, y):
    n = len(x)
    rx = {v: i for i, v in enumerate(sorted(range(n), key=lambda k: x[k]))}
    ry = {v: i for i, v in enumerate(sorted(range(n), key=lambda k: y[k]))}
    a = [rx[i] for i in range(n)]; b = [ry[i] for i in range(n)]
    ma, mb = st.mean(a), st.mean(b)
    num = sum((p-ma)*(q-mb) for p, q in zip(a, b))
    den = (sum((p-ma)**2 for p in a)*sum((q-mb)**2 for q in b))**.5
    return num/den if den else 0.0

import math
ncell = len(qs) + 1
ncol = 4
nrow = math.ceil(ncell / ncol)
fig, axes = plt.subplots(nrow, ncol, figsize=(20, 5 * nrow))
axes = axes.flatten()

for i, q in enumerate(qs):
    ax = axes[i]
    g = [r for r in ok if r["qid"] == q]
    # favored = top quartile by overall
    srt = sorted(g, key=lambda r: r["scores"]["overall"]); k = max(4, len(g)//4)
    fav_ids = set(id(r) for r in srt[-k:])
    cons = st.median([r["probability"] for r in g])
    for r in g:
        c = RCOL[r["rephrasing_id"]]
        favored = id(r) in fav_ids
        ax.scatter(r["probability"], r["scores"]["overall"],
                   c=c, s=90 if favored else 38,
                   edgecolors="black" if favored else "none",
                   linewidths=1.4 if favored else 0, alpha=0.85 if favored else 0.5,
                   zorder=3 if favored else 2)
    rho = spearman([r["probability"] for r in g], [r["scores"]["overall"] for r in g])
    ax.axvline(cons, color="grey", ls="--", lw=1, zorder=1)
    ax.text(cons, 1.01, f"consensus p={cons:.2f}", fontsize=8, color="grey", ha="center")
    ax.set_title(f"{q}\nrho(p,quality)={rho:+.2f}   (n={len(g)})", fontsize=10)
    ax.set_xlabel("probability given to rollout")
    ax.set_ylabel("Opus judged reasoning quality")
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.05)
    ax.grid(alpha=0.2)

# hide any unused panels, put legend in the panel right after the questions
for j in range(len(qs), len(axes)):
    axes[j].axis("off")
ax = axes[len(qs)]; ax.axis("off")
handles = [plt.Line2D([0],[0], marker="o", color="w", markerfacecolor=RCOL[r],
           markersize=10, label=f"rephrasing {r}") for r in REPS]
handles.append(plt.Line2D([0],[0], marker="o", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=12, markeredgewidth=1.5,
               label="favored (top-quartile quality)"))
handles.append(plt.Line2D([0],[0], ls="--", color="grey", label="consensus (median p)"))
ax.legend(handles=handles, loc="center", fontsize=11, frameon=False)
ax.text(0.5, 0.12, "big ringed points = Opus's favored rollouts\n"
        "x = probability given to rollout, y = reasoning quality", ha="center", fontsize=10, color="#333")

fig.suptitle("Probabilities given by 8B across 4 rephrasings vs Opus judge of "
             "reasoning quality using rubric", fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig("cross_phrasing_plot.png", dpi=130)
print("wrote cross_phrasing_plot.png")
