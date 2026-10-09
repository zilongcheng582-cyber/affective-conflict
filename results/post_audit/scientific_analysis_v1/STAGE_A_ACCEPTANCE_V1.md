# Stage A acceptance — scientific_analysis_v1 (2026-10-09)

Targeted acceptance only; not a forensic audit.

| Check | Result |
|---|---|
| Diff vs `main` (f8432837) touches `frozen/`, `manifests/`, `evidence/`, `results/post_audit/closure_v1`, `anchor_hardening_v1`, `results/mainline_summary` | None (additions only: `analyses/post_audit/sci_*.py`, `results/post_audit/scientific_analysis_v1/`) |
| Replay of R1, R2, R3 in an isolated venv (Python 3.13, numpy/scipy/pandas/sklearn/statsmodels) before corrections | All three ran; every committed CSV/JSON reproduced byte-identically (clean `git status`) |
| Regression tests, documented env (Python 3.12 + `requirements.txt`) | `67 passed, 15 subtests passed` |
| Regression tests, Python 3.13 analysis venv | 4 environmental failures (AST-hash drift across Python versions; torch not installed); identical failures on clean `main` |
| R1 leakage | StandardScaler and coefficients fit on training folds only; label/position codings are fixed transforms, not fitted encodings; utterance and speaker groupings are both group-disjoint across folds |
| R2 support | 268/294 (frozen resolved) and 268/402 (coverage-aware) are reported separately; partial-coverage rules are now also compared with always-majority on their own resolved rows |
| R3 identity | 3A/3B/3C joined only on identical item base, measurement IDs, evidence SHA256 and source labels; 0 forced joins; OTHER kept as an outcome (technical missing = 0) |
| CI | `CI_NOT_CONFIGURED` (no `.github/` workflows in the repository); local test results above are the acceptance evidence |

Corrections made:
- R1 wording on source probability and margin.
- R2 B5 now compared on its paired 286-row support (200/286 vs 207/286).
- R1 A–T utterance count corrected from 58 to 61.

No scientific verdict changed.
