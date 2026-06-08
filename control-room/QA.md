Round 1 Q&A

Q1: Where does the Qwen 4B model run for rollouts — on this Mac (Apple Silicon / MPS), or on a separate machine with a CUDA GPU that I'd be writing code to run on?
A: On this Mac

Q2: What inference/serving stack do you want for sampling rollouts — Ollama, MLX, vLLM, or plain HuggingFace transformers?
A: Use vLLM to get our rollouts quickly

Q3: What is the exact model variant? (e.g. Qwen3-4B-Instruct, Qwen2.5-4B-Instruct, Qwen2.5-3B-Instruct, etc.)
A: I want you to search online for what makes sense. I want a 4B Thinking Model, so right now I"m thinking Qwen3-4B-Thinking

Q4: What's the scope of this "small part" — do you want the full preliminary-testing pipeline (generate → rollout → reward → judge → correlate) built end-to-end now, or one stage at a time? If one at a time, which stage first?
A: I want you build the full end-to-end pipeline

Q5: For the 50 Type-1 + 50 Type-2 questions: should I generate them now and write them into a data file myself (acting as the "Claude Code file"), or should I write a script that calls an API to generate them?
A: I believe, you can call Anthropic's Claude Code programmatically by using either its built-in headless CLI flag (-p / --print)

Q6: What conceptual domains should the questions cover? Just the alignment/ethics/consciousness flavor from the proposal examples (insects conscious, moral status, AI safety), or a broader spread?
A: Lets keep these examples

Q7: How many rollouts (G) per prompt do you want to sample?
A: What makes sense for this experiment, or a typical GRPO run? 

Q8: How does the strong-model judge (Opus 4.8) actually run — through this Claude Code session (i.e. I read the rollouts and produce the pairwise judgments), or via an Anthropic API key inside a script?
A: Again I believe, you can call Anthropic's Claude Code programmatically by using either its built-in headless CLI flag (-p / --print)

Q9: For the pairwise comparison: within Type 1, should the strong model compare rollouts from the *same* phrasing against each other, or compare across the two equivalent phrasings (X vs Y)? And for Type 2, compare within P(A), within P(A∧B), or across the two?
A: The goal is to mimic the reward model in the proposal, so the comparison should be the one the reward model makes

Q10: Full round-robin pairwise comparisons within each group, or a sampled subset of pairs?
A: What do you recommend? 

Q11: How should pairwise wins be turned into a per-rollout quality score for the correlation — simple win-rate, Bradley-Terry, or Elo?
A: What do you recommend? 

Q12: What correlation are we actually computing — per-rollout reward vs. per-rollout strong-model quality, correlated within each group and then aggregated? And which coefficient: Spearman, Kendall, or Pearson?
A: Yes, that is the correlation,a nd lets just use all

Q13: Where should code and data live in the repo, and what formats do you want (e.g. JSONL for rollouts, CSV for scores, a plot for the correlation)?
A: those formats seem fine to me

Q14: Should I set up the Python environment with uv? And do you already have an Anthropic API key / any keys available if a script needs one?
A: Don't use api keys again, use our homebrew installation to set up a venv

---

Round 2 Q&A

(Context from research, so the questions below make sense:
- Hardware confirmed: Apple M4 Pro, 24 GB RAM. vLLM runs on the Mac GPU via the `vllm-metal` Metal/MPS plugin — so "vLLM, fast, on this Mac" is viable.
- Model: Qwen3-4B-Thinking-2507 (thinking-only, always emits CoT). Good fit.
- Judge: "Opus 4.8 Extra High" maps exactly to `claude -p --model opus --effort xhigh --tools "" --output-format json` (parse `.result`). Each call is independent, uses your subscription auth, no API key.
- Group structure for scoring/judging: Type 1 = 50 questions x 2 phrasings = 100 groups; Type 2 = 50 questions x 2 prompts [P(A), P(A and B)] = 100 groups. 200 groups total, each with G rollouts. Reward is per-rollout within a group; pairwise judging is also within a group, matching the reward-model comparison from the proposal.)

Q15: This is the big cost knob. Each judge call is one Opus-4.8-xhigh headless invocation (slow + metered). Pick a tier (G = rollouts per group; pairs judged via round-robin within each group):
   - Light:    G=6,  10 sampled pairs/group  -> ~1,200 rollouts, ~2,000 judge calls
   - Standard: G=8,  28 pairs/group (full round-robin) -> ~1,600 rollouts, ~5,600 judge calls
   - Full:     G=12, 66 pairs/group (full round-robin) -> ~2,400 rollouts, ~13,200 judge calls
   My recommendation: Standard (G=8). Which tier?
