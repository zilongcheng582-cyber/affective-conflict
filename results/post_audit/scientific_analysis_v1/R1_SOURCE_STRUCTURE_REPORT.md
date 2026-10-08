# R1 — EmotionTalk Source Predictive Structure

Analysis origin: `POST_AUDIT_SCIENTIFIC_ANALYSIS_V1` (new post-audit diagnostic analysis, not a preregistered confirmatory test).
Code: `analyses/post_audit/sci_r1_source_structure.py`. Seed `20261008`; 2,000 cluster-bootstrap replicates.

## Population and identity

- 663 resolved pairwise conflict records, 274 utterances (A–T 116, A–V 284, V–T 263), rebuilt from
  `evidence/emotiontalk/phase2_observed_responses.jsonl` + `manifests/emotiontalk/source_measurements.csv`.
- Row identity, outcome, order and scaled features match `frozen/source_model/publication_cv_records.json` row by row (|Δ| < 1e-9).
- Outcome: `y = 1` if the canonical modality-1 label was output (A in A–T/A–V, V in V–T). Evidence features are raw
  modality-1 minus modality-2 differences in source-label probability, normalized entropy and top1–top2 margin.
- Alignment check: the R1 M3a-aligned specification, unpenalized, with the historical fold seed `20260928`, gives AUROC 0.80180
  and log loss 0.53442. The published publication-CV M3a gives AUROC 0.80182 and log loss 0.53442, so the two agree.
- **R1_* models are diagnostic CV models. They do not replace, refit or rename the frozen M3a/M3b transfer models.**

## Design

- One shared utterance-grouped 5-fold split (seed 20261008) for all models. Speaker-grouped 5-fold is the sensitivity analysis
  (the `speaker_id` field has 19 levels).
- Standardization and all coefficients are estimated on training folds only.
- Primary fit: L2 logistic regression with C = 1, fixed before the analysis and not tuned. Unpenalized fits are reported as a sensitivity analysis.
- Label identity is coded antisymmetrically (Bradley–Terry style: +1 if the label belongs to modality 1, −1 if it belongs to modality 2,
  with `neutral` as the reference). Candidate position is coded as the position difference plus a "modality-1 label listed first" indicator.

| Model | Features |
|---|---|
| R1_M0 | pair |
| R1_M1 | pair + order (shared) |
| R1_M1x | pair × order |
| R1_M2 | M1 + label identity + candidate position |
| R1_M3 | M1 + srcprob + entropy + margin |
| R1_M3a-aligned | M1 + srcprob + entropy (original M3a spec) |
| R1_M4 / M4x | M2 (/ with pair × order) + evidence |
| R1_M5 | M1 + entropy only |
| R1_M6 / M6b | separate per-pair fits: order + evidence / order only |

## Results (utterance-grouped CV, L2 C=1, out-of-fold)

| Model | AUROC | Log loss | Brier | AUROC mean ± SD over 20 alternative splits |
|---|---:|---:|---:|---:|
| M0 pair | 0.501 | 0.693 | 0.250 | 0.482 ± 0.014 |
| M1 pair+order | 0.577 | 0.682 | 0.244 | 0.566 ± 0.006 |
| M1x pair×order | 0.583 | 0.676 | 0.242 | 0.575 ± 0.004 |
| M2 +label+position | 0.638 | 0.679 | 0.241 | 0.652 ± 0.013 |
| M3 +evidence | 0.801 | 0.537 | 0.182 | 0.803 ± 0.004 |
| M3a-aligned | 0.803 | 0.536 | 0.181 | 0.804 ± 0.003 |
| M4 M2+evidence | 0.795 | 0.552 | 0.187 | 0.804 ± 0.007 |
| M4x | 0.803 | 0.545 | 0.183 | 0.812 ± 0.008 |
| M5 entropy only | 0.803 | 0.535 | 0.181 | 0.806 ± 0.003 |
| M6 pair-specific evidence | 0.813 | 0.521 | 0.176 | 0.811 ± 0.003 |
| M6b pair-specific order only | 0.583 | 0.676 | 0.242 | 0.575 ± 0.004 |

Paired differences (utterance-cluster bootstrap 95% CI, `R1_PAIRED_UNCERTAINTY.csv`):

