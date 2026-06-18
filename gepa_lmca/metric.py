"""Weighted pairwise ranking error — matches Cooper/Oesterheld et al. (LMCA paper, App B.1).

Per position: for every critique pair (i,j), loss = |h_i - h_j| if the model orders
them the *wrong* way, else 0; divide by the TOTAL number of pairs on the position
(not by the sum of weights). Average across positions (macro). Gold = a single rater
(default Emery Cooper, the primary rater the paper benchmarks against).

Scale (paper, simple baseline prompt, vs EC): random 0.173 · gpt-4.1-mini 0.128 ·
gpt-5 0.080. Model ties on a non-tied human pair count as 0.5·|h_i−h_j| (coin-flip).
"""
GOLD = "Emery Cooper"


def position_loss(model, human):
    """model, human: aligned lists for the critiques of ONE position."""
    n = len(model)
    if n < 2:
        return None
    tot = 0.0
    npairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            npairs += 1
            dh = human[i] - human[j]
            if dh == 0:
                continue  # human has no order on this pair -> 0 loss
            dm = model[i] - model[j]
            if dm == 0:
                tot += 0.5 * abs(dh)
            elif (dm > 0) != (dh > 0):
                tot += abs(dh)
    return tot / npairs if npairs else None


def _gold_aligned(it, ms, gold):
    """Return (model_scores, gold_human_scores) over critiques the gold rater rated."""
    m, h = [], []
    for k, c in enumerate(it["critiques"]):
        g = c["rater_overall"].get(gold)
        if g is not None:
            m.append(ms[k])
            h.append(g)
    return m, h


def dataset_error(items, model_scores, gold=GOLD):
    """Macro-average of per-position weighted ranking loss vs the gold rater."""
    losses = []
    for it, ms in zip(items, model_scores):
        m, h = _gold_aligned(it, ms, gold)
        pl = position_loss(m, h)
        if pl is not None:
            losses.append(pl)
    return sum(losses) / len(losses) if losses else None


def inter_rater_ceiling(items, gold=GOLD):
    """How well do OTHER raters predict the gold rater's ordering — the human floor."""
    losses = []
    for it in items:
        # gold scores per critique idx
        g = {k: c["rater_overall"].get(gold)
             for k, c in enumerate(it["critiques"])}
        raters = set()
        for c in it["critiques"]:
            raters |= set(c["rater_overall"])
        for r in raters:
            if r == gold:
                continue
            idx = [k for k, c in enumerate(it["critiques"])
                   if g[k] is not None and r in c["rater_overall"]]
            if len(idx) < 2:
                continue
            m = [it["critiques"][k]["rater_overall"][r] for k in idx]
            h = [g[k] for k in idx]
            pl = position_loss(m, h)
            if pl is not None:
                losses.append(pl)
    return sum(losses) / len(losses) if losses else None


def position_score(model, human):
    """GEPA score for one position: 1 - weighted ranking loss (higher better)."""
    pl = position_loss(model, human)
    return None if pl is None else 1.0 - pl


def position_feedback(critiques, model_scores, model_texts=None, gold=GOLD,
                      max_chars=380, snippet=420, top=3):
    """Textual feedback (μf) for the reflection LM: parse-failure warnings, the
    position's biggest ranking errors, the critique texts, AND the judge model's
    own reasoning for each misranked critique (the natural-language signal GEPA
    relies on). model_scores may contain None for critiques that failed to parse."""
    lines = []
    failed = sum(1 for m in model_scores if m is None)
    if failed:
        lines.append(
            f"WARNING: {failed}/{len(model_scores)} critiques produced UNPARSEABLE output "
            f"(no valid 7-key JSON). The output format is FIXED — the guidance must not "
            f"change, restate, or override it. This alone makes the candidate score badly.")
    texts = model_texts or [""] * len(critiques)
    rows = [(model_scores[k], c["rater_overall"][gold], c["text"], texts[k])
            for k, c in enumerate(critiques)
            if model_scores[k] is not None and c["rater_overall"].get(gold) is not None]
    pl = position_loss([r[0] for r in rows], [r[1] for r in rows])
    if pl is not None:
        lines.append(f"Weighted ranking error on parsed critiques = {pl:.2f} "
                     f"(0 = ordered exactly like the human).")
    errs = []
    for a in range(len(rows)):
        for b in range(a + 1, len(rows)):
            ma, ha, ta, ra = rows[a]
            mb, hb, tb, rb = rows[b]
            if ha == hb:
                continue
            dm, dh = ma - mb, ha - hb
            if ((dm == 0) or ((dm > 0) != (dh > 0))) and abs(dh) >= 0.15:
                hi = (ma, ha, ta, ra) if ha > hb else (mb, hb, tb, rb)
                lo = (mb, hb, tb, rb) if ha > hb else (ma, ha, ta, ra)
                errs.append((abs(dh), hi, lo))
    errs.sort(key=lambda e: -e[0])
    if not errs and not failed:
        lines.append("All clearly-ordered critique pairs were ranked correctly.")
    for w, (hm, hh, ht, hr), (lm, lh, lt, lr) in errs[:top]:
        blk = (f"\nRANKING ERROR (human gap {w:.2f}): the human ranks critique A ABOVE B, "
               f"but your scores do not.\n"
               f"  A — human {hh:.2f}, you gave {hm:.2f}: {ht[:max_chars]}\n")
        if hr:
            blk += f"    your reasoning for A: {hr[:snippet]}\n"
        blk += f"  B — human {lh:.2f}, you gave {lm:.2f}: {lt[:max_chars]}"
        if lr:
            blk += f"\n    your reasoning for B: {lr[:snippet]}"
        lines.append(blk)
    return "\n".join(lines)


if __name__ == "__main__":
    import random
    import statistics as st
    from data import load_lmca

    items = load_lmca()
    # positions usable vs EC
    usable = [it for it in items
              if sum(1 for c in it["critiques"] if c["rater_overall"].get(GOLD) is not None) >= 2]
    print(f"{len(usable)} positions with >=2 critiques rated by {GOLD}")

    rnd = random.Random(0)
    errs = []
    for _ in range(300):
        ms = [[rnd.random() for _ in it["critiques"]] for it in items]
        errs.append(dataset_error(items, ms))
    print(f"random model            : {st.mean(errs):.3f}   (paper: 0.173)")
    print(f"HUMAN ceiling (others->{GOLD[:2]}): {inter_rater_ceiling(items):.3f}")
    perfect = dataset_error(items, [[c["rater_overall"].get(GOLD, c["human_overall"])
                                     for c in it["critiques"]] for it in items])
    print(f"perfect (gold as model) : {perfect:.3f}   (sanity ~0)")
