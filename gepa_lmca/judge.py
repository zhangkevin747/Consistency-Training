"""OpenRouter chat client + LMCA judge call (parse 7-dim JSON) + reflection LM.

LMCA is private: paid models only (no free OpenRouter). TASK_MODEL is the judge
under optimization; the reflection LM (self-reflection) uses the same model.
"""
import json
import os
import re
import time
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK_MODEL = os.environ.get("TASK_MODEL", "openai/gpt-5.4-mini")
REFLECT_MODEL = os.environ.get("REFLECT_MODEL", "openai/gpt-5.4-mini")
DIMS = ["centrality", "strength", "correctness", "clarity",
        "dead weight", "single issue", "overall"]


def load_openrouter_key():
    with open(os.path.join(ROOT, ".env")) as f:
        for line in f:
            if "=" in line and line.split("=", 1)[0].strip() == "OPENROUTER":
                return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("OPENROUTER key not found in .env")


def chat(key, messages, model, temperature=0.0, max_tokens=None):
    payload = {"model": model, "temperature": temperature, "messages": messages}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    body = json.dumps(payload).encode()
    for attempt in range(6):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"] or ""
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if attempt < 5:
                time.sleep(2 ** attempt + attempt)
                continue
            raise
    return ""


def parse_scores(text):
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not blocks:
        blocks = re.findall(r"(\{[^{}]*\"overall\"[^{}]*\})", text, re.S)
    for b in reversed(blocks):
        try:
            d = json.loads(b)
            if "overall" in d:
                return {k: float(d[k]) for k in DIMS
                        if k in d and isinstance(d[k], (int, float))}
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def run_judge(key, prompt, model=None, temperature=0.0):
    """Return (scores_dict_or_None, raw_text) for a fully-built judge prompt."""
    raw = chat(key, [{"role": "user", "content": prompt}], model or TASK_MODEL, temperature)
    return parse_scores(raw), raw


def make_reflection_lm(key, model=None, max_tokens=8000):
    """Build a gepa reflection_lm callable: (prompt:str|messages) -> str."""
    mdl = model or REFLECT_MODEL

    def lm(prompt):
        messages = ([{"role": "user", "content": prompt}]
                    if isinstance(prompt, str) else prompt)
        return chat(key, messages, mdl, temperature=1.0, max_tokens=max_tokens)
    return lm
