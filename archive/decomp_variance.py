#!/usr/bin/env python3
"""
Decomposition component-variance probe (Route B-1, stability localization).

For ONE conservation-constraint question, elicit each of the four law-of-total-
probability components 32 times from the 8B model and compare their spreads:

    a  = P(H)              "What probability do you assign to [hypothesis]?"
    e  = P(E)              "What probability do you assign to [evidence]?"
    p1 = P(H|E)            "Assume [evidence] is TRUE.  P([hypothesis])?"
    p0 = P(H|¬E)           "Assume [evidence] is FALSE. P([hypothesis])?"

Identity: a = p1*e + p0*(1-e). The question is whether the *instability* (sample
variance) concentrates on one component — i.e. whether the model 'knows less'
about one of the four. If so, stability alone localizes the suspect component.

Usage: python decomp_variance.py [path/to/constraint.yaml]
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

from demo_judge import load_openrouter_key, load_question, ROOT, DEFAULT_Q

MODEL = os.environ.get("GEN_MODEL", "qwen/qwen3-vl-8b-thinking")
N_SAMPLES = 32
CONCURRENCY = 32
TEMP = 1.0

SYS = ("Think it through carefully, then state your probability. End your "
       "response with exactly one line of the form:\nANSWER: <probability between 0 and 1>")


def component_prompts(q):
    h, e = q["hypothesis"], q["evidence"]
    return {
        "a_P(H)":      f"What probability do you assign to the following claim?\n\n{h}",
        "e_P(E)":      f"What probability do you assign to the following claim?\n\n{e}",
        "p1_P(H|E)":   (f"Assume that the following is TRUE:\n\n{e}\n\n"
                        f"Given this assumption, what probability do you assign to the "
                        f"following claim?\n\n{h}"),
        "p0_P(H|~E)":  (f"Assume that the following is FALSE:\n\n{e}\n\n"
                        f"Given this assumption, what probability do you assign to the "
                        f"following claim?\n\n{h}"),
    }


def call_model(key, user):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": SYS},
                     {"role": "user", "content": user}],
        "temperature": TEMP,
    }).encode()
    text = None
    for attempt in range(6):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read())
            text = data["choices"][0]["message"].get("content") or ""
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                json.JSONDecodeError, KeyError, IndexError) as ex:  # noqa: F841
            if attempt < 5:
                time.sleep(2 ** attempt + attempt)
                continue
            return None  # drop this sample rather than kill the whole batch
    if text is None:
        return None
    p = None
    for line in reversed(text.splitlines()):
        if "ANSWER:" in line.upper():
            try:
                p = float(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
            break
    return p


def stats(xs):
    xs = [x for x in xs if x is not None]
    n = len(xs)
    if n == 0:
        return dict(n=0, mean=None, sd=None, lo=None, hi=None, vals=[])
    mean = sum(xs) / n
    sd = (sum((x - mean) ** 2 for x in xs) / n) ** 0.5
    return dict(n=n, mean=mean, sd=sd, lo=min(xs), hi=max(xs), vals=sorted(xs))


def histogram(xs, bins=10):
    xs = [x for x in xs if x is not None]
    counts = [0] * bins
    for x in xs:
        counts[min(int(x * bins), bins - 1)] += 1
    return "\n".join(f"  [{b/bins:.1f},{(b+1)/bins:.1f}) {'#'*counts[b]} {counts[b]}"
                     for b in range(bins))


def main():
    qpath = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_Q
    q = load_question(qpath)
    key = load_openrouter_key()
    prompts = component_prompts(q)

    print("=" * 80)
    print("DECOMPOSITION VARIANCE PROBE —", os.path.basename(qpath))
    print(f"model={MODEL}  N={N_SAMPLES}  temp={TEMP}  concurrency={CONCURRENCY}")
    print("=" * 80)
    print("\nHYPOTHESIS:", q["hypothesis"])
    print("\nEVIDENCE:", q["evidence"])

    # build all 4 x N tasks, run flat at concurrency 32
    tasks = [(comp, prompts[comp]) for comp in prompts for _ in range(N_SAMPLES)]
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        results = list(ex.map(lambda t: (t[0], call_model(key, t[1])), tasks))

    by_comp = {comp: [] for comp in prompts}
    for comp, p in results:
        by_comp[comp].append(p)

    st = {comp: stats(by_comp[comp]) for comp in prompts}

    print("\n" + "=" * 80)
    print("COMPONENT VARIANCE")
    print("=" * 80)
    print(f"{'component':14} n   mean   sd     min   max")
    for comp in ["a_P(H)", "e_P(E)", "p1_P(H|E)", "p0_P(H|~E)"]:
        s = st[comp]
        if s["n"]:
            print(f"{comp:14} {s['n']:<3} {s['mean']:.3f}  {s['sd']:.3f}  "
                  f"{s['lo']:.2f}  {s['hi']:.2f}")
        else:
            print(f"{comp:14} 0   (no valid parses)")

    # consistency check on the means
    a, e = st["a_P(H)"]["mean"], st["e_P(E)"]["mean"]
    p1, p0 = st["p1_P(H|E)"]["mean"], st["p0_P(H|~E)"]["mean"]
    if None not in (a, e, p1, p0):
        implied = p1 * e + p0 * (1 - e)
        print(f"\nLTP on means: P(H)={a:.3f}  vs  implied {implied:.3f}  "
              f"(residual {a - implied:+.3f})")

    # most/least variable
    valid = {c: st[c]["sd"] for c in prompts if st[c]["sd"] is not None}
    if valid:
        hi = max(valid, key=valid.get)
        lo = min(valid, key=valid.get)
        print(f"\nMOST variable component:  {hi}  (sd {valid[hi]:.3f})")
        print(f"LEAST variable component: {lo}  (sd {valid[lo]:.3f})")

    print("\nper-component histograms:")
    for comp in ["a_P(H)", "e_P(E)", "p1_P(H|E)", "p0_P(H|~E)"]:
        print(f"\n{comp}:")
        print(histogram(by_comp[comp]))

    # ---- md ----
    def mdrow(comp):
        s = st[comp]
        if not s["n"]:
            return f"| {comp} | 0 | | | | |"
        return (f"| {comp} | {s['n']} | {s['mean']:.3f} | **{s['sd']:.3f}** | "
                f"{s['lo']:.2f} | {s['hi']:.2f} |")
    tag = MODEL.split("/")[-1].replace(".", "")
    qtag = os.path.basename(qpath).replace(".yaml", "")
    md = f"""# Decomposition component-variance probe

**Question:** `{os.path.basename(qpath)}`
**Model:** {MODEL}  ·  N={N_SAMPLES} per component  ·  temp {TEMP}

**Hypothesis (H):** {q['hypothesis']}

**Evidence (E):** {q['evidence']}

## Component variance
| component | n | mean | sd | min | max |
|---|---|---|---|---|---|
{mdrow('a_P(H)')}
{mdrow('e_P(E)')}
{mdrow('p1_P(H|E)')}
{mdrow('p0_P(H|~E)')}

LTP on means: P(H) {a:.3f} vs implied {p1*e + p0*(1-e):.3f} (residual {a-(p1*e+p0*(1-e)):+.3f})

### per-component sorted samples
- a_P(H): {st['a_P(H)']['vals']}
- e_P(E): {st['e_P(E)']['vals']}
- p1_P(H|E): {st['p1_P(H|E)']['vals']}
- p0_P(H|~E): {st['p0_P(H|~E)']['vals']}
"""
    out = os.path.join(ROOT, f"decomp_variance_{tag}_{qtag}.md")
    with open(out, "w") as f:
        f.write(md)
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
