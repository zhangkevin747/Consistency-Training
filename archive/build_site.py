#!/usr/bin/env python3
"""
Assemble a single self-contained interactive HTML site from BOTH datasets:
  - cross_phrasing_8b.jsonl  (phrasing-variance: 15 claims x 4 rephrasings, Opus-judged)
  - decomp_consistency_8b.jsonl (LTP decomposition: 5 H/E questions x 4 components)

Features: click any rollout to read the model CoT/reasoning + judge scoring; view the
exact model prompt and judge prompt used; browse the original claims, hypotheses, and
evidence. Output: decomp_site.html (open directly in a browser).
"""
import json, os, statistics as st, random
from demo_judge import (load_question, ROOT, JUDGE_SYSTEM, DIMS)
from decomp_variance import component_prompts, SYS as DECOMP_SYS
from decomp_consistency import QUESTIONS as DQ, CDIR

random.seed(0)

# ---------------- model + judge prompt templates (verbatim) ----------------
GEN_TEMPLATE = (
    "Is the following claim true?\n\n"
    "CLAIM: {CLAIM}\n\n"
    "In your response, lay out your reasoning about whether the claim is true "
    "(a short paragraph), then end with exactly one line of the form:\n"
    "ANSWER: <probability between 0 and 1>"
)
JUDGE_USER_TEMPLATE = (
    "CLAIM (contested, no ground truth):\n{CLAIM}\n\n"
    "POSITION TO EVALUATE:\nStated credence: {CRED}\nReasoning:\n{REASONING}\n\n"
    "Evaluate along all six dimensions and return ONLY the JSON object."
)

# ---------------- cross-phrasing rows ----------------
def spearman(x, y):
    n = len(x)
    if n < 3:
        return None
    rx = {i: r for r, i in enumerate(sorted(range(n), key=lambda k: x[k]))}
    ry = {i: r for r, i in enumerate(sorted(range(n), key=lambda k: y[k]))}
    a = [rx[i] for i in range(n)]; b = [ry[i] for i in range(n)]
    ma, mb = st.mean(a), st.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = (sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b)) ** 0.5
    return num / den if den else None

cp_raw = [json.loads(l) for l in open("data/cross_phrasing_8b.jsonl")]
cp_rows, cp_questions = [], {}
for r in cp_raw:
    if not (r["ok"] and r.get("reasoning") and r["probability"] is not None
            and r["scores"].get("overall") is not None):
        continue
    judge = None
    try:
        judge = json.loads(r["judge_raw"]) if r.get("judge_raw") else None
    except (json.JSONDecodeError, TypeError):
        judge = None
    cp_rows.append({
        "qid": r["qid"], "domain": r.get("domain", ""), "rid": r["rephrasing_id"],
        "text": r["rephrasing_text"], "idx": r["rollout_idx"],
        "p": r["probability"], "reasoning": r["reasoning"],
        "scores": r["scores"], "judge": judge,
    })
    q = cp_questions.setdefault(r["qid"], {"domain": r.get("domain", ""), "rephrasings": {}})
    q["rephrasings"].setdefault(r["rephrasing_id"], r["rephrasing_text"])

cp_qstats = {}
for qid in cp_questions:
    g = [r for r in cp_rows if r["qid"] == qid]
    ps = [r["p"] for r in g]; ov = [r["scores"]["overall"] for r in g]
    cp_qstats[qid] = {
        "n": len(g), "median_p": st.median(ps),
        "rho": spearman(ps, ov), "mean_overall": st.mean(ov),
    }

# ---------------- decomposition rows ----------------
COMPS = ["a_P(H)", "e_P(E)", "p1_P(H|E)", "p0_P(H|~E)"]
dq_raw = [json.loads(l) for l in open("data/decomp_consistency_8b.jsonl")]

# Opus judge scores for the decomp rollouts (may be partial/absent while judging runs)
djudged = {}
djpath = "data/decomp_judged_8b.jsonl"
if os.path.exists(djpath):
    for line in open(djpath):
        try:
            j = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not j.get("ok"):
            continue
        try:
            judge = json.loads(j["judge_raw"]) if j.get("judge_raw") else None
        except (json.JSONDecodeError, TypeError):
            judge = None
        djudged[(j["qid"], j["component"], j["rollout_idx"])] = {
            "scores": j["scores"], "judge": judge}

