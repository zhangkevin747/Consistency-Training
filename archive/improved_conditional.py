#!/usr/bin/env python3
"""
Improved conditional elicitation. The CoT analysis showed the model never
actually conditions: it (a) treats 'assume E true' as endorsing the claim,
(b) ignores E and answers unconditionally, (c) tangles on the negation, and
(d) never asks whether E pushes H up or down. This prompt targets each, while
keeping the evidential DIRECTION neutral (more/less/unchanged) so the sign is
still the model's to get right.

Compares improved P(H|E), P(H|~E) against P(H) on the 8B. Saves stats + CoT.
Usage: python improved_conditional.py
"""
import json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from demo_judge import load_openrouter_key, load_question, ROOT, DEFAULT_Q
from decomp_variance import MODEL

N = 32
CONC = 32
TEMP = 1.0
SYS = ("Think it through carefully, then state your probability. End your "
       "response with exactly one line of the form:\nANSWER: <probability between 0 and 1>")

# plain-language negation of E for this question (direction-neutral: just the logical
# negation, no hint about how it bears on H). Hardcoded for the costly-punishment item.
NOT_E_RESTATE = ("costly punishment does NOT stabilize arbitrary individually costly "
                 "behaviors just as effectively as it stabilizes cooperation — its "
                 "stabilizing power is not fully general.")


def prompts(q):
    h, e = q["hypothesis"], q["evidence"]
    base_marg = f"What probability do you assign to the following claim?\n\n{h}"

    cond_true = (
        f"Consider this CLAIM:\n\n{h}\n\n"
        f"For the sake of argument, suppose you learned that the following statement is "
        f"definitely TRUE. Treat it strictly as a hypothetical supposition: supposing it is "
        f"true does NOT mean the CLAIM is true, and you must not assume the CLAIM is correct "
        f"just because we are supposing this.\n\nSUPPOSE TRUE:\n{e}\n\n"
        f"Your task — reason about this supposition AS EVIDENCE bearing on the CLAIM:\n"
        f"1. State plainly whether learning this would make the CLAIM more likely, less "
        f"likely, or no different than before, and WHY.\n"
        f"2. Then give your probability that the CLAIM is true, under this supposition.\n"
        f"End with: ANSWER: <probability between 0 and 1>")

    cond_false = (
        f"Consider this CLAIM:\n\n{h}\n\n"
        f"For the sake of argument, suppose you learned that the following is the case. Treat "
        f"it strictly as a hypothetical supposition: supposing it does NOT settle whether the "
        f"CLAIM is true, and you must not assume the CLAIM is correct or incorrect just "
        f"because we are supposing this.\n\nSUPPOSE TRUE:\n{NOT_E_RESTATE}\n\n"
        f"Your task — reason about this supposition AS EVIDENCE bearing on the CLAIM:\n"
        f"1. State plainly whether learning this would make the CLAIM more likely, less "
        f"likely, or no different than before, and WHY.\n"
        f"2. Then give your probability that the CLAIM is true, under this supposition.\n"
        f"End with: ANSWER: <probability between 0 and 1>")

    return {"a_P(H)": base_marg, "p1_P(H|E)": cond_true, "p0_P(H|~E)": cond_false}


def call(key, user):
    body = json.dumps({"model": MODEL,
                       "messages": [{"role": "system", "content": SYS},
                                    {"role": "user", "content": user}],
                       "temperature": TEMP}).encode()
    text = ""
    for a in range(6):
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=body, headers={"Authorization": f"Bearer {key}",
                                "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
            msg = d["choices"][0]["message"]
            rsn = msg.get("reasoning")
            text = (("<reasoning>\n" + rsn + "\n</reasoning>\n\n") if rsn else "") + (msg.get("content") or "")
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and a < 5:
                time.sleep(2 ** a); continue
            raise
    p = None
    for line in reversed(text.splitlines()):
        if "ANSWER:" in line.upper():
            try: p = float(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError): pass
            break
    return text, p


def stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs: return (0, None, None)
    m = sum(xs) / len(xs)
    sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5
    return (len(xs), m, sd)


def main():
    qpath = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_Q
    q = load_question(qpath)
    key = load_openrouter_key()
    P = prompts(q)
    order = ["a_P(H)", "p1_P(H|E)", "p0_P(H|~E)"]

    tasks = [(c, P[c]) for c in order for _ in range(N)]
    with ThreadPoolExecutor(max_workers=CONC) as ex:
        res = list(ex.map(lambda t: (t[0], *call(key, t[1])), tasks))
    by = {c: [] for c in order}
    for c, text, p in res:
        by[c].append((p, text))

    print("=" * 70)
    print("IMPROVED CONDITIONAL PROMPT —", os.path.basename(qpath), MODEL)
    print("=" * 70)
    st = {}
    for c in order:
        ps = [p for p, _ in by[c]]
        n, m, sd = stats(ps)
        st[c] = (m, sd)
        print(f"{c:12} n={n:2d}  mean={m:.3f}  sd={sd:.3f}  probs={sorted(x for x in ps if x is not None)}")
    p1 = st["p1_P(H|E)"][0]; p0 = st["p0_P(H|~E)"][0]
    print(f"\nSIGN CHECK: P(H|E)={p1:.3f}  P(H|~E)={p0:.3f}  -> "
          f"{'CORRECT (E lowers H)' if p1 < p0 else 'STILL WRONG (E raises H)'}")

    # save CoT + stats
    out = [f"# Improved conditional elicitation — {os.path.basename(qpath)}",
           f"\n**Model:** {MODEL}  temp {TEMP}  N={N}\n",
           f"\n**H:** {q['hypothesis']}\n\n**E:** {q['evidence']}\n",
           "\n## Prompts used\n",
           f"\n**P(H|E) prompt:**\n```\n{P['p1_P(H|E)']}\n```\n",
           f"\n**P(H|~E) prompt:**\n```\n{P['p0_P(H|~E)']}\n```\n",
           "\n## Stats\n"]
    for c in order:
        m, sd = st[c]
        out.append(f"- {c}: mean={m:.3f} sd={sd:.3f}")
    out.append(f"\n**Sign:** P(H|E)={p1:.3f} vs P(H|~E)={p0:.3f} -> "
               f"{'CORRECT' if p1 < p0 else 'WRONG'}\n")
    out.append("\n## Sample CoTs (first 4 of each conditional)\n")
    for c in ["p1_P(H|E)", "p0_P(H|~E)"]:
        for i, (p, text) in enumerate(by[c][:4]):
            out.append(f"\n### {c} #{i+1} — ANSWER={p}\n\n{text}\n\n---")
    path = os.path.join(ROOT, "improved_conditional_output.md")
    with open(path, "w") as f:
        f.write("\n".join(out))
    print(f"\n[wrote {path}]")


if __name__ == "__main__":
    main()