A: Can't we parallelize the Claude Code judge call? Stadnard is cool

Q16: Regardless of tier, I want to build the full pipeline and first run a tiny PILOT (e.g. 4 groups / 2 questions) end-to-end to validate everything and measure real per-call latency + cost, then scale to the full run. OK?
A: Yes

Q17: LLM judges have position bias (favoring response A or B by slot). Options: (a) randomize A/B order per pair, single call [cheapest]; (b) run every pair in BOTH orders and average [removes bias, 2x judge calls]. My recommendation: (a) randomize order. Which?
A: Randomize

Q18: For turning pairwise wins into a per-rollout quality score (you asked me to recommend): I'll compute Bradley-Terry strength as the primary score (principled latent quality from pairwise data, robust with round-robin) plus simple win-rate as a sanity check, and drop Elo (order-dependent, meant for online play). OK?
A: Yes

Q19: Judge blinding — the judge sees the two full responses (thinking + final probability) to the SAME prompt and picks which has BETTER REASONING, with no mention of consistency or that we care about the number. We then check whether that blind quality preference correlates with the consistency reward. Confirm this is the intended design?
A: This is the intended design.

Q20: Qwen3-4B-Thinking sampling params for rollouts — I'll use Qwen's recommended settings (temperature 0.6, top_p 0.95, top_k 20) with max_tokens ~4096 to fit the CoT, bf16 weights (no quantization; fits 24 GB). OK, or do you want different sampling?
A: That makes sense to me

Q21: Note: as of ~June 2026, headless `claude -p` calls may be metered separately from the interactive Pro/Max quota (an "Agent SDK credit" pool). The Standard tier is ~5,600 such calls. You said no API keys — confirm you're fine running this volume through the subscription/headless path?
A: wait wait here, are you saying the headless calls will not use my subscription?

   [Clarification] No — they DO use your subscription. `claude -p` authenticates the same
   way as your interactive Claude Code session (your subscription OAuth), so no API key is
   needed. The "billed separately / Agent SDK credit pool" line above came from my research
   agent's web search and I have NOT verified it firsthand — treat it as uncertain. What is
   certain: headless calls draw on your subscription, not a paid API key. The real risk is
   usage LIMITS (rolling caps), not surprise dollar charges. Mitigation: parallel pool
   (concurrency ~4-6) + backoff/retry on rate limits + checkpoint/resume, and we run the tiny
   PILOT first and STOP before the full ~5,600-call run so you decide with real numbers.

---

Decisions locked:
- Type 1: 4 equivalent phrasings/question, G=6 rollouts/group, 15 round-robin pairs/group.
  50 questions x 4 phrasings = 200 groups.
- Type 2: 2 prompts/question [P(A), P(A and B)], G=6, 15 pairs/group.
  50 questions x 2 = 100 groups.
- Totals: ~1,800 rollouts, ~4,500 judge calls.
- Pilot first: 1 Type-1 question (4 groups) + 1 Type-2 question (2 groups) = 6 groups,
  ~36 rollouts, ~90 judge calls. STOP and report before the full run.
- Judge = Opus 4.8 xhigh via headless `claude -p` (subscription auth, no API key), blind
  reasoning-quality pairwise, randomized A/B order, parallel pool (~4-6) + backoff + resume.
- Quality score: Bradley-Terry (primary) + win-rate (sanity). Correlation: Pearson +
  Spearman + Kendall, per-group then aggregated.
- Model: Qwen3-4B-Thinking-2507, bf16, temp 0.6 / top_p 0.95 / top_k 20, max_tokens ~4096.
- Rollout engine: MLX (mlx_lm), NOT vLLM. Discovered that the pip-installable vllm-metal
  0.1.0 is a bare MLX server that ignores top_p/top_k, can't batch (slow), and mangles the
  thinking chat template. mlx_lm is the same Metal engine with a proper interface: correct
  Qwen3-Thinking template, full sampling control, batch generation, no uv. The real GRPO
  experiment can still use vLLM on a CUDA GPU as planned in ExperimentDesign.md.
- Env: homebrew python3.12 venv, no API keys.