| Contrast | ΔAUROC [95% CI] | ΔLog loss [95% CI] |
|---|---|---|
| M3 − M1 | +0.223 [+0.169, +0.275] | −0.145 [−0.192, −0.093] |
| M5 (entropy only) − M1 | +0.226 [+0.170, +0.278] | −0.147 [−0.195, −0.095] |
| M4 − M2 | +0.156 [+0.110, +0.210] | −0.127 [−0.179, −0.077] |
| M3 − M2 | +0.163 [+0.108, +0.223] | −0.142 [−0.201, −0.087] |
| M4x − M1x | +0.220 [+0.169, +0.271] | −0.132 [−0.187, −0.073] |
| M2 − M1 | +0.061 [+0.000, +0.119] | −0.003 [−0.045, +0.042] |
| M3 − M5 | −0.002 [−0.006, +0.001] | +0.002 [−0.001, +0.005] |
| M6 − M3 | +0.012 [+0.001, +0.023] | −0.016 [−0.028, −0.003] |

Speaker-grouped CV (19 speaker clusters) gives the same answer. M3 − M1 ΔAUROC is +0.237 [+0.194, +0.270] and ΔLL is −0.152 [−0.186, −0.112].
M5 − M1 ΔAUROC is +0.241, and M4 − M2 ΔAUROC is +0.153 [+0.106, +0.194].
Pair-specific fitting (M6) gives a small extra gain over pooled M3 (+0.012 AUROC). Under speaker grouping its AUROC CI includes 0 ([−0.003, +0.024]). Unpenalized fits change no conclusion (M3 − M1 ΔAUROC is +0.222 [+0.167, +0.273]).

## Answers to the R1 questions

1. **Does evidence beat the order / label / position baseline?** Yes, by a large and stable margin. Adding evidence to M2
   raises AUROC by 0.16 and lowers log loss by 0.13 (CIs exclude 0). It does so under both utterance and speaker grouping and in every pair.
   Label identity and position help only modestly (M2 − M1: +0.06 AUROC, no log-loss gain). Adding them to the evidence model does not help: M4 is not better than M3.
2. **Is entropy alone sufficient?** Yes. M5 (pair + order + Δentropy) matches the full three-feature model
   (ΔAUROC −0.002 [−0.006, +0.001]). In the pooled full-data diagnostic GLM, Δentropy has a coefficient of −7.57 per unit, with an utterance-cluster 95% CI of −10.9 to −4.3.
   Source-probability and margin are not distinguishable from 0 given entropy, and their fold-wise signs flip. **Practically all incremental information is in the normalized-entropy difference:**
   the model tends to choose the modality whose own unimodal output was less uncertain.
3. **Is A–T weaker?** Yes. Pair-specific M3 − M1 AUROC gains are A–T +0.234 [+0.107, +0.348], A–V +0.270 and V–T +0.228. But A–T's
   log-loss gain is not established (−0.056 [−0.165, +0.069]). Absolute out-of-fold AUROC for M3 is A–T 0.69, A–V 0.79 and V–T 0.85.
   A–T has only 116 rows from 58 utterance pairs.
4. **Are coefficient signs stable across pairs?** The entropy direction is negative in all three pairs when entropy is fitted alone
   (A–T −5.5 [−9.1, −1.9]; A–V −6.3 [−8.2, −4.4]; V–T −7.5 [−9.3, −5.7]).
   With all three collinear evidence features in A–T, the entropy sign becomes unstable: 3/5 positive folds, and the full-fit CI spans 0. Source-probability and margin
   signs are not stable in any pair. The test of pair × evidence heterogeneity is not significant (cluster-robust Wald χ²₆ p = 0.12).
   **The order effect is clearly heterogeneous:** pair × order Wald p = 1.4e-4. A–T shows no order effect. A–V shows recency
   (order coef −0.58 [−0.99, −0.17]). V–T shows strong recency: the first-presented modality is chosen only 36% of the time in both orders (order coef −1.83).
5. **Is the result sensitive to speaker grouping?** No. Every conclusion holds under speaker-grouped CV, and point AUROCs change by less than 0.02.
   Caveat: `speaker_id` may be a within-dialogue code with only 19 levels, so the speaker-grouped analysis is coarse and possibly conservative.

## Interpretation limits

- The entropy feature is a **model-internal** uncertainty from the same Qwen model's unimodal pass. It is not an objective
  measure of emotional evidence strength, and the analysis is associational. It shows that the model's bimodal arbitration
  is predictable from its own unimodal confidence asymmetry. It does not show a causal mechanism.
- All R1 models are post-audit diagnostics on a source population already used to build the frozen models. The CV estimate
  is an honest out-of-sample estimate *within EmotionTalk*, not a transfer claim.

**R1 verdict: SUPPORTED.** Within the EmotionTalk source, there is stable, incremental predictive information beyond
pair, order, label and position, and it is carried almost entirely by the normalized-entropy difference. Two qualifications apply: A–T is weaker, and the order effect is pair-specific.
