# PR1 evidence anchor hardening V1

Scope: verifier, tests and documentation only. No GPU run, inference, refit, threshold or baseline change. The B3 evidence (6354 measurements, 5515 forwards), Phase2 and Phase3 observations, target populations and source parameters are unchanged.

## Gap closed

Before this change, `verify_evidence()` compared recovered evidence only with `evidence/EVIDENCE_MANIFEST_V1.json`, which the same PR supplied. Phase3 observed outputs were checked only through aggregate counts (402/294/268/108). An edit to an evidence file together with a regenerated manifest, or two compensating Phase3 label edits, could therefore pass.

## Anchors now enforced

`analyses/post_audit/replay.py:verify_evidence_anchors()` runs before any analysis in `python -m analyses.post_audit.replay` and in `python -m analyses.phase3.report`. There is no option to skip it; any failure raises before output is created.

| Check | Anchor | Pre-existing? |
|---|---|---|
| `B3_PREEXISTING_ANCHOR_CHECK` | `frozen/identity/corrected_output_catalog.json`, SHA256 `b696fb1d…e34c`, pinned in code, listed in v1.0.0 `RELEASE_MANIFEST_V1.json`, and compared with the blob at baseline commit `e597e6d` when Git history is present | Yes: committed in v1.0.0 (tag `v1.0.0`) |
| | Each of the nine shipped B3 files is re-hashed and compared with the catalog entry of the same filename. Both checksum lists shipped in `evidence/b3/` must also agree with the catalog. | |
| `PHASE3_PREEXISTING_ANCHOR` | `results/mainline_summary/phase3/EMOTIONTALK_PHASE3_LIMITED_INFERENTIAL_AUDIT_V1.json`, SHA256 `0ed5acb2…8961` (same three cross-checks), whose `authoritative_analysis_input_sha256` = `2ea12d5b…bb4` must equal the re-hashed `evidence/emotiontalk/phase3_original_merged_analysis.csv` | Yes: committed in v1.0.0 |
| `PHASE3_PROJECTION_BINDING` | Every `(utterance_id, tri_order)` row of `phase3_observed_outputs.jsonl` must equal the deterministic projection of the original merged row. The projection covers `raw_generation`, `parser_status`, `parsed_label`, the generation/parser execution flags, `observed_outcome_class`, `failure_type`, the modality labels, the majority/minority labels, the candidate sequence identity, `primary_key` and `actual_evidence_order`. Rows are joined by key, so row order is irrelevant. Historical `composition_correct`/`prediction_resolved` fields are never read. | Internal semantic binding to the anchored file |

Six catalogued execution artifacts are **not** released and are not treated as recovered: `B3_CORRECTED_EXECUTION_LOG.txt`, `B3_EXECUTION_RUNNER_PID.txt`, `B3_EXECUTION_TECHNICAL_AMENDMENT_001.json`, `B3_EXECUTION_VERIFIER_TECHNICAL_AMENDMENT_001.json`, `B3_FORWARD_RESULTS_V1.jsonl`, `B3_REMOTE_EXECUTION_MINIMAL_PREFLIGHT_V1.json`.
- If any of them appears in `evidence/b3/` without being declared recovered, the check fails.
- They are not needed for the CPU metric replay. Without them, the raw-runner → finalize projection step cannot be replayed.

`B3_RELEASE_EVIDENCE_SHA256SUMS.txt` and `historical_corrected_zero_refit_predictions.csv` were supplied after the audit and have no v1.0.0 anchor. They are reported as `post_audit_supplied_not_anchored`.

## Verification levels

| Level | What is established |
|---|---|
| Exact byte identity | The nine B3 files and the original merged Phase3 table equal SHA256 values committed in v1.0.0. |
| Semantic identity | The Phase3 and Phase2 observed-response projections are not original bytes. Phase3 is bound row by row to the anchored merged table. Phase2 must reconstruct the 663 frozen source records exactly (1e-12). |
| Floating-point tolerance | Replayed predictions and metrics are compared with absolute tolerance 1e-12. A Linux replay differs from the Windows-sealed results by at most 2.2e-16, and the line endings differ (LF vs CRLF). This is numerical agreement, not byte identity. |
| Historical anchor | Anchors prove that the evidence has not changed since the v1.0.0 commit. They do not authenticate the original GPU run beyond what that release recorded. |
| Independent CPU metric reproduction | The corrected B3 metrics, Phase3 268/294 with 108 unresolved, the LISTEN 3C metrics and the source M0 baseline are reproduced by `python -m analyses.post_audit.replay` on a clean checkout. |

## Regression tests

`tests/test_evidence_anchors.py`:
- **Test A:** a B3 edit with an updated post-audit manifest still fails. So does an edit with the catalog and the v1.0.0 receipt both rewritten.
- **Test B:** two Phase3 label edits that keep 268 correct fail the binding.
- **Test C:** shuffled row order passes.
- **Test D:** an edit to `raw_generation` that parses to the same label fails, as does an edit to any other bound field.
- **Test E:** a missing or altered merged table, an altered recorded anchor, a missing recovered B3 file, or an unreleased/uncatalogued B3 file all fail.
- **Entry point:** the replay entry point refuses to run (and creates no output) when an anchor fails.

Results: `results/post_audit/anchor_hardening_v1/`.
