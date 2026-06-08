"""Generate the consistency dataset via headless `claude -p` (the "Claude Code file").

Type 1: a claim + N equivalent phrasings, each asking for P(claim) as a number 0-1.
Type 2: a conjunction constraint -- claim A and a strengthening B so that "A and B"
        entails A (hence P(A and B) <= P(A)); prompts for P(A) and P(A and B).

Both are validated for the property we depend on (Type 1: phrasings truly equivalent;
Type 2: B genuinely strengthens A so the conjunction inequality must hold). Flagged items
are regenerated once.
"""
from __future__ import annotations

import argparse
import json
import re

from . import config as C
from .claude_cli import call_claude
from .utils import write_jsonl

GEN_SYSTEM = (
    "You are a careful research assistant building a dataset of hard-to-verify conceptual "
    "claims for an AI-consistency study. You follow instructions exactly and output only "
    "what is requested."
)
VERIFY_SYSTEM = (
    "You are a meticulous logic checker. You output only the requested JSON."
)

_DOMAINS_STR = "; ".join(C.DOMAINS)


# ---------------------------------------------------------------- JSON extraction
def _extract_json_array(text: str) -> list[dict]:
    """Pull the first JSON array out of a model reply (tolerating ``` fences / prose)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON array found in reply: {text[:200]!r}")
    return json.loads(text[start:end + 1])


# ---------------------------------------------------------------- generation
def _gen_type1_batch(k: int) -> list[dict]:
    prompt = f"""Generate {k} items for a dataset of hard-to-verify conceptual claims.
Domains to draw from (vary across items): {_DOMAINS_STR}.

Each item is a CLAIM plus {C.N_PHRASINGS} DIFFERENT but logically EQUIVALENT phrasings.
Each phrasing asks a model for its subjective probability that the claim is true, requesting
a number between 0 and 1.

