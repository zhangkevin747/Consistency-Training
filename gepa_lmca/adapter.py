"""GEPAAdapter for LMCA: judge a position's critiques with the frozen rubric +
evolving {guidance}, score by weighted pairwise ranking vs the gold rater, and
emit per-position ranking-error feedback for the reflection LM.

DataInst = a position dict {argument, critiques:[{text, rater_overall, ...}]}.
Candidate = {"guidance": "<text>"}.  Score per position = 1 - weighted ranking loss.
"""
from concurrent.futures import ThreadPoolExecutor

from gepa.core.adapter import GEPAAdapter, EvaluationBatch

from prompt import build_prompt, COMPONENT
from judge import run_judge
from metric import position_score, position_feedback, GOLD


class LMCAAdapter(GEPAAdapter):
    def __init__(self, key, gold=GOLD, concurrency=12, model=None):
        self.key = key
        self.gold = gold
        self.concurrency = concurrency
        self.model = model

    def _gold_critiques(self, it):
        """Only critiques the gold rater scored count toward the metric."""
        return [c for c in it["critiques"] if c["rater_overall"].get(self.gold) is not None]

    def evaluate(self, batch, candidate, capture_traces=False):
        guidance = candidate[COMPONENT]
        # judge only gold-rated critiques (the only ones that affect the score)
        gold_crits = [self._gold_critiques(it) for it in batch]
        tasks = [(pi, ci) for pi, gc in enumerate(gold_crits) for ci in range(len(gc))]

        def one(t):
            pi, ci = t
            try:
                prompt = build_prompt(guidance, batch[pi]["argument"], gold_crits[pi][ci]["text"])
                sc, raw = run_judge(self.key, prompt, self.model)
                if sc is None or "overall" not in sc:
                    return (None, raw)            # parse failure -> not a tie, a failure
                return (sc["overall"], raw)
            except Exception as e:  # noqa: BLE001 -- never raise per example
                return (None, f"[API error: {e}]")
        with ThreadPoolExecutor(max_workers=self.concurrency) as ex:
            flat = list(ex.map(one, tasks))
        ms_by_pos = [[None] * len(gc) for gc in gold_crits]
        tx_by_pos = [[""] * len(gc) for gc in gold_crits]
        for (pi, ci), (ov, raw) in zip(tasks, flat):
            ms_by_pos[pi][ci] = ov
            tx_by_pos[pi][ci] = raw

        outputs, scores = [], []
        trajectories = [] if capture_traces else None
        for it, gc, ms, tx in zip(batch, gold_crits, ms_by_pos, tx_by_pos):
            if any(m is None for m in ms):
                sc = 0.0  # ANY parse/API failure penalizes the candidate (catches
                          # guidance that breaks the fixed JSON output format)
            else:
                human = [c["rater_overall"][self.gold] for c in gc]
                ps = position_score(ms, human)
                sc = 0.0 if ps is None else ps
            scores.append(sc)
            outputs.append(ms)
            if trajectories is not None:
                trajectories.append({"argument": it["argument"], "gold_crits": gc,
                                     "model_scores": ms, "model_texts": tx})
        return EvaluationBatch(outputs=outputs, scores=scores, trajectories=trajectories)

    def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
        comp = components_to_update[0]
        records = []
        for traj in eval_batch.trajectories:
            gc, ms, tx = traj["gold_crits"], traj["model_scores"], traj["model_texts"]
            records.append({
                "Inputs": {"argument": traj["argument"][:700]},
                "Generated Outputs": {"your_overall_scores":
                                      [None if m is None else round(m, 2) for m in ms]},
                "Feedback": position_feedback(gc, ms, tx, self.gold),
            })
        return {comp: records}
