# STATUS AND SUPERSESSION — four-regime synthesis and later decisions

Navigation metadata added by PR4 Targeted Remediation V1 (review finding F02). **No historical report in this directory or elsewhere was edited**; every superseded version is retained byte-for-byte. Machine-readable twin: `STATUS_AND_SUPERSESSION.json` (the two must list the same documents).

## Current research state (single source of truth)

**NEXT_STEP = CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION** — source: `results/recovered_evidence_scientific_analysis_v1/06_QWEN_NEXT_EXPERIMENT_DECISION.md`.

Nature: `CONDITIONAL_RECOMMENDATION_NOT_AUTHORIZATION`. Objective scope: Explaining the frozen Transfer measurement failure only. GPU authorized: **no**.

- Not a GPU execution authorization and not an approval of any acquisition.
- Does not assert that CA-MER 16-class continuous measurement is scientifically more important than every ERI1 follow-up control.
- If the objective is ERI1 mechanism identification, the EmotionTalk consistent-sample control and the video reverse intervention retain independent value (see 08_QWEN_GPU_EXPERIMENT_DECISION_V2.md candidates B/C, historical rationale retained).
- For a bounded descriptive manuscript, stopping further Qwen acquisition and second-model replication (SECOND_MODEL_WITHOUT_ADDITIONAL_QWEN) remains a CONDITIONAL alternative for a different objective.

## Supersession chain for Qwen / GPU decisions

`05_QWEN_GPU_EXPERIMENT_DECISION.md` (V1, ONE_FINAL_QWEN_EXPERIMENT_REQUIRED) → `08_QWEN_GPU_EXPERIMENT_DECISION_V2.md` (Revision V2, CPU_ANALYSIS_INCOMPLETE; archive premises now outdated) → `../historical_evidence_reconciliation_v2/QWEN_GPU_PRIORITY_REVISED_V2.md` (post-recovery correction) → `../recovered_evidence_scientific_analysis_v1/06_QWEN_NEXT_EXPERIMENT_DECISION.md` (post-Transfer-Phase4, **CURRENT**, conditional).

## Document status register

| path | status | decision value | superseded by | note |
|---|---|---|---|---|
| `results/four_regime_structural_synthesis_v1/05_QWEN_GPU_EXPERIMENT_DECISION.md` | SUPERSEDED | ONE_FINAL_QWEN_EXPERIMENT_REQUIRED | `results/four_regime_structural_synthesis_v1/08_QWEN_GPU_EXPERIMENT_DECISION_V2.md` | Historical first decision; already carries its own superseded banner. |
| `results/four_regime_structural_synthesis_v1/06_SCIENTIFIC_SYNTHESIS_EXECUTIVE_SUMMARY.md` | SUPERSEDED | ONE_FINAL_QWEN_EXPERIMENT_REQUIRED (headline); banner defers to 08 | `results/recovered_evidence_scientific_analysis_v1/06_QWEN_NEXT_EXPERIMENT_DECISION.md` | Its banner points to 08, which is itself superseded for the decision; withdrawn premises W1, W2, W6 appear here. |
| `results/four_regime_structural_synthesis_v1/08_QWEN_GPU_EXPERIMENT_DECISION_V2.md` | SUPERSEDED | CPU_ANALYSIS_INCOMPLETE | `results/recovered_evidence_scientific_analysis_v1/06_QWEN_NEXT_EXPERIMENT_DECISION.md` | Revision V2. Archive-access premises (archive inaccessible; A_ONLY/V_ONLY not obtained) are now outdated (W1). Its identification-value discussion of ERI1 candidates B/C is retained as HISTORICAL rationale; its 'do not run CA-MER 16-class now' ranking is replaced by the later conditional ordering. |
| `results/four_regime_structural_synthesis_v1/07_REVISION_V2_VERIFICATION_AND_ERRATA.md` | HISTORICAL | — | `results/historical_evidence_reconciliation_v2/FOUR_REGIME_SYNTHESIS_ERRATA_V2.json` | V2 verification remains valid except the archive-dependent statements about A_ONLY/V_ONLY (W1). |
| `results/four_regime_structural_synthesis_v1/04_CLAIM_EVIDENCE_MATRIX.md` | HISTORICAL | per-claim GPU column | `results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX.csv` | Four-regime claim matrix; per-claim GPU needs reflect pre-recovery evidence state. |
| `results/four_regime_structural_synthesis_v1/02_WITHIN_DATASET_STRUCTURAL_ANALYSIS.md` | HISTORICAL | — | `results/historical_evidence_reconciliation_v2/FOUR_REGIME_SYNTHESIS_ERRATA_V2.json` | Contains withdrawn premises W1 (line 178) and W2 (line 95). |
| `results/four_regime_structural_synthesis_v1/01_FOUR_DATASET_EVIDENCE_INVENTORY.md` | HISTORICAL | refers to 05 GPU decision | `results/historical_evidence_reconciliation_v2/HISTORICAL_EVIDENCE_RECONCILIATION_V2.md` | Pre-recovery repository-only inventory. |
| `results/historical_evidence_reconciliation_v2/QWEN_GPU_PRIORITY_REVISED_V2.md` | SUPERSEDED | CPU first; no additional Qwen GPU; CA-MER 16-class conditional and lower priority | `results/recovered_evidence_scientific_analysis_v1/06_QWEN_NEXT_EXPERIMENT_DECISION.md` | Post-recovery correction. Its factual corrections (A/V executed, 3000 A/V generations need not be repeated, 16-class scores not saved) remain valid; its priority ordering is replaced after Phase4. |
| `results/historical_evidence_reconciliation_v2/HISTORICAL_EVIDENCE_RECONCILIATION_V2.md` | HISTORICAL | section D GPU priority (same as QWEN_GPU_PRIORITY_REVISED_V2.md) | `results/recovered_evidence_scientific_analysis_v1/06_QWEN_NEXT_EXPERIMENT_DECISION.md` | Reconciliation facts remain the record; section D priority superseded. |
| `results/historical_evidence_reconciliation_v2/FOUR_REGIME_SYNTHESIS_ERRATA_V2.json` | CURRENT | — | — | Errata of record for W1-W5. |
| `results/recovered_evidence_scientific_analysis_v1/06_QWEN_NEXT_EXPERIMENT_DECISION.md` | CURRENT | NEXT_STEP = CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION | — | Conditional recommendation for the Transfer-failure objective; not an authorization. |
| `results/recovered_evidence_scientific_analysis_v1/07_FINAL_SCIENTIFIC_EXECUTIVE_SUMMARY.md` | CURRENT | mirrors 06_QWEN_NEXT | — | Summary consistent with the current conditional recommendation. |
| `results/recovered_evidence_scientific_analysis_v1/04_RECOVERED_EVIDENCE_CROSS_STUDY_SYNTHESIS.md` | CONDITIONAL | SECOND_MODEL superseded for transfer explanation; bounded-manuscript alternative | — | Alternative objective branch, not the current Transfer-failure step. |
| `results/transfer_failure_integration_v1/RUN_PROVENANCE.json` | CURRENT | NEXT_STEP = CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION; bounded_manuscript_alternative = SECOND_MODEL_WITHOUT_ADDITIONAL_QWEN (CONDITIONAL) | — | Machine mirror of the current recommendation. |
| `results/transfer_failure_integration_v1/PHASE4_COMPLETION_RECEIPT.json` | CURRENT | NEXT_STEP = CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION | — | Machine mirror of the current recommendation. |
| `analyses/recovered_evidence_scientific_analysis_v1/finalize.py` | HISTORICAL | NEXT_STEP = SECOND_MODEL (pre-Phase4 generator) | `analyses/transfer_failure_integration_v1/phase4_finalize.py` | Archived generator of the pre-Phase4 report version (held on AutoDL as phase4_before_update); do not execute. |
| `analyses/recovered_evidence_scientific_analysis_v1/verify.py` | HISTORICAL | checks NEXT_STEP == SECOND_MODEL (pre-Phase4) | `analyses/transfer_failure_integration_v1/phase4_finalize.py` | Archived pre-Phase4 verifier; do not execute. |
| `analyses/transfer_failure_integration_v1/phase4_finalize.py` | HISTORICAL | generator of the current NEXT_STEP text | — | Archived generator code; do not execute (appends AutoDL navigation docs). |

