# PR #4 Remediation V1 — Regression Test Report

Environment: Claude Code cloud container (not AutoDL), Linux 6.18.44 x86_64, Python 3.13.16, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, pytest 9.0.3. No torch, no GPU, no AutoDL assets. Unless stated otherwise, every item ran on a fresh clone of `f53d245`, the exact remote head.

| # | Check | Command / script | Result | Log |
|---|---|---|---|---|
| 1 | All migration SHA256 | `validate_migration.py` + `review_scripts/r01_integrity.py` | PASS: 264/264 migration entries; package manifests 52/68/31 with 0 missing and 0 mismatches | `logs/v_fresh.json`, `logs/r01_new.json` |
| 2 | Main frozen files unchanged | validator `check_base_unchanged` | PASS: 324/324 base blobs unchanged; 0 checkout drift (autocrlf=false) | `logs/v_fresh.json` |
| 3 | Allowlist vs actual files | validator + r01 | PASS: 222 rows, 16,358,604 B (recorded = allowlist = actual = Git blob) | same |
| 4 | 18 Transfer groups, independent replay | `r06_transfer_replay.py` | PASS: error 0.0 vs PR table and vs main frozen table; output JSON identical to the pre-fix review | `logs/r06_transfer_replay_new.*` |
| 4b | 116 Phase4 subgroups | `r07_subgroup_replay.py` | 115/116 match; the remaining 1 cannot be reconstructed by the reviewer script (same as pre-fix) | `logs/r07_*` |
| 5 | MCR/LISTEN/CA-MER populations and denominators | `r03`/`r04`/`r05`/`r08` | PASS: outputs identical to the pre-fix review | `logs/r0*_new.json` |
| 6 | Claim–Evidence Matrix (6 categories / 25 claims) + companion | validator `check_claims`, new test | PASS | — |
| 7 | Existing 36 evidence tests | `pytest tests/test_post_audit_closure.py tests/test_evidence_anchors.py` | **36 passed** | `logs/test_36.txt` |
| 8 | 29 independent-review tests | `PR4_CHECKOUT=<fix> pytest review_tests_v2` | **29 passed** | `logs/review_tests_v2.txt` |
| 9 | `python -O` + corrupted fixture | new tests (tamper with and without -O, missing file, manifest mismatch, unlisted file, modified main file) | All return **FAIL with non-zero exit**; PASS is never printed | `logs/test_new.txt` |
| 10 | Newline sensitivity | autocrlf=false clone and autocrlf=true clone | Both PASS: migration 264/264 under both; under autocrlf=true, 231 main files show informational checkout drift but 324/324 are identical at object level | `logs/v_crlf.json`, `logs/r01_crlf.json` |
| 11 | Static parse / import safety | validator AST parse (38 files); `-B` import of the validator in an empty directory | PASS; validator contains 0 `assert` | — |
| 12 | Security / authorization | secret/email/personal-path scan of the 18 changed files; retained-text rescan | PASS: no findings; the set of retained public text is unchanged; new files contain only authored metadata; the F06 register stores hashes, not text | `logs/text_scan_new.txt` |
| 13 | Four-regime reproducibility | `python -m analyses.four_regime_synthesis_v1.run_all` in a clone | 61 science outputs byte-identical; only RUN_PROVENANCE_V2 and OUTPUT_MANIFEST_V2 differ (as before) | `logs/four_regime_replay_new.stdout` |
| 14 | New repository regression tests | `pytest tests/test_pr4_migration_regressions.py` | **16 passed** (local and on the remote clone) | `logs/test_new.txt` |
| 15 | Remote independent checkout | clone from GitHub, `pull/4/head` = f53d245 | Validator PASS (also under `-O`); 16+36 = **52 passed** | `logs/v_remote*.json` |

## Converted review tests

The original review tests that proved defects were rewritten so they now assert the defect is gone:
- `test_single_class_validate_migration_crashes` → `..._reports_undefined`
- `test_validator_reports_pass_on_corruption_under_python_O` → `test_validator_fails_on_corruption_under_python_O`
- `test_validator_does_not_detect_unlisted_new_files` → `test_validator_detects_unlisted_new_files`
- The corruption test now expects a named FAIL instead of `AssertionError`.

Tests for findings that are still open (F07 seed-dependent CIs, F14 `truth()` divergence) and the documented case-sensitive mapping still assert the current behaviour and are labelled as open.

## Full suite (environment failures disclosed)

`pytest tests`: **87 passed, 4 failed, 1 skipped**. The same 4 failures occur on base `544ca0e`:
- `test_frozen_measurement::...multitoken_candidates` and `test_pipeline_regressions::...exact_generated_suffix`: torch is not installed.
- `test_release_contracts::test_frozen_source_binding_and_unmodified_metric_equations` and `::test_unchanged_scientific_kernel_asts`: the frozen AST hashes were produced under the original Python, and `ast.dump` differs under Python 3.13.
- The skip is `test_reliability_v1` (torch).

No GPU environment was created to work around these.
