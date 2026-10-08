# Post-audit repair V1

Baseline main commit: e597e6de0a488f803709498cc9905289d9768c6c. Remote main/tag were checked before branching and had not advanced. Branch: fix/post-audit-mainline-closure-v1. Original main, tag v1.0.0, ZIPs, AutoDL project and historical outputs remain unchanged. The repository remains private and code remains MIT.

All added CPU outputs are POST_AUDIT_REANALYSIS under results/post_audit/closure_v1. No GPU inference, Qwen run, target refit, scaler fitting, calibration, threshold optimization, sample reselection or assignment regeneration occurred. The only new fit is diagnostic M0+order on the verified 663 source resolved-conflict records; it uses the historical unpenalized source Newton/IRLS algorithm and is not labeled predeclared.

The release already included torch>=2.8,<3. Python 3.12 was retained. Host pytest temp-directory permission failure was resolved with a new writable basetemp, without changing scientific code. This is not counted as a confirmed implementation defect.

## PA01 — EVALUATION_ESTIMAND_BUG

Root cause: Mixed LISTEN conditions were labeled as arbitration evidence.

Original behavior: 518 pooled evaluated rows combined text-only, audio-only and joint trials.

Fixed behavior: Historical pooled metrics preserved; 3C-only 167/378 and separate 3A/3B diagnostics added.

Files: analyses/post_audit/replay.py; README.md; LISTEN reports.

Validation: test_listen_joint_excludes_both_single_modality_conditions; test_listen_joint_denominator_and_scientific_identities.

Scientific impact: Changes estimand labeling; frozen population remains unchanged.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.

## PA02 — MISSING_ANALYSIS

Root cause: Declared source-fixed constant baseline absent from target evaluation.

Original behavior: Only transferred model metrics were shown.

Fixed behavior: Frozen M0 and source-only diagnostic M0+order compared on identical target rows with paired cluster CIs.

Files: analyses/post_audit/replay.py; SOURCE_BASELINE_BINDING_V1.json; baseline comparison.

Validation: test_m0_binds_frozen_source_parameters_and_rejects_target_fit; test_baseline_cannot_fit_changed_or_target_records; test_target_prediction_never_calls_fit_or_calibration.

Scientific impact: Makes source-baseline probability performance explicit; no target fitting or model selection.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.

## PA03 — IMPLEMENTATION_BUG

Root cause: Report finalized a fixed success ruling without a scientific decision rule.

Original behavior: Always emitted SURVIVES_WITH_CORRECTION and fixed interpretation prose.

Fixed behavior: Computed metrics retained; SCIENTIFIC_RULING=REQUIRES_INTERPRETATION; old author judgment explicitly labeled.

Files: src/cross_regime/zero_refit/evaluate.py; analyses/cross_regime/report.py.

Validation: test_scientific_ruling_is_not_unconditional_success; test_changed_predictions_change_reported_metrics.

Scientific impact: Removes unsupported code-certified scientific acceptance; numerical results unchanged.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.

## PA04 — IMPLEMENTATION_BUG

Root cause: Path-based duplicate classification did not validate identical WAV bytes at different paths.

Original behavior: Different file paths could conceal content duplicates and conflicting GT.

Fixed behavior: Streaming content-hash validator and warning report; historical selector unchanged; separate sensitivity excludes all seven affected IDs.

Files: src/reconstruction/mcr/content_duplicates.py; reconstruct.py; MCR reports.

Validation: test_different_paths_same_bytes_flag_conflicting_gt; test_different_paths_same_bytes_same_gt_are_still_duplicates.

Scientific impact: Flags 3 groups/7 records including conflicting labels; original 909 population intact.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.

## PA05 — DOCUMENTATION_ERROR

Root cause: Pair routing could imply pair-specific source slopes/order coefficients.

Original behavior: Pooled transfer was insufficiently distinguished from pair-specific models.

Fixed behavior: Explicit pair-specific intercepts and shared slopes/order coefficient.

