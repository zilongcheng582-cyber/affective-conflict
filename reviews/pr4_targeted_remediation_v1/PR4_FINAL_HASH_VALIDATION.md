# PR #4 — Final hash validation (head `f53d245dd5408fb97e9459a7ca13c80afc772f01`)

| Quantity | Value |
|---|---|
| Files added vs main 544ca0e | 265 (all `A`; 0 modified or deleted main files) |
| Migration `SHA256SUMS.txt` entries | 264 (= 265 − itself), 0 failures; file SHA256 `49131321b4dc1197eb99c8085a019cb8a44a4aee2a78f761b869977be72b8fa5` |
| Manifest coverage | 264/264 in-scope added files listed; 0 unlisted; 0 extraneous |
| Payload | 222 files, **16,358,604 bytes** (recorded = allowlist column = working tree = Git blobs), 209 byte-identical + 13 sanitized derivatives; 0 payload files changed by this remediation |
| Package manifests | historical_reconciliation 52/52; recovered 68/68 (+1 companion); transfer 31/31 (validator hash refreshed) |
| Main identity | 324/324 base blobs unchanged |
| Binary diff `git diff --binary 544ca0e f53d245` SHA256 | `5b7722c18ff6ed0e2a898c4b7b2d9cbb8055aea6f14e3de2f6be40e3ad97715a` |
| Excluded assets | 58 rows; 0 excluded SHA256 values present in the tree |

## Snapshot history (from MIGRATION_PROVENANCE.remediation_v1)

| Snapshot | Manifest entries | Payload bytes |
|---|---:|---:|
| pre-commit local replay | 245 | — |
| be83e51 | 254 | 16,372,023 (CRLF-converted, superseded) |
| 41f2681 | 256 | 16,358,604 |
| 18b99ca (reviewed) | 259 | 16,358,604 |
| **f53d245 (remediated)** | **264** | **16,358,604** |

Report value 16,372,203 was erroneous; it is now registered only as `erroneous_report_value_corrected`.

## Exact-byte clone

`git clone -c core.autocrlf=false https://github.com/zilongcheng582-cyber/affective-conflict && git checkout f53d245dd5408fb97e9459a7ca13c80afc772f01`. Every migration file is `-text` and therefore stable under any setting. Pre-existing main files without attributes may be newline-converted under `core.autocrlf=true`. The validator verifies their identity on Git objects and reports checkout drift as information only. We do not claim checkout-byte identity for those historical files under arbitrary Git configuration.
