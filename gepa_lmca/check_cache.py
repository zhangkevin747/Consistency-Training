"""Verify OpenRouter prompt caching for gpt-5.4-mini on the real judge prompt.

Fires the ~16k-token rubric prompt three times and reads usage.prompt_tokens_details:
  call 1 = cold (cache miss, cached_tokens ~0)
  call 2 = identical prompt          -> expect cached_tokens high
  call 3 = SAME rubric prefix, DIFFERENT argument/critique (the real GEPA pattern)
           -> expect cached_tokens ~= the shared prefix length
"""
import json
import time
import urllib.request

from data import load_lmca, ec_scoreable
from prompt import build_prompt, SEED_GUIDANCE
from judge import load_openrouter_key, TASK_MODEL

key = load_openrouter_key()
items = ec_scoreable(load_lmca())
a, b = items[0], items[1]
prompts = [
    build_prompt(SEED_GUIDANCE, a["argument"], a["critiques"][0]["text"]),  # cold
    build_prompt(SEED_GUIDANCE, a["argument"], a["critiques"][0]["text"]),  # identical
    build_prompt(SEED_GUIDANCE, b["argument"], b["critiques"][0]["text"]),  # same prefix, new suffix
]
labels = ["cold (miss expected)", "identical prompt", "same prefix, new suffix"]


def call(prompt):
    body = json.dumps({
        "model": TASK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 50,
        "usage": {"include": True},
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


print(f"model={TASK_MODEL}\n")
for i, (p, lab) in enumerate(zip(prompts, labels), 1):
    d = call(p)
    u = d.get("usage", {})
    cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    pt = u.get("prompt_tokens", 0)
    print(f"call {i} [{lab}]")
    print(f"   prompt_tokens={pt}  cached_tokens={cached}  "
          f"({100*cached/pt:.0f}% cached)  cost=${u.get('cost', 0):.4f}")
    print(f"   raw usage: {json.dumps(u)}")
    if i < len(prompts):
        time.sleep(3)  # let the cache register before the next call

print("\nIf call 2/3 show cached_tokens ~= prompt_tokens, caching works -> use the CACHED estimate.")
