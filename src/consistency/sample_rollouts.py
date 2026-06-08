"""Sample CoT rollouts from Qwen3-4B-Thinking-2507 on the Metal GPU via mlx_lm.

For each group we sample G rollouts (same prompt, stochastic decoding):
  Type 1: one group per phrasing  -> N_PHRASINGS groups per question.
  Type 2: groups "A" and "AandB"  -> 2 groups per question.
A constant system instruction pins the output format (ANSWER: <0..1>) so the final probability
is reliably parseable; it is identical across all phrasings/groups, so it is not a confound.
Results are written incrementally and existing rollout_ids are skipped (resume-safe).
"""
from __future__ import annotations

import argparse
import os
import time

from . import config as C
from .claude_cli import parallel_each
from .utils import (ANSWER_FORMAT_INSTRUCTION, COT_INSTRUCTION, append_jsonl,
                    parse_probability, read_jsonl, rollout_id, split_thinking,
                    type1_group_id, type2_group_id)

_MODEL = None
_TOK = None


def load_model():
    global _MODEL, _TOK
    if _MODEL is None:
        from mlx_lm import load
        print(f"Loading {C.MODEL_ID} via mlx_lm ...")
        t0 = time.time()
        _MODEL, _TOK = load(C.MODEL_ID)
        print(f"  loaded in {time.time() - t0:.1f}s")
    return _MODEL, _TOK


def _prompt_ids(tok, user_prompt: str) -> list[int]:
    messages = [
        {"role": "system", "content": ANSWER_FORMAT_INSTRUCTION},
        {"role": "user", "content": user_prompt},
    ]
    text = tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
    return tok.encode(text)


def build_tasks(t1: list[dict], t2: list[dict]) -> list[dict]:
    """One task per rollout: (rollout_id, group_id, group_kind, question_id, type, prompt)."""
    tasks = []
    for q in t1:
        for p_idx, phrasing in enumerate(q["phrasings"]):
            gid = type1_group_id(q["id"], p_idx)
            for r in range(C.G_ROLLOUTS):
                tasks.append({"rollout_id": rollout_id(gid, r), "group_id": gid,
                              "group_kind": f"p{p_idx}", "question_id": q["id"],
                              "type": 1, "prompt": phrasing})
    for q in t2:
        for kind, key in (("A", "prompt_A"), ("AandB", "prompt_AandB")):
            gid = type2_group_id(q["id"], kind)
            for r in range(C.G_ROLLOUTS):
                tasks.append({"rollout_id": rollout_id(gid, r), "group_id": gid,
                              "group_kind": kind, "question_id": q["id"],
                              "type": 2, "prompt": q[key]})
    return tasks


def _pending(pilot: bool) -> tuple[list[dict], object, int]:
    t1 = read_jsonl(C.questions_file(1, pilot))
    t2 = read_jsonl(C.questions_file(2, pilot))
    if not t1 and not t2:
        raise SystemExit("no questions found -- run generate_questions first")
    out_path = C.rollouts_file(pilot)
    done = {r["rollout_id"] for r in read_jsonl(out_path)}
    tasks = [t for t in build_tasks(t1, t2) if t["rollout_id"] not in done]
    return tasks, out_path, len(done)


def sample(pilot: bool = False) -> list[dict]:
    """Dispatch to the configured rollout backend."""
    if C.ROLLOUT_BACKEND == "openrouter":
        return sample_openrouter(pilot)
    return sample_mlx(pilot)


# ---------------------------------------------------------------- OpenRouter (cloud)
def _openrouter_call(prompt: str, api_key: str) -> tuple[str | None, str | None, str | None, str | None]:
    """Return (content, reasoning, finish_reason, error). Reasoning models put their chain of
    thought in a separate `reasoning` field; content holds the post-thinking answer + ANSWER line."""
    import requests
    body = {
        "model": C.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": COT_INSTRUCTION},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": C.OPENROUTER_MAX_TOKENS,
        **C.OPENROUTER_SAMPLING,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
               "X-Title": "consistency-training-preliminary"}
    last = "unknown"
    for attempt in range(5):
        try:
            r = requests.post(C.OPENROUTER_URL, json=body, headers=headers, timeout=240)
            if r.status_code == 200:
                d = r.json()
                if "choices" not in d:
                    last = f"no choices: {str(d)[:200]}"
                else:
                    ch = d["choices"][0]
                    msg = ch["message"]
                    reasoning = msg.get("reasoning") or msg.get("reasoning_content")
                    return msg.get("content"), reasoning, ch.get("finish_reason"), None
            elif r.status_code in (429, 500, 502, 503, 520, 524):
                last = f"http {r.status_code}"
            else:
                return None, None, None, f"http {r.status_code}: {r.text[:200]}"
        except Exception as e:  # network / json errors -> retry
            last = f"{type(e).__name__}: {e}"
        time.sleep(4 * (attempt + 1))
    return None, None, None, f"failed after retries: {last}"


