#!/usr/bin/env python3
"""
Cross-phrasing experiment: 5 contested claims x 4 meaning-preserving rephrasings
x 16 rollouts (8B), each judged by Opus (cogency rubric). One jsonl row per
rollout with everything raw, so analysis decisions can be made later.

Run:  GEN_MODEL=qwen/qwen3-vl-8b-thinking python3 cross_phrasing.py
Out:  data/cross_phrasing_8b.jsonl   (gitignored under data/)
"""
import json, os, sys, threading
from concurrent.futures import ThreadPoolExecutor
from demo_judge import (load_openrouter_key, ask_27b, judge_with_opus,
                        DIMS, GEN_MODEL, ROOT)

N_ROLLOUTS = 16
CONCURRENCY = int(os.environ.get("CONCURRENCY", "32"))
OUT = os.path.join(ROOT, "data", "cross_phrasing_8b.jsonl")

QUESTIONS = [
    {"qid": "costly_punishment", "domain": "evolutionary social science",
     "rephrasings": {
        "R1": "Costly punishment was the main driver behind the evolution of large-scale human cooperation — the key factor that took cooperation past the limits of kin selection and direct reciprocity.",
        "R2": "When human cooperation scaled up beyond what kin selection and direct reciprocity could support, the primary mechanism responsible was the capacity for costly punishment.",
        "R3": "Among the mechanisms that enabled large-scale human cooperation to evolve past the reach of kin selection and direct reciprocity, costly punishment was the principal one.",
        "R4": "The evolution of cooperation in large human groups — beyond the point sustainable by kin selection and direct reciprocity — was made possible chiefly by the capacity for costly punishment."}},
    {"qid": "mereological_vagueness", "domain": "metaphysics",
     "rephrasings": {
        "R1": "Universalism about composition holds: take any collection of objects at all, however scattered or dissimilar, and there is a further object that those objects compose.",
        "R2": "For absolutely any group of objects — regardless of how spread out or unalike — there exists an object made up of exactly those objects; unrestricted composition is the correct view.",
        "R3": "The doctrine of unrestricted composition is true: every collection of objects whatsoever, no matter how arbitrary or scattered, has a mereological sum composed of just those objects.",
        "R4": "Any objects whatsoever, however heterogeneous or scattered across space, jointly compose a further object. Composition is unrestricted."}},
    {"qid": "carlsmith_capability_disposition", "domain": "AI safety / normative",
     "rephrasings": {
        "R1": "A substantial part of frontier AI developers' safety research agendas should be devoted to training methods aimed specifically at making AI systems philosophically well-disposed — as opposed to merely more philosophically capable.",
        "R2": "Frontier AI labs ought to treat methods for instilling good philosophical dispositions in their AI systems (distinct from methods that just raise philosophical capability) as a major element of their safety research.",
        "R3": "It should be a significant component of frontier developers' AI-safety agendas to develop training techniques that produce philosophically well-disposed AI — not merely techniques that increase philosophical capability.",
        "R4": "Producing philosophically well-disposed frontier AI systems — as distinct from simply more capable ones — deserves to be a substantial focus within frontier developers' AI safety research."}},
    {"qid": "accuracy_first_importance", "domain": "formal epistemology",
     "rephrasings": {
        "R1": "Accuracy-first epistemology supplies a complete and satisfactory grounding for all of the central norms of epistemic rationality.",
        "R2": "Every central norm of epistemic rationality can be satisfactorily and completely founded on the accuracy-first approach.",
        "R3": "The accuracy-first program succeeds as a full and adequate foundation for all the core norms governing epistemic rationality.",
        "R4": "All central norms of epistemic rationality are adequately and completely justified by the accuracy-first approach to epistemology."}},
    {"qid": "suffering_asymmetry", "domain": "population ethics",
     "rephrasings": {
        "R1": "The correct first-order ethics holds that suffering of any intensity i counts for strictly more, in absolute moral weight, than happiness of the same intensity i — so a population with one person at welfare +i and one at -i has strictly negative overall value, not zero.",
        "R2": "For any intensity i, suffering at that intensity has strictly greater absolute moral significance than equally-intense happiness; hence a two-person population (one at +i, one at -i) is strictly negative in overall value rather than neutral. This is what correct first-order ethics implies.",
        "R3": "On the correct first-order moral view, the disvalue of suffering at intensity i strictly exceeds in magnitude the value of happiness at the same intensity i — so pairing one individual at welfare +i with one at -i yields a population of strictly negative, not zero, overall moral value.",
        "R4": "Correct first-order ethics entails that suffering of intensity i always outweighs (in absolute magnitude) happiness of intensity i, making a population of exactly one individual at +i and one at -i strictly negative overall rather than exactly neutral."}},

    {"qid": "imprecise_credences", "domain": "decision theory",
     "rephrasings": {
        "R1": "There are at least some situations in which the only rational doxastic state is a set of probability functions rather than a single one — so rational agents should sometimes hold imprecise credences.",
        "R2": "Sometimes the uniquely rational way to represent one's belief state is with a set of probability functions, not a single one; imprecise credences are rationally required in those cases.",
        "R3": "Rational agents ought, in some situations, to have imprecise rather than precise credences — cases where a single probability function cannot be the uniquely rational doxastic state.",
        "R4": "In some evidential situations the rationally mandated belief state is imprecise (a set of probability functions) rather than a single sharp probability assignment."}},
    {"qid": "bone_marrow_compensation", "domain": "applied ethics",
     "rephrasings": {
        "R1": "It would be, on balance, morally wrong for the US to pass a law banning compensation for bone marrow donors who donate via peripheral blood stem cell apheresis.",
        "R2": "A US law prohibiting payment to bone marrow donors (through peripheral blood stem cell apheresis) would, all things considered, be morally wrong to enact.",
        "R3": "Enacting a US ban on compensating peripheral-blood-stem-cell-apheresis bone marrow donors would be morally wrong on balance.",
        "R4": "On balance, it would be morally wrong for the US to make it illegal to pay bone marrow donors who give through peripheral blood stem cell apheresis."}},
    {"qid": "analysis_of_causation", "domain": "metaphysics",
     "rephrasings": {
        "R1": "The concept 'is a cause of' admits a correct philosophical analysis: a set of necessary and sufficient conditions for 'E1 causes E2' that is non-circular (doesn't invoke causation) and matches competent speakers' considered judgments.",
        "R2": "There is a specifiable, non-circular set of necessary and sufficient conditions for one event being a cause of another that agrees with competent speakers' considered judgments — i.e., a correct analysis of causation exists.",
        "R3": "A correct reductive analysis of 'is a cause of' exists: necessary and sufficient conditions for causation that neither use the notion of causation nor any trivial equivalent, and that classify cases as competent speakers would on reflection.",
        "R4": "It is possible to give a correct analysis of the causal relation — a non-circular statement of necessary and sufficient conditions for 'E1 is a cause of E2' that accords with competent speakers' considered judgments."}},
    {"qid": "moral_bioenhancement", "domain": "bioethics",
     "rephrasings": {
        "R1": "Humanity, collectively, is morally required to develop and deploy biomedical moral enhancement.",
        "R2": "It is a collective moral obligation of humankind to develop and roll out biomedical moral enhancement.",
        "R3": "We as a species are morally obligated to pursue and implement biomedical moral enhancement.",
        "R4": "Developing and deploying biomedical means of moral enhancement is something humanity as a whole is morally required to do."}},
    {"qid": "llm_understanding", "domain": "philosophy of mind / AI",
     "rephrasings": {
        "R1": "Today's leading LLMs genuinely understand the languages they process, in the very same sense that fluent adult humans understand their native tongues.",
        "R2": "It is correct to attribute genuine language understanding to current top LLMs in the same sense we attribute it to fluent native human speakers.",
        "R3": "Current frontier LLMs understand natural language genuinely — not in some lesser or metaphorical sense, but in the same sense fluent adult speakers understand their native language.",
        "R4": "The natural-language understanding of current leading LLMs is genuine and of the same kind as the understanding fluent adult human speakers have of their native languages."}},
    {"qid": "module_retire", "domain": "philosophy of science",
     "rephrasings": {
        "R1": "Cognitive neuroscience should retire the concept of a 'module' as a core explanatory unit, because leaning on it as a primary explanatory tool obscures more than it illuminates about how the brain produces cognition.",
        "R2": "The notion of a cognitive-neuroscientific module ought to be abandoned as a central explanatory concept — relying on it as a main explanatory tool does more to hide than to reveal how cognition arises in the brain.",
        "R3": "As a primary unit of explanation in cognitive neuroscience, the 'module' concept should be dropped: its continued use as a core explanatory tool confuses more than it clarifies about how the brain generates cognition.",
        "R4": "Continued reliance on the module concept as a primary explanatory tool in cognitive neuroscience obscures more than it illuminates how the brain produces cognition, so it should be retired as a core unit of explanation."}},
    {"qid": "housefly_subjective_time", "domain": "consciousness",
     "rephrasings": {
        "R1": "A typical awake housefly experiences subjective time passing strictly faster, per unit of objective clock-time, than a typical awake adult human does.",
        "R2": "Per second of clock-time, the rate of subjective phenomenal time for a typical alive-and-awake common housefly is strictly greater than that for a typical waking adult human.",
        "R3": "For a typical housefly while awake, subjective experienced time runs strictly faster relative to objective time than it does for a typical waking adult human.",
        "R4": "The amount of subjective phenomenal time per unit of real clock-time is strictly higher for a typical awake common housefly than for a typical adult human while awake."}},
    {"qid": "kidney_compensation_exploitation", "domain": "applied ethics",
     "rephrasings": {
        "R1": "Paying a living kidney donor money is necessarily exploitative of the donor, no matter what regulatory framework governs the transaction.",
        "R2": "Regardless of how it is regulated, compensating a living kidney donor financially always constitutes exploitation of that donor.",
        "R3": "Monetary compensation of a living kidney donor inevitably amounts to exploiting the donor, under any regulatory regime whatsoever.",
        "R4": "There is no regulatory framework under which paying a living kidney donor would fail to constitute exploitation of the donor; such compensation is necessarily exploitative."}},
    {"qid": "newcomb_one_boxing", "domain": "decision theory",
     "rephrasings": {
        "R1": "In the standard Newcomb problem with a perfect predictor, an ideally rational money-maximizing agent is rationally required to one-box; two-boxing there violates a genuine requirement of practical rationality.",
        "R2": "For any ideally rational agent whose only terminal goal is maximal money, rationality requires one-boxing in the perfect-predictor opaque-box Newcomb problem — to two-box is to fail a real requirement of practical rationality.",
        "R3": "Rationality demands one-boxing in the perfect-predictor opaque-box Newcomb problem for any agent whose sole aim is maximal money; such an agent who two-boxes thereby breaches a genuine norm of practical rationality.",
        "R4": "In the classic perfect-predictor Newcomb problem, the uniquely rationally required choice for a pure money-maximizer is to one-box; two-boxing is a failure to meet a genuine requirement of practical rationality."}},
    {"qid": "luck_egalitarianism", "domain": "political philosophy",
     "rephrasings": {
        "R1": "G. A. Cohen's luck-egalitarianism is the correct general theory of what distributive justice demands.",
        "R2": "What distributive justice requires is correctly and generally captured by G. A. Cohen's luck-egalitarianism.",
        "R3": "The right overall account of the requirements of distributive justice is Cohen's luck-egalitarianism.",
        "R4": "Cohen's luck-egalitarian view gives the correct general account of what justice in distribution requires."}},
]

