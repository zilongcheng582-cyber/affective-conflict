# MCR Controlled Scientific Analysis V2

Status: `COMPLETE_V2`; results status: `FROZEN_V2`. CPU-only analysis; no model loaded, no GPU, no inference.

## Integrity and populations

| Metric | N | Share |
|---|---|---|
| Readable audio | 466 | 0.512651 |
| Readable text | 909 | 1.000000 |
| Dual-Readable | 466 | 0.512651 |

## Dual-Readable primary order-specific results

| Order | Category | N | Share |
|---|---|---|---|
| A_THEN_T | SIDE_AUDIO | 22 | 0.047210 |
| A_THEN_T | SIDE_TEXT | 444 | 0.952790 |
| A_THEN_T | OTHER | 0 | 0.000000 |
| A_THEN_T | PARSE_FAIL | 0 | 0.000000 |
| T_THEN_A | SIDE_AUDIO | 82 | 0.175966 |
| T_THEN_A | SIDE_TEXT | 375 | 0.804721 |
| T_THEN_A | OTHER | 9 | 0.019313 |
| T_THEN_A | PARSE_FAIL | 0 | 0.000000 |

## Dual-Readable order-averaged estimates

| Estimate | Share | Detail |
|---|---|---|
| SIDE_AUDIO | 0.111588 | 52.0 |
| SIDE_TEXT | 0.878755 | 409.5 |
| OTHER | 0.009657 | 4.5 |
| PARSE_FAIL | 0.000000 | 0.0 |
| ResolvedAudioShare | 0.112676 | denominator weight=461.5 |

## Order stability

| Category | N / denominator | Share |
|---|---|---|
| STABLE_AUDIO | 17 | 0.036481 |
| STABLE_TEXT | 371 | 0.796137 |
| RECENCY_FLIP | 65 | 0.139485 |
| PRIMACY_FLIP | 4 | 0.008584 |
| OTHER_OR_INVALID | 9 | 0.019313 |
| OS_RESOLVED | 69/457 | 0.150985 |

## Full-pool sensitivity

| Order | Category | N | Share |
|---|---|---|---|
| A_THEN_T | SIDE_AUDIO | 22 | 0.024202 |
| A_THEN_T | SIDE_TEXT | 876 | 0.963696 |
| A_THEN_T | OTHER | 11 | 0.012101 |
| A_THEN_T | PARSE_FAIL | 0 | 0.000000 |
| T_THEN_A | SIDE_AUDIO | 85 | 0.093509 |
| T_THEN_A | SIDE_TEXT | 751 | 0.826183 |
| T_THEN_A | OTHER | 73 | 0.080308 |
| T_THEN_A | PARSE_FAIL | 0 | 0.000000 |

## Directional pair and selection diagnostics

Directional-pair results are frozen in `MCR_CONTROLLED_DIRECTIONAL_PAIR_RESULTS_V2.csv`; Full-vs-Dual-Readable diagnostics are frozen in `MCR_CONTROLLED_DUAL_READABLE_DIAGNOSTICS_V2.csv`. These are descriptive and do not alter the subset.

## Bootstrap status

The frozen spec does not specify bootstrap replicate count, seed/deterministic mechanism, CI level, or interval construction. Therefore clustered CIs were not computed and no post-hoc parameter was selected. See the bootstrap artifact for the exact gap record.

## Boundary

Descriptive arbitration behavior within acoustic perceptual affective evidence versus explicit propositional textual affective evidence; no universal modality hierarchy or cross-regime transfer claim.
