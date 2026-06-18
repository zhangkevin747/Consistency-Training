# Intra-coherence pre-test  (n=955 rollouts, 15 questions)

Label-free signal: **calib_coh** = does verbal confidence (hedge vs certainty words) match numeric extremity |p-0.5|.  No judge output used to build it.

## HEADLINE — calib_coh vs judge OVERALL
- within-question Spearman (the fair test): **mean rho = +0.037** across 15 questions
- pooled Spearman: -0.037
- within-question AUC (top vs bottom-half quality): mean 0.519, min 0.264, #>0.55: 6/15

## VALIDATION — does the cheap proxy capture the judge's own coherence notion?
- calib_coh vs judge CALIBRATION dim: mean within-q rho = +0.092

## SCOPE CHECK — predicted WEAK on content dims (floor-raiser, not ceiling)
- vs calibration   : mean within-q rho = +0.092
- vs overall       : mean within-q rho = +0.037
- vs sufficiency   : mean within-q rho = +0.017
- vs reasonableness: mean within-q rho = +0.027
- vs acceptability : mean within-q rho = -0.041
- vs relevance     : mean within-q rho = -0.005

## BASELINES (within-question Spearman vs overall)
- numeric extremity |p-0.5|         : -0.316
- hedge density                     : +0.173
- certainty density                 : -0.031
- linguistic confidence (cert-hedge): -0.157

## DIMENSION ANALYSIS (judge scores, within-question mean Spearman)
Judge CALIBRATION dim (the rubric's prose↔number coherence measure) vs others:
- calibration vs overall: +0.55 ; vs sufficiency: +0.50 ; vs reasonableness: +0.40 ;
  vs acceptability: +0.23 ; vs relevance: +0.22

But the judge's calibration dim is largely the EXTREMITY/humility effect re-expressed:
- pooled: extremity |p-0.5| vs judge-calibration = **-0.56** ; extremity vs overall = **-0.57**

What actually drives OVERALL quality (within-q mean rho): **sufficiency +0.85**,
**reasonableness +0.76** — depth-of-support and crux-engagement. Calibration (+0.55)
and acceptability (+0.52) are secondary. Quality = substance + engaging the counter.

## VERDICT
1. **Label-free matching-coherence (calib_coh) is NULL** (mean rho +0.04, AUC 0.52).
   It conflates *coherently-confident* (quality-penalized) with *coherently-uncertain*
   (quality-rewarded) — same score, opposite quality → cancels to zero.
2. The only robust label-free signal is **HUMILITY**: extremity → worse (-0.32 within-q,
   -0.57 pooled), hedging → better (+0.17). A *level* prior, not a *coherence* signal —
   the same humility prior that beats decomposition-direction rewards (memory). Degenerate
   as a reward (collapses answers toward 0.5; reward-hackable).
3. The judge's calibration dim tracking quality is mostly (2) re-expressed, NOT
   independent evidence that prose↔number coherence drives quality.
4. UNTESTED: the *polarity* slice (conclusion denies the claim but number affirms it,
   e.g. the bone_marrow 0.10-quality rollout). Real but likely rare — a floor-raiser for
   a tail failure, not a broad signal.

**Bottom line:** intra-coherence as a broad label-free reward does NOT survive the full
dataset. Quality lives in sufficiency + reasonableness (irreducibly content). The
ground-truth-transfer route (structural coherence) is untouched by this null.

## per-question calib_coh vs overall
| qid | rho | n |
|---|---|---|
| mereological_vagueness | -0.425 | 64 |
| newcomb_one_boxing | -0.266 | 63 |
| analysis_of_causation | -0.032 | 64 |
| bone_marrow_compensation | -0.028 | 63 |
| costly_punishment | -0.025 | 64 |
| moral_bioenhancement | -0.023 | 64 |
| llm_understanding | -0.014 | 64 |
| carlsmith_capability_disposition | -0.005 | 64 |
| module_retire | +0.025 | 64 |
| accuracy_first_importance | +0.098 | 64 |
| luck_egalitarianism | +0.158 | 64 |
| suffering_asymmetry | +0.177 | 64 |
| imprecise_credences | +0.187 | 64 |
| kidney_compensation_exploitation | +0.254 | 64 |
| housefly_subjective_time | +0.468 | 61 |
