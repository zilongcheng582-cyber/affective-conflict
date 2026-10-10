# Migration validation report

POST_HOC_EXPLORATORY. Main baseline: `544ca0efae158df369a7b25dd110dc4254f67a7d`. Reused commits: `8679809a184408423f346f3d24d22c7f652ff09a`, followed by verified V2 `566e41c8f32ccf8090bc1c2ba20e366913434054`. No main push, forced checkout of historical assets, GPU, or model fitting.

## Identity and source differences

135 candidate files missing from checked GitHub branches; 87 byte-identical files reused from existing Claude branch; 86 frozen input files already identical on main. Thus 222 scientific/evidence payload files added relative to main, with 16,358,604 payload bytes (Git blob bytes = allowlist `bytes` column = working-tree sizes; corrected by Remediation V1, see below). Same-path differing-hash main assets: zero. These counts exclude newly authored migration documentation and validation code. 58 source artifacts are held or superseded, with explicit reasons; raw originals have no upload authorization inferred from the private repository.

All 177 entries in the final AutoDL science manifest independently rehashed: zero failures. Source manifest SHA256 `3cc3cc1e4ba594dd3e50ad9512378b64c6db7b9516c05b84a4dcbafc27874c0a`. Original manifests are preserved as historical manifests, not falsely presented as complete public-checkout manifests. Migration SHA256SUMS covers every new tracked file except itself. Transformations retain original hashes and all rows; no original sample, label or trial is altered.

## Actual CPU validation

`AUTODL_LOCAL_REPLAY_PASS`: an independent new-output invocation of frozen Phase4 replay yielded six exact SHA256 matches. It verified 6,354 corrected measurements, 9,219 frozen predictions and the fixed source bindings without refitting. Full historical extraction still uses restricted AutoDL inputs and reference backups.

Independent stdlib validation over public frozen prediction features re-evaluated all 18 route/baseline groups (legal M0, diagnostic source-only M0+ORDER, frozen M3a/M3b). Identities and evaluated denominators match; maximum metric absolute error `2.220446049250313e-16` <= 1e-12. CIs are preserved from their original frozen reports; this portable check does not regenerate bootstrap CIs or redefine populations. 5,199 strict recovered links and all six claim categories / 25 claims checked. MCR 4,000, CA-MER 6,000 and LISTEN 1,149 per-version safe projections parse and preserve planned failures; CA-MER scientific usable count is 5,825.

## Safety and limitations

Secret, private-key, personal-path, file-type and size checks: no findings in allowlisted content. Media, dataset archives, weights, environments, complete logs, credentials and unauthorized raw text remain excluded. New scientific payloads use scoped byte-preserving Git attributes. Existing main byte comparison passes; Windows checkout conversion was corrected only in the new migration clone, with no content changes to Git blobs.

Clean checkout at commit `be83e51` (historical snapshot): **PASS** for all 254 then-current manifest entries, 18 frozen route/baseline groups, 6 safe CPU module imports and 36 frozen evidence tests. Final metadata receipt update is verified again against its resulting commit before push. The public repository supports independent audit and fixed metric replay; **GITHUB_CLEAN_CHECKOUT_FULLY_REPRODUCIBLE** is not claimed for complete raw-archive extraction or every exploratory bootstrap. Native and controlled MCR, V3/V4 LISTEN, seven-class B3 and sixteen-class CA-MER remain distinct. Earlier GPU proposals are preserved historical interpretations, not new experiment authorization.

Six CPU library modules imported successfully. Frozen closure and evidence-anchor tests: **36 passed**. Initial default Temp fixture setup was inaccessible; the successful rerun used an explicit workspace temp directory. Post-replay AutoDL source recheck again verified all177science entries, zero historical navigation changes and cleanERI1worktree.

Staged review: additions only; all staged Git blobs matched the checkout hash manifest. Archived CSV CRLF and eight original report EOF blank lines were deliberately retained; diff check passed with only `cr-at-eol,-blank-at-eof`, without reformatting evidence. Final per-file migration identities were reconciled to canonical Git blobs after correcting Windows checkout conversion; 209 payload files are byte-identical and 13 are registered sanitized derivatives.

## Remediation V1 correction (PR4 independent review F01)

An earlier version of this report stated 16,372,203 payload bytes. That value matched no snapshot: commit `be83e51` recorded 16,372,023 bytes, measured from a Windows working tree whose newline conversion had altered 86 unsanitized files (only 123/222 then recorded byte-identical, versus 209/222 on canonical Git blobs), and the digits were additionally transposed. The canonical value is **16,358,604** bytes for 222 payload files (209 byte-identical, 13 registered sanitized derivatives), recomputed independently from Git blobs, the allowlist and the working tree; the payload set is unchanged by Remediation V1.

| Snapshot | Migration manifest entries | Payload bytes recorded | Record |
|---|---:|---:|---|
| Pre-commit local replay | 245 | — | `LOCAL_FIXED_METRIC_REPLAY_CHECK.json` (`sha256_files`) |
| `be83e51` | 254 | 16,372,023 (CRLF-converted checkout; superseded) | `CLEAN_CHECKOUT_VALIDATION_V1.json`; clean-checkout PASS above |
| `41f2681` | 256 | 16,358,604 | `MIGRATION_PROVENANCE.json` correction |
| `18b99ca` (reviewed head) | 259 | 16,358,604 | Independent review: 259/259 PASS (external record, branch `claude/focused-mayer-p99eh8`) |
| Remediation V1 commit | see `SHA256SUMS.txt` | 16,358,604 | Receipt bound to the pushed commit SHA is kept outside the commit (independent review record / PR comment) to avoid self-referencing hashes |

The historical receipts above are not presented as validation of any later commit. `validate_migration.py` now checks `recorded payload_bytes == sum(allowlist bytes) == sum(actual payload sizes)` explicitly.

