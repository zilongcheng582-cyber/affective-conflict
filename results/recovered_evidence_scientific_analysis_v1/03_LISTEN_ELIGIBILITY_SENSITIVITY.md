# 03_LISTEN_ELIGIBILITY_SENSITIVITY

POST_HOC_EXPLORATORY — recovered historical outputs; CPU analysis only.

Frozen R3 full3C conflict outcome is102A/65T/211OTHER over378, binary167/378; its existing full transitions, persistentOTHER and frozen-transfer evaluation are read and cited, not rerun.381joint includes3same-source-label cases, which are kept separate. Existing V4 single-modal answers are native3A/3B, not B3 top1 and not a historic correctness inclusion gate. Original older Phase1 gates and the V4six-case technical gate are documented as different lineages.

Current new support uses unique original/source-text identity for text-only outputs and unique content identity for audio-only outputs. Text-only never consumed its paired audio, so `actual_input` and stricter `full_content` joins are separately logged; neither is guessed by filenames. On378conflicts,242 have common observed unilateral support,136do not; the unmatched137figure in R3 includes one nonconflict joint item. Of242 common conflicts:22dual,71A-only,46T-only,103neither. Exact identity/key/hashes and both join flags are in `03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv`; strict-content dual count22 matches actual-input dual count22.

| Common native support | N | Full outcome | Binary coverage | Conditional audio/95%WilsonCI | OTHER/95%WilsonCI |
| --- | --- | --- | --- | --- | --- |
| COMMON_CONFLICT | 242 | A=71, SIDE_T=42, OTHER=129, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 46.69% | 62.83% [53.64, 71.18] | 53.31% [47.02, 59.49] |
| DUAL_MATCH_CONFLICT | 22 | A=12, SIDE_T=9, OTHER=1, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 95.45% | 57.14% [36.55, 75.53] | 4.55% [0.81, 21.80] |
| COMMON_NON_DUAL | 220 | A=59, SIDE_T=33, OTHER=128, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 41.82% | 64.13% [53.95, 73.18] | 58.18% [51.58, 64.50] |
| NO_TEXT_IDENTITY | 136 | A=31, SIDE_T=23, OTHER=82, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 39.71% | 57.41% [44.16, 69.67] | 60.29% [51.90, 68.13] |
| A_ONLY_MATCH | 71 | A=55, SIDE_T=3, OTHER=13, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 81.69% | 94.83% [85.86, 98.23] | 18.31% [11.02, 28.85] |
| T_ONLY_MATCH | 46 | A=0, SIDE_T=24, OTHER=22, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 52.17% | 0.00% [0.00, 13.80] | 47.83% [34.12, 61.86] |
| NEITHER_MATCH | 103 | A=4, SIDE_T=6, OTHER=93, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 9.71% | 40.00% [16.82, 68.73] | 90.29% [83.04, 94.64] |
| COMMON_CONFLICT_RIDICULE | 92 | A=59, SIDE_T=17, OTHER=16, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 82.61% | 77.63% [67.07, 85.54] | 17.39% [11.00, 26.40] |
| COMMON_CONFLICT_NON_RIDICULE | 150 | A=12, SIDE_T=25, OTHER=113, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 24.67% | 32.43% [19.63, 48.54] | 75.33% [67.86, 81.54] |
| DUAL_MATCH_CONFLICT_RIDICULE | 22 | A=12, SIDE_T=9, OTHER=1, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 95.45% | 57.14% [36.55, 75.53] | 4.55% [0.81, 21.80] |
| DUAL_MATCH_CONFLICT_NON_RIDICULE | 0 | A=0, SIDE_T=0, OTHER=0, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | undefined | undefined [undefined] | undefined [undefined] |

Answer RQ-L1: within observed dual22, OTHER1/22=4.55%,95%WilsonCI [0.81, 21.80], versus common full129/242=53.31% and common nondual128/220=58.18%. **The high overall OTHER rate does not persist on this observed subgroup.** However all22audio-source labels are ridicule, zero non-ridicule dual support. This does not establish that general dual-readable LISTEN resolves OTHER or replicates EmotionTalk's eligibility. Binary audio12/21=57.14%,CI [36.55, 75.53]; 12versus9 is not compelling modality dominance and all12audio choices are ridicule.

| Selection association | Dual−nondual /95%item bootstrapCI | Fisher p | Holm p, family3 |
| --- | --- | --- | --- |
| SIDE_A | +27.73 pp, 95% CI [5.91, 49.55] pp | 0.012056 | 0.012056 |
| SIDE_T | +25.91 pp, 95% CI [5.45, 47.73] pp | 0.00544392 | 0.0108878 |
| OTHER | -53.64 pp, 95% CI [-63.18, -41.82] pp | 8.96381e-07 | 2.68914e-06 |

These tests describe a selected observational association, not the causal effect of readability. Native label confounding is complete for dual support. Item intervals do not claim speaker/show/dialogue independence. On common support, non-ridicule150 yields12A/25T/113OTHER; the dual non-ridicule group is empty (INSUFFICIENT_EVIDENCE). The previously known ridicule concentration is not a new independent replication; discovering the entire22dual group is ridicule adds an important support restriction.

Seven-class correctedB3 and native LISTEN emotion ontology are different. Literal paired source-label support0/381; labels like ridicule/frustration/excitement lack measured seven-class categories, and lexical variants are not silently merged. Existing frozen margin sensitivity remains a sensitivity, not a native label probability model. No frozen refit, reinterpretation of unsupported nulls, or cross-version pooling. V3/V4all1149 prompt/candidate sequences differ; no credible historical T_THEN_A execution found in the existing recovered scope. Order effects on native3C remain NOT_IDENTIFIABLE.
