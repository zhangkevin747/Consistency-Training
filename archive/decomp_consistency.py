#!/usr/bin/env python3
"""
Pure-consistency LTP decomposition across several questions (NO judge).

For each (H, E) conservation-constraint question we elicit the four law-of-total-
probability components, N times each, from the 8B model and SAVE EVERY ROLLOUT to
jsonl (the old decomp_variance.py only kept aggregate md):

    a  = P(H)        "What probability do you assign to [H]?"
    e  = P(E)        "What probability do you assign to [E]?"
    p1 = P(H|E)      "Assume [E] is TRUE.  P([H])?"
    p0 = P(H|~E)     "Assume [E] is FALSE. P([H])?"

Identity: a = p1*e + p0*(1-e).  Components are sampled INDEPENDENTLY (separate
calls), so there is no paired rollout -- the LTP-implied P(H) is a derived
(Monte-Carlo) distribution, and the residual is a distribution-level quantity.

Pure consistency = needs only the four numbers, no Opus, no external label.

Row schema (data/decomp_consistency_8b.jsonl):
  {qid, qpath, e_role, component, rollout_idx, probability, content, reasoning_field, ok}

Resumable + append-only + thread-safe, like cross_phrasing.py.
Usage: python decomp_consistency.py
"""
import json
import os
import sys
import time
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

from demo_judge import load_openrouter_key, load_question, ROOT
from decomp_variance import component_prompts, SYS

MODEL = os.environ.get("GEN_MODEL", "qwen/qwen3-vl-8b-thinking")
N_SAMPLES = int(os.environ.get("N_SAMPLES", "32"))
CONCURRENCY = int(os.environ.get("CONCURRENCY", "32"))
TEMP = 1.0
OUT = os.path.join(ROOT, "data", "decomp_consistency_8b.jsonl")
COMP_ORDER = ["a_P(H)", "e_P(E)", "p1_P(H|E)", "p0_P(H|~E)"]

CDIR = ("acorn-dataset/acorn consistency dataset/constraints_shared_unzipped/"
        "constraint_data")
# (qid, filename, hand-labeled expected direction of E on H)
#   supporter  -> E TRUE should RAISE P(H)  (expect p1 > p0)
#   undercutter-> E TRUE should LOWER P(H)  (expect p1 < p0)
QUESTIONS = [
    ("costly_punishment", "agent4_conservation_costly_punishment.yaml", "undercutter"),
    ("bone_marrow", "agent100_batch05em_conservation_bone_marrow_compensation.yaml", "supporter"),
    ("imprecise_credences", "agent100_2bc3a20e_conservation_imprecise_credences.yaml", "undercutter"),
    ("belief_dependent", "agent100_7bfd07bd_conservation_belief_dependent_evidence.yaml", "undercutter"),
    ("quasi_realist", "agent100_177cccd1_conservation_quasi_realist_implications.yaml", "supporter"),
]

_write_lock = threading.Lock()


def parse_answer(text):
    for line in reversed((text or "").splitlines()):
        if "ANSWER:" in line.upper():
            try:
                return float(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                return None
    return None


def call_model(key, user):
    """Return (probability, content, reasoning_field) or (None, '', '') on failure."""
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": SYS},
                     {"role": "user", "content": user}],
        "temperature": TEMP,
    }).encode()
    for attempt in range(6):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read())
            msg = data["choices"][0]["message"]
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning") or ""
            return parse_answer(content), content, reasoning
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                json.JSONDecodeError, KeyError, IndexError):
            if attempt < 5:
                time.sleep(2 ** attempt + attempt)
                continue
            return None, "", ""
    return None, "", ""


def write_row(row):
    with _write_lock:
        with open(OUT, "a") as f:
            f.write(json.dumps(row) + "\n")


def one(key, qid, qpath, e_role, prompts, comp, idx):
    try:
        p, content, reasoning = call_model(key, prompts[comp])
        ok = p is not None
        row = {"qid": qid, "qpath": qpath, "e_role": e_role, "component": comp,
               "rollout_idx": idx, "probability": p, "content": content,
               "reasoning_field": reasoning, "ok": ok}
    except Exception as e:  # noqa: BLE001 -- never kill the batch
        row = {"qid": qid, "qpath": qpath, "e_role": e_role, "component": comp,
               "rollout_idx": idx, "probability": None, "content": "",
               "reasoning_field": "", "ok": False, "error": str(e)}
    write_row(row)
    return row


def load_done():
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("ok"):
                done.add((r["qid"], r["component"], r["rollout_idx"]))
    return done


def main():
    key = load_openrouter_key()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    done = load_done()
    print(f"model={MODEL}  N={N_SAMPLES}/component  concurrency={CONCURRENCY}")
    print(f"out={OUT}   already-ok rows: {len(done)}")

    tasks = []
    for qid, fname, e_role in QUESTIONS:
        qpath = os.path.join(ROOT, CDIR, fname)
        q = load_question(qpath)
        prompts = component_prompts(q)
        for comp in COMP_ORDER:
            for idx in range(N_SAMPLES):
                if (qid, comp, idx) in done:
                    continue
                tasks.append((qid, qpath, e_role, prompts, comp, idx))
    print(f"tasks to run: {len(tasks)}  (of {len(QUESTIONS)*4*N_SAMPLES} total)")
    if not tasks:
        print("nothing to do -- all done.")
        return

    n_ok = 0
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        for i, row in enumerate(ex.map(lambda t: one(key, *t), tasks), 1):
            n_ok += 1 if row["ok"] else 0
            if i % 32 == 0 or i == len(tasks):
                print(f"  {i}/{len(tasks)}  ok-so-far={n_ok}", flush=True)
    print(f"done. {n_ok}/{len(tasks)} ok this run.")


if __name__ == "__main__":
    main()
