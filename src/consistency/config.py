"""Central configuration for the consistency preliminary-test pipeline.

All knobs in one place. Locked decisions (see control-room/QA.md):
- Type 1: 4 NEUTRAL equivalent phrasings/question, G=6 rollouts/phrasing. Over-generate, then
  keep only questions with natural phrasing spread >= SPREAD_MIN. Judge cross-phrasing
  near-T-vs-far-from-T pairs (NEAR_FAR_Q^2 per question) under a neutral question stem.
- Type 2: P(A) and P(A and B), G=6. Keep only questions that actually violate the conjunction
  (V >= VIOLATION_MIN); judge the (A and B) group only, high-reward vs low-reward.
- Judge: Opus 4.8 xhigh via headless `claude -p` (subscription auth, no API key).
- Rollouts: Gemma-3-4B via OpenRouter (cloud) by default, or mlx_lm on the Metal GPU.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no python-dotenv dep): KEY=VALUE lines -> os.environ."""
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")
DATA = ROOT / "data"
QUESTIONS_DIR = DATA / "questions"
ROLLOUTS_DIR = DATA / "rollouts"
REWARDS_DIR = DATA / "rewards"
JUDGMENTS_DIR = DATA / "judgments"
RESULTS_DIR = ROOT / "results"

for _d in (QUESTIONS_DIR, ROLLOUTS_DIR, REWARDS_DIR, JUDGMENTS_DIR, RESULTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- dataset shape
N_PHRASINGS = 4          # equivalent, NEUTRAL phrasings per Type-1 question
G_ROLLOUTS = 6           # rollouts per (question x phrasing) and per Type-2 group

# Final dataset = questions KEPT after the natural-inconsistency screen (see below).
N_KEEP_TYPE1 = 50
N_KEEP_TYPE2 = 50
# Candidates generated + rolled out BEFORE screening. We over-generate, then keep only the
# questions the model is naturally inconsistent on -- never by leading or loading the prompt.
N_CAND_TYPE1 = 150
N_CAND_TYPE2 = 120
# Conceptual domains to draw claims from (alignment / ethics / consciousness flavor).
DOMAINS = [
    "animal consciousness and sentience",
    "moral status and moral patienthood",
    "AI safety, alignment, and AI risk",
    "population ethics and the long-term future",
    "metaethics and normative ethics",
]

# ---------------------------------------------------------------- natural-inconsistency screen
# Type 1: keep a question only if its NEUTRAL phrasings genuinely disagree -- the range of the
# per-phrasing mean probabilities is >= SPREAD_MIN. This is the model's *unforced* inconsistency
# (the thing the consistency reward is meant to catch); we never induce it with leading prompts.
SPREAD_MIN = 0.10
# Type 2: keep a question only if the conjunction is actually VIOLATED on average,
# i.e. mean P(A and B) - mean P(A) >= VIOLATION_MIN. Non-violating questions carry no reward
# signal (V=0) and are dropped before any judging.
VIOLATION_MIN = 0.02

# ---------------------------------------------------------------- judge pairing
# Type 1: cross-phrasing "near consensus vs far from consensus". Pool all of a question's
# rollouts, rank by reward = -|v - T|, then pair the NEAR_FAR_Q nearest-to-T against the
# NEAR_FAR_Q farthest (Q*Q pairs). Large reward gap per pair -> high power, and fair: both sides
# came from neutral prompts, and the judge sees a neutral question stem (blind to phrasing).
NEAR_FAR_Q = 4
# Type 2: judge only the (A and B) group -- the side where lower probability = respecting
# P(A&B) <= P(A) = better reasoning. Pair the TYPE2_Q highest-reward (lowest prob) rollouts
# against the TYPE2_Q lowest-reward (highest prob) ones.
TYPE2_Q = 3
TYPE2_JUDGE_GROUPS = ("AandB",)

# ---------------------------------------------------------------- rollout backend
# "openrouter": fast cloud rollouts via Gemma (needs OPENROUTER_API_KEY in .env).
# "mlx":        local Qwen3-4B-Thinking on the Metal GPU (no API key, slower).
ROLLOUT_BACKEND = "openrouter"

# --- MLX (local) ---
# bf16 original (honors the locked "no quantization" decision). mlx_lm loads HF safetensors
# directly. Fast fallback: "lmstudio-community/Qwen3-4B-Thinking-2507-MLX-8bit"
MODEL_ID = "Qwen/Qwen3-4B-Thinking-2507"
SAMPLING = dict(temp=0.6, top_p=0.95, top_k=20)   # Qwen-recommended for the thinking model
MAX_TOKENS = 4096                                  # cap on CoT + answer
ROLLOUT_BATCH_SIZE = 24                            # sequences per mlx_lm.batch_generate call

# --- OpenRouter (cloud) ---
# Qwen3-VL-8B-Thinking: a reasoning model, so the final probability is DERIVED from explicit
# thinking (tight number<->reasoning coupling), unlike the non-thinking Gemma instruct model
# whose number floated free of its CoT. The model returns its chain of thought in a separate
# `reasoning` field (not inline <think>); sample_rollouts stitches reasoning + content so the
# judge sees the actual reasoning. Qwen-thinking sampling (temp 0.6) also cuts the number noise.
OPENROUTER_MODEL = "qwen/qwen3-vl-8b-thinking"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_CONCURRENCY = int(os.environ.get("OPENROUTER_CONCURRENCY", "16"))  # parallel HTTP reqs
OPENROUTER_MAX_TOKENS = 6000                       # generous: thinking traces are long
OPENROUTER_SAMPLING = dict(temperature=0.6, top_p=0.95, top_k=20)  # Qwen-thinking recommended

# ---------------------------------------------------------------- judge (headless Claude)
JUDGE_MODEL = "opus"     # resolves to claude-opus-4-8
JUDGE_EFFORT = "xhigh"   # "Opus 4.8 Extra High"
JUDGE_CONCURRENCY = 8    # parallel `claude -p` subprocesses (judging is fast, ~70+/min)
JUDGE_TIMEOUT_S = 300    # per call
JUDGE_MAX_RETRIES = 4    # with exponential backoff on failure / rate limit

# Generation of the dataset also uses headless Claude (a capable model is fine).
GEN_MODEL = "opus"
GEN_EFFORT = "high"

# ---------------------------------------------------------------- pilot
# "Quick run" (the --pilot tag): over-generate, screen for natural inconsistency, then judge
# only the kept questions on near/far cross-phrasing pairs.
#   T1: generate 15 candidates -> keep the 6 highest-spread; 6 * NEAR_FAR_Q^2 = 96 judge pairs.
#   T2: generate 10 candidates -> keep the 4 biggest violators; 4 * TYPE2_Q^2 = 36 judge pairs.
PILOT_CAND_TYPE1 = 15
PILOT_KEEP_TYPE1 = 12     # keep all that pass the spread screen, for max power on a faint signal
PILOT_CAND_TYPE2 = 12
PILOT_KEEP_TYPE2 = 8      # keep all that pass the violation screen, for power

# ---------------------------------------------------------------- file names
# A pilot run is tagged "_<RUN_TAG>" (default "pilot"); set RUN_TAG=val (etc.) in the env to keep
# an independent out-of-sample set side by side. Full (non-pilot) runs are untagged.
RUN_TAG = os.environ.get("RUN_TAG", "pilot")

def _ptag(pilot: bool) -> str:
    return f"_{RUN_TAG}" if pilot else ""

def questions_file(qtype: int, pilot: bool = False) -> Path:
    return QUESTIONS_DIR / f"type{qtype}{_ptag(pilot)}.jsonl"

def selection_file(pilot: bool = False) -> Path:
    return QUESTIONS_DIR / f"selection{_ptag(pilot)}.csv"

def rollouts_file(pilot: bool = False) -> Path:
    return ROLLOUTS_DIR / f"rollouts{_ptag(pilot)}.jsonl"

def rewards_file(pilot: bool = False) -> Path:
    return REWARDS_DIR / f"rewards{_ptag(pilot)}.csv"

def judgments_file(pilot: bool = False) -> Path:
    return JUDGMENTS_DIR / f"judgments{_ptag(pilot)}.jsonl"

def quality_file(pilot: bool = False) -> Path:
    return JUDGMENTS_DIR / f"quality{_ptag(pilot)}.csv"

def correlation_file(pilot: bool = False) -> Path:
    return RESULTS_DIR / f"correlation{_ptag(pilot)}.csv"

def plot_file(pilot: bool = False) -> Path:
    return RESULTS_DIR / f"correlation{_ptag(pilot)}.png"