decomp_rows = []
for r in dq_raw:
    if not (r["ok"] and r["probability"] is not None):
        continue
    jd = djudged.get((r["qid"], r["component"], r["rollout_idx"]))
    decomp_rows.append({
        "qid": r["qid"], "role": r.get("e_role", ""), "component": r["component"],
        "idx": r["rollout_idx"], "p": r["probability"],
        "content": r.get("content", ""), "cot": r.get("reasoning_field", ""),
        "scores": jd["scores"] if jd else None, "judge": jd["judge"] if jd else None,
    })

decomp_questions, decomp_qstats = {}, {}
for qid, fname, role in DQ:
    q = load_question(os.path.join(ROOT, CDIR, fname))
    prompts = component_prompts(q)
    decomp_questions[qid] = {
        "role": role, "hypothesis": q["hypothesis"], "evidence": q["evidence"],
        "prompts": prompts,
    }
    cv = {c: [r["p"] for r in decomp_rows if r["qid"] == qid and r["component"] == c]
          for c in COMPS}
    e, p1, p0 = cv["e_P(E)"], cv["p1_P(H|E)"], cv["p0_P(H|~E)"]
    implied = [random.choice(p1) * ev + random.choice(p0) * (1 - ev)
               for ev in (random.choice(e) for _ in range(20000))] if (e and p1 and p0) else []
    a_m = st.mean(cv["a_P(H)"]) if cv["a_P(H)"] else None
    im_m = st.mean(implied) if implied else None
    p1m = st.mean(p1) if p1 else 0; p0m = st.mean(p0) if p0 else 0
    dlt = p1m - p0m
    align = dlt * (1 if role == "supporter" else -1)
    sd_e = st.pstdev(e) if len(e) > 1 else 0
    resid = (a_m - im_m) if (a_m is not None and im_m is not None) else None
    if abs(dlt) < 0.10:
        mech = "E treated as ~irrelevant"
    elif align < 0:
        mech = "conditional sign INVERTED"
    elif resid is not None and abs(resid) < 0.18:
        mech = "broadly coherent"
    elif sd_e > 0.30:
        mech = "won't propagate premise uncertainty"
    elif sd_e < 0.10:
        mech = "marginal ignores ~certain premise"
    else:
        mech = "marginal ≠ own components"
    decomp_qstats[qid] = {
        "role": role,
        "means": {c: (st.mean(cv[c]) if cv[c] else None) for c in COMPS},
        "sds": {c: (st.pstdev(cv[c]) if len(cv[c]) > 1 else 0) for c in COMPS},
        "implied_mean": im_m, "implied_sub": random.sample(implied, min(160, len(implied))) if implied else [],
        "a_mean": a_m, "residual": resid, "delta": dlt, "align": align,
        "sd_e": sd_e, "mechanism": mech,
    }

payload = {
    "cp_rows": cp_rows, "cp_questions": cp_questions, "cp_qstats": cp_qstats,
    "decomp_rows": decomp_rows, "decomp_questions": decomp_questions,
    "decomp_qstats": decomp_qstats,
    "prompts": {
        "gen_template": GEN_TEMPLATE, "decomp_sys": DECOMP_SYS,
        "judge_system": JUDGE_SYSTEM, "judge_user_template": JUDGE_USER_TEMPLATE,
        "gen_model": "qwen/qwen3-vl-8b-thinking", "judge_model": "claude-opus-4-8 (Opus 4.8)",
    },
    "dims": DIMS, "comps": COMPS,
}

html = open(os.path.join(ROOT, "_site_template.html")).read()
# escape "</" so no embedded reasoning text can break out of the <script> tag
# ("<\/" is valid JSON and JSON.parse restores it to "</")
data_json = json.dumps(payload).replace("</", "<\\/")
out = html.replace("/*__DATA__*/", data_json)
with open(os.path.join(ROOT, "decomp_site.html"), "w") as f:
    f.write(out)
sz = os.path.getsize(os.path.join(ROOT, "decomp_site.html")) / 1e6
print(f"wrote decomp_site.html  ({sz:.1f} MB)")
print(f"  cross-phrasing: {len(cp_rows)} rollouts, {len(cp_questions)} claims")
print(f"  decomposition:  {len(decomp_rows)} rollouts, {len(decomp_questions)} H/E questions"
      f"  ({len(djudged)} judged)")
