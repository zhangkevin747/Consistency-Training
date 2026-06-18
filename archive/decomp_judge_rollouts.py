#!/usr/bin/env python3
"""
Judge the EXISTING decomposition rollouts with the Opus cogency rubric.

Reads data/decomp_consistency_8b.jsonl (the pure-consistency rollouts already in the
site) and scores each one's committed reasoning, WITHOUT re-generating — so the judge
scores attach to the same probabilities / CoT the explorer already shows. Each component
is judged against its own claim framing:
    a=P(H)   -> H
    e=P(E)   -> E
    p1=P(H|E)-> H, "under the explicit assumption E is TRUE"
    p0=P(H|¬E)-> H, "under the explicit assumption E is FALSE"

Judge the committed `content` (clean position); fall back to cot+content only if content
is too thin (<150 chars), mirroring the phrasing-variance Option-B rule.

Resumable, append-only, thread-safe. Out: data/decomp_judged_8b.jsonl
Usage: CONCURRENCY=32 python3 decomp_judge_rollouts.py
"""
import json, os, threading
from concurrent.futures import ThreadPoolExecutor

from demo_judge import (load_openrouter_key, load_question, ROOT, DIMS,
                        judge_with_opus)
from decomp_judge import claim_for
from decomp_consistency import QUESTIONS as DQ, CDIR

SRC = os.path.join(ROOT, "data", "decomp_consistency_8b.jsonl")
OUT = os.path.join(ROOT, "data", "decomp_judged_8b.jsonl")
CONCURRENCY = int(os.environ.get("CONCURRENCY", "32"))

# qid -> loaded question (for claim framing)
QMAP = {qid: load_question(os.path.join(ROOT, CDIR, fname)) for qid, fname, _ in DQ}
_lock = threading.Lock()
_done = [0]


def reasoning_to_judge(r, CAP=3000):
    """Judge the clean committed position (content). For the ~38% of rollouts
    (mostly conditionals) whose content is thin, fall back to the TAIL of the
    thinking channel — where the concluding/committed reasoning sits — capped at
    CAP chars, rather than the full multi-KB raw scratch."""
    content = (r.get("content") or "").strip()
    if len(content) >= 150:
        return content
    cot = (r.get("reasoning_field") or "").strip()
    tail = cot[-CAP:] if len(cot) > CAP else cot
    return (tail + "\n\n" + content).strip() or content


def write_row(row):
    with _lock:
        with open(OUT, "a") as f:
            f.write(json.dumps(row) + "\n")
        _done[0] += 1
        if _done[0] % 20 == 0:
            print(f"  {_done[0]} judged", flush=True)


def judge_one(r):
    key3 = (r["qid"], r["component"], r["rollout_idx"])
    out = {"qid": r["qid"], "component": r["component"], "rollout_idx": r["rollout_idx"],
           "probability": r["probability"], "scores": {d: None for d in DIMS},
           "judge_raw": None, "ok": False}
    try:
        claim = claim_for(r["component"], QMAP[r["qid"]])
        verdict = judge_with_opus(claim, r["probability"], reasoning_to_judge(r))
        out["judge_raw"] = verdict
        parsed = json.loads(verdict)
        out["scores"] = {d: parsed.get(d, {}).get("score") for d in DIMS}
        out["ok"] = True
    except Exception as e:  # noqa: BLE001 -- one failure must not kill the batch
        out["error"] = str(e)
        print(f"  [FAIL {key3}] {e}", flush=True)
    write_row(out)
    return out["ok"]


def main():
    load_openrouter_key()  # not needed for judge, but validates env early
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            try:
                j = json.loads(line)
            except json.JSONDecodeError:
                continue
            if j.get("ok"):
                done.add((j["qid"], j["component"], j["rollout_idx"]))

    rows = [json.loads(l) for l in open(SRC)]
    todo = [r for r in rows if r.get("ok") and r["probability"] is not None
            and (r["qid"], r["component"], r["rollout_idx"]) not in done]
    print(f"judge=Opus 4.8  concurrency={CONCURRENCY}  already-judged={len(done)}  "
          f"to-judge={len(todo)}\n-> {OUT}", flush=True)
    if not todo:
        print("nothing to do.")
        return
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        oks = list(ex.map(judge_one, todo))
    print(f"DONE  {sum(oks)}/{len(todo)} ok this run -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
