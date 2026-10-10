# 01_MCR_DUPLICATE_SENSITIVITY

POST_HOC_EXPLORATORY — recovered historical outputs; CPU analysis only.

Native1000 released IDs represent947 physical audio paths and943 byte-SHA clusters. There are39 conflicting-GT hash groups containing79 released records; the original frozen path audit excluded38 path groups/76records and15 further same-label duplicate-path representatives. Controlled909 paths represent905 byte contents. Retain original1000native and909controlled denominators; do not rewrite frozen pools.

| Population | N/cluster | Weighting | Contrast | Effect/95%CI |
| --- | --- | --- | --- | --- |
| released1000 | 1000/943 | released_item | adversarial-faithful | -98.80 pp, 95% CI [-99.49, -98.07] pp |
| released1000 | 1000/943 | equal_audio_hash | adversarial-faithful | -98.99 pp, 95% CI [-99.58, -98.36] pp |
| released1000 | 1000/943 | released_item | irrelevant-neutral | -1.30 pp, 95% CI [-5.05, 2.69] pp |
| released1000 | 1000/943 | equal_audio_hash | irrelevant-neutral | -1.47 pp, 95% CI [-5.36, 2.37] pp |
| controlled_members909 | 909/905 | released_item | adversarial-faithful | -99.23 pp, 95% CI [-99.78, -98.58] pp |
| controlled_members909 | 909/905 | equal_audio_hash | adversarial-faithful | -99.23 pp, 95% CI [-99.78, -98.56] pp |
| controlled_members909 | 909/905 | released_item | irrelevant-neutral | -1.43 pp, 95% CI [-5.38, 2.43] pp |
| controlled_members909 | 909/905 | equal_audio_hash | irrelevant-neutral | -1.36 pp, 95% CI [-5.41, 2.73] pp |
| exclude_all_conflicting_GT_hashes | 921/904 | released_item | adversarial-faithful | -99.24 pp, 95% CI [-99.78, -98.69] pp |
| exclude_all_conflicting_GT_hashes | 921/904 | equal_audio_hash | adversarial-faithful | -99.23 pp, 95% CI [-99.78, -98.67] pp |
| exclude_all_conflicting_GT_hashes | 921/904 | released_item | irrelevant-neutral | -1.09 pp, 95% CI [-5.19, 3.05] pp |
| exclude_all_conflicting_GT_hashes | 921/904 | equal_audio_hash | irrelevant-neutral | -1.38 pp, 95% CI [-5.42, 2.60] pp |
| irrelevant_parse_complete_case | 995/938 | item | irrelevant-neutral | -1.11 pp, 95% CI [-4.93, 2.79] pp |

Excluding all39 conflicting-label SHA groups gives921 released IDs/904hashes and is a labeled sensitivity, not the new primary pool. Equal-SHA weighting estimates a different (content-weighted) estimand. Neither procedure proves dataset ground truth; unresolved source-label ambiguity is carried forward. Both replicate the main assertion-following contrast and near-zero aggregate irrelevant−neutral source-match contrast. The latter does not imply distributional invariance.

The retained controlled ambiguity is SHA `d6a4044bfffbe760e2f2a0812b8fa45f846fa4f0318b2b8846202de12a1412a7`: native source indices692/752/838; source labels happy/angry/neutral; same acoustic bytes. Native neutral outputs angry on allthree; faithful outputs happy/angry/neutral and adversarial angry/neutral/angry, tracking each record's supplied assertion. Irrelevant captions differ, with neutral/fearful/angry outputs. Thus source-label accuracy is inherently annotation-dependent and does not demonstrate three distinguishable acoustic truths. Diagnosis preserves all attempts/rows.

No trustworthy official speaker/dialogue cluster was recovered in the source contract used here. Existing filename-derived dialogue IDs are explicitly nonofficial and are not used as population-robust clusters. Primary audio-SHA bootstrap addresses exact-content repetition; larger dependence may remain. Per-hash records/labels/control membership are in `intermediate/MCR_DUPLICATE_DIAGNOSTICS.json`.
