"""Headless `claude -p` wrapper: single-shot, pure-text calls using your subscription auth
(no API key). Includes JSON-envelope parsing, retry/backoff (with longer waits on rate
limits), and a parallel map that reports results incrementally for checkpoint/resume.

Validated invocation (CLI v2.1.168):
    printf '%s' "<prompt>" | claude -p --model opus --effort xhigh \
        --system-prompt "<minimal>" --output-format json \
        --disallowedTools "..." --no-session-persistence
  -> parse stdout JSON, read `.result`.
"""
from __future__ import annotations

import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Sequence

# Disable every tool so each call is a pure text completion (no agentic loop / file access).
DEFAULT_DISALLOWED = (
    "Bash Edit Write Read WebSearch WebFetch Glob Grep Task TodoWrite "
    "NotebookEdit MultiEdit SlashCommand"
)
RATE_LIMIT_MARKERS = (
    "rate limit", "rate_limit", "overloaded", "usage limit", "429",
    "too many requests", "capacity", "quota",
)


@dataclass
class ClaudeResult:
    ok: bool
    text: str
    error: str | None = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    raw: dict | None = None


def _build_cmd(model: str, effort: str | None, system_prompt: str | None) -> list[str]:
    cmd = [
        "claude", "-p", "--model", model,
        "--output-format", "json",
        "--disallowedTools", DEFAULT_DISALLOWED,
        "--no-session-persistence",
    ]
    if effort:
        cmd += ["--effort", effort]
    if system_prompt:
        cmd += ["--system-prompt", system_prompt]
    return cmd


def _is_rate(text: str) -> bool:
    t = (text or "").lower()
    return any(m in t for m in RATE_LIMIT_MARKERS)


def _try_parse_json(out: str) -> dict | None:
    out = out.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        # tolerate stray leading log lines: try the last brace-balanced line
        for line in reversed(out.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    return None


def call_claude(
    prompt: str,
    model: str = "opus",
    effort: str | None = None,
    system_prompt: str | None = None,
    timeout: int = 300,
    max_retries: int = 4,
    backoff_base: float = 5.0,
) -> ClaudeResult:
    """Run one headless call with retries. Returns ClaudeResult(ok=False, ...) if all fail."""
    cmd = _build_cmd(model, effort, system_prompt)
    last_err = None
    for attempt in range(max_retries + 1):
        rate = False
        try:
            proc = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            last_err = "timeout"
        else:
            d = _try_parse_json(proc.stdout)
            if d is None:
                last_err = f"exit={proc.returncode} no-json stderr={proc.stderr[:300]!r}"
                rate = _is_rate(proc.stderr)
            elif d.get("is_error") or not d.get("result"):
                blob = f"{d.get('subtype')} {d.get('result')} {d.get('api_error_status')} {proc.stderr}"
                last_err = f"is_error: {blob[:300]}"
                rate = _is_rate(blob)
            else:
                return ClaudeResult(
                    ok=True,
                    text=str(d["result"]).strip(),
                    cost_usd=float(d.get("total_cost_usd") or 0.0),
                    duration_ms=int(d.get("duration_ms") or 0),
                    raw=d,
                )
        if attempt < max_retries:
            wait = (30.0 * (attempt + 1)) if rate else (backoff_base * (2 ** attempt))
            time.sleep(wait)
    return ClaudeResult(ok=False, text="", error=last_err)


def parallel_each(
    func: Callable[[object], object],
    items: Sequence[object],
    concurrency: int,
    on_done: Callable[[object, object], None] | None = None,
) -> list[object]:
    """Run func over items with a thread pool. Calls on_done(item, result) as each finishes
    (use it to append results to disk for checkpoint/resume). Returns results in input order.
    """
    results: list[object] = [None] * len(items)
    if not items:
        return results
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        fut_to_idx = {ex.submit(func, it): i for i, it in enumerate(items)}
        for fut in as_completed(fut_to_idx):
            i = fut_to_idx[fut]
            res = fut.result()
            results[i] = res
            if on_done is not None:
                on_done(items[i], res)
    return results
