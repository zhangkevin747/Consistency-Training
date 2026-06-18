#!/usr/bin/env python3
"""
Pure-consistency LTP decomposition viz (no judge).

Two layers:
  (1) Per question, a 5-row strip panel: LTP-implied P(H) (derived) on top, then
      the four elicited components a=P(H), e=P(E), p1=P(H|E), p0=P(H|¬E). Jittered
      points reveal multimodality + the 0/1 deductive conditionals the mean hides;
      the implied-vs-direct gap on the top two rows IS the consistency residual.
  (2) A MECHANISM MAP: all 5 questions in (direction-alignment x signed-residual)
      space, marker size = premise uncertainty sd(P(E)). Shows the residual has
      qualitatively different CAUSES -- sign inversion, irrelevance, failure to
      propagate a (un)certain premise -- not just different magnitudes.
"""
import json, random, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

random.seed(0)
ROWS = [json.loads(l) for l in open("data/decomp_consistency_8b.jsonl")]
OK = [r for r in ROWS if r["ok"] and r["probability"] is not None]

COMPS = ["a_P(H)", "e_P(E)", "p1_P(H|E)", "p0_P(H|~E)"]
YPOS = {"implied": 4, "a_P(H)": 3, "e_P(E)": 2, "p1_P(H|E)": 1, "p0_P(H|~E)": 0}
RLAB = {"implied": "LTP-implied P(H)", "a_P(H)": "a = P(H)  [direct]",
        "e_P(E)": "e = P(E)", "p1_P(H|E)": "p1 = P(H|E)", "p0_P(H|~E)": "p0 = P(H|¬E)"}
CCOL = {"implied": "#7f7f7f", "a_P(H)": "#1f77b4", "e_P(E)": "#9467bd",
        "p1_P(H|E)": "#2ca02c", "p0_P(H|~E)": "#d62728"}

seen, QIDS = set(), []
for r in OK:
    if r["qid"] not in seen:
        seen.add(r["qid"]); QIDS.append(r["qid"])

def vals(qid, comp):
    return [r["probability"] for r in OK if r["qid"] == qid and r["component"] == comp]

def implied_mc(e, p1, p0, B=20000):
    return [random.choice(p1) * ev + random.choice(p0) * (1 - ev)
            for ev in (random.choice(e) for _ in range(B))]

def mechanism(align, resid, sd_e, dlt):
    if abs(dlt) < 0.10:
        return "E treated as ~irrelevant", "E≈irrelevant"
    if align < 0:
        return "conditional sign INVERTED", "INVERTED"
    if abs(resid) < 0.18:
        return "broadly coherent", "direction ✓"
    if sd_e > 0.30:
        return "won't propagate premise uncertainty", "direction ✓"
    if sd_e < 0.10:
        return "marginal ignores ~certain premise", "direction ✓"
    return "marginal ≠ own components", "direction ✓"

# ---------- gather per-question summary ----------
SUM = []
for qid in QIDS:
    cv = {c: vals(qid, c) for c in COMPS}
    e_role = next(r["e_role"] for r in OK if r["qid"] == qid)
    imp = implied_mc(cv["e_P(E)"], cv["p1_P(H|E)"], cv["p0_P(H|~E)"])
    a_m = st.mean(cv["a_P(H)"]); im_m = st.mean(imp)
    resid = a_m - im_m
    p1m, p0m = st.mean(cv["p1_P(H|E)"]), st.mean(cv["p0_P(H|~E)"])
    dlt = p1m - p0m
    exp_sign = 1 if e_role == "supporter" else -1
    align = dlt * exp_sign
    sd_e = st.pstdev(cv["e_P(E)"])
    mech, tag = mechanism(align, resid, sd_e, dlt)
    SUM.append(dict(qid=qid, role=e_role, cv=cv, imp=imp, a_m=a_m, im_m=im_m,
                    resid=resid, dlt=dlt, align=align, sd_e=sd_e, mech=mech, tag=tag))

# ---------- figure ----------
ncol = 3
nrow = (len(QIDS) + 1 + ncol - 1) // ncol
fig, axes = plt.subplots(nrow, ncol, figsize=(7.2 * ncol, 4.6 * nrow))
axes = axes.flatten()

