"""Blind pairwise reasoning-quality judging with Opus 4.8 (xhigh) via headless `claude -p`.

Pairs are built to MAXIMISE the reward gap, so the judge compares responses that genuinely
differ in conclusion (high power), and are fair to compare (both came from neutral prompts):

  Type 1 (cross-phrasing): pool all of a kept question's rollouts, rank by reward = -|v - T|,
    and pair the NEAR_FAR_Q nearest-to-consensus rollouts against the NEAR_FAR_Q farthest. The
    judge sees a NEUTRAL question stem (built from the claim), blind to which phrasing produced
    each response and blind to the number, so the quality preference is independent of the reward.
  Type 2 (within the A-and-B group): pair the TYPE2_Q highest-reward (lowest P(A and B)) rollouts
    against the TYPE2_Q lowest-reward ones -- i.e. respecting vs violating P(A and B) <= P(A).

The correlation unit is the QUESTION for Type 1 and the GROUP for Type 2; we carry it as
`unit_id`. A/B display order is randomized per pair (deterministically, for reproducible resume),
and results stream to disk so a rate-limited run can resume.
"""
from __future__ import annotations

import argparse
import hashlib
import random
from collections import defaultdict

import pandas as pd

from . import config as C
from .claude_cli import call_claude, parallel_each
from .select import load_selection
from .utils import append_jsonl, read_jsonl, type2_group_id

JUDGE_SYSTEM = (
    "You are an expert evaluator of reasoning quality. You judge how well-reasoned a response "
    "is, considering the entire response. You follow the output format exactly."
)


def _rng_for(pair_id: str) -> random.Random:
    seed = int(hashlib.md5(pair_id.encode()).hexdigest()[:8], 16)
    return random.Random(seed)


def _neutral_stem(claim: str) -> str:
    return ("Estimate the probability that the following claim is true. "
            "Answer with a single number between 0 and 1.\n\n"
            f"Claim: {claim}")


def _mk_pair(pair_id: str, unit_id: str, qtype: int, ra: dict, rb: dict, prompt: str) -> dict:
    disp_first = "a" if _rng_for(pair_id).random() < 0.5 else "b"
    return {
        "pair_id": pair_id, "unit_id": unit_id, "type": qtype,
        "rollout_a": ra["rollout_id"], "rollout_b": rb["rollout_id"],
        "prompt": prompt, "displayed_first": disp_first,
        "text_a": ra["full_text"], "text_b": rb["full_text"],
    }


def build_pairs(rollouts: list[dict], reward_by_id: dict[str, float],
                claim_by_qid: dict[str, str], kept_t1: set[str],
                kept_t2: set[str]) -> list[dict]:
    """Reward-gap-maximised pairs for the kept questions (see module docstring)."""
    by_id = {r["rollout_id"]: r for r in rollouts
             if r.get("parse_ok") and reward_by_id.get(r["rollout_id"]) is not None}

    def rwd(r: dict) -> float:
        return reward_by_id[r["rollout_id"]]

    pairs: list[dict] = []

    # ---- Type 1: cross-phrasing, near-consensus vs far-from-consensus ----
    Q = C.NEAR_FAR_Q
    by_q: dict[str, list[dict]] = defaultdict(list)
    for r in by_id.values():
        if r.get("type") == 1 and r["question_id"] in kept_t1:
            by_q[r["question_id"]].append(r)
    for qid, rs in by_q.items():
        if len(rs) < 2 * Q:
            continue
        rs.sort(key=lambda r: (rwd(r), r["rollout_id"]))
        far = rs[:Q]        # lowest reward  = farthest from consensus T
        near = rs[-Q:]      # highest reward = nearest consensus T
        stem = _neutral_stem(claim_by_qid.get(qid, qid))
        for ni, a in enumerate(near):
            for fj, b in enumerate(far):
                if rwd(a) <= rwd(b):
                    continue  # no reward gap -> uninformative
                pairs.append(_mk_pair(f"{qid}__n{ni}f{fj}", qid, 1, a, b, stem))

    # ---- Type 2: within the (A and B) group, high-reward vs low-reward ----
    Q2 = C.TYPE2_Q
    for qid in kept_t2:
        for kind in C.TYPE2_JUDGE_GROUPS:
            gid = type2_group_id(qid, kind)
            rs = [r for r in by_id.values() if r.get("type") == 2 and r["group_id"] == gid]
            if len(rs) < 2 * Q2:
                continue
            rs.sort(key=lambda r: (rwd(r), r["rollout_id"]))
            low = rs[:Q2]       # lowest reward  (violates conjunction most)
            high = rs[-Q2:]     # highest reward (respects conjunction most)
            prompt = rs[0]["prompt"]  # same prompt within a Type-2 group
            for hi, a in enumerate(high):
                for lj, b in enumerate(low):
                    if rwd(a) <= rwd(b):
                        continue
                    pairs.append(_mk_pair(f"{gid}__h{hi}l{lj}", gid, 2, a, b, prompt))
    return pairs