## Withdrawn or limited historical premises

Errata of record: `../historical_evidence_reconciliation_v2/FOUR_REGIME_SYNTHESIS_ERRATA_V2.json`.

| id | historical premise | status | current fact | reference |
|---|---|---|---|---|
| W1 | CA-MER controlled A_ONLY/V_ONLY were never executed / not obtained | WITHDRAWN | Executed: A_ONLY 1499/1500 usable (1 parse fail), V_ONLY 1442/1500 usable (58 OOM); discrete labels only | `FOUR_REGIME_SYNTHESIS_ERRATA_V2.json[0]` |
| W2 | MCR other three text conditions (neutral/faithful/irrelevant) were never run | LIMITED | Native 1000x4 = 4000 outputs exist; controlled-protocol counterfactual text conditions were indeed not run | `FOUR_REGIME_SYNTHESIS_ERRATA_V2.json[2]` |
| W3 | 909 MCR items represent 909 distinct audio byte contents | WITHDRAWN | 909 paths / 905 unique audio SHA256, including one three-item conflicting-GT group | `FOUR_REGIME_SYNTHESIS_ERRATA_V2.json[3]` |
| W4 | LISTEN V3 and V4 can be pooled directly | WITHDRAWN | 1149/1149 source identities match but 0 candidate orders and 0 prompt hashes match; pooling not allowed | `FOUR_REGIME_SYNTHESIS_ERRATA_V2.json[4]` |
| W5 | CA-MER 16-class continuous probabilities exist or can be recovered from generation outputs | WITHDRAWN | Runner saved generated labels only; 16-class vectors were never measured; 7-class B3 scores are not a substitute | `FOUR_REGIME_SYNTHESIS_ERRATA_V2.json[1]` |
| W6 | One final new Qwen GPU experiment is required | WITHDRAWN | No GPU run is required to report present evidence; any acquisition needs a separate CPU design freeze and explicit authorization | `08_QWEN_GPU_EXPERIMENT_DECISION_V2.md; QWEN_GPU_PRIORITY_REVISED_V2.md; 06_QWEN_NEXT_EXPERIMENT_DECISION.md` |

Status vocabulary: CURRENT (governs now), SUPERSEDED (decision replaced; text retained), HISTORICAL (record retained; not a current decision), CONDITIONAL (applies only to a different, explicitly named objective).
