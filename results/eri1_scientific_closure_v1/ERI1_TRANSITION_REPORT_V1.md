# POST_HOC_ROBUSTNESS_V1: RECODE → SNR00 transitions

Strictly paired 146 items × two orders = 292 joint transitions. Pooled inference resamples items with both orders together; 292 rows are not treated as independent.

| From / to | SIDE_A | SIDE_V | OTHER | PARSE_FAIL | TECHNICAL_FAILURE |
| --- | --- | --- | --- | --- | --- |
| SIDE_A | 69 | 35 | 15 | 0 | 0 |
| SIDE_V | 17 | 141 | 4 | 0 | 0 |
| OTHER | 1 | 3 | 7 | 0 | 0 |
| PARSE_FAIL | 0 | 0 | 0 | 0 | 0 |
| TECHNICAL_FAILURE | 0 | 0 | 0 | 0 | 0 |

| Outcome | RECODE n | SNR00 n | Change pp | Item CI pp |
| --- | --- | --- | --- | --- |
| SIDE_A | 119 | 87 | -10.9589 | [-17.4658, -4.4521] |
| SIDE_V | 162 | 179 | 5.8219 | [0.0000, 11.9863] |
| OTHER | 11 | 26 | 5.137 | [1.3699, 9.2466] |
| PARSE_FAIL | 0 | 0 | 0.0 | [0.0000, 0.0000] |
| TECHNICAL_FAILURE | 0 | 0 | 0.0 | [0.0000, 0.0000] |

SIDE_A → SIDE_V: 35; SIDE_A → OTHER: 15. Reverse transitions are retained. Net audio-side loss is not interpreted as entirely video-side gain. PARSE_FAIL and technical failures are separate zero-count categories. Order-specific complete matrices and CIs are in the companion CSVs. All findings in this section are post-hoc descriptions.
