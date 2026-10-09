# SCIENTIFIC_ANALYSIS_V1 — Final Report

Analysis origin: `POST_AUDIT_SCIENTIFIC_ANALYSIS_V1`. This is a new post-audit analysis, not the preregistered confirmatory experiment.
Base commit: `f8432837fe64316195ccbcab2d9eaac46080b244` (main). Everything ran on CPU, with no model loading and no GPU inference. No file under `frozen/`, `manifests/`,
`evidence/` or the historical `results/` was modified. No frozen transfer model was refitted. All R1_* models are new diagnostic CV models.

Detailed reports: `R1_SOURCE_STRUCTURE_REPORT.md`, `R2_COMPOSITIONALITY_REPORT.md`, `R3_LISTEN_BEHAVIOR_REPORT.md`.

## 1. R1 — Source evidence effect → **SUPPORTED**

Within EmotionTalk (663 resolved pairwise conflicts, 274 utterances), the model's unimodal uncertainty predicts its bimodal choice
well beyond pair, presentation order, emotion-label identity and candidate-list position. Results use the same utterance-grouped 5-fold split throughout, with fold-local fitting:

- Pair + order AUROC is 0.577. Adding label + position gives 0.638. Adding evidence gives 0.801, or **0.803 with normalized-entropy difference alone**.
- Evidence over the label/position baseline (M4 − M2): ΔAUROC +0.156 [+0.110, +0.210], Δlog loss −0.127 [−0.179, −0.077].
  The speaker-grouped CV, the unpenalized fits and 20 alternative fold splits all agree.
- **Entropy alone carries essentially all of the gain** (M3 − M5: ΔAUROC −0.002 [−0.006, +0.001]). The model tends to choose the modality whose
  own unimodal output was less uncertain. In the current sample, model specification and evaluation precision, source-label probability and
  margin show no confirmable additional predictive gain beyond normalized entropy. This is not proof that they carry no information.
- Qualifications: A–T is weaker (out-of-fold AUROC 0.69 vs 0.79/0.85, and its log-loss gain is not established). The order effect is pair-specific
  (A–T none, A–V moderate recency, V–T strong recency; pair×order Wald p = 1.4e-4). The direction of the entropy effect is consistent across pairs
  when entropy is fitted alone. The historical publication-CV M3a AUROC (0.8018) reproduces exactly.
- Limits: this is associational and uses a model-internal feature. It says nothing about objective emotional evidence strength or about causal mechanism.

## 2. R2 — Compositionality → **NOT_ESTABLISHED** (beyond item-level preference)

The narrower claim, TWO_VS_ONE within-item pairwise→trimodal consistency, is SUPPORTED.

- 268/294 (0.912) beats always-majority (0.735) by **+17.7 pts [+7.2, +28.5]**. The whole gain comes from the 95 minority-side predictions
  (72 correct vs 20 for always-majority). 73% of correct predictions are majority-side ones that the base rate alone reproduces.
- Coverage-aware on all 402 planned rows: B1 0.667 vs always-majority 0.716 (−0.050 [−0.152, +0.057]).
- Against shuffled pairwise edges (topology- and order-matched donor derangements): 0.912 vs a null mean of 0.419 (max 0.561), p ≈ 0.0005.
  So the edges carry **item-specific** information.
- Against item-level label preference (vote over both orders of the same informative edges): **the predictions are identical on all 272 rows where
  the vote is decisive.** Matched-order edges help only on 22 tie rows (6 utterances) and against the opposite-order edges (+8.4 pts [+2.4, +15.8]).
  The full-coverage item preference beats B1 coverage-aware (0.799 vs 0.667).
- A genuine unseen-item composition fails. When the edges are predicted from unimodal evidence by a cross-fitted source model (B5), it resolves 286 rows.
  On those same rows it gets 200/286 = 0.6993, against always-majority's 207/286 = 0.7238 (paired −0.024 [−0.135, +0.077]).
- So Phase3 shows that **pairwise probes reveal stable item-level label preferences that recur in TWO_VS_ONE trimodal responses**,
  with a modest order-specific component. It does not show trimodal behaviour composed from separately predictable pairwise rules. Nothing here concerns ALL_DIFFERENT.

## 3. R3 — LISTEN behavior

- OTHER is a stable majority outcome in **every** condition: 3A 0.525, 3B 0.553, 3C 0.558. There are no condition differences, and technical missingness is 0.
  The 44% binary-resolvable rate is therefore not specific to joint input.
- OTHER is **item-persistent**: 85% of 3B-OTHER items stay OTHER in 3C, and 35% of triple-matched items are OTHER in all conditions.
  It is **label-dependent**. Outside *ridicule* (sarcasm) items, the model almost never outputs the implicit audio label, even from audio alone
  (3B OTHER: ridicule 6%, anger 91%, disgust 88%, frustration 75%, sadness 92%). 89% of 3B SIDE_A and 83% of 3C SIDE_A come from ridicule items.
  B3 unimodal entropy and margin, which are computed over a mismatched 7-label space, are not associated with OTHER.
- On exactly matched items, 3C's A/T split lies between the unimodal conditions: binary SIDE_A share is 0.41 (3A), 0.61 (3C) and 0.82 (3B).
  Adding text to audio moves A→T and OTHER→T. Adding audio to text moves T→A and OTHER→A. All of these are **associational condition contrasts**. Prompts,
  option shuffles and ground-truth definitions differ by condition, so they are not causal modality contributions.
