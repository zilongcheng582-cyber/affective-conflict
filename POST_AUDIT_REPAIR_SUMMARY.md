# Post-audit closeout summary

Two confirmed implementation defects are repaired: fixed scientific-success reporting and missing content-hash duplicate validation. Two evaluation issues are remediated: LISTEN mixed-condition estimand and missing source-fixed baseline comparison. Evidence/documentation/limitations are classified individually in docs/POST_AUDIT_REPAIR_V1.md.

The full corrected B3 row replay reproduces the frozen metrics, source coefficients/scalers, threshold and populations. 663 source analysis records are independently reconstructed from 2132 observed ordered responses plus unimodal source measurements. Phase3 derives all 402 prediction/outcome joins: 294 resolved, 268 correct, 108 unresolved; role is TWO_VS_ONE_PAIRWISE_TO_TRIMODAL_CONSISTENCY.

LISTEN 3C alone is 167/378 conflict rows (381 planned), AUROC 0.605732, BA 0.515460, log loss 0.981644; M0 log loss 0.697116. Pooled 518-row historical evaluation is preserved. M0+order is an explicitly post-audit source-only fit, never target fitted. Paired cluster intervals use fixed seed 20261008 and 2000 replicates. The source M3 models remain pooled shared-slope/order fits with pair-specific intercepts.

MCR actual WAV hashes confirm three groups/seven frozen samples including conflicting labels. Original 909 remain unchanged; duplicate-exclusion sensitivity is separate. MCR is later-added/exploratory relative to the early transfer declaration. Scientific ruling requires interpretation; the historical author's SURVIVES_WITH_CORRECTION remains immutable evidence.

Necessary predicted probabilities and observed responses are tracked in the private repository. Authorized reviewers can independently run CPU closeout; raw data/model acquisition and public access remain separate boundaries. No GPU, inference, calibration, target refit, frozen sample reselection, assignment regeneration, historical overwrite, force push, tag update or main merge occurs.

Actual validation and clean-checkout receipts are in POST_AUDIT_REPAIR_TEST_RESULTS.txt; current payload hashes are POST_AUDIT_REPAIR_MANIFEST_V1.json and POST_AUDIT_REPAIR_SHA256SUMS.txt. The old release manifests remain historical v1.0.0 receipts. Publication changes are a branch and PR only.
