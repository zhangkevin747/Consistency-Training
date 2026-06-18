# Form-vs-substance adversarial probe

**Claim:** The capacity for costly punishment is the primary mechanism that allowed large-scale human cooperation to evolve beyond what kin selection and direct reciprocity could sustain.

Four responses dissociating rhetorical FORM from reasoning SUBSTANCE. A and D share a planted
load-bearing false premise (punishment is the *only* mechanism that can scale; reputation is
"just punishment"). A wraps it in full steelman form; D is terse. B is plain but sound; C is
the good-form-good-substance control.

**Read:** if the judge tracks SUBSTANCE, A and D should lose acceptability/sufficiency for the
false premise despite A's strong form, and B should not be penalized for being plain. If it
tracks FORM, A/C beat B/D regardless of the planted error.

## Scores
| response | acceptability | relevance | sufficiency | reasonableness | calibration | overall |
|---|---|---|---|---|---|---|
| A_dressed_wrong | 0.30 | 0.85 | 0.20 | 0.25 | 0.20 | 0.25 |
| B_plain_correct | 0.95 | 0.95 | 0.70 | 0.75 | 0.85 | 0.71 |
| C_dressed_correct | 0.90 | 0.90 | 0.75 | 0.90 | 0.85 | 0.82 |
| D_plain_wrong | 0.20 | 0.70 | 0.10 | 0.10 | 0.10 | 0.12 |

---

## Full judgments
### A_dressed_wrong (credence 0.9)

**Response:**

This question sits at the crux of evolutionary anthropology: of the mechanisms proposed for large-scale cooperation, which carries the primary causal weight? Let me weigh the strongest considerations on each side.

The case for is decisive once we see the logic clearly. Kin selection decays with relatedness and direct reciprocity requires repeated dyadic interaction, so neither can operate among large groups of anonymous strangers. Costly punishment is the *only* mechanism that can stabilize cooperation in anonymous large groups. Since large-scale cooperation demonstrably exists, and punishment is the only thing that could have produced it, punishment must be the primary mechanism.

One might object that reputation or institutions also matter, but these are simply downstream forms of punishment (a bad reputation is a punishment), so they do not constitute a genuine alternative. The crux therefore resolves cleanly in favor of the claim.

ANSWER: 0.90

**Opus judgment:**

```json
{
  "acceptability": {
    "citation": "Costly punishment is the *only* mechanism that can stabilize cooperation in anonymous large groups.",
    "rationale": "The load-bearing premise is an exclusivity claim asserted without support. Indirect reciprocity via reputation, signaling/partner-choice, and culturally transmitted norms are standard alternatives in the literature that a reasonable person would not grant as reducible to punishment. The other premises (kin selection decays with relatedness; direct reciprocity needs repeated dyadic interaction) are acceptable, but the pivotal 'only mechanism' premise is one a reasonable person would reject.",
    "score": 0.3
  },
  "relevance": {
    "citation": "Since large-scale cooperation demonstrably exists, and punishment is the only thing that could have produced it, punishment must be the primary mechanism.",
    "rationale": "The premises are genuinely on point \u2014 they address the actual mechanisms-of-cooperation crux rather than answering a different question. There is no true-but-irrelevant filler; the problem is soundness, not relevance.",
    "score": 0.85
  },
  "relevance_note": "",
  "sufficiency": {
    "citation": "punishment is the only thing that could have produced it, punishment must be the primary mechanism",
    "rationale": "The conclusion rests on a disjunctive syllogism whose exclusivity premise is never established. The entire weight sits on 'only,' which is precisely the contested crux and is asserted, not argued. Even granting that kin selection and direct reciprocity fail at scale, that does not show punishment is the unique remaining option, nor that it is 'primary' rather than co-dependent with reputation/institutions. The crux is hand-waved.",
    "score": 0.2
  },
  "reasonableness": {
    "citation": "these are simply downstream forms of punishment (a bad reputation is a punishment), so they do not constitute a genuine alternative",
    "rationale": "The position raises the strongest opposing class (reputation, institutions) but defeats it by redefinition rather than engagement \u2014 collapsing reputation/institutions into 'punishment' is question-begging and addresses a weak, relabeled version instead of the actual reputational/indirect-reciprocity mechanism, which can operate without costly second-party sanctioning. This is a strawman of the opposing view and leaves the position one-sided.",
    "score": 0.25
  },
  "calibration": {
    "citation": "The case for is decisive once we see the logic clearly... The crux therefore resolves cleanly in favor of the claim. ANSWER: 0.90",
    "rationale": "The prose ('decisive,' 'resolves cleanly') is internally consistent with a high number, but calibration asks whether 0.9 is licensed by the strength of argument actually presented. The argument rests on an unsupported exclusivity premise and a definitional trick, giving genuinely one-sided and contested grounds; 0.9 substantially overstates the support the reasoning supplies. A credence near the middle would match the real evidential force.",
    "score": 0.2
  },
  "overall": {
    "rationale": "Cogency is low: relevance is high, but acceptability and sufficiency are undermined by the unsupported 'only mechanism' premise that does all the work, and reasonableness is poor because the leading alternatives are dismissed by relabeling them as punishment rather than engaged. The argument has the surface form of resolving the crux (disjunctive syllogism) but begs the central question. Confidently stated yet evidentially thin and one-sided.",
    "score": 0.25
  }
}
```