Files: README.md; docs/KNOWN_LIMITATIONS.md; docs/SCIENTIFIC_CLAIM_STATUS_V1.md.

Validation: test_frozen_source_binding_and_unmodified_metric_equations; source binding inspected.

Scientific impact: No frozen M3 coefficients or source scaler changes.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.

## PA06 — RELEASE_EVIDENCE_GAP

Root cause: Only catalogs/minimal prepared records/summary readers were available.

Original behavior: Independent target and Phase3 row-level replay needed inaccessible external outputs.

Fixed behavior: 6354 measurement/5515 forward rows, 2132 responses, 402 observed trimodal outputs and hashes supplied; replay derives metrics and correct identities.

Files: evidence/; ARTIFACT_RECOVERY_MATRIX_V1.csv; analyses/post_audit/replay.py; analyses/phase3/report.py.

Validation: test_missing_or_changed_evidence_fails_closed; test_source_reconstructed_from_observed_responses; test_phase3_independent_observed_join_counts; full clean replay.

Scientific impact: Closes authorized-reviewer CPU evidence gap; no public or raw-media closure claimed.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.

## PA07 — SCIENTIFIC_LIMITATION

Root cause: Primary Phase3 population is TWO_VS_ONE only.

Original behavior: 268/294 described broadly as compositionality.

Fixed behavior: Report scoped to TWO_VS_ONE_PAIRWISE_TO_TRIMODAL_CONSISTENCY with all unresolved identities.

Files: Phase3 row report; README.md; claim status.

Validation: test_phase3_independent_observed_join_counts; test_phase3_duplicate_or_missing_join_fails; test_phase3_changed_observed_label_changes_correct_identity.

Scientific impact: Does not establish ALL_DIFFERENT or general three-modality compositionality.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.

## PA08 — DOCUMENTATION_ERROR

Root cause: MCR was not in the earlier declared transfer mapping.

Original behavior: Historical primary role could be mistaken for early confirmatory role; cross-dataset ranking prose overreached.

Fixed behavior: Later-added/exploratory chronology explicit; preserve completed-protocol primary metrics; remove common-mechanism ranking claim.

Files: protocols/emotiontalk/CROSS_REGIME_TRANSFER_SPEC_V1.json; evidence/provenance/CROSS_REGIME_ZERO_REFIT_SPEC_V1.json; docs.

Validation: Direct early/later specification inspection; source/frozen regressions.

Scientific impact: Corrects scientific role without changing dataset or completed-protocol metric definition.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.

## PA09 — SCIENTIFIC_LIMITATION

Root cause: LISTEN 3C uses only A_THEN_T.

Original behavior: Order effect could be inferred from condition-specific performance.

Fixed behavior: Explicit no counterbalanced order-effect identification from 3C.

Files: LISTEN_JOINT_ONLY_REPORT.csv; claim status.

Validation: test_listen_joint_denominator_and_scientific_identities.

Scientific impact: Records identifiability boundary; no new order trials.

Historical results modified: NO. Scientific population changed: NO for the frozen mainline; all new subsets are separately labeled diagnostics. Evidence status: RECOVERED_AND_ROW_VERIFIED; raw-media permissions remain an access boundary.


## Counts and decision status

Confirmed implementation defects fixed: 2 (PA03/PA04). Evaluation issues remediated: 2 (PA01 estimand and PA02 missing baseline comparison). Release/documentation/limitations are separately classified above. No executable scientific acceptance rule was declared, so the new report requires interpretation. Old report numbers and author interpretation remain immutable evidence.

## Verification

See POST_AUDIT_REPAIR_TEST_RESULTS.txt for actual clean-checkout test/environment/replay results, POST_AUDIT_REPAIR_MANIFEST_V1.json for current payload identities, ARTIFACT_RECOVERY_MATRIX_V1.csv for recovery identity and publication eligibility, and EVIDENCE_MANIFEST_V1.json for original versus projection hashes. Required CSV filenames are present under results/post_audit/closure_v1. The old release manifest is a historical receipt, not a current-payload assertion.
