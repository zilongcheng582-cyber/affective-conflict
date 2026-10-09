# POST_HOC_ROBUSTNESS_V1: dialogue sensitivity

[Official EmotionTalk paper](https://aclanthology.org/2026.findings-acl.440.pdf), Appendix A.1, defines group/session/speaker/utterance fields. Dialogue IDs use official mm.csv group/session directories, including both speakers, cross-checked against all 1500 master-panel paths; no arbitrary ID truncation.

| Measure | Value |
| --- | --- |
| analysis_label | POST_HOC_ROBUSTNESS_V1 |
| status | IDENTIFIED |
| dialogue_count | 134 |
| item_count | 146 |
| max_cluster_items | 3 |
| min_cluster_items | 1 |
| median_cluster_items | 1.0 |
| effect_item_weighted | -0.1095890410958904 |
| CI_low | -0.17687606292517005 |
| CI_high | -0.04421768707482993 |
| CI_width | 0.13265837585034013 |
| item_bootstrap_CI_low | -0.17465753424657535 |
| item_bootstrap_CI_high | -0.04452054794520548 |
| width_ratio_to_item_bootstrap | 1.0193748881131397 |
| excludes_zero | True |
| bootstrap_seed | 20261110 |
| bootstrap_replicates | 10000 |
| method | Dialogue cluster percentile bootstrap; item-weighted pooled mean per resample; random total items per draw |
| official_unique_sessions | 742 |
| paper_reported_dialogues | 744 |
| official_paper_count_difference | Current official mm.csv has 742 group/session folders vs paper 744; all 1500 panel items joined without ambiguity. No invented clusters. |

Effect direction remains negative. Cluster CI excludes zero; width is 1.019 times the item-bootstrap width. This is post-hoc uncertainty sensitivity and does not replace the registered H1 decision. Dialogue independence does not remove actor/group dependence; repeated actors can span dialogues. No new population or estimand is introduced. Official available metadata contains 742 sessions whereas the paper reports 744; this source-version/count difference is disclosed and does not create ambiguous joins.