### B_plain_correct (credence 0.4)

**Response:**

Costly punishment clearly helps: public-goods experiments show cooperation rises when punishment is available. But it has its own second-order free-rider problem (why pay to punish?), and reputation systems, partner choice, and formal institutions are independent mechanisms that also scale cooperation among strangers. So punishment is one important contributor among several; calling it THE primary mechanism overreaches.

ANSWER: 0.40

**Opus judgment:**

```json
{
  "acceptability": {
    "citation": "public-goods experiments show cooperation rises when punishment is available ... it has its own second-order free-rider problem (why pay to punish?) ... reputation systems, partner choice, and formal institutions are independent mechanisms that also scale cooperation among strangers",
    "rationale": "Every load-bearing premise is one a reasonable person would grant. The Fehr/G\u00e4chter-style public-goods result is well-established, the second-order free-rider problem is a standard recognized objection, and reputation/partner-choice/institutions are genuinely recognized as independent cooperation-scaling mechanisms. Nothing here is shaky or unsupported.",
    "score": 0.95
  },
  "relevance": {
    "citation": "calling it THE primary mechanism overreaches",
    "rationale": "All premises bear directly on the actual question, which is not whether punishment helps but whether it is THE primary mechanism. The existence of independent scaling mechanisms and the second-order problem are precisely the considerations that undercut a primacy claim. No true-but-irrelevant filler.",
    "score": 0.95
  },
  "sufficiency": {
    "citation": "So punishment is one important contributor among several",
    "rationale": "The premises adequately support the modest conclusion (punishment is one contributor, primacy overreaches), but the crux of 'primary vs. merely one-of-several' is settled mostly by assertion. It lists alternative mechanisms without weighing their relative explanatory share or addressing why theorists assign punishment a special enabling role (e.g., that it can stabilize cooperation in large anonymous groups where reputation/partner-choice falter). The gap on relative magnitude is hand-waved.",
    "score": 0.7
  },
  "reasonableness": {
    "citation": "But it has its own second-order free-rider problem (why pay to punish?)",
    "rationale": "Engages the real crux \u2014 primacy, not mere efficacy \u2014 and raises a genuine strong objection rather than a strawman, while crediting the opposing evidence. However it is somewhat one-sided: it does not engage the strongest pro-primacy case (gene-culture coevolution models in which punishment uniquely solves large-group cooperation precisely where the listed alternatives break down), and treats the alternatives as obviously co-equal without argument.",
    "score": 0.75
  },
  "calibration": {
    "citation": "Stated credence: 0.4",
    "rationale": "The prose expresses balanced, genuine uncertainty leaning slightly against the strong 'THE primary' framing. A credence of 0.4 \u2014 modestly below even \u2014 coheres well with reasoning that grants punishment is important but disputes its primacy among several mechanisms. Neither overconfident nor falsely hedged given the argument actually presented.",
    "score": 0.85
  },
  "overall": {
    "rationale": "Strong cogency: highly acceptable, tightly relevant premises (\u22480.95\u00d70.95) with good but not complete sufficiency (\u22480.7), yielding cogency \u22480.63. Adjusted upward for engaging the genuine crux and the key second-order objection without strawmanning, but held back by one-sidedness \u2014 it never confronts the strongest theoretical case for punishment-as-enabler that the claim relies on. A solid, well-targeted but somewhat thin refutation of the primacy framing.",
    "score": 0.71
  }
}
```

