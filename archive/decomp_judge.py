#!/usr/bin/env python3
"""
Judge the decomposition component rollouts (Route B-2 + agreement test).

Re-elicits each of the four LTP components 32x WITH reasoning text (the variance
probe discarded the text, keeping only the parsed number), then has Opus score
each derivation with the cogency-triad rubric. Aggregates judge scores by
component, so we can check: is the component the VARIANCE/violation flagged
(P(E) unstable; P(H|E) sign-inverted) also the one the JUDGE scores worst?

Generation: 8B via OpenRouter.  Judge: Opus 4.8 via claude CLI.  Concurrency 32.
Usage: python decomp_judge.py [path/to/constraint.yaml]
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

from demo_judge import (load_openrouter_key, load_question, ROOT, DEFAULT_Q,
                        judge_with_opus, DIMS)
from decomp_variance import MODEL, SYS, component_prompts

N_SAMPLES = 32
CONCURRENCY = 32
TEMP = 1.0
COMP_ORDER = ["a_P(H)", "e_P(E)", "p1_P(H|E)", "p0_P(H|~E)"]


def call_model_text(key, user):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": SYS},
                     {"role": "user", "content": user}],
        "temperature": TEMP,
    }).encode()
    text = ""
    for attempt in range(6):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.load(r)
            text = data["choices"][0]["message"]["content"]
            break
        except urllib.error.HTTPError as ex:
            if ex.code in (429, 500, 502, 503) and attempt < 5:
                time.sleep(2 ** attempt + attempt)
                continue
            raise
    p = None
    for line in reversed(text.splitlines()):
        if "ANSWER:" in line.upper():
            try:
                p = float(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
            break
    return text, p


def claim_for(comp, q):
    h, e = q["hypothesis"], q["evidence"]
    if comp == "a_P(H)":
        return h
    if comp == "e_P(E)":
        return e
    if comp == "p1_P(H|E)":
        return f"{h}\n\n(Evaluated under the explicit assumption that the following is TRUE: {e})"
    if comp == "p0_P(H|~E)":
        return f"{h}\n\n(Evaluated under the explicit assumption that the following is FALSE: {e})"


def gen_and_judge(key, comp, prompt, claim):
    try:
        text, p = call_model_text(key, prompt)
        verdict = judge_with_opus(claim, p, text)
        parsed = json.loads(verdict)
        scores = {d: parsed.get(d, {}).get("score") for d in DIMS}
    except Exception as e:  # noqa: BLE001
        print(f"[{comp} FAILED] {e}")
        return {"comp": comp, "cred": None, "scores": {d: None for d in DIMS}}
    print(f"[{comp}] cred={p} overall={scores.get('overall')}")
    return {"comp": comp, "cred": p, "scores": scores}


def stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return (None, None)
    m = sum(xs) / len(xs)
    sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5
    return (m, sd)


def main():
    qpath = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_Q
    q = load_question(qpath)
    key = load_openrouter_key()
    prompts = component_prompts(q)

    print("=" * 80)
    print("DECOMPOSITION JUDGE —", os.path.basename(qpath))
    print(f"model={MODEL}  N={N_SAMPLES}/component  judge=opus  concurrency={CONCURRENCY}")
    print("=" * 80)

    tasks = []
    for comp in COMP_ORDER:
        claim = claim_for(comp, q)
        for _ in range(N_SAMPLES):
            tasks.append((comp, prompts[comp], claim))

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        results = list(ex.map(lambda t: gen_and_judge(key, *t), tasks))

    by_comp = {c: [] for c in COMP_ORDER}
    for r in results:
        by_comp[r["comp"]].append(r)

    print("\n" + "=" * 80)
    print("JUDGE SCORES BY COMPONENT (mean / sd)")
    print("=" * 80)
    header = f"{'component':12} " + "  ".join(f"{d[:6]:>11}" for d in DIMS) + "   credSD"
    print(header)
    agg = {}
    for comp in COMP_ORDER:
        rs = by_comp[comp]
        cells = []
        agg[comp] = {}
        for d in DIMS:
            m, sd = stats([r["scores"][d] for r in rs])
            agg[comp][d] = (m, sd)
            cells.append(f"{(m if m is not None else float('nan')):.2f}±{(sd if sd is not None else 0):.2f}")
        _, csd = stats([r["cred"] for r in rs])
        cm, _ = stats([r["cred"] for r in rs])
        print(f"{comp:12} " + "  ".join(f"{c:>11}" for c in cells) +
              f"   {(csd if csd else 0):.2f}")

    # who is worst-reasoned?
    ov = {c: agg[c]["overall"][0] for c in COMP_ORDER if agg[c]["overall"][0] is not None}
    suf = {c: agg[c]["sufficiency"][0] for c in COMP_ORDER if agg[c]["sufficiency"][0] is not None}
    if ov:
        print(f"\nWORST overall (reasoning):     {min(ov, key=ov.get)}  ({min(ov.values()):.3f})")
        print(f"BEST  overall (reasoning):     {max(ov, key=ov.get)}  ({max(ov.values()):.3f})")
    if suf:
        print(f"WORST sufficiency:             {min(suf, key=suf.get)}  ({min(suf.values()):.3f})")

    # ---- md ----
    tag = MODEL.split("/")[-1].replace(".", "")
    qtag = os.path.basename(qpath).replace(".yaml", "")
    rows = ["| component | " + " | ".join(DIMS) + " | credSD |",
            "|" + "---|" * (len(DIMS) + 2)]
    for comp in COMP_ORDER:
        rs = by_comp[comp]
        cells = []
        for d in DIMS:
            m, sd = agg[comp][d]
            cells.append("" if m is None else f"{m:.2f}±{sd:.2f}")
        _, csd = stats([r["cred"] for r in rs])
        rows.append(f"| {comp} | " + " | ".join(cells) + f" | {(csd if csd else 0):.2f} |")
    md = f"""# Decomposition component rollouts — Opus judge scores

**Question:** `{os.path.basename(qpath)}`
**Model:** {MODEL} (N={N_SAMPLES}/component, temp {TEMP})  ·  **Judge:** Opus 4.8

**H:** {q['hypothesis']}

**E:** {q['evidence']}

Each cell is mean±sd of the Opus rubric score across {N_SAMPLES} rollouts of that component.

{chr(10).join(rows)}

**Agreement check:** variance probe flagged P(E) as least stable and P(H|E) as
sign-inverted (P(H|E) > P(H|¬E) on an undercutting evidence). Does the judge
independently score P(H|E) / P(E) reasoning worst?
"""
    out = os.path.join(ROOT, f"decomp_judge_{tag}_{qtag}.md")
    with open(out, "w") as f:
        f.write(md)
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
