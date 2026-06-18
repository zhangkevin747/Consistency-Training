#!/usr/bin/env python3
"""Capture full CoT text for the conditional elicitations so we can read what
the model actually does when it conditions on E. Saves to a md file."""
import json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from demo_judge import load_openrouter_key, load_question, ROOT, DEFAULT_Q
from decomp_variance import MODEL, SYS, component_prompts

N = 8
CONC = 8
TEMP = 1.0


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
            # capture reasoning trace too if the endpoint returns it separately
            text = (msg.get("reasoning") or "") and ("<reasoning>\n" + msg["reasoning"]
                    + "\n</reasoning>\n\n")
            text = (text or "") + (msg.get("content") or "")
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


def main():
    qpath = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_Q
    q = load_question(qpath)
    key = load_openrouter_key()
    prompts = component_prompts(q)

    want = ["p1_P(H|E)", "p0_P(H|~E)", "a_P(H)"]
    tasks = [(c, prompts[c]) for c in want for _ in range(N)]
    with ThreadPoolExecutor(max_workers=CONC) as ex:
        res = list(ex.map(lambda t: (t[0], *call(key, t[1])), tasks))

    by = {c: [] for c in want}
    for c, text, p in res:
        by[c].append((p, text))

    out = [f"# Conditional CoT capture — {os.path.basename(qpath)}",
           f"\n**Model:** {MODEL}  temp {TEMP}\n",
           f"\n**H:** {q['hypothesis']}\n", f"\n**E:** {q['evidence']}\n"]
    for c in want:
        ps = [p for p, _ in by[c] if p is not None]
        out.append(f"\n\n## {c}  (n={len(by[c])}, probs={sorted(ps)})\n")
        for i, (p, text) in enumerate(by[c]):
            out.append(f"\n### {c} rollout {i+1} — ANSWER={p}\n\n{text}\n\n---")
    path = os.path.join(ROOT, "cot_capture.md")
    with open(path, "w") as f:
        f.write("\n".join(out))
    print(f"[wrote {path}]  counts: " +
          ", ".join(f"{c}={[p for p,_ in by[c]]}" for c in want))


if __name__ == "__main__":
    main()
