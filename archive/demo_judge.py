#!/usr/bin/env python3
"""
Minimal demo: 27B (Qwen3.6-27B via OpenRouter) answers ONE acorn conservation
constraint question; Opus 4.8 (via the local `claude` CLI) judges it with the
cogency-triad rubric (judge_prompt_v1.md).

Prints the full 27B answer and Opus's full rubric judgment.

Usage:
    python demo_judge.py [path/to/constraint.yaml]
"""
import json
import os
import subprocess
import time
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_Q = os.path.join(
    ROOT,
    "acorn-dataset/acorn consistency dataset/constraints_shared_unzipped/"
    "constraint_data/agent4_conservation_costly_punishment.yaml",
)
GEN_MODEL = os.environ.get("GEN_MODEL", "qwen/qwen3-vl-8b-thinking")  # subject model
JUDGE_MODEL = "claude-opus-4-8"      # Opus 4.8 via local CLI (subscription)


# ---------------------------------------------------------------- env / yaml
def load_openrouter_key():
    with open(os.path.join(ROOT, ".env")) as f:
        for line in f:
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "OPENROUTER":
                    return v.strip().strip("\"'")
    raise RuntimeError("OPENROUTER key not found in .env")


def load_question(path):
    """Tiny block-scalar YAML reader for the acorn constraint files."""
    fields, key, buf = {}, None, []
    with open(path) as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line and not line.startswith(" ") and ":" in line:
                if key:
                    fields[key] = " ".join(buf).strip()
                head, rest = line.split(":", 1)
                key, buf = head.strip(), []
                rest = rest.strip()
                if rest and rest not in (">-", ">", "|", "|-"):
                    buf.append(rest)
            elif key:
                buf.append(line.strip())
    if key:
        fields[key] = " ".join(buf).strip()
    return fields


import re as _re


def _body_no_answer(content):
    """The content with the trailing ANSWER line stripped, for substantiveness check."""
    return _re.sub(r"ANSWER\s*:.*", "", content, flags=_re.IGNORECASE).strip()


def _post_openrouter(key, prompt):
    body = json.dumps({
        "model": GEN_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": GEN_TEMP,
    }).encode()
    for attempt in range(6):  # exponential backoff: cheap endpoints 429 under load
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 5:
                time.sleep(2 ** attempt + attempt)
                continue
            raise
    raise RuntimeError("openrouter: exhausted retries")