def sample_openrouter(pilot: bool = False) -> list[dict]:
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY (or OPENROUTER) not set -- add it to .env")
    tasks, out_path, n_done = _pending(pilot)
    print(f"[openrouter:{C.OPENROUTER_MODEL}] {len(tasks)} rollouts to sample "
          f"({n_done} done), G={C.G_ROLLOUTS}, concurrency={C.OPENROUTER_CONCURRENCY}")
    if not tasks:
        return read_jsonl(out_path)

    state = {"n": 0, "parsed": 0, "fail": 0, "t0": time.time()}

    def work(task: dict) -> dict:
        content, reasoning, finish, err = _openrouter_call(task["prompt"], api_key)
        if content is None and reasoning is None:
            return {**task, "full_text": "", "answer": "", "probability": None,
                    "parse_ok": False, "truncated": False, "error": err}
        content = content or ""
        # Stitch reasoning + answer so the judge sees the actual chain of thought, not just the
        # terse summary. The ANSWER: marker lives in `content`, so parse the probability there.
        full = (f"{reasoning}\n\n---\n\n{content}" if reasoning else content)
        prob = parse_probability(content) if content else parse_probability(full)
        return {**task, "full_text": full, "answer": content, "probability": prob,
                "parse_ok": prob is not None, "truncated": finish == "length",
                "n_chars": len(full)}

    def on_done(_t, row):
        append_jsonl(out_path, row)
        state["n"] += 1
        state["parsed"] += int(row["parse_ok"])
        state["fail"] += int(row.get("error") is not None)
        if state["n"] % 20 == 0 or state["n"] == len(tasks):
            dt = time.time() - state["t0"]
            print(f"  {state['n']}/{len(tasks)} parsed={state['parsed']} fail={state['fail']} "
                  f"({dt:.0f}s, {state['n'] / max(dt, 1e-9):.1f}/s)")

    parallel_each(work, tasks, C.OPENROUTER_CONCURRENCY, on_done=on_done)
    print(f"Done. parsed {state['parsed']}/{state['n']}, failures {state['fail']} -> {out_path}")
    return read_jsonl(out_path)


# ---------------------------------------------------------------- MLX (local)
def sample_mlx(pilot: bool = False) -> list[dict]:
    from mlx_lm import batch_generate
    from mlx_lm.sample_utils import make_sampler

    tasks, out_path, n_done = _pending(pilot)
    print(f"[mlx:{C.MODEL_ID}] {len(tasks)} rollouts to sample ({n_done} done), "
          f"G={C.G_ROLLOUTS}, batch={C.ROLLOUT_BATCH_SIZE}, max_tokens={C.MAX_TOKENS}")
    if not tasks:
        return read_jsonl(out_path)

    model, tok = load_model()
    sampler = make_sampler(**C.SAMPLING)

    t0 = time.time()
    n_done = 0
    n_parsed = 0
    n_trunc = 0
    for start in range(0, len(tasks), C.ROLLOUT_BATCH_SIZE):
        chunk = tasks[start:start + C.ROLLOUT_BATCH_SIZE]
        prompts = [_prompt_ids(tok, t["prompt"]) for t in chunk]
        resp = batch_generate(model, tok, prompts=prompts, max_tokens=C.MAX_TOKENS,
                              sampler=sampler, verbose=False)
        for t, full in zip(chunk, resp.texts):
            thinking, answer = split_thinking(full)
            prob = parse_probability(answer if answer else full)
            truncated = "</think>" not in full
            row = {**t, "full_text": full, "answer": answer, "probability": prob,
                   "parse_ok": prob is not None, "truncated": truncated,
                   "n_chars": len(full)}
            append_jsonl(out_path, row)
            n_done += 1
            n_parsed += int(prob is not None)
            n_trunc += int(truncated)
        dt = time.time() - t0
        print(f"  {n_done}/{len(tasks)} rollouts  parsed={n_parsed}  truncated={n_trunc}  "
              f"({dt:.0f}s, {n_done / max(dt, 1e-9):.2f} rollouts/s)")

    print(f"Done. parsed {n_parsed}/{n_done} ({100 * n_parsed / max(n_done, 1):.0f}%), "
          f"truncated {n_trunc}. -> {out_path}")
    return read_jsonl(out_path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    args = ap.parse_args()
    sample(pilot=args.pilot)


if __name__ == "__main__":
    main()