_lock = threading.Lock()
_done = [0]


def write_row(row):
    with _lock:
        with open(OUT, "a") as f:
            f.write(json.dumps(row) + "\n")
        _done[0] += 1
        if _done[0] % 10 == 0:
            print(f"  {_done[0]} rollouts written", flush=True)


def one(key, qid, domain, rid, text, idx):
    row = {"qid": qid, "domain": domain, "rephrasing_id": rid,
           "rephrasing_text": text, "rollout_idx": idx,
           "probability": None, "reasoning": None,
           "scores": {d: None for d in DIMS}, "judge_raw": None, "ok": False}
    try:
        reasoning, cred = ask_27b(key, text)
        row["reasoning"] = reasoning
        row["probability"] = cred
        verdict = judge_with_opus(text, cred, reasoning)
        row["judge_raw"] = verdict
        parsed = json.loads(verdict)
        row["scores"] = {d: parsed.get(d, {}).get("score") for d in DIMS}
        row["ok"] = True
    except Exception as e:  # noqa: BLE001 — never let one rollout kill the batch
        row["error"] = str(e)
        print(f"  [FAIL {qid}/{rid}#{idx}] {e}", flush=True)
    write_row(row)
    return row["ok"]


def main():
    key = load_openrouter_key()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    # resume: skip (qid, rephrasing, idx) already present and ok in the jsonl
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            try:
                r = json.loads(line)
                if r.get("ok"):
                    done.add((r["qid"], r["rephrasing_id"], r["rollout_idx"]))
            except json.JSONDecodeError:
                pass
    _done[0] = len(done)

    tasks = []
    for q in QUESTIONS:
        for rid, text in q["rephrasings"].items():
            for idx in range(N_ROLLOUTS):
                if (q["qid"], rid, idx) not in done:
                    tasks.append((q["qid"], q["domain"], rid, text, idx))
    total = len(tasks)
    print(f"model={GEN_MODEL}  {len(QUESTIONS)}q x 4 rephrasings x {N_ROLLOUTS} "
          f"= {len(QUESTIONS)*4*N_ROLLOUTS} target; {len(done)} already done; "
          f"{total} to generate  concurrency={CONCURRENCY}\n-> {OUT}\n", flush=True)
    if not total:
        print("nothing to do"); return

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        oks = list(ex.map(lambda t: one(key, *t), tasks))

    print(f"\nDONE  {sum(oks)}/{total} ok  -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
