# 01_MCR_NATIVE_FOUR_CONDITION_REPORT

POST_HOC_EXPLORATORY — recovered historical outputs; CPU analysis only.

## Actual construct and full outcomes

Audio is actually supplied in every native condition. Neutral supplies only the classification question. Faithful asserts the source emotion; adversarial asserts a different emotion. Irrelevant supplies unrelated captions with the same warning/description wrapper as faithful/adversarial. These are input-package contrasts, not a pure isolated semantic relation effect versus neutral. The source GT is a released dataset annotation, with conflicting labels on some identical audio bytes; it is not unquestionable acoustic truth. OTHER is a valid seven-label output outside the audio source and, only where defined, the explicit-text source. Failure is separate. Neutral/irrelevant have no text-side accuracy.

| Condition | Full N | Audio-source match | 95% audio-SHA CI | Explicit-text match | OTHER | Parse fail |
| --- | --- | --- | --- | --- | --- | --- |
| neutral | 1000 | 445/1000 (44.50%) | [41.48, 47.49] | NOT_DEFINED | 555 | 0 |
| faithful | 1000 | 994/1000 (99.40%) | [98.90, 99.80] | 994/1000 | 6 | 0 |
| adversarial | 1000 | 6/1000 (0.60%) | [0.20, 1.11] | 988/1000 | 6 | 0 |
| irrelevant | 1000 | 432/1000 (43.20%) | [40.00, 46.41] | NOT_DEFINED | 563 | 5 |

Adversarial explicit-text adherence988/1000=98.80%, audio-SHA95%CI [98.10, 99.40]. Faithful994/1000 cannot discriminate audio listening from copying its matching assertion. Adversarial largely follows the conflicting assertion despite the discretion warning. This is bounded evidence of assertion-following in this prompt, not universal text preference or audio absence. Four aggregate accuracies were already in historical `mcr_qwen25_native_metrics_v1.json`; their numerical recovery is a replication of existing results.

## New paired and distributional projection

| Paired to−from | Effect /95%CI | Holm p (family6) | Changed labels/1000 |
| --- | --- | --- | --- |
| faithful−neutral | +54.90 pp, 95% CI [51.81, 58.10] pp | 0.0003 | 550 |
| adversarial−neutral | -43.90 pp, 95% CI [-47.04, -40.79] pp | 0.0003 | 886 |
| irrelevant−neutral | -1.30 pp, 95% CI [-5.03, 2.51] pp | 0.54355 | 572 |
| adversarial−faithful | -98.80 pp, 95% CI [-99.49, -98.02] pp | 0.0003 | 992 |
| irrelevant−faithful | -56.20 pp, 95% CI [-59.38, -52.91] pp | 0.0003 | 563 |
| irrelevant−adversarial | +42.60 pp, 95% CI [39.52, 45.65] pp | 0.0003 | 889 |

Only3/1000 retain the same valid label across allfour conditions;997/1000 show at least one change (failure state included). Of995 items valid in allfour,992 change labels. Faithful→adversarial changes992 labels. Pairwise full8×8 transition tables retain the5 irrelevant parse failures. The six source-match tests use paired SHA-cluster sign flips,19999 draws; raw p=.00005 is the Monte Carlo resolution floor, **not an exact p smaller than that floor**. Holm-adjusted p=.0003 for five contrasts; irrelevant−neutral p=.54355. Pointwise cluster CIs are descriptive, not simultaneous. Conditions were not randomized; exchangeability and dependence assumptions limit inferential generalization.

The apparent near-preservation of overall match under irrelevant text is misleading:445→432 matches (−1.30pp, CI [-5.03, 2.51]), but572/1000 outputs change. Predicted neutral labels rise387→746 (38.7%→74.6%), paired +35.90 pp, 95% CI [32.16, 39.72] pp. This full-ontology descriptive contrast was part of the predeclared label-distribution diagnostics, without a separate confirmatory p claim. Neutral-source items improve237/468→368/468 while happy87/165→26/165, angry44/118→16/118, sad27/80→6/80 and surprised44/125→11/125 deteriorate. Therefore “irrelevant captions do not change behavior” is contradicted, while “irrelevant captions reduce aggregate source-match” is not established. This cancellation and neutral-output concentration are new projections of the historical data; the earlier metrics already reported379 correctness-state flips, so correctness flipping itself is not new.

| Audio source label | N | Neutral match | Irrelevant match | Paired irrelevant−neutral /95%CI |
| --- | --- | --- | --- | --- |
| sad | 80 | 27 | 6 | -26.25 pp, 95% CI [-37.50, -16.25] pp |
| happy | 165 | 87 | 26 | -36.97 pp, 95% CI [-45.73, -28.14] pp |
| fearful | 19 | 4 | 5 | +5.26 pp, 95% CI [-21.05, 31.58] pp |
| angry | 118 | 44 | 16 | -23.73 pp, 95% CI [-32.48, -15.25] pp |
| surprised | 125 | 44 | 11 | -26.40 pp, 95% CI [-34.40, -19.20] pp |
| disgusted | 25 | 2 | 0 | -8.00 pp, 95% CI [-20.00, 0.00] pp |
| neutral | 468 | 237 | 368 | +27.99 pp, 95% CI [22.41, 33.33] pp |

All seven source strata were predeclared; pointwise CIs and no subgroup-confirmatory claims. Fearful N19 and disgusted N25 are small. Caption semantics, extra wrapper, class imbalance468neutral, source-label ambiguity and speaker/dialogue dependence remain alternatives; no neutral-target interpretation is assigned to the captions.

## Robustness and accounting

4000 unique item×condition keys,1000 complete groups,4000 generation successes,3995 parser successes,5 failures only in irrelevant, no added model calls or retries. Item-weighted audio-SHA bootstrap uses943 distinct content clusters. Original909controlled is not the native1000 denominator. Sensitivities keep the original outputs: equal-hash weighting; native909 intersection; removal of whole conflicting-label SHA groups (secondary921);995 parse-complete items. The principal faithful→adversarial collapse persists. See duplicate report and machine results. Native aggregate results are not independent replication of the controlled protocol or prior reports, and full pairing adds analytical value without adding independent inference data.

Trace: `analysis.py::mcr`, `diagnostics.py::run`; raw/manifest source hashes in00lock, per-item identities in `intermediate/MCR_ITEM_IDENTITY_OUTCOMES.csv`, numerical CIs in `numeric/MCR_RESULTS.json` and `numeric/MCR_SECONDARY_DIAGNOSTICS.json`.
