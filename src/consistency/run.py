"""End-to-end orchestrator for the consistency preliminary test.

Stages (in order): generate -> rollout -> select -> reward -> judge -> quality -> correlate.
`select` screens the over-generated candidates down to the naturally-inconsistent questions
(Type 1: phrasing spread; Type 2: actual conjunction violations) before any judging.

    # quick pilot (over-generate, screen, judge near/far cross-phrasing pairs)
    PYTHONPATH=src .venv/bin/python -m consistency.run --pilot

    # full run
    PYTHONPATH=src .venv/bin/python -m consistency.run

    # run a single stage (e.g. resume judging) on the pilot
    PYTHONPATH=src .venv/bin/python -m consistency.run --pilot --stage judge
"""
from __future__ import annotations

import argparse
import time

STAGES = ["generate", "rollout", "select", "reward", "judge", "quality", "correlate"]


def run(pilot: bool, stages: list[str], verify: bool) -> None:
    from . import (correlate, generate_questions, judge, quality, rewards,
                   sample_rollouts, select)

    banner = "PILOT" if pilot else "FULL"
    for st in stages:
        print(f"\n{'=' * 70}\n[{banner}] STAGE: {st}\n{'=' * 70}")
        t0 = time.time()
        if st == "generate":
            generate_questions.generate(pilot=pilot, verify=verify)
        elif st == "rollout":
            sample_rollouts.sample(pilot=pilot)
        elif st == "select":
            select.select(pilot=pilot)
        elif st == "reward":
            _write_rewards(pilot)
        elif st == "judge":
            judge.judge(pilot=pilot)
        elif st == "quality":
            _write_quality(pilot)
        elif st == "correlate":
            correlate.correlate(pilot=pilot)
        print(f"[{banner}] {st} done in {time.time() - t0:.0f}s")


# small helpers so each stage can also be re-run standalone from disk
def _write_rewards(pilot: bool) -> None:
    import pandas as pd
    from . import config as C
    from .rewards import compute_rewards
    from .utils import read_jsonl
    df = pd.DataFrame(compute_rewards(read_jsonl(C.rollouts_file(pilot))))
    df.to_csv(C.rewards_file(pilot), index=False)
    scored = df[df["reward"].notna()]
    print(f"  rewards: {len(scored)}/{len(df)} scored -> {C.rewards_file(pilot)}")


def _write_quality(pilot: bool) -> None:
    import pandas as pd
    from . import config as C
    from .quality import compute_quality
    from .utils import read_jsonl
    rows = compute_quality(read_jsonl(C.judgments_file(pilot)))
    pd.DataFrame(rows).to_csv(C.quality_file(pilot), index=False)
    print(f"  quality: {len(rows)} rollouts scored -> {C.quality_file(pilot)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot", action="store_true", help="tiny end-to-end validation run")
    ap.add_argument("--stage", choices=STAGES + ["all"], default="all", help="run a single stage")
    ap.add_argument("--from", dest="from_stage", choices=STAGES, default=None,
                    help="run from this stage to the end (e.g. --from rollout skips generate)")
    ap.add_argument("--no-verify", action="store_true", help="skip dataset equivalence checks")
    args = ap.parse_args()
    if args.from_stage:
        stages = STAGES[STAGES.index(args.from_stage):]
    elif args.stage == "all":
        stages = STAGES
    else:
        stages = [args.stage]
    run(pilot=args.pilot, stages=stages, verify=not args.no_verify)


if __name__ == "__main__":
    main()
