# PR #4 Targeted Remediation V1 — Changelog

| Item | Value |
|---|---|
| PR | https://github.com/zilongcheng582-cyber/affective-conflict/pull/4 |
| Reviewed head (before) | `18b99caa5c11c3719e67ccbd3a0c71a0d70a77d7` |
| New head (after push) | `f53d245dd5408fb97e9459a7ca13c80afc772f01` |
| Base / main (unchanged) | `544ca0efae158df369a7b25dd110dc4254f67a7d` |
| Push | fast-forward to `evidence/recovered-science-transfer-phase4-v1` only; no force push; main untouched; not merged |
| Phase 0 check | Before work: remote head = 18b99ca, 0 reviews, 0 comments, 0 check runs (no CI configured); no third-party commits to preserve |

## Files changed relative to the reviewed head (18 total: 13 modified, 5 added)

| File | Change | Finding |
|---|---|---|
| `.gitattributes` | +3 lines: `-text` for `.gitattributes`, `docs/RECOVERED_EVIDENCE_MIGRATION_V1.md`, `tests/test_pr4_migration_regressions.py` | F03 |
| `docs/RECOVERED_EVIDENCE_MIGRATION_V1.md` | Appended a current-status navigation link and an exact-byte clone note | F02, F03 |
| `analyses/transfer_failure_integration_v1/validate_migration.py` | Explicit checks (0 `assert`), named failures, exit code 1 on failure, manifest coverage, Git-object identity for main files, single-class metrics → None; also checks payload bytes, exclusions, status index, claim companion and retained-text register | F04, F09, F01, F02, F05, F06, F10 |
| `evidence/provenance/recovered_evidence_migration_v1/MIGRATION_VALIDATION_REPORT.md` | 16,372,203 → 16,358,604; the 254 count marked as the `be83e51` snapshot; correction section with the 245/254/256/259 history | F01 |
| `.../MIGRATION_PROVENANCE.json` | Added a `remediation_v1` block (canonical bytes, snapshot history, corrected wrong value, added files). Existing keys unchanged | F01 |
| `.../MIGRATION_EXCLUSIONS.csv` | `status` regenerated from the gap analysis; new columns `gap_status`, `upload_decision=NOT_UPLOADED`, `status_before_remediation_v1`, `status_note`; all 58 rows kept; `reason` text unchanged | F05 |
| `.../MIGRATION_ALLOWLIST.csv`, `MIGRATION_FILE_SHA256.csv`, `MIGRATION_LINEAGE_MAP.csv`, `GITHUB_GAP_ANALYSIS.csv` | In the `MCR_POOL_AND_DUPLICATE_AUDIO_AUDIT_V2` row only, `transformation_rule` now also names the retained fields. Hashes and bytes unchanged | F06 |
| `.../SANITIZATION_RETAINED_FIELDS_REGISTER_V1.json` (new) | 30 retained MCR prompt values (3 files), recorded as hashes only. Each value is verified to be verbatim public in main `manifests/mcr/canonical_arbitration.csv` | F06 |
| `results/four_regime_structural_synthesis_v1/STATUS_AND_SUPERSESSION.{md,json}` (new) | 18 indexed documents (CURRENT/SUPERSEDED/HISTORICAL/CONDITIONAL), the supersession chain, withdrawn premises W1–W6, and one current conditional NEXT_STEP | F02 |
| `results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX_EVIDENCE_STATUS_V1.csv` (new) | Companion metadata: integration origin vs upstream evidence status. Only ERI1 X2 is marked citable as confirmatory | F10 |
| `results/recovered_evidence_scientific_analysis_v1/SHA256SUMS.txt` | Added 1 line (the companion file) | hashes |
| `results/transfer_failure_integration_v1/SHA256SUMS.txt` | 1 line updated (validator hash) | hashes |
| `.../recovered_evidence_migration_v1/SHA256SUMS.txt` | Regenerated: 259 → 264 entries (all added in-scope files except itself) | hashes |
| `tests/test_pr4_migration_regressions.py` (new) | 16 regression tests | all |

**Not changed:** all 222 scientific payload files (0 touched); B3 corrected measurements; the 9,219 frozen predictions; models, scalers and thresholds; R1, R2, ERI1 and Transfer results; MCR, LISTEN and CA-MER outcomes; every historical report, including superseded versions (05, 06, 07, 08 and QWEN_GPU_PRIORITY_REVISED_V2 are byte-identical); `CLAIM_EVIDENCE_MATRIX.csv`; `MIGRATION_SAFETY_REVIEW.json`, `CLEAN_CHECKOUT_VALIDATION_V1.json` and `LOCAL_FIXED_METRIC_REPLAY_CHECK.json` (kept as historical receipts). No media, datasets, caches or new raw text were added.

No GPU, model loading, refitting or scientific re-analysis was performed.
