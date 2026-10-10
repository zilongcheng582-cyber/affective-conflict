# PR #4 — Remaining risks after Remediation V1

## Open P3 items (no merge blocker; for follow-up)

| ID | Item | Why not fixed now |
|---|---|---|
| F07 | Identical populations receive different bootstrap CIs because seeds are derived from tags (e.g. LISTEN DUAL vs STRICT_DUAL [0.500, 0.964] vs [0.490, 0.956]) | Fixing it would regenerate archived CIs, which counts as scientific re-analysis |
| F08 | Three byte-identical lineage tables; 16 identical generic READMEs | Cosmetic; the validator now checks the twins stay identical |
| F11 | Spaces stripped from archived report prose | Would require rewriting archived reports |
| F12 | References to pre-sanitization file names | Navigation only; the mapping exists in the allowlist |
| F14 | `truth('1')` differs between two archived modules | Archived code; not triggered by data |
| F16 | Archived scripts execute at import; finalizers append to AutoDL navigation docs | Archived code; README warning only. A header guard is recommended |
| F18 | Field name `base_commit_main` records HEAD | Archived code |
| N01 | PR description still says 260 files / 259 SHA256 entries; actual is now 265 / 264 | The PR body is outside the repository; update on owner request |

## Documented limitations

* F03 / F09c: under `core.autocrlf=true`, 231 pre-existing main files differ at checkout-byte level. Identity is guaranteed only at the Git-object level for those files. After merge, run the validator on the PR4 merge commit.
* F15: absolute AutoDL paths remain in provenance fields.
* F17 / reproducibility boundary: not verifiable from the public checkout:
  - the 177-entry AutoDL rehash and the six AutoDL replay hashes;
  - the CA-MER scientific-equivalence decision JSON;
  - the original SHA of 2 expanded-package sanitized files;
  - all bootstrap CIs, which were cited, not regenerated.
  `AUTODL_RESTRICTED_SOURCE_REPLAY_PASS` remains **not verified**.
* Full test suite: 4 pre-existing environment failures (torch missing ×2; Python 3.13 AST hashes ×2), identical on main.

## Process risk

The remediation was written and verified by the same agent that performed the original review. All checks are scripted and logged, but a human reviewer should look at the 18-file diff, especially the status index wording and the companion classifications, before merging.
