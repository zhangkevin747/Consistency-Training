"""Shared helpers: JSONL IO, thinking/answer splitting, and a robust probability parser."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Iterator


# ---------------------------------------------------------------- JSONL IO
def read_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    out = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def append_jsonl(path: str | Path, row: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def iter_jsonl(path: str | Path) -> Iterator[dict]:
    path = Path(path)
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# ---------------------------------------------------------------- thinking/answer
def split_thinking(text: str) -> tuple[str, str]:
    """Return (thinking, answer). Qwen3-Thinking emits reasoning then </think> then answer.

    The chat template opens <think> in the prompt, so the generated text usually starts
    inside the reasoning and contains a closing </think>. If there is no </think> (e.g.
    truncated at max_tokens), the whole text is treated as thinking and answer is "".
    """
    if "</think>" in text:
        idx = text.rindex("</think>")
        thinking = text[:idx]
        answer = text[idx + len("</think>"):]
    else:
        thinking, answer = text, ""
    # strip a stray leading <think> if present
    thinking = thinking.replace("<think>", "").strip()
    return thinking, answer.strip()


# ---------------------------------------------------------------- probability parsing
# Constant system prompt used for every rollout (identical across phrasings/groups, so it
# standardizes extraction without being a phrasing confound). See sample_rollouts.py.
ANSWER_FORMAT_INSTRUCTION = (
    "After your reasoning, end your reply with your final probability on its own line "
    "in exactly this form:\nANSWER: <a single number between 0 and 1>"
)
# For non-thinking models (e.g. Gemma): elicit an explicit chain of thought, then the answer.
COT_INSTRUCTION = (
    "Reason through the question step by step, weighing the key considerations. "
    "Then end your reply with your final probability on its own line in exactly this "
    "form:\nANSWER: <a single number between 0 and 1>"
)

# explicit final-answer marker (preferred)
_ANSWER_RE = re.compile(
    r"(?:ANSWER|FINAL(?:\s+ANSWER)?)\s*[:=]\s*"
    r"(\d{1,3}(?:\.\d+)?\s*%|0?\.\d+|1(?:\.0+)?|0(?:\.0+)?)",
    re.IGNORECASE,
)
# any percentage OR a bare decimal/0/1 in [0,1], scanned in document order
_NUM_RE = re.compile(
    r"(\d{1,3}(?:\.\d+)?\s*%)|((?<![\d.])(?:0?\.\d+|1(?:\.0+)?|0(?:\.0+)?)(?![\d]))"
)


def _to_float(token: str) -> float | None:
    token = token.strip()
    if token.endswith("%"):
        try:
            v = float(token[:-1].strip()) / 100.0
        except ValueError:
            return None
    else:
        try:
            v = float(token)
        except ValueError:
            return None
    return v if 0.0 <= v <= 1.0 else None


def parse_probability(answer: str) -> float | None:
    """Extract the model's final probability in [0,1] from the answer text.

    Strategy (most reliable first):
      1. the last explicit "ANSWER: <x>" / "FINAL: <x>" marker (what we instruct).
      2. otherwise the last numeric value (percentage or decimal) by position, since a
         thinking model states its final answer at the very end.
    Returns None if nothing valid is found.
    """
    if not answer:
        return None

    marked = _ANSWER_RE.findall(answer)
    for tok in reversed(marked):
        v = _to_float(tok)
        if v is not None:
            return v

    last_val = None
    for m in _NUM_RE.finditer(answer):
        tok = m.group(1) or m.group(2)
        v = _to_float(tok)
        if v is not None:
            last_val = v
    return last_val


# ---------------------------------------------------------------- id helpers
def type1_group_id(qid: str, phrasing_idx: int) -> str:
    return f"{qid}__p{phrasing_idx}"


def type2_group_id(qid: str, kind: str) -> str:  # kind in {"A", "AandB"}
    return f"{qid}__{kind}"


def rollout_id(group_id: str, idx: int) -> str:
    return f"{group_id}__r{idx}"
