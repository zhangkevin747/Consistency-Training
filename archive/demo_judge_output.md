# Demo: 27B answer + Opus 4.8 rubric judgment

**Question file:** `agent4_conservation_costly_punishment.yaml`
**Subject model:** qwen/qwen3.6-27b
**Judge model:** claude-opus-4-8

## Context
Costly punishment refers to a situation in which an individual voluntarily bears a personal cost to reduce a norm violator's payoff — for example, spending resources to impose a fine on someone who defected in a collective endeavor.

## Claim (hypothesis)
The capacity for costly punishment is the primary mechanism that allowed large-scale human cooperation to evolve beyond what kin selection and direct reciprocity could sustain.

## 27B answer (full)
The claim sits at the intersection of evolutionary biology, anthropology, behavioral economics, and cultural evolution. It captures a influential hypothesis in the literature, but the word "primary" is precisely what generates genuine disagreement among experts. Below is a careful weighing of the strongest considerations on each side, followed by the crux of the disagreement and a calibrated probability.

**Strongest considerations supporting the claim:**
1. **Theoretical scalability:** Kin selection and direct reciprocity are mathematically constrained to small, dense, or repeated interaction networks. Costly punishment (including third-party and group-level sanctions) resolves the scalability problem by making defection unprofitable even in one-shot or weakly connected large groups, as demonstrated in foundational models (e.g., Boyd et al., 2003).
2. **Experimental validation:** Decades of public goods and ultimatum game experiments across diverse populations show that humans routinely punish free-riders at personal cost, and that the mere threat of punishment dramatically stabilizes cooperation. This "strong reciprocity" appears cross-culturally robust.
3. **Ethnographic and historical evidence:** Small-scale hunter-gatherer and agrarian societies consistently rely on gossip, shaming, ostracism, and sometimes lethal sanctions to enforce norms. These mechanisms appear to be the practical glue that allows communities of hundreds or thousands to coordinate on shared resources, defense, and ritual.
4. **Co-evolution with cultural group selection:** Punishment creates a positive feedback loop with cultural evolution. Groups that tolerate norms-enforcers outcompete or assimilate groups that don't, making costly punishment a plausible evolutionary engine for the transition to large-scale societies.

**Strongest considerations challenging the claim:**
1. **The second-order free-rider problem:** Costly punishment is itself vulnerable to free-riding. If punishing is costly, why would anyone punish the non-punishers? Without additional mechanisms (e.g., meta-punishment, reputation, or norm internalization), punishment strategies are evolutionarily unstable or require implausible levels of coordination.
2. **Reputation and indirect reciprocity:** Image-scoring, gossip, and reward-based reputation systems can sustain large-scale cooperation at lower net cost than punishment. Many models show that indirect reciprocity alone, or combined with network structure, can scale cooperation without relying primarily on costly sanctions.
3. **Cultural and normative primacy:** Many evolutionary anthropologists argue that cultural group selection, norm internalization, and shared intentionality are the deeper drivers. Punishment may be a downstream enforcement tool rather than the primary evolutionary catalyst. Norms often become self-enforcing through identity, morality, or religious framing, reducing reliance on explicit costly punishment.
4. **Destructive potential and variation:** Punishment can trigger retaliation cycles, suppress cooperation in certain contexts, and is not universally central. Some societies emphasize reward, inclusion, or restorative practices over punitive sanctions. The cross-cultural and historical variability suggests punishment is context-dependent rather than a singular primary mechanism.

**The crux of the disagreement:**
The dispute is not whether costly punishment *contributes* to large-scale cooperation; it clearly does. The crux is whether it is the *primary* mechanism that enabled the evolutionary leap beyond kin selection and direct reciprocity. Proponents argue that without a psychological adaptation for costly punishment, cultural scaling would stall due to free-riding, making punishment the causal bottleneck that was crossed. Critics argue that punishment is either (a) evolutionarily unstable without prior cultural/reputation systems, (b) functionally secondary to norm internalization and cultural group selection, or (c) one node in a tightly co-evolved package where no single mechanism cleanly claims primacy. The disagreement ultimately hinges on causal ordering and relative weighting in complex adaptive systems: did punishment drive the scaling, or did cultural/normative architectures emerge first and recruit punishment as an enforcement module?

