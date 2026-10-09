# ANALYSIS PLAN V1 — EMOTIONTALK_RELIABILITY_INTERVENTION_V1

Locked before any GPU execution. Implementation: `src/emotiontalk/reliability_v1/analyze.py`, which is SHA256-frozen in `DESIGN_FREEZE_RECORD_V1.json`.
The script has been exercised only on clearly labelled SYNTHETIC data (`--synthetic-dry-run`). Pilot records are refused by the script.

## 1. Notation and population

- Items i = 1..146, all eligible items. This is an **intention-to-treat** analysis, and the denominator never changes.
- Conditions c ∈ {CLEAN, RECODE, SNR20, SNR10, SNR00}. Orders o ∈ {A_THEN_V, V_THEN_A}.
- Joint outcome for item i, condition c, order o: SIDE_A (output = y_A), SIDE_V (output = y_V), OTHER, or PARSE_FAIL. **All four are retained.**
- Y_A(i,c,o) = 1 if SIDE_A, else 0. Here OTHER and PARSE_FAIL count as "not audio-side".
- H_A(i,c) is the audio-only normalized entropy, with primary probabilities from softmax(mean-token log-probability), as in Phase1. H_V(i) is the video-only entropy (CLEAN).
- The population is never redefined by post-intervention readability, resolution or parse status.

## 2. Hypotheses

- **H1 (primary, behavioural causal effect).** Degrading the audio lowers the probability that the joint output is the audio-side label.
  Expected sign: **negative**.
- **H0.** E[Y_A(SNR00)] − E[Y_A(RECODE)] = 0.
- Manipulation hypothesis (S1). Degrading the audio raises audio-only normalized entropy. Expected sign: positive.

## 3. Primary endpoint and test

For each item, D_i = mean over the two orders of Y_A(i, SNR00, o), minus mean over the two orders of Y_A(i, RECODE, o).
The estimand is the mean of D_i over all 146 eligible items.

- CI: item-level nonparametric bootstrap, percentile 95%, 10,000 replicates, seed 20261009.
- Test: two-sided paired sign-flip randomization test on D_i, 100,000 random flips.
- **H1 is SUPPORTED iff the CI upper bound is < 0 and p < 0.05.**
- RECODE, not CLEAN, is the reference, so the contrast differs only by the added noise. The two conditions share the same read, mono, 16 kHz and float-WAV pipeline.

Power, stated only as a planning heuristic: the historical CLEAN item-level SIDE_A mean is 0.43 (SD 0.44). For SD(D) between 0.35 and 0.55, the 80%-power
minimum detectable |mean D| at α = 0.05 is about 0.08–0.13. There is a floor: 69 of 146 items had no historical SIDE_A response, which limits how far the rate can fall.

## 4. Secondary endpoints

Confirmatory secondary family S1–S5 is Holm-adjusted together.

| ID | Endpoint | Method | Expected |
|---|---|---|---|
| S1 | Δ audio-only entropy, SNR00 − RECODE (manipulation check) | item bootstrap CI + sign-flip p | > 0 |
| S2 | Dose–response over RECODE < SNR20 < SNR10 < SNR00 (ordinal 0–3) | GEE logistic, binomial, exchangeable, item clusters: Y_A ~ level + A_first + level×A_first; Wald on `level` | level coef < 0 |
| S3 | Δ SIDE_V rate, SNR00 − RECODE | as primary | > 0 |
| S4 | Δ OTHER+PARSE_FAIL rate, SNR00 − RECODE | as primary | two-sided, no direction |
| S5 | Order interaction: D(A_THEN_V) − D(V_THEN_A) | item bootstrap + sign-flip | two-sided, no direction |

Further secondary or descriptive endpoints (not in the Holm family):
- **S6**, pipeline control. RECODE − CLEAN differences in SIDE_A rate and in audio-only entropy, with CIs. Expected near 0, reported descriptively.
- **S7**, magnitude check. A frozen external prediction from R1 (AV pair-specific diagnostic fit: intercept 0.14389, A-first −0.58096, Δentropy(A−V) −6.31217)
  is evaluated at the measured H_A(RECODE), H_A(SNR00) and H_V for each item and order. The predicted mean ΔP(SIDE_A) is compared with the primary CI.
  "Predicted value outside the observed CI" means the observational coefficient does not transport to the intervention.
- **S8**, exploratory. Spearman correlation between item ΔH_A and D_i. This is **associational only, not mediation**.
- **SEC-joint-continuous.** The teacher-forced joint probability of the audio-side label, SNR00 − RECODE, with item bootstrap.
- **SEC-conditional-binary.** The share of SIDE_A among SIDE_A + SIDE_V per condition. This is **conditional, explicitly labelled, and never the primary**.
- Full outcome accounting: condition × order × {SIDE_A, SIDE_V, OTHER, PARSE_FAIL, TECHNICAL_FAILURE}, and audio-only accuracy (output = y_A) per condition.

## 5. Missingness and technical-failure policy

- One identical re-execution is allowed for technically failed trials. The latest attempt is analysed, and all attempts are reported.
- **Residual joint technical failures:** in the primary analysis they are imputed as Y_A = 1, which counts against H1. A complete-case sensitivity analysis is also reported.
- **Residual audio-only failures:** H_A(c) is imputed equal to H_A(RECODE), making ΔH = 0 and counting against S1. Complete-case sensitivity is reported.
- PARSE_FAIL and OTHER are outcomes. Sensitivity: the primary is recomputed with PARSE_FAIL counted as SIDE_A, the conservative direction.
- If residual technical failures exceed 5% of joint trials, the primary result is reported with a TECHNICAL_RISK flag and the analysis is not re-run.

## 6. Decision and falsification rules

These rules are applied mechanically by `analyze.decide`:

| Result | Condition |
|---|---|
| **H1_SUPPORTED** | primary CI upper < 0 and p < 0.05 |
| **H1_CONTRADICTED_OPPOSITE_DIRECTION** | primary CI lower > 0 |
| **H1_DISCONFIRMED** | S1 CI lower > 0 (entropy rose) **and** primary CI lower > −0.05 (any reduction in audio-side choice is bounded to under 5 points) |
| **H1_NOT_SUPPORTED** | otherwise |
| Manipulation failure | S1 CI lower ≤ 0. The entropy link is uninterpretable, but the behavioural result is still reported as is. |
| **Entropy up, choice not in predicted direction** | S1 CI lower > 0 and primary CI upper ≥ 0. This is explicitly counted as **evidence against the core hypothesis**. |
| Magnitude inconsistency | S7 predicted value outside the primary CI. Reported as evidence that the observational relation does not transport quantitatively. |

No result of this experiment will be described as showing that entropy **mediates** arbitration. Entropy, choice and other input properties change
together under one intervention. A positive H1 shows that **input reliability causally affects arbitration**. S1/S7/S8 then describe whether that
effect is *consistent with* the R1 entropy relation.

## 7. Multiple comparisons

There is one primary test at α = 0.05, two-sided. S1–S5 are Holm-adjusted as one family. Everything else is descriptive or exploratory, labelled as such, and unadjusted.

## 8. Not allowed

- Changing the noise levels, noise type, population, reference condition or endpoints after the pilot or after seeing any outcome.
- Dropping items or trials because of OTHER, PARSE_FAIL or readability under degradation.
- Analysing the pilot scientifically, or pooling it with the full run.
- Re-fitting R1 or any frozen transfer model. S7 uses the fixed coefficients above.