for i, s in enumerate(SUM):
    ax = axes[i]; cv = s["cv"]
    # implied strip (subsample) on top row
    imp_sub = random.sample(s["imp"], 160)
    ax.scatter(imp_sub, [4 + random.uniform(-0.15, 0.15) for _ in imp_sub],
               s=14, c=CCOL["implied"], alpha=0.30, edgecolors="none", zorder=2)
    ax.scatter([s["im_m"]], [4], marker="X", s=90, c="black", zorder=5)
    # four elicited components
    for c in COMPS:
        xs = cv[c]; y0 = YPOS[c]
        ax.scatter(xs, [y0 + random.uniform(-0.15, 0.15) for _ in xs],
                   s=34, c=CCOL[c], alpha=0.6, edgecolors="none", zorder=2)
        ax.scatter([st.mean(xs)], [y0], marker="D", s=70, c=CCOL[c],
                   edgecolors="black", linewidths=1.1, zorder=4)
    # residual connector between direct-a (y=3) and implied (y=4)
    ax.annotate("", xy=(s["im_m"], 3.5), xytext=(s["a_m"], 3.5),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.3), zorder=6)
    ax.text((s["a_m"] + s["im_m"]) / 2, 3.62, f"residual {s['resid']:+.2f}",
            ha="center", fontsize=8.5, fontweight="bold")
    # direction note near conditional rows
    ax.text(0.02, 0.5, f"Δ(p1−p0)={s['dlt']:+.2f}", fontsize=8.5, color="#222",
            transform=ax.get_yaxis_transform() if False else ax.transData)

    ax.set_yticks(list(YPOS.values()))
    ax.set_yticklabels([RLAB[k] for k in YPOS])
    ax.tick_params(axis="y", labelsize=9)
    ax.set_ylim(-0.6, 4.7); ax.set_xlim(-0.02, 1.02)
    ax.set_xlabel("probability assigned by 8B")
    ax.axhline(3.5, color="#ccc", lw=0.6, zorder=0)
    ax.set_title(f"{s['qid']}   (E is {s['role']})\n"
                 f"[{s['tag']}]  {s['mech']}", fontsize=10)
    ax.grid(axis="x", alpha=0.2)

# ---------- mechanism map ----------
ax = axes[len(QIDS)]
ax.axvline(0, color="#bbb", lw=1); ax.axhline(0, color="#bbb", lw=1)
ax.axvspan(-1.05, 0, color="#d62728", alpha=0.05)
for s in SUM:
    size = 120 + s["sd_e"] * 900
    ax.scatter(s["align"], s["resid"], s=size, c=CCOL["a_P(H)"],
               alpha=0.45, edgecolors="black", linewidths=1.2, zorder=3)
    ax.annotate(f"{s['qid']}\n{s['mech']}", (s["align"], s["resid"]),
                textcoords="offset points", xytext=(8, 6), fontsize=8.0)
ax.set_xlim(-1.15, 1.15)
ax.set_xlabel("direction alignment  Δ·sign(expected)\n"
              "←inverted    ~0: E irrelevant    perfect→")
ax.set_ylabel("LTP residual  (direct P(H) − implied)")
ax.set_title("MECHANISM MAP — same residual, different causes\n"
             "(marker size = premise uncertainty sd[P(E)])", fontsize=10)
ax.grid(alpha=0.2)

for j in range(len(QIDS) + 1, len(axes)):
    axes[j].axis("off")

fig.suptitle("LTP decomposition (8B, N=32/component, no judge): the model is "
             "internally incoherent — and the incoherence breaks differently each time",
             fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig("decomp_consistency_plot.png", dpi=130)
print("wrote decomp_consistency_plot.png\n")
print(f"{'qid':20} {'role':11} {'resid':>7} {'Δ':>7} {'align':>7} {'sd(e)':>6}  mechanism")
for s in SUM:
    print(f"{s['qid']:20} {s['role']:11} {s['resid']:>+7.2f} {s['dlt']:>+7.2f} "
          f"{s['align']:>+7.2f} {s['sd_e']:>6.2f}  {s['mech']}")
