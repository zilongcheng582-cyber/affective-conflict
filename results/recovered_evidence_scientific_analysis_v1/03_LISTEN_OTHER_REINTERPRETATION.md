# 03_LISTEN_OTHER_REINTERPRETATION

POST_HOC_EXPLORATORY — recovered historical outputs; CPU analysis only.

Raw assistant answers, parsed letters, item-specific candidate arrays and canonical output labels were strictly rejoined. All3813C rows include both source labels in offered choices. Historical parser assignments are retained; no new parser changes the frozen outcome. OTHER here is a valid offered emotion that matches neither source annotation, **not a refusal, absent option or parser failure**. A/T source labels do not exhaust the ontology; disagreement alone is not proof the model answer is objectively wrong. Full raw generations remain in their original archive; `03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv` saves the assistant answer, letter, option list and raw output key.

| Support | Actual selected OTHER label | Count | OTHER denominator |
| --- | --- | --- | --- |
| ALL_3C_CONFLICT | anger | 2 | 211 |
| ALL_3C_CONFLICT | disgust | 6 | 211 |
| ALL_3C_CONFLICT | excitement | 11 | 211 |
| ALL_3C_CONFLICT | frustration | 25 | 211 |
| ALL_3C_CONFLICT | happiness | 9 | 211 |
| ALL_3C_CONFLICT | neutral | 20 | 211 |
| ALL_3C_CONFLICT | ridicule | 124 | 211 |
| ALL_3C_CONFLICT | sadness | 2 | 211 |
| ALL_3C_CONFLICT | surprise | 12 | 211 |
| COMMON_CONFLICT | anger | 2 | 129 |
| COMMON_CONFLICT | disgust | 4 | 129 |
| COMMON_CONFLICT | excitement | 7 | 129 |
| COMMON_CONFLICT | frustration | 15 | 129 |
| COMMON_CONFLICT | happiness | 5 | 129 |
| COMMON_CONFLICT | neutral | 12 | 129 |
| COMMON_CONFLICT | ridicule | 75 | 129 |
| COMMON_CONFLICT | sadness | 2 | 129 |
| COMMON_CONFLICT | surprise | 7 | 129 |
| DUAL_MATCH_CONFLICT | happiness | 1 | 1 |

Of211 full3Cconflict OTHER outputs,124select ridicule (58.77% ofOTHER). Ridicule is also85/102source-A choices in frozen R3. It therefore appears both as a matched source choice and as a third-label choice when the source annotations differ. This new recovered semantic decomposition sharpens the prior label-selectivity result; it is **not** evidence the overallOTHER bucket was merely parse failure. Remaining87OTHER labels are frustration25,neutral20,surprise12,excitement11,happiness9,disgust6,anger2,sadness2. The sole dual-groupOTHER selects happiness, and no non-ridicule dual case is available.

Mechanisms remain ambiguous: pragmatic/sarcasm content, native question format, option/letter biases, source-label validity and lexical ontology differences may each matter. Without new controlled input changes or validated annotations, one cannot claim ridicule is an acoustic latent emotion or resolve model-versus-source correctness. No guessed semantic remapping to B3 is applied.