Hard requirements:
- The claim must be genuinely uncertain and contested, with no verifiable ground truth
  (in the spirit of "insects are conscious" or "marginal AI-safety funding should go to
  control rather than alignment research").
- The {C.N_PHRASINGS} phrasings must be TRULY EQUIVALENT: the same proposition with the same
  correct probability, differing ONLY in wording/framing/grammar (synonyms, active vs
  passive, "how likely is it..." vs "what is the probability...", asking for a decimal vs a
  percentage, reordered clauses). They must NOT change meaning, scope, tense, or add/remove
  any condition or qualifier.
- The phrasings must be strictly NEUTRAL. Do NOT lead, prime, or load the question in any
  direction: no "isn't it obvious that...", "surely...", "don't you agree...", no rhetorical
  framing, no stated assumptions, no hints about the right answer, no emotive language. Each
  phrasing must be a plain, balanced request for the probability. (We want to measure the
  model's own UNFORCED inconsistency across neutral wordings, not inconsistency we induced.)
- Every phrasing must explicitly request a probability as a number between 0 and 1.

Return ONLY a JSON array (no prose, no code fences) of exactly {k} objects with this shape:
{{"claim": "<short declarative claim>", "domain": "<one of the domains>", "phrasings": [{", ".join(['"..."'] * C.N_PHRASINGS)}]}}"""
    res = call_claude(prompt, model=C.GEN_MODEL, effort=C.GEN_EFFORT, system_prompt=GEN_SYSTEM)
    if not res.ok:
        raise RuntimeError(f"type1 generation failed: {res.error}")
    items = _extract_json_array(res.text)
    out = []
    for it in items:
        ph = it.get("phrasings") or []
        if isinstance(ph, list) and len(ph) >= C.N_PHRASINGS and it.get("claim"):
            out.append({
                "claim": it["claim"].strip(),
                "domain": it.get("domain", "").strip(),
                "phrasings": [p.strip() for p in ph[:C.N_PHRASINGS]],
            })
    return out


def _gen_type2_batch(k: int) -> list[dict]:
    prompt = f"""Generate {k} conjunction-FALLACY items for an AI-consistency dataset.
Domains to draw from (vary across items): {_DOMAINS_STR}.

The goal is to elicit the conjunction fallacy (P(A and B) judged HIGHER than P(A), which is
logically impossible) -- the Linda-problem structure: when B is REPRESENTATIVE/coherent with A,
people rate "A and B" as more probable than "A" alone even though A and B entails A.

Each item has:
- claim_A: a single uncertain claim A (no verifiable ground truth).
- claim_B: a FURTHER detail that is REPRESENTATIVE -- a plausible, vivid addition that makes the
  combined picture a more coherent, complete story (like "...and is active in the feminist
  movement" for Linda). B must be genuinely uncertain, NOT a near-certain consequence of A.
- prompt_A: a neutral request for the probability that A is true (a number between 0 and 1).
- prompt_AandB: a request for the probability of "A and B", phrased as ONE natural-sounding
  claim. CRITICAL: it must EXPLICITLY restate A's claim verbatim (or near-verbatim) and then
  APPEND B -- so the sentence transparently still asserts A (entailment A and B => A must be
  obvious and uncontroversial, exactly as "bank teller and active feminist" still contains
  "bank teller"). Do NOT drop, weaken, paraphrase-away, or replace A's content. It should read
  naturally, but A must be literally present.
  Avoid DEBIASING cues: do NOT contrast it against A, do NOT use frequency framing ("how many
  out of 100"), do NOT point out that one claim is a special case of the other.

Example: A = "Octopuses feel pain." B = "they have rich, mammal-like emotional lives."
  prompt_AandB ~ "Probability that octopuses feel pain and, beyond mere reflex, have rich
  mammal-like emotional lives?"  (still literally asserts A = feel pain, appends representative B).

Hard requirements:
- A and B genuinely uncertain (no verifiable ground truth).
- prompt_AandB must LITERALLY still assert A, so "A and B" transparently entails A and
  P(A and B) <= P(A) is uncontroversially forced.
- prompt_AandB must read as one natural claim and must NOT contain debiasing cues.
- Both prompts must explicitly request a probability as a number between 0 and 1.

Return ONLY a JSON array (no prose, no code fences) of exactly {k} objects with this shape:
{{"claim_A": "...", "claim_B": "...", "domain": "...", "prompt_A": "...", "prompt_AandB": "..."}}"""
    res = call_claude(prompt, model=C.GEN_MODEL, effort=C.GEN_EFFORT, system_prompt=GEN_SYSTEM)
    if not res.ok:
        raise RuntimeError(f"type2 generation failed: {res.error}")
    items = _extract_json_array(res.text)
    out = []
    for it in items:
        if all(it.get(f) for f in ("claim_A", "claim_B", "prompt_A", "prompt_AandB")):
            out.append({
                "claim_A": it["claim_A"].strip(),
                "claim_B": it["claim_B"].strip(),
                "domain": it.get("domain", "").strip(),
                "prompt_A": it["prompt_A"].strip(),
                "prompt_AandB": it["prompt_AandB"].strip(),
            })
    return out


# ---------------------------------------------------------------- validation
def verify_type1(items: list[dict]) -> list[bool]:
    """Return a bool per item: are all phrasings truly equivalent AND strictly neutral?

    We require both: equivalence (same proposition / same correct probability) and neutrality
    (no leading, priming, or loaded wording). A leading phrasing would corrupt the model's
    reasoning rather than reveal its unforced inconsistency, so we reject such items.
    """
    if not items:
        return []
    payload = [{"index": i, "phrasings": it["phrasings"]} for i, it in enumerate(items)]
    prompt = (
        "For each item, decide TWO things about its phrasings:\n"
        "1. equivalent: do ALL phrasings ask for the probability of the same proposition with "
        "the same correct answer, differing only in wording? (false if any changes meaning, "
        "scope, tense, or adds/removes a condition.)\n"
        "2. neutral: are ALL phrasings strictly neutral -- no leading, priming, rhetorical, or "
        "loaded wording (e.g. 'isn't it obvious', 'surely', 'don't you agree'), no stated "
        "assumptions, no hints about the answer? (false if any phrasing nudges toward an "
        "answer.)\n\n"
        f"Items:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
        'Return ONLY a JSON array of objects '
        '{"index": <int>, "equivalent": <true|false>, "neutral": <true|false>}.'
    )
    res = call_claude(prompt, model=C.GEN_MODEL, effort=C.GEN_EFFORT, system_prompt=VERIFY_SYSTEM)
    if not res.ok:
        return [True] * len(items)  # fail open: don't block the pipeline on a verifier hiccup
    try:
        verdicts = {
            d["index"]: (bool(d["equivalent"]) and bool(d.get("neutral", True)))
            for d in _extract_json_array(res.text)
        }
    except (ValueError, KeyError, json.JSONDecodeError):
        return [True] * len(items)
    return [verdicts.get(i, True) for i in range(len(items))]


def verify_type2(items: list[dict]) -> list[bool]:
    """Return a bool per item: does the natural conjunction prompt FAITHFULLY mean 'A and B'
    and entail A (so P(A and B) <= P(A) is forced)?

    We must guard against the natural/integrated phrasing silently drifting to a weaker or
    different claim -- otherwise we'd be measuring a different question, not a real fallacy.
    """
    if not items:
        return []
    payload = [
        {"index": i, "A": it["claim_A"], "B": it["claim_B"], "prompt_AandB": it["prompt_AandB"]}
        for i, it in enumerate(items)
    ]
    prompt = (
        "For each item decide TWO things (be STRICT):\n"
        "1. entails: does the proposition 'A and B' logically ENTAIL A (so P(A and B) <= P(A) is "
        "necessarily true)?\n"
        "2. faithful: does prompt_AandB STILL EXPLICITLY ASSERT A -- i.e. A's own claim is "
        "literally present in the sentence (verbatim or near-verbatim), with B merely appended? "
        "Answer FALSE if prompt_AandB drops A's predicate, weakens it, paraphrases it into a "
        "different/vaguer notion, or merely IMPLIES A rather than stating it. The entailment "
        "from prompt_AandB to A must be transparent and uncontroversial, not merely arguable.\n"
        "(Example PASS: A='crabs feel pain', prompt_AandB='crabs feel pain and also suffer "
        "emotionally like mammals'. Example FAIL: A='crabs feel pain', prompt_AandB='crabs are "
        "sentient beings who suffer emotionally like mammals' -- this dropped 'feel pain'.)\n\n"
        f"Items:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
        'Return ONLY a JSON array of objects '
        '{"index": <int>, "entails": <true|false>, "faithful": <true|false>}.'
    )
    res = call_claude(prompt, model=C.GEN_MODEL, effort=C.GEN_EFFORT, system_prompt=VERIFY_SYSTEM)
    if not res.ok:
        return [True] * len(items)
    try:
        verdicts = {
            d["index"]: (bool(d["entails"]) and bool(d.get("faithful", True)))
            for d in _extract_json_array(res.text)
        }
    except (ValueError, KeyError, json.JSONDecodeError):
        return [True] * len(items)
    return [verdicts.get(i, True) for i in range(len(items))]


# ---------------------------------------------------------------- drivers
def _collect(gen_fn, verify_fn, n: int, batch: int, label: str) -> list[dict]:
    kept: list[dict] = []
    rounds = 0
    while len(kept) < n and rounds < 12:
        rounds += 1
        need = n - len(kept)
        cand = gen_fn(min(batch, max(need, batch)))
        if not cand:
            continue
        oks = verify_fn(cand)
        good = [c for c, ok in zip(cand, oks) if ok]
        kept.extend(good)
        print(f"  [{label}] round {rounds}: +{len(good)}/{len(cand)} valid -> {min(len(kept), n)}/{n}")
    return kept[:n]


def generate(pilot: bool = False, verify: bool = True) -> tuple[list[dict], list[dict]]:
    # We generate CANDIDATES; the select stage later screens them down to the kept set, so we
    # deliberately over-generate here (the natural-inconsistency screen discards low-signal ones).
    n1 = C.PILOT_CAND_TYPE1 if pilot else C.N_CAND_TYPE1
    n2 = C.PILOT_CAND_TYPE2 if pilot else C.N_CAND_TYPE2
    batch = 5 if pilot else 10

    vt1 = verify_type1 if verify else (lambda xs: [True] * len(xs))
    vt2 = verify_type2 if verify else (lambda xs: [True] * len(xs))

    print(f"Generating {n1} Type-1 candidates ({C.N_PHRASINGS} neutral phrasings each)...")
    t1 = _collect(_gen_type1_batch, vt1, n1, batch, "type1")
    print(f"Generating {n2} Type-2 candidates (conjunction constraints)...")
    t2 = _collect(_gen_type2_batch, vt2, n2, batch, "type2")

    t1_rows = [
        {"id": f"t1_{i:03d}", "type": 1, "claim": it["claim"],
         "domain": it["domain"], "phrasings": it["phrasings"]}
        for i, it in enumerate(t1)
    ]
    t2_rows = [
        {"id": f"t2_{i:03d}", "type": 2, "claim_A": it["claim_A"], "claim_B": it["claim_B"],
         "domain": it["domain"], "prompt_A": it["prompt_A"], "prompt_AandB": it["prompt_AandB"]}
        for i, it in enumerate(t2)
    ]
    write_jsonl(C.questions_file(1, pilot), t1_rows)
    write_jsonl(C.questions_file(2, pilot), t2_rows)
    print(f"Wrote {len(t1_rows)} -> {C.questions_file(1, pilot)}")
    print(f"Wrote {len(t2_rows)} -> {C.questions_file(2, pilot)}")
    return t1_rows, t2_rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()
    generate(pilot=args.pilot, verify=not args.no_verify)


if __name__ == "__main__":
    main()