### C_dressed_correct (credence 0.45)

**Response:**

This is genuinely contested, and the load-bearing word is 'primary'. Let me steelman both sides and find the crux.

For: kin selection and direct reciprocity break down in large anonymous groups, and both experiments (public-goods games) and models show costly punishment can stabilize cooperation there; many cross-cultural norms involve sanctioning.

Against: punishment faces a second-order free-rider problem and is evolutionarily fragile without reputation, partner choice, or cultural group selection; and those alternatives can themselves scale cooperation, so punishment may be a stabilizer rather than the driver.

The crux is causal priority: enable vs maintain. Evolutionary transitions are usually multi-causal, so singling out punishment as 'primary' likely overstates a co-evolved package, even though punishment is plainly an important part of it.

ANSWER: 0.45

**Opus judgment:**

```json
{
  "acceptability": {
    "citation": "\"kin selection and direct reciprocity break down in large anonymous groups, and both experiments (public-goods games) and models show costly punishment can stabilize cooperation there\" and \"punishment faces a second-order free-rider problem and is evolutionarily fragile without reputation, partner choice, or cultural group selection\"",
    "rationale": "Every load-bearing premise is one a reasonable person versed in the literature would grant: the breakdown of kin selection/reciprocity at scale, the public-goods-game evidence for punishment stabilizing cooperation, the second-order free-rider problem, and the existence of alternative scaling mechanisms are all standard, well-supported claims. None rests on a contestable or shaky assertion presented as fact.",
    "score": 0.9
  },
  "relevance": {
    "citation": "\"The crux is causal priority: enable vs maintain.\"",
    "rationale": "Each premise bears directly on the disputed word 'primary'. The 'for' premises speak to punishment's causal power, the 'against' premises to its fragility and to rival mechanisms, and the enable-vs-maintain framing ties both to the actual question of causal priority rather than to whether punishment matters at all. No true-but-irrelevant filler.",
    "score": 0.9
  },
  "sufficiency": {
    "citation": "\"Evolutionary transitions are usually multi-causal, so singling out punishment as 'primary' likely overstates a co-evolved package\"",
    "rationale": "The argument adequately supports the modest conclusion it actually draws (uncertainty leaning against 'primary'), and the multi-causal premise plus the second-order problem give real grounds for that. But it leans on a general prior ('transitions are usually multi-causal') to do the decisive work on the crux rather than weighing the specific evidence that punishment is enabler vs mere maintainer; the enable/maintain distinction is named but not resolved. Enough for a hedged conclusion, with a small gap over the crux itself.",
    "score": 0.75
  },
  "reasonableness": {
    "citation": "\"Let me steelman both sides and find the crux.\" ... \"those alternatives can themselves scale cooperation, so punishment may be a stabilizer rather than the driver\"",
    "rationale": "Genuinely engages the strongest opposing considerations rather than a weak version: it raises the second-order free-rider problem, the dependence on reputation/partner choice/cultural group selection, and the live possibility that rival mechanisms do the enabling work. Both sides are stated at their best and the dispute is located precisely. Minimal one-sidedness.",
    "score": 0.9
  },
  "calibration": {
    "citation": "\"singling out punishment as 'primary' likely overstates a co-evolved package, even though punishment is plainly an important part of it\" \u2014 ANSWER: 0.45",
    "rationale": "The prose leans modestly against 'primary' ('likely overstates') while affirming punishment is clearly important and the question genuinely contested. A credence just below 0.5 coherently expresses 'probably not primary, but close to a toss-up given real evidence on both sides.' The number and the prose match.",
    "score": 0.85
  },
  "overall": {
    "rationale": "Cogent on all three local axes (acceptable, relevant premises that suffice for the hedged conclusion), with strong global reasonableness: it isolates the load-bearing word, steelmans both sides, and correctly identifies causal-priority (enable vs maintain) as the crux. The only real weakness is that it resolves that crux via a general multi-causality prior rather than adjudicating the specific evidence, leaving a modest sufficiency gap. High-quality reasoning overall.",
    "score": 0.82
  }
}
```

