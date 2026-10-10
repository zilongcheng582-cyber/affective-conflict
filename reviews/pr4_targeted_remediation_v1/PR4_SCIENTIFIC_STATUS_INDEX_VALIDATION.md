# PR #4 — Scientific status index validation (F02, F10)

## Status index

Location: `results/four_regime_structural_synthesis_v1/STATUS_AND_SUPERSESSION.md`, with machine twin `.json`; linked from `docs/RECOVERED_EVIDENCE_MIGRATION_V1.md`.

**Detection rule (enforced by the validator):** any migration-scope file outside provenance, tests and SHA256 manifests that contains `NEXT_STEP=<VALUE>`, `ONE_FINAL_QWEN_EXPERIMENT_REQUIRED`, `CPU_ANALYSIS_INCOMPLETE`, `QWEN_CAN_FREEZE_AND_MOVE_TO_NEXT_MODEL` or `SECOND_MODEL`, or whose name matches `QWEN_*DECISION|PRIORITY` or `EXECUTIVE_SUMMARY`, must appear in the index. **Result: 0 missing** (18 documents indexed).

| Status | Documents |
|---|---|
| CURRENT | `06_QWEN_NEXT_EXPERIMENT_DECISION.md`, `07_FINAL_SCIENTIFIC_EXECUTIVE_SUMMARY.md`, Transfer `RUN_PROVENANCE.json`, `PHASE4_COMPLETION_RECEIPT.json`, `FOUR_REGIME_SYNTHESIS_ERRATA_V2.json` |
| SUPERSEDED | `05_QWEN_GPU_EXPERIMENT_DECISION.md`, four-regime `06_SCIENTIFIC_SYNTHESIS_EXECUTIVE_SUMMARY.md`, `08_QWEN_GPU_EXPERIMENT_DECISION_V2.md`, `QWEN_GPU_PRIORITY_REVISED_V2.md` |
| HISTORICAL | four-regime 01/02/04/07; `HISTORICAL_EVIDENCE_RECONCILIATION_V2.md`; archived generators `finalize.py`, `verify.py`, `phase4_finalize.py` |
| CONDITIONAL | `04_RECOVERED_EVIDENCE_CROSS_STUDY_SYNTHESIS.md` (bounded-manuscript / second-model branch) |

Validator checks:
- Every CURRENT document that states a NEXT_STEP states the same value, `CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION`. ✅
- Every SUPERSEDED entry names an existing `superseded_by` target. ✅
- `gpu_authorized` = false. ✅
- The md and json list the same paths. ✅

**Current statement (verbatim intent):** this is a conditional research recommendation for explaining the Transfer measurement failure. It is:
- not a GPU authorization;
- not a claim that CA-MER 16-class measurement outranks every ERI1 follow-up control.

For ERI1 mechanism identification, the EmotionTalk consistent-sample control and the video reverse intervention keep independent value. Second-model replication remains CONDITIONAL for a bounded manuscript.

**Withdrawn or limited premises:**

| ID | Premise | Status | Errata reference |
|---|---|---|---|
| W1 | CA-MER A_ONLY/V_ONLY never executed | WITHDRAWN | errata[0] |
| W2 | MCR other three text conditions never run | LIMITED: native 4000 exist; controlled-protocol counterfactuals not run | errata[2] |
| W3 | 909 MCR items = 909 distinct audio files | WITHDRAWN: 905 unique audio hashes | errata[3] |
| W4 | LISTEN V3/V4 can be pooled | WITHDRAWN | errata[4] |
| W5 | CA-MER 16-class continuous probabilities exist | WITHDRAWN | errata[1] |
| W6 | A new Qwen GPU experiment is required | WITHDRAWN | 08 / QWEN_GPU_PRIORITY_REVISED_V2 / 06_QWEN_NEXT |

No historical report was edited. The new index does not choose a new hypothesis; it records the ordering already stated by the latest document in the PR.

## Claim–Evidence companion (F10)

`CLAIM_EVIDENCE_MATRIX_EVIDENCE_STATUS_V1.csv` has 25 rows matching the matrix ids. Claim statuses are unchanged (checked against the matrix), and `integration_analysis_origin` is still POST_HOC_EXPLORATORY for all rows.

| upstream_evidence_status | Rows | Upstream record in main |
|---|---|---|
| PREREGISTERED_CONFIRMATORY_FROZEN | X2 | `results/eri1_scientific_closure_v1/CLAIM_REGISTER_V1.md` (CONFIRMATORY_SUPPORTED) |
| POST_AUDIT_DIAGNOSTIC_NOT_PREREGISTERED | R1_SOURCE, R2_COMP | R1/R2 report headers ("not a preregistered confirmatory test") |
| FROZEN_ZERO_REFIT_METRIC_WITH_POST_AUDIT_BASELINE_COMPARISON | T_MCR_RANK, T_LISTEN, T_CA_SUPPORT, T_CA_MARGIN | `ZERO_REFIT_BASELINE_COMPARISON_V1.csv`; `SCIENTIFIC_CLAIM_STATUS_V1.md` ("not a hypothesis acceptance test") |
| POST_HOC_EXPLORATORY_OVER_FROZEN_PREDICTIONS | F_MCR_THRESHOLD, F_LISTEN_SELECTION, F_CA_ENTROPY, X1 | — |
| HISTORICAL_RECORD_OR_PRIOR_AUDIT_FINDING | M5, L4, C5 | — |
| HISTORICAL_DESCRIPTIVE_AGGREGATE_PLUS_POST_HOC_PROJECTION | M1 | — |
| POST_HOC_EXPLORATORY_ON_RECOVERED_OUTPUTS | other 10 | — |

Only X2 is `may_be_cited_as_confirmatory`, and only for the frozen ERI1 primary effect. No exploratory result was promoted. Every upstream file path cited in the companion exists (validator check).

Result: **CLAIM_STATUS_CONSISTENCY = PASS**.