# ---------------------------------------------------------------- 27B answer
def ask_27b(key, claim):
    # Option B: elicit the model's reasoning INTO the committed answer (content),
    # so the judge scores a clean position, not the raw thinking-channel scratch.
    # Neutral on content (no "engage the crux") to avoid confounding capability
    # with instruction-following.
    prompt = (
        f"Is the following claim true?\n\n"
        f"CLAIM: {claim}\n\n"
        "In your response, lay out your reasoning about whether the claim is true "
        "(a short paragraph), then end with exactly one line of the form:\n"
        "ANSWER: <probability between 0 and 1>"
    )
    content, reasoning_trace = "", ""
    for _ in range(4):  # retry if the model emits an answer-only content
        msg = _post_openrouter(key, prompt)["choices"][0]["message"]
        content = msg.get("content") or ""
        reasoning_trace = msg.get("reasoning") or ""
        if len(_body_no_answer(content)) >= 150:  # substantive committed reasoning
            break
    # judge the committed position (content); fall back to the thinking trace only
    # if the model never produced substantive content after retries.
    text = content if len(_body_no_answer(content)) >= 150 else \
        (reasoning_trace + "\n\n" + content).strip()
    cred = None
    for line in reversed(text.splitlines()):
        if "ANSWER:" in line.upper():
            try:
                cred = float(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
            break
    return text, cred


# ---------------------------------------------------------------- Opus judge
JUDGE_SYSTEM = """You are an expert evaluator of conceptual reasoning, trained in informal logic and \
argumentation theory. You assess the QUALITY OF REASONING in a position taken on a genuinely \
contested claim — one where thoughtful, well-informed people disagree and there is NO settled \
ground-truth answer.

Because there is no ground truth, you do NOT score whether the conclusion is correct, and you do \
NOT reward agreement with your own view. You score whether the reasoning is GOOD: whether the \
argument, on its own terms and against the broader debate, gives genuine grounds to believe its \
conclusion to the degree it claims.

You evaluate along the classic cogency triad (Johnson & Blair / Wachsmuth) plus two further axes. \
For every dimension you must FIRST quote the specific span(s) of the position you are judging, THEN \
reason, THEN assign a score in [0,1]. If you cannot cite a span, you cannot deduct for it.

DIMENSIONS:
1. ACCEPTABILITY (local) — Are the premises believable on their own? (1.0 all load-bearing premises \
acceptable/supported; 0.5 at least one materially shaky & unsupported; 0.0 rests on premises a \
reasonable person would reject.)
2. RELEVANCE (local) — Do the premises actually bear on the conclusion? Penalize true-but-irrelevant \
filler and answering a different claim than asked.
3. SUFFICIENCY (local) — Taken together, do the premises give ENOUGH to believe the conclusion? \
Catch missing steps, gaps, overreach, hand-waving over the crux.
4. REASONABLENESS (global) — Does the position engage the actual CRUX and the strongest opposing \
considerations, not a weak version? Penalize one-sidedness and strawmanning.
5. CALIBRATION (separate axis, does NOT feed argument quality) — Is the stated numerical credence \
justified by the strength of the argument actually presented? INTERNAL prose-vs-number coherence, \
NOT agreement with your own probability. Genuine uncertainty -> mid credence; strong one-sided \
grounds license a more extreme credence.
6. OVERALL — All-things-considered quality of the REASONING (dimensions 1–4; calibration reported \
but NOT folded in). Anchor to cogency = acceptability × relevance × sufficiency, then adjust for \
reasonableness and insight.

RULES:
- Judge the reasoning ONLY. Do not reward length, confidence, vocabulary, or formatting.
- Do not reward agreement with your own opinion; you may disagree with a conclusion and still score \
its reasoning 1.0.
- Cite a span before every non-trivial score. No citation -> no deduction.
- "Acceptable" means "a reasonable person would grant it," not "verified true." Do not penalize a \
premise merely for being contested, only for being unreasonable to grant.

Return ONLY this JSON (with the citation/rationale/score keys):
{"acceptability":{"citation":"","rationale":"","score":0},
 "relevance":{"citation":"","rationale":"","score":0},
 "sufficiency":{"citation":"","rationale":"","score":0},
 "reasonableness":{"citation":"","rationale":"","score":0},
 "calibration":{"citation":"","rationale":"","score":0},
 "overall":{"rationale":"","score":0}}"""


def judge_with_opus(claim, credence, reasoning):
    user = (
        f"CLAIM (contested, no ground truth):\n{claim}\n\n"
        f"POSITION TO EVALUATE:\nStated credence: {credence}\nReasoning:\n{reasoning}\n\n"
        "Evaluate along all six dimensions and return ONLY the JSON object."
    )
    full = JUDGE_SYSTEM + "\n\n=====\n\n" + user
    last_err = ""
    for attempt in range(6):  # local CLI rate-limits under concurrency; long backoff
        out = subprocess.run(
            ["claude", "-p", full, "--model", JUDGE_MODEL],
            capture_output=True, text=True, timeout=600,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
        last_err = out.stderr or f"empty stdout (rc={out.returncode})"
        time.sleep(5 * (attempt + 1) + 5 * attempt)  # 5,15,30,50,75s
    raise RuntimeError(f"claude CLI failed after retries:\n{last_err}")


# ---------------------------------------------------------------- main
DIMS = ["acceptability", "relevance", "sufficiency",
        "reasonableness", "calibration", "overall"]
N_ROLLOUTS = 32
CONCURRENCY = 32
GEN_TEMP = 1.0


def one_rollout(i, key, claim):
    """Generate one 27B answer and judge it. Runs in its own thread.
    Never raises — a failed rollout returns None scores so the batch survives."""
    try:
        answer, cred = ask_27b(key, claim)
        verdict = judge_with_opus(claim, cred, answer)
    except Exception as e:  # noqa: BLE001 — one bad rollout must not kill the batch
        print(f"[rollout {i+1} FAILED] {e}")
        return {"answer": "", "cred": None, "verdict": str(e),
                "parsed": None, "scores": {d: None for d in DIMS}}
    try:
        parsed = json.loads(verdict)
        scores = {d: parsed.get(d, {}).get("score") for d in DIMS}
    except json.JSONDecodeError:
        parsed, scores = None, {d: None for d in DIMS}
    print(f"[rollout {i+1} done] credence={cred} "
          f"overall={scores.get('overall')}")
    return {"answer": answer, "cred": cred, "verdict": verdict,
            "parsed": parsed, "scores": scores}


def stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return (None, None, None, None)
    n = len(xs)
    mean = sum(xs) / n
    sd = (sum((x - mean) ** 2 for x in xs) / n) ** 0.5
    return (mean, sd, min(xs), max(xs))


def main():
    qpath = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_Q
    q = load_question(qpath)
    claim = q["hypothesis"]
    key = load_openrouter_key()

    print("=" * 80)
    print("ACORN CONSTRAINT QUESTION:", os.path.basename(qpath))
    print("=" * 80)
    if q.get("context"):
        print("\nCONTEXT:\n" + q["context"])
    print("\nCLAIM (hypothesis):\n" + claim)

    print(f"\nGenerating + judging {N_ROLLOUTS} rollouts "
          f"(concurrency {CONCURRENCY})...\n")
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        rollouts = list(ex.map(lambda i: one_rollout(i, key, claim),
                               range(N_ROLLOUTS)))

    # ---- variance summary ----
    print("\n" + "=" * 80)
    print(f"JUDGE SCORE VARIANCE ACROSS {N_ROLLOUTS} ROLLOUTS")
    print("=" * 80)
    print(f"{'dimension':16} mean   sd    min   max")
    summary_rows = []
    for d in DIMS:
        col = [r["scores"][d] for r in rollouts]
        mean, sd, lo, hi = stats(col)
        print(f"{d:16} {mean:.2f}  {sd:.2f}  {lo:.2f}  {hi:.2f}")
        summary_rows.append((d, col, mean, sd, lo, hi))
    creds = [r["cred"] for r in rollouts]
    cmean, csd, clo, chi = stats(creds)
    print(f"\n27B credence: mean {cmean:.2f}, sd {csd:.2f}, "
          f"range [{clo:.2f}, {chi:.2f}]")

    def histogram(xs, lo=0.0, hi=1.0, bins=10):
        xs = [x for x in xs if x is not None]
        edges = [lo + (hi - lo) * b / bins for b in range(bins + 1)]
        counts = [0] * bins
        for x in xs:
            b = min(int((x - lo) / (hi - lo) * bins), bins - 1)
            counts[max(b, 0)] += 1
        lines = []
        for b in range(bins):
            lines.append(f"  [{edges[b]:.2f},{edges[b+1]:.2f}) "
                         f"{'#' * counts[b]} {counts[b]}")
        return "\n".join(lines)

    overall_col = [r["scores"]["overall"] for r in rollouts]
    print("\noverall-score histogram:")
    print(histogram(overall_col))

    # ---- write md ----
    def md_table():
        head = "| dimension | mean | sd | min | max |"
        sep = "|---|---|---|---|---|"
        rows = []
        for d, col, mean, sd, lo, hi in summary_rows:
            rows.append(f"| {d} | {mean:.2f} | {sd:.2f} | {lo:.2f} | {hi:.2f} |")
        return "\n".join([head, sep] + rows)

    def md_scores_table():
        head = "| # | cred | " + " | ".join(DIMS) + " |"
        sep = "|" + "---|" * (len(DIMS) + 2)
        rows = []
        for i, r in enumerate(rollouts):
            cells = " | ".join("" if r["scores"][d] is None else f"{r['scores'][d]:.2f}"
                               for d in DIMS)
            rows.append(f"| {i+1} | {r['cred']} | {cells} |")
        return "\n".join([head, sep] + rows)

    blocks = []
    for i, r in enumerate(rollouts):
        if r["parsed"] is not None:
            vb = "```json\n" + json.dumps(r["parsed"], indent=2) + "\n```"
        else:
            vb = "```\n" + r["verdict"] + "\n```"
        blocks.append(
            f"### Rollout {i+1}  (credence {r['cred']})\n\n"
            f"**27B answer:**\n\n{r['answer']}\n\n**Opus judgment:**\n\n{vb}\n")

    md = f"""# {N_ROLLOUTS}-rollout variance demo — 27B answers, Opus 4.8 judges

**Question file:** `{os.path.basename(qpath)}`
**Subject:** {GEN_MODEL} (neutral prompt, temp {GEN_TEMP})
**Judge:** {JUDGE_MODEL}

## Claim (hypothesis)
{claim}

## Context
{q.get('context', '(none)')}

## Judge-score variance across {N_ROLLOUTS} rollouts
{md_table()}

27B credence: mean {cmean:.2f}, sd {csd:.2f}, range [{clo:.2f}, {chi:.2f}]

### overall-score histogram
```
{histogram(overall_col)}
```

## Per-rollout scores
{md_scores_table()}

---

## Full rollouts
{chr(10).join(blocks)}
"""
    tag = GEN_MODEL.split("/")[-1].replace(".", "")
    out_path = os.path.join(ROOT, f"demo_variance_{tag}.md")
    with open(out_path, "w") as f:
        f.write(md)
    print(f"\n[wrote {out_path}]")


if __name__ == "__main__":
    main()