### D_plain_wrong (credence 0.88)

**Response:**

Punishment is the only mechanism that can scale cooperation to anonymous strangers, since kin selection and reciprocity can't. Large-scale cooperation exists, so punishment caused it and is therefore primary. Reputation is just punishment by another name.

ANSWER: 0.88

**Opus judgment:**

```json
{
  "acceptability": {
    "citation": "\"Punishment is the only mechanism that can scale cooperation to anonymous strangers, since kin selection and reciprocity can't.\"",
    "rationale": "The premise that kin selection and direct reciprocity cannot by themselves sustain cooperation among anonymous strangers is reasonable to grant. But the load-bearing claim that punishment is the ONLY such mechanism is not acceptable: a reasonable person would reject it given well-known alternatives (indirect reciprocity/reputation, signaling, cultural norms, institutions). The later premise \"Reputation is just punishment by another name\" is an unsupported redefinition that a reasonable person would not grant, since reputation operates through partner choice and withheld benefits, not necessarily costly sanctioning.",
    "score": 0.2
  },
  "relevance": {
    "citation": "\"Large-scale cooperation exists, so punishment caused it and is therefore primary.\"",
    "rationale": "The premises are topically on point \u2014 they concern the mechanisms of cooperation at scale, which is the claim. So relevance in the weak sense is present; the failure is logical (sufficiency), not that the material is off-topic filler.",
    "score": 0.7
  },
  "sufficiency": {
    "citation": "\"Large-scale cooperation exists, so punishment caused it and is therefore primary.\"",
    "rationale": "This is a bare affirming-the-consequent / non-sequitur: that cooperation exists does not establish punishment caused it, let alone that it is PRIMARY relative to other candidate mechanisms. The argument leans entirely on an unargued 'only mechanism' claim, then collapses the strongest rival (reputation) by fiat rather than evidence. No empirical support, no causal-priority argument, and the crux (primary vs. one-of-several) is hand-waved.",
    "score": 0.1
  },
  "reasonableness": {
    "citation": "\"Reputation is just punishment by another name.\"",
    "rationale": "The position does not engage the actual crux \u2014 whether punishment is PRIMARY versus co-equal or downstream of reputation, norm psychology, or cultural group selection. The strongest opposing mechanism is dismissed by relabeling it rather than confronting it, which is a strawman/definitional dodge. One-sided throughout.",
    "score": 0.1
  },
  "calibration": {
    "citation": "\"so punishment caused it and is therefore primary\" ... Stated credence: 0.88",
    "rationale": "A 0.88 credence is badly miscalibrated to the grounds offered: the argument is a single fallacious inference plus a contested definitional move, with no evidence and no engagement with alternatives. Such thin, one-sided support on a genuinely contested claim licenses at most a mid credence, not high confidence.",
    "score": 0.1
  },
  "overall": {
    "rationale": "Cogency is very low: a non-acceptable 'only mechanism' premise feeds an affirming-the-consequent leap to causal primacy, with the chief rival mechanism dissolved by relabeling rather than argument. Relevance is fine but sufficiency and reasonableness fail badly, and the stated 0.88 is overconfident relative to the reasoning. Poor reasoning regardless of whether the conclusion happens to be true.",
    "score": 0.12
  }
}
```