def _judge_prompt(prompt: str, text_first: str, text_second: str) -> str:
    return f"""Two independent responses were written to the SAME question below. Each response
shows the writer's full reasoning followed by a final probability.

QUESTION:
{prompt}

===== Response 1 =====
{text_first}

===== Response 2 =====
{text_second}

Which response demonstrates BETTER REASONING overall -- more careful, logically coherent,
well-calibrated, and intellectually honest -- judging the entire response (the quality of the
reasoning, not merely whether you agree with the final number)?

Reply with EXACTLY one character and nothing else:
1  = Response 1 reasons better
2  = Response 2 reasons better
T  = genuinely equal
"""


def _parse_choice(text: str) -> str | None:
    for ch in text.strip():
        if ch in "12":
            return ch
        if ch in "Tt":
            return "T"
    return None


def _judge_one(pair: dict) -> dict:
    if pair["displayed_first"] == "a":
        first, second = pair["text_a"], pair["text_b"]
    else:
        first, second = pair["text_b"], pair["text_a"]
    res = call_claude(
        _judge_prompt(pair["prompt"], first, second),
        model=C.JUDGE_MODEL, effort=C.JUDGE_EFFORT, system_prompt=JUDGE_SYSTEM,
        timeout=C.JUDGE_TIMEOUT_S, max_retries=C.JUDGE_MAX_RETRIES,
    )
    out = {
        "pair_id": pair["pair_id"], "unit_id": pair["unit_id"], "type": pair["type"],
        "rollout_a": pair["rollout_a"], "rollout_b": pair["rollout_b"],
        "displayed_first": pair["displayed_first"],
        "ok": res.ok, "raw": res.text, "error": res.error,
        "cost_usd": res.cost_usd, "duration_ms": res.duration_ms,
        "winner": None,
    }
    if res.ok:
        choice = _parse_choice(res.text)
        if choice == "T":
            out["winner"] = "tie"
        elif choice in ("1", "2"):
            # map displayed slot back to logical rollout a/b
            first_is = "a" if pair["displayed_first"] == "a" else "b"
            second_is = "b" if pair["displayed_first"] == "a" else "a"
            out["winner"] = first_is if choice == "1" else second_is
        else:
            out["ok"] = False
            out["error"] = f"unparseable choice: {res.text[:80]!r}"
    return out


def _load_inputs(pilot: bool) -> tuple[list[dict], dict[str, float], dict[str, str], set, set]:
    rollouts = read_jsonl(C.rollouts_file(pilot))
    if not rollouts:
        raise SystemExit(f"no rollouts at {C.rollouts_file(pilot)} -- run sample_rollouts first")
    rdf = pd.read_csv(C.rewards_file(pilot))
    reward_by_id = {row.rollout_id: float(row.reward)
                    for row in rdf.itertuples() if pd.notna(row.reward)}
    claim_by_qid = {q["id"]: q.get("claim", q["id"]) for q in read_jsonl(C.questions_file(1, pilot))}
    kept_t1, kept_t2 = load_selection(pilot)
    return rollouts, reward_by_id, claim_by_qid, kept_t1, kept_t2


def judge(pilot: bool = False) -> list[dict]:
    rollouts, reward_by_id, claim_by_qid, kept_t1, kept_t2 = _load_inputs(pilot)
    pairs = build_pairs(rollouts, reward_by_id, claim_by_qid, kept_t1, kept_t2)
    if not pairs:
        raise SystemExit("no judge pairs built -- check the selection / rewards stages")

    out_path = C.judgments_file(pilot)
    done = {j["pair_id"] for j in read_jsonl(out_path) if j.get("ok")}
    todo = [p for p in pairs if p["pair_id"] not in done]
    n_units = len({p["unit_id"] for p in pairs})
    print(f"Judging {len(todo)} pairs ({len(done)} already done) across {n_units} units "
          f"({len(kept_t1)} Type-1 questions, {len(kept_t2)} Type-2 questions), "
          f"concurrency={C.JUDGE_CONCURRENCY}")

    state = {"n": 0, "cost": 0.0, "fail": 0}

    def _on_done(_pair, result):
        append_jsonl(out_path, result)
        state["n"] += 1
        state["cost"] += result.get("cost_usd", 0.0)
        if not result.get("ok"):
            state["fail"] += 1
        if state["n"] % 10 == 0 or state["n"] == len(todo):
            print(f"  judged {state['n']}/{len(todo)}  fails={state['fail']}  "
                  f"cost=${state['cost']:.2f}")

    parallel_each(_judge_one, todo, C.JUDGE_CONCURRENCY, on_done=_on_done)
    all_judgments = read_jsonl(out_path)
    print(f"Total judgments on disk: {len(all_judgments)} -> {out_path}")
    return all_judgments


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    args = ap.parse_args()
    judge(pilot=args.pilot)


if __name__ == "__main__":
    main()
