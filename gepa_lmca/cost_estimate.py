"""Cost estimate for a 5-fold GEPA run on LMCA with gpt-5.4-mini (self-reflection).

Grounded in the real prompt size + data. GEPA's max_metric_calls is a HARD cap on
position-evaluations per fold, so cost is bounded by budget. Each position-eval =
(avg gold-rated critiques) judge calls, and every judge call resends the frozen
~62k-char rubric -> input tokens dominate. The rubric prefix is identical across
calls, so prompt caching (if the provider honors it) cuts input cost ~10x.
"""
import os
from data import load_lmca, ec_scoreable
from prompt import RUBRIC_TEMPLATE
from metric import GOLD

# ---- gpt-5.4-mini pricing ($/1M tokens) ----
IN, OUT, CACHED_IN = 0.75, 4.50, 0.075        # cached input ~= 10% of input
OUT_TOKENS = 700                               # step-by-step reasoning + JSON (assumption)
CHARS_PER_TOK = 4.0

# ---- MEASURED prompt + caching (from check_cache.py on gpt-5.4-mini) ----
in_tokens = 13300        # real tokenizer count for a full judge prompt
CACHE_FRAC = 0.88        # empirical cache-hit on the real varying-suffix pattern (call 3)

cost_uncached = in_tokens * IN / 1e6 + OUT_TOKENS * OUT / 1e6
cost_cached = (in_tokens * (CACHE_FRAC * CACHED_IN + (1 - CACHE_FRAC) * IN) / 1e6
               + OUT_TOKENS * OUT / 1e6)

# ---- data shape ----
items = ec_scoreable(load_lmca())
n = len(items)
gold_crit = [sum(1 for c in it["critiques"] if c["rater_overall"].get(GOLD) is not None)
             for it in items]
avg_crit = sum(gold_crit) / len(gold_crit)
test_pos = n // 5                              # held-out fold size

print(f"measured prompt ~{in_tokens} input tok, {100*CACHE_FRAC:.0f}% cached (real pattern)")
print(f"per judge call: uncached ${cost_uncached:.4f} | cached ${cost_cached:.4f}  "
      f"(out={OUT_TOKENS} tok assumed)")
print(f"data: {n} EC-scoreable positions, avg {avg_crit:.1f} gold critiques/position, "
      f"test fold ~{test_pos} positions\n")

print(f"{'budget/fold':>11} {'judge calls (5 folds)':>22} {'UNCACHED':>10} {'CACHED':>9}")
for budget in (300, 600, 1000, 1500):
    # per fold: optimization (budget position-evals) + seed&gepa test eval (2*test_pos)
    calls_per_fold = (budget + 2 * test_pos) * avg_crit
    calls = calls_per_fold * 5
    # reflection LM calls (~budget/8 proposals/fold), cheap; approximate at cached judge cost
    refl = (budget / 8) * 5 * 0.006
    print(f"{budget:>11} {calls:>22,.0f} "
          f"${calls*cost_uncached+refl:>8,.0f} ${calls*cost_cached+refl:>7,.0f}")

print("\nNotes:")
print("- cost is bounded by budget (max_metric_calls is a hard cap per fold).")
print("- input tokens dominate because the 62k rubric is resent every call.")
print("- CACHED assumes the provider caches the fixed rubric prefix (~10x cheaper input).")
print(f"- a meaningful GEPA run typically wants budget >= ~600 (valset ~{n*4//5 - 50} +"
      " several accepted candidates).")
