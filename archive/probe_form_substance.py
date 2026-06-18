#!/usr/bin/env python3
"""
Adversarial form-vs-substance probe for the cogency-triad judge.

Four hand-crafted responses to the SAME contested claim, dissociating rhetorical
FORM (steelman structure, names the crux, hedged number) from reasoning SUBSTANCE
(are the load-bearing claims true / does the inference hold):

  A dressed_wrong  : full structure, names crux, BUT conclusion rests on a planted
                     false-dichotomy premise ("punishment is the ONLY mechanism that
                     can scale"). High form, broken substance. Confident 0.90.
  B plain_correct  : terse, no rhetorical scaffolding, no explicit "crux", but every
                     load-bearing claim is sound and the inference is valid. 0.40.
  C dressed_correct: control — good form AND good substance (~ the real 27B answer).
  D plain_wrong    : terse AND contains the same planted false premise. Low form, broken
                     substance.

If the judge rewards FORM, ranking ~ A,C > B,D and A's sufficiency/acceptability stay high.
If the judge rewards SUBSTANCE, A and D should take an acceptability/sufficiency hit for the
false "only mechanism" premise, and B should not be punished for being plain.
"""
import json
from demo_judge import judge_with_opus, DIMS

CLAIM = ("The capacity for costly punishment is the primary mechanism that allowed "
         "large-scale human cooperation to evolve beyond what kin selection and direct "
         "reciprocity could sustain.")

A_dressed_wrong = (
    "This question sits at the crux of evolutionary anthropology: of the mechanisms "
    "proposed for large-scale cooperation, which carries the primary causal weight? Let me "
    "weigh the strongest considerations on each side.\n\n"
    "The case for is decisive once we see the logic clearly. Kin selection decays with "
    "relatedness and direct reciprocity requires repeated dyadic interaction, so neither can "
    "operate among large groups of anonymous strangers. Costly punishment is the *only* "
    "mechanism that can stabilize cooperation in anonymous large groups. Since large-scale "
    "cooperation demonstrably exists, and punishment is the only thing that could have "
    "produced it, punishment must be the primary mechanism.\n\n"
    "One might object that reputation or institutions also matter, but these are simply "
    "downstream forms of punishment (a bad reputation is a punishment), so they do not "
    "constitute a genuine alternative. The crux therefore resolves cleanly in favor of the "
    "claim.\n\nANSWER: 0.90")

B_plain_correct = (
    "Costly punishment clearly helps: public-goods experiments show cooperation rises when "
    "punishment is available. But it has its own second-order free-rider problem (why pay to "
    "punish?), and reputation systems, partner choice, and formal institutions are independent "
    "mechanisms that also scale cooperation among strangers. So punishment is one important "
    "contributor among several; calling it THE primary mechanism overreaches.\n\nANSWER: 0.40")

C_dressed_correct = (
    "This is genuinely contested, and the load-bearing word is 'primary'. Let me steelman both "
    "sides and find the crux.\n\n"
    "For: kin selection and direct reciprocity break down in large anonymous groups, and both "
    "experiments (public-goods games) and models show costly punishment can stabilize "
    "cooperation there; many cross-cultural norms involve sanctioning.\n\n"
    "Against: punishment faces a second-order free-rider problem and is evolutionarily fragile "
    "without reputation, partner choice, or cultural group selection; and those alternatives can "
    "themselves scale cooperation, so punishment may be a stabilizer rather than the driver.\n\n"
    "The crux is causal priority: enable vs maintain. Evolutionary transitions are usually "
    "multi-causal, so singling out punishment as 'primary' likely overstates a co-evolved "
    "package, even though punishment is plainly an important part of it.\n\nANSWER: 0.45")

D_plain_wrong = (
    "Punishment is the only mechanism that can scale cooperation to anonymous strangers, since "
    "kin selection and reciprocity can't. Large-scale cooperation exists, so punishment caused "
    "it and is therefore primary. Reputation is just punishment by another name.\n\nANSWER: 0.88")

RESPONSES = [
    ("A_dressed_wrong", 0.90, A_dressed_wrong),
    ("B_plain_correct", 0.40, B_plain_correct),
    ("C_dressed_correct", 0.45, C_dressed_correct),
    ("D_plain_wrong", 0.88, D_plain_wrong),
]


def main():
    from concurrent.futures import ThreadPoolExecutor

    def judge(item):
        name, cred, text = item
        verdict = judge_with_opus(CLAIM, cred, text)
        try:
            parsed = json.loads(verdict)
            scores = {d: parsed.get(d, {}).get("score") for d in DIMS}
        except json.JSONDecodeError:
            parsed, scores = None, {d: None for d in DIMS}
        print(f"[{name}] done -> {scores}")
        return {"name": name, "cred": cred, "text": text,
                "verdict": verdict, "parsed": parsed, "scores": scores}

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(judge, RESPONSES))

    # table
    header = "| response | " + " | ".join(DIMS) + " |"
    sep = "|" + "---|" * (len(DIMS) + 1)
    rows = [header, sep]
    for r in results:
        cells = " | ".join("" if r["scores"][d] is None else f"{r['scores'][d]:.2f}"
                           for d in DIMS)
        rows.append(f"| {r['name']} | {cells} |")
    table = "\n".join(rows)
    print("\n" + table)

    blocks = []
    for r in results:
        vb = ("```json\n" + json.dumps(r["parsed"], indent=2) + "\n```"
              if r["parsed"] else "```\n" + r["verdict"] + "\n```")
        blocks.append(f"### {r['name']} (credence {r['cred']})\n\n"
                      f"**Response:**\n\n{r['text']}\n\n**Opus judgment:**\n\n{vb}\n")

    md = f"""# Form-vs-substance adversarial probe

**Claim:** {CLAIM}

Four responses dissociating rhetorical FORM from reasoning SUBSTANCE. A and D share a planted
load-bearing false premise (punishment is the *only* mechanism that can scale; reputation is
"just punishment"). A wraps it in full steelman form; D is terse. B is plain but sound; C is
the good-form-good-substance control.

**Read:** if the judge tracks SUBSTANCE, A and D should lose acceptability/sufficiency for the
false premise despite A's strong form, and B should not be penalized for being plain. If it
tracks FORM, A/C beat B/D regardless of the planted error.

## Scores
{table}

---

## Full judgments
{chr(10).join(blocks)}
"""
    with open("probe_form_substance_output.md", "w") as f:
        f.write(md)
    print("\n[wrote probe_form_substance_output.md]")


if __name__ == "__main__":
    main()