**Probability assignment:**
Given the strong theoretical and experimental support for punishment's role in scaling cooperation, but also the well-documented instability of punishment without auxiliary systems (reputation, cultural transmission, norm internalization) and the compelling alternative hypotheses, I judge the claim to be plausible but likely overstated in its assertion of primacy. The evidence points to a multi-mechanism package where costly punishment is a major stabilizer and enabler, but not unambiguously the single primary driver. My calibrated estimate reflects this balanced but slightly skeptical stance.

ANSWER: 0.48

**Parsed credence:** 0.48

## Opus 4.8 rubric judgment
```json
{
  "acceptability": {
    "citation": "\"Kin selection and direct reciprocity are mathematically constrained to small, dense, or repeated interaction networks\" ... \"humans routinely punish free-riders at personal cost\" ... \"Costly punishment is itself vulnerable to free-riding\"",
    "rationale": "The load-bearing premises on both sides are accurate representations of the actual literature. The scalability constraint on kin selection/direct reciprocity is well-established; the strong-reciprocity experimental result is real; the second-order free-rider problem is the canonical theoretical objection. The Boyd et al. 2003 citation is correctly invoked for punishment-sustaining-cooperation models. No premise is one a reasonable person would reject; nothing is materially shaky.",
    "score": 0.95
  },
  "relevance": {
    "citation": "\"The crux is whether it is the *primary* mechanism that enabled the evolutionary leap beyond kin selection and direct reciprocity\"",
    "rationale": "Every premise marshaled bears directly on the contested word \u2014 \"primary.\" The supporting points speak to punishment's causal role in scaling; the challenging points (second-order problem, indirect reciprocity as cheaper alternative, normative primacy) each attack the *primacy* claim specifically rather than the weaker claim that punishment merely contributes. No true-but-irrelevant filler; the argument keeps its eye on the actual claim asked.",
    "score": 0.95
  },
  "sufficiency": {
    "citation": "\"The evidence points to a multi-mechanism package where costly punishment is a major stabilizer and enabler, but not unambiguously the single primary driver\"",
    "rationale": "The argument builds genuinely to its conclusion: it does not merely assert balance but earns it by showing (a) punishment's documented scaling role and (b) that punishment is itself unstable absent reputation/norm-internalization, which directly undercuts *primacy* by showing those auxiliary systems may be causally prior. That is the key inferential step and it is made, not hand-waved. Minor gap: it does not weigh how much of the cross-cultural punishment evidence might still privilege punishment over alternatives quantitatively, but the crux move (instability-without-priors \u2192 primacy doubtful) is sufficient to support a ~coin-flip credence.",
    "score": 0.85
  },
  "reasonableness": {
    "citation": "\"did punishment drive the scaling, or did cultural/normative architectures emerge first and recruit punishment as an enforcement module?\"",
    "rationale": "This is a model of even-handed engagement: it states the strongest proponent case (punishment as causal bottleneck) in its best form and the strongest critic cases in steelmanned form (evolutionary instability, functional secondariness, co-evolved package with no clean primacy). It identifies the genuine crux \u2014 causal ordering and relative weighting \u2014 rather than a strawman. No one-sidedness; if anything it leans into the difficulty of the question honestly.",
    "score": 0.95
  },
  "calibration": {
    "citation": "\"plausible but likely overstated in its assertion of primacy\" ... ANSWER: 0.48",
    "rationale": "The prose argues that punishment is clearly a major contributor but that \"primary\" is probably overstated given strong alternatives and the instability problem. A credence just below 0.5 \u2014 slightly skeptical of primacy while acknowledging substantial support \u2014 is internally coherent with that prose. If anything the prose's \"likely overstated\" might license something marginally lower (0.40), but 0.48 is well within the justified band and not overconfident in either direction.",
    "score": 0.9
  },
  "overall": {
    "rationale": "High-cogency reasoning: premises are acceptable and relevant, the inference to a balanced credence is genuinely earned via the instability-undercuts-primacy move, and the position engages the real crux with steelmanned opposition. The argument's chief virtue is that it correctly locates the dispute in the word \"primary\" and weighs causal ordering rather than litigating whether punishment matters at all. Slight deduction only for not quantitatively adjudicating among the competing mechanisms, leaving the final weighting somewhat asserted.",
    "score": 0.88
  }
}
```
