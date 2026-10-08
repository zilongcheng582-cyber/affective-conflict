# R2 — Phase3 Compositionality Falsification

Analysis origin: `POST_AUDIT_SCIENTIFIC_ANALYSIS_V1`. Code: `analyses/post_audit/sci_r2_compositionality.py`.
Seed `20261008`. Statistics use a 2,000-replicate utterance-cluster bootstrap (67 utterances; 61 have ≥1 frozen-resolved row) and 2,000 shuffle replicates.

## Scope

- All 402 planned rows (67 utterances × 6 orders) are **TWO_VS_ONE**. Patterns: T=A≠V 258 rows (43 utterances), A=V≠T 96 rows (16), T=V≠A 48 rows (8).
  **Nothing here addresses ALL_DIFFERENT trimodal conflict.** These results are not evidence about general trimodal compositionality.
- The frozen composition B1 is reproduced exactly from Phase2 edges with the frozen rule: 294 resolved, 268 correct, 108 unresolved
  (93 edge disagreements, 15 involving an OTHER edge). It is not modified.
- Observed Phase3 outputs: on all 402 rows, majority label 288, minority 99, other 15. On the frozen 294 rows: 216 / 74 / 4.

## Baselines

| ID | Rule | Data used | Role |
|---|---|---|---|
| B0 | always majority label | topology | baseline |
| B2a / B2b | label of first / last presented modality | order | order heuristic |
| B2c | per-(pair, arm) source selection rate, each edge predicted from order only, frozen composition rule | Phase2, leave-test-utterance-out | order-only source baseline |
| B3a | item preference: vote of the parsed labels over **both orders** of the two informative edges (4 Phase2 responses); abstains on a tie | Phase2, same item | item-level label preference |
| B3a_t | B3a with ties broken toward the majority label | as B3a | full-coverage variant |
| B3b | frozen rule applied to the **opposite-order** arms of the same edges | Phase2, same item | order-mismatch control |
| B3c | label of the modality with the lowest Phase1 normalized entropy | Phase1 | unimodal-confidence heuristic |
| B3d | global label preference (Phase2 conflict win rates of other utterances) | Phase2 LOUO | global label prior |
| B5 | edges *predicted* by an M3a-spec source model fitted on other utterances (5-fold utterance cross-fit), frozen rule | Phase1 features + Phase2 of other items | **unseen-item compositional prediction** |
| B4 | each utterance's matched edges replaced by a donor's edges at the same arms; donors are deranged within the same minority-modality stratum (topology and order matched) | Phase2, shuffled | null |
| DIAG | majority vote of the other 5 Phase3 orders of the same utterance | **Phase3 outcomes** | within-item oracle-like diagnostic; *not a baseline* |

No baseline uses the Phase3 outcome being predicted, except the DIAG row, which is labelled as such. The B4 shuffle never selects permutations by outcome.

## Main results (`R2_BASELINE_COMPARISON.csv`, `R2_CLUSTERED_UNCERTAINTY.csv`)

Accuracy on the frozen 294 rows counts abstentions as errors. "Common" is the subset of the 294 where the baseline also resolves.

| Baseline | Coverage /402 | Correct /402 | Acc on frozen 294 | Common support n: baseline vs B1 | B1 − baseline on 294 [95% CI] |
|---|---:|---:|---:|---|---|
| **B1 frozen matched pairwise** | 0.731 | 268 | **0.912** | — | — |
| B0 always majority | 1.000 | **288** | 0.735 | 294: 0.735 vs 0.912 | **+0.177 [+0.072, +0.285]** |
| B2a first presented | 1.000 | 210 | 0.524 | 294 | +0.388 [+0.309, +0.463] |
| B2b last presented | 1.000 | 249 | 0.633 | 294 | +0.279 [+0.213, +0.339] |
| B2c source order-only composition | 0.517 | 79 | 0.180 | 151: 0.351 vs 0.907 | +0.731 |
| B3a item preference (order-pooled) | 0.836 | 277 | 0.840 | **272: 0.908 vs 0.908 (identical predictions)** | +0.071 [+0.021, +0.132] (abstentions only) |
| B3a_t item preference, tie→majority | 1.000 | **321** | 0.881 | 294 | +0.031 [+0.007, +0.060] |
| B3b order-mismatched edges | 0.731 | 230 | 0.690 | 238: 0.853 vs 0.937 | common: +0.084 [+0.024, +0.158] |
| B3c Phase1 lowest-entropy modality | 1.000 | 285 | 0.762 | 294 | +0.150 [+0.047, +0.258] |
| B3d global label preference | 1.000 | 255 | 0.673 | 294 | +0.238 [+0.119, +0.360] |
| B5 cross-fit predicted-edge composition | 0.711 | 200 | 0.568 | 218: 0.766 vs 0.899 | common: +0.133 [+0.043, +0.233] |
| B4 shuffled pairwise (mean of 2,000) | 0.731 | 166.1 (SD 12.5, max 209) | 0.419 (SD 0.043, max 0.561) | — | permutation p = 1/2001 ≈ 0.0005 |
| DIAG within-item oracle-like | 0.993 | 339 | 0.888 | 293: 0.891 vs 0.915 | +0.024 [−0.043, +0.085] |