- The labels OTHER contains cannot be analysed, because raw LISTEN generations are not published here (marked not executable).
- Evaluation: the pooled 518-row AUROC mixes unimodal conditions with systematically different A/T shares. The 3C 167/378 subset is selected by a
  label-dependent, item-persistent process. The order effect is unidentifiable because every row is A_THEN_T, and the EmotionTalk recency offset is miscalibrated (M0+order is already worse than M0).
  Log loss 0.982 vs M0 0.697 (+0.285 [+0.168, +0.402]) means the transferred probabilities are worse than a constant.

## 4. Paper implications

- **EmotionTalk source as the first core contribution: yes, with scoped wording.** The finding is "in a controlled bimodal conflict
  paradigm, an omni model's arbitration is predicted by its own unimodal uncertainty asymmetry (CV AUROC ≈ 0.80; robust to
  label/position/order controls and speaker grouping), with pair-specific order biases." It must be presented as a predictive or associational
  regularity of one model on one dataset, not as an emotion-evidence mechanism.
- **Phase3 as a second core contribution: no.** Report it as a secondary consistency result: TWO_VS_ONE item-level consistency, a significant shuffle test,
  and an order-matching increment. Include the negative controls explicitly: no gain over item preference, unseen-item composition fails, and coverage-aware results do not beat majority.
- **LISTEN: a valuable behavioral diagnostic and an explicit transfer limitation.** The label-dependent OTHER phenomenon is a concrete
  benchmark and construct finding about implicit-affect labels. It is not evidence of joint-arbitration transfer.
- **CA-MER and MCR: frozen zero-refit transfer evidence, heterogeneous and secondary.** MCR shows large log-loss improvement over M0
  (−0.432) and AUROC ≈ 0.73–0.74, but BA 0.5 under extreme imbalance, and it is LATER_ADDED/EXPLORATORY. CA-MER supported coverage shows AUROC
  0.686 with a log-loss difference vs M0 of +0.052 [−0.032, +0.137], and its full margin coverage is worse than M0. Present both as a transfer table that shows
  heterogeneity, without a common-mechanism ranking.
- **Key questions that still need a GPU:**
  (a) whether the entropy–arbitration link is causal, which needs manipulation of unimodal reliability;
  (b) generality to another model;
  (c) ALL_DIFFERENT trimodal behaviour;
  (d) a counterbalanced LISTEN joint order;
  (e) the identity of LISTEN OTHER labels, which needs either the unpublished raw generations or re-inference.
  None of these can be answered from the current CPU data.

## 5. Recommended next step

**NEXT_STAGE = CONTROLLED_GPU_INTERVENTION**

Reason: the only robust positive result (R1) is associational, and its natural reviewer challenge is that entropy may be a proxy for
item difficulty or label content. Phase3 and LISTEN cannot carry the paper on their own. A small, preregistered intervention on EmotionTalk source
items would test the central claim directly and would make R1 a strong first contribution: graded degradation of one modality (audio SNR,
video blur/occlusion, text masking), then measuring whether unimodal entropy and the bimodal choice shift as the frozen R1/M3a model predicts.
This is cheaper and more decisive than a full second-model replication, which would replicate a correlation without resolving it.
Paper sections for R1, R2 and R3 can be drafted in parallel with the current scoped claims, but they should not be finalized before this test.
This stage has not been executed.

## Run record

- Python 3.13.16 in an isolated venv (numpy 2.5.3, scipy 1.18.1, pandas 3.0.6, scikit-learn 1.9.1, statsmodels 0.15.0). The frozen environment was not modified.
- Commands, run from the repository root:
  `python -m analyses.post_audit.sci_r1_source_structure`;
  `python -m analyses.post_audit.sci_r2_compositionality`;
  `python -m analyses.post_audit.sci_r3_listen_behavior`
- Seeds: 20261008 for folds, bootstrap and shuffle. The R1 alignment check also uses the historical 20260928. 2,000 bootstraps and 2,000 shuffles.
- Data files used: `frozen/source_model/publication_cv_records.json` and `frozen/source_model/binding.json` (identity checks),
  `frozen/source_model/08_M0_M3_model_results.csv` (cited), `manifests/emotiontalk/source_measurements.csv`, `manifests/emotiontalk/trimodal_plan.csv`,
  `evidence/emotiontalk/phase2_observed_responses.jsonl`, `evidence/emotiontalk/phase3_observed_outputs.jsonl`,
  `results/post_audit/closure_v1/PHASE3_ROW_LEVEL_VERIFICATION_V1.csv`, `manifests/listen/frozen_joint_outcomes.csv`,
  `results/post_audit/closure_v1/LISTEN_JOINT_ONLY_REPORT.csv`, `LISTEN_CONDITION_DIAGNOSTICS.csv`, `ZERO_REFIT_BASELINE_COMPARISON_V1.csv` (cited).
- Per-analysis metadata: `R1_RUN_METADATA.json`, `R2_RUN_METADATA.json`, `R3_RUN_METADATA.json`.

## Revision note (Stage A, 2026-10-09)

Two wording corrections were made: the R1 claim about source probability and margin, and the R2 B5 comparison, which is now paired on the same 286 rows.
A–T is now reported as 61 utterances. No other numbers, verdicts or recommendations changed. The R1–R3 scripts were replayed in an isolated environment and reproduced
the committed tables exactly. The R2 script now also writes same-support comparisons against always-majority, without changing any existing value.
