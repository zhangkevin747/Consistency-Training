#!/usr/bin/env python3
"""
PRE-TEST for the intra-rollout-coherence training idea.

Question: does a LABEL-FREE, JUDGE-FREE intra-coherence score predict the Opus
judge's quality on the 955 cross_phrasing rollouts?  If a cheap self-contained
signal tracks quality, the training target's PREMISE survives the full dataset.

We build the most robust programmatic slice of intra-coherence:
  calib_coh = does the rollout's LINGUISTIC confidence (hedging vs certainty
  language in the reasoning) match its NUMERIC confidence (how extreme the
  probability is)?  A model that hedges heavily but answers 0.95 -- or speaks
  decisively but answers 0.55 -- is internally incoherent.

We deliberately do NOT use any judge output to build the score. We then correlate
it with the judge's OVERALL (headline), its CALIBRATION dim (validation that the
cheap proxy captures the judge's own coherence notion), and the content dims
(acceptability/sufficiency/reasonableness) -- where we PREDICT a weak relation,
since intra-coherence is a floor-raiser (kills self-contradiction) not a
ceiling-raiser (won't make premises true / engage counters).

Pure stdlib. Writes intra_coherence_result.md.
"""
import json, re, statistics as st

ROWS = [json.loads(l) for l in open("data/cross_phrasing_8b.jsonl")]
OK = [r for r in ROWS if r["ok"] and r.get("reasoning")
      and r["probability"] is not None and r["scores"].get("overall") is not None]
QS = sorted(set(r["qid"] for r in OK))

HEDGE = ["might", "perhaps", "possibly", "seems", "arguably", "may", "could",
         "uncertain", "unclear", "not necessarily", "tentative", "plausibly",
         "suggests", "tends", "somewhat", "relatively", "debatable", "contested",
         "potentially", "to some extent", "not clear", "hard to say"]
CERT = ["clearly", "obviously", "definitely", "certainly", "must", "cannot",
        "necessarily", "undeniably", "of course", "indeed", "strongly",
        "decisively", "conclusively", "unequivocally", "without doubt", "plainly"]


def densities(text):
    t = text.lower()
    n = len(re.findall(r"[a-z']+", t)) or 1
    hedge = sum(t.count(w) for w in HEDGE) / n * 100
    cert = sum(t.count(w) for w in CERT) / n * 100
    return hedge, cert


def extremity(p):
    return 2 * abs(p - 0.5)  # 0 = maximally uncertain (0.5), 1 = maximally sure (0/1)


# ---- stats helpers (stdlib) ----
def rank01(xs):
    """percentile rank in [0,1], average-rank for ties."""
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    out = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 / (n - 1 if n > 1 else 1)
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def spearman(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    rx, ry = rank01(x), rank01(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def auc(labels, scores):
    """AUC of scores ranking positives (label=1) above negatives."""
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return float("nan")
    wins = sum((s > t) + 0.5 * (s == t) for s in pos for t in neg)
    return wins / (len(pos) * len(neg))


# ---- build features per rollout ----
for r in OK:
    h, c = densities(r["reasoning"])
    r["_hedge"], r["_cert"] = h, c
    r["_LCraw"] = c - h                 # linguistic confidence (raw)
    r["_NE"] = extremity(r["probability"])

# calib_coh = 1 - |rank(LC) - rank(NE)|, ranks computed GLOBALLY
LC_all = [r["_LCraw"] for r in OK]
NE_all = [r["_NE"] for r in OK]
LCr, NEr = rank01(LC_all), rank01(NE_all)
for r, a, b in zip(OK, LCr, NEr):
    r["_calib_coh"] = 1 - abs(a - b)

DIMS = ["overall", "calibration", "acceptability", "sufficiency",
        "relevance", "reasonableness"]


def pooled_spear(feat):
    return spearman([r[feat] for r in OK], [r["scores"]["overall"] for r in OK])


def within_q_spear(feat, dim="overall"):
    vals = []
    for q in QS:
        g = [r for r in OK if r["qid"] == q]
        s = spearman([r[feat] for r in g], [r["scores"][dim] for r in g])
        if s == s:  # not nan
            vals.append((q, s))
    return vals


def within_q_auc(feat):
    aucs = []
    for q in QS:
        g = [r for r in OK if r["qid"] == q]
        med = st.median(r["scores"]["overall"] for r in g)
        lab = [1 if r["scores"]["overall"] > med else 0 for r in g]
        sc = [r[feat] for r in g]
        if len(set(lab)) > 1:
            aucs.append(auc(lab, sc))
    return aucs


# ---- report ----
lines = []
def out(s=""):
    print(s); lines.append(s)

out(f"# Intra-coherence pre-test  (n={len(OK)} rollouts, {len(QS)} questions)")
out()
out("Label-free signal: **calib_coh** = does verbal confidence (hedge vs "
    "certainty words) match numeric extremity |p-0.5|.  No judge output used to build it.")
out()

out("## HEADLINE — calib_coh vs judge OVERALL")
wq = within_q_spear("_calib_coh", "overall")
mean_wq = st.mean(v for _, v in wq)
out(f"- within-question Spearman (the fair test): **mean rho = {mean_wq:+.3f}** "
    f"across {len(wq)} questions")
out(f"- pooled Spearman: {pooled_spear('_calib_coh'):+.3f}")
aucs = within_q_auc("_calib_coh")
out(f"- within-question AUC (top vs bottom-half quality): mean {st.mean(aucs):.3f}, "
    f"min {min(aucs):.3f}, #>0.55: {sum(1 for a in aucs if a>0.55)}/{len(aucs)}")
out()

out("## VALIDATION — does the cheap proxy capture the judge's own coherence notion?")
wq_cal = within_q_spear("_calib_coh", "calibration")
out(f"- calib_coh vs judge CALIBRATION dim: mean within-q rho = "
    f"{st.mean(v for _,v in wq_cal):+.3f}")
out()

out("## SCOPE CHECK — predicted WEAK on content dims (floor-raiser, not ceiling)")
for dim in ["calibration", "overall", "sufficiency", "reasonableness", "acceptability", "relevance"]:
    w = within_q_spear("_calib_coh", dim)
    out(f"- vs {dim:14}: mean within-q rho = {st.mean(v for _,v in w):+.3f}")
out()

out("## BASELINES (within-question Spearman vs overall)")
for feat, name in [("_NE", "numeric extremity |p-0.5|"),
                   ("_hedge", "hedge density"),
                   ("_cert", "certainty density"),
                   ("_LCraw", "linguistic confidence (cert-hedge)")]:
    w = within_q_spear(feat, "overall")
    out(f"- {name:34}: {st.mean(v for _,v in w):+.3f}")
out()

out("## per-question calib_coh vs overall")
out("| qid | rho | n |")
out("|---|---|---|")
for q, s in sorted(wq, key=lambda x: x[1]):
    n = sum(1 for r in OK if r["qid"] == q)
    out(f"| {q} | {s:+.3f} | {n} |")

with open("intra_coherence_result.md", "w") as f:
    f.write("\n".join(lines) + "\n")
print("\n[wrote intra_coherence_result.md]")
