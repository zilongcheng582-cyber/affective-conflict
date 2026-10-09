# PRE-EXECUTION AMENDMENT 001 — ERI1 analysis plan

- Date: 2026-10-09. The amendment was made **before any media binding, pilot or GPU execution**. No intervention data exist, so no outcome could have
  informed this change.
- Original design freeze: commit `2419be327931be11d66cc7e124198f05873c05a3`. Original `DESIGN_FREEZE_RECORD_V1.json` SHA256:
  `2215b0c566c052f370441ca1753e7f66b4e793cc718724afcee76496ce5fd3a7`.
- Scope: `src/emotiontalk/reliability_v1/analyze.py`, `ANALYSIS_PLAN_V1.md` (§4 S7, §5, §6), `tests/test_reliability_v1.py`, and the freeze record.
- **Unchanged:** population (146 items), pilot items (6), conditions and SNR levels (CLEAN, RECODE, 20/10/0 dB), primary hypothesis and endpoint
  (ITT D_i = SNR00 − RECODE in the SIDE_A rate), secondary endpoint definitions, the trial manifest (`FROZEN_TRIAL_MANIFEST_V1.csv`, SHA256 `09a755ac…`),
  the eligibility table, the audio specification, the runner and all historical files.

## Change 1 — directional conservative handling of residual technical failures

**Problem.** The frozen rule imputed Y_A = 1 for every residual joint technical failure. For D_i = Y_A(SNR00) − Y_A(RECODE), a failure in the
**RECODE** reference filled with 1 lowers D_i. That moves the estimate toward the hypothesised negative effect, so a failing reference could
manufacture support for H1. The audio-only entropy rule had a similar but smaller issue: a missing H_A(RECODE) was filled from the cross-item mean, which could create a ΔH in S1's favour.

**Fix.**
- Residual failures are kept as missing (complete case) and filled only through condition-directional maps:
  - Y_A (primary, S2): RECODE/SNR20 → 0 and SNR10/SNR00 → 1.
  - Y_V (S3): the mirror image.
  - Two-sided endpoints (S4, S5) and descriptive endpoints: complete case.
- S1: if either cell is missing, the item's ΔH = 0.
- Reported in addition: complete case, the H1-favourable mirror bound, the PARSE_FAIL-as-SIDE_A sensitivity, both S4 bounds, and a flag for whether the
  complete-case direction agrees with the primary.
- Verdict-specific bounds: support for H1 is judged on the conservative bound. Contradiction and disconfirmation must also hold on the
  H1-favourable bound. No verdict can therefore come from imputation alone.
- Empty complete-case sets give NaN or "not evaluable" instead of an error or a coerced 0.

**Verification.** New CPU tests construct data with no true effect (always SIDE_V) and a 100% failure rate in RECODE, or in SNR00.
The primary estimate is ≥ 0, H1 is never supported, and no contradiction verdict is produced. Under the old rule the RECODE case gave D = −1.
Another test checks that a true effect is recovered with coinciding bounds when there are no failures.

## Change 2 — scope of S7

**Problem.** The R1 coefficients used by S7 were estimated only on binary-resolvable source records (SIDE outcomes), so they model
P(audio side | a side was chosen). The ERI1 primary endpoint is ITT and counts OTHER and PARSE_FAIL as not-audio-side. The frozen plan compared the S7
prediction with the primary CI and used the result in the decision output (`magnitude_consistent_with_R1`). That treated a conditional model as a quantitative validation of an
unconditional causal effect.

**Fix.** S7 is renamed `S7_EXPLORATORY_CONDITIONAL_R1_REFERENCE`.
- It shows the R1-predicted change next to the observed change in the **conditional binary share** P(SIDE_A | SIDE_A or SIDE_V) only (complete case, item bootstrap),
  labelled with its caveats.
- It has no pass/fail criterion, it is removed from `decide()`, and it is never compared with the ITT primary.
- It is never evidence of mediation. The conditioning set is itself affected by the intervention.

## Effect on execution assets

None. The manifest, eligibility table, binding procedure, runner, pilot gates and GPU plan are byte-identical to the original freeze.
`run.py` checks only the manifest SHA256 and the design inputs, and these are unchanged. `DESIGN_FREEZE_RECORD_V1.json` is re-issued with updated hashes
for the amended files. It carries an `amendments` entry that points to this document and to the original record's SHA256.