Coverage-aware comparison on all 402 rows, with abstention counted as an error (B1 = 0.667):
- vs B0 always majority (0.716): −0.050 [−0.152, +0.057]
- vs B3a_t (0.799): **−0.132 [−0.194, −0.077]**
- vs B3a (0.689): −0.022 [−0.080, +0.040]
- vs B5 (0.498): +0.169 [+0.067, +0.271]

The B4 shuffle keeps exactly 294 resolved rows and 95 minority predictions in every replicate. It therefore isolates the
**item correspondence** of the edges from the marginal rate of minority predictions.

## Majority vs minority structure

- B1 predicted MAJORITY on 199 rows, with 196 correct (0.985 [0.966, 1.000]). It predicted MINORITY on 95 rows (25 utterances), with 72 correct (0.758 [0.613, 0.876]).
- Always-majority is correct on the same 196 majority-predicted rows. **All of B1's +52-row gain over B0 (268 vs 216) comes from
  the 95 minority predictions**: 72 correct for B1 against 20 for always-majority on those rows.
- 196 of the 268 correct B1 predictions (73%) are majority-side predictions that the base rate alone would also get right.
- 39 of 67 utterances output the same label in all 6 orders. 30 utterances ever output the minority label, and 5 output it in all 6 orders.

## Answers

1. **268/294 vs always-majority:** +17.7 accuracy points on the frozen 294 rows (+52 rows, [+7.2, +28.5] pts). The gain comes entirely from minority-side predictions.
   On the full 402 planned rows, B1's abstentions (108) make it *not better* than always-majority (0.667 vs 0.716; difference CI includes 0).
2. **Does matched pairwise beat item preference?** No. On the 272 rows where the order-pooled item vote (B3a) is decisive, B1 and B3a make
   **identical predictions**. B1's only advantage is on the 22 rows (6 utterances) where the item vote ties. There B1 gets 21/22 correct
   against 12/22 for tie→majority (+0.41 [+0.23, +0.50]), but with only 6 clusters. Coverage-aware, the full-coverage item preference (B3a_t) beats B1 (0.799 vs 0.667).
3. **Does it beat shuffled pairwise?** Yes, decisively: 0.912 vs a null mean of 0.419 (max 0.561 over 2,000 topology- and order-matched derangements; p ≈ 0.0005).
   Pairwise responses carry **item-specific** information about the trimodal response.
4. **How much of the accuracy comes from majority-side selection?** 73% of correct predictions are majority-side and are reproduced by the base rate. Also, B1 resolves
   mostly where both edges agree, and agreement is easier on majority-dominated items.
5. **Compositional prediction or within-item consistency?** The evidence supports **within-item consistency**. Pairwise responses on the
   *same item* predict that item's TWO_VS_ONE trimodal responses well. Order matching adds a modest, real signal: B1 beats the
   order-mismatched edges by +8.4 pts on common support and wins the tie subset. But the order-pooled item preference already captures everything else.
   When the edges must be *predicted* from unimodal evidence for unseen items (B5, a genuine compositional forecast), accuracy on resolved rows
   (0.699) does not exceed the always-majority base rate (0.716). The phenomenon is therefore best described as stable item-level label
   preference that pairwise probes reveal. It is not evidence that trimodal behaviour is composed from separately predictable pairwise arbitration rules.

**R2 verdict: NOT_ESTABLISHED** for compositionality beyond item-level preference. The narrower claim, *TWO_VS_ONE
within-item pairwise-to-trimodal consistency (non-shuffled, partially order-specific)*, is **SUPPORTED** within this
67-utterance set. Neither statement extends to ALL_DIFFERENT trimodal conflict.
