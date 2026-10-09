# ERI1 scientific closure final report V1

## Frozen results

146 items / 2336 full trials; zero technical failures or retries. ITT primary SNR00−RECODE = -10.9589 pp, 95% CI [-17.4658, -4.4521] pp, two-sided sign-flip p=0.00171998. H1_SUPPORTED. Audio-only entropy increases by 0.060772, 95% CI [0.039229, 0.083803].

| Secondary | Holm-adjusted p |
| --- | --- |
| S1 | 4.9999500004999955e-05 |
| S4 | 0.06115938840611594 |
| S2 | 0.06115938840611594 |
| S3 | 0.14857851421485785 |
| S5 | 0.6199438005619944 |

S2 dose-response and S4 OTHER change are not established after multiplicity correction. S3 SIDE_V change and S5 order interaction are also not significant. CLEAN–RECODE controls are descriptive: SIDE_A delta −2.05 pp (CI includes zero), entropy +0.000606 (CI includes zero); this does not prove pipeline equivalence. Zero residual failures makes conservative and favourable missing-data bounds coincide; complete-case primary agrees. Full SIDE_A/SIDE_V/OTHER/PARSE_FAIL/TECHNICAL_FAILURE accounting is provided with explicit zero cells.

## Independent CPU verification

Frozen JSON and outcome CSV replay byte-identically. Independent row-level reconstruction of primary and S1 mean, bootstrap CI and sign-flip p agrees within 1e-12. All 146×16 planned cells and outcome classes are retained, with no Pilot pooling.

## Post-hoc robustness

**POST_HOC_ROBUSTNESS_V1.** Dialogue-cluster bootstrap over 134 official group/session clusters (max 3 items) keeps the same item-weighted point estimate; 95% CI [-17.6876, -4.4218] pp, width ratio 1.019. Interval excludes zero. Actors may recur across dialogues, so this is not a speaker-independent generalization test. Official mm.csv has 742 session folders vs the paper's 744 total; all 1500 panel rows map unambiguously.

| Outcome | RECODE n/292 | SNR00 n/292 | Net pp |
| --- | --- | --- | --- |
| SIDE_A | 119 | 87 | -10.9589 |
| SIDE_V | 162 | 179 | 5.8219 |
| OTHER | 11 | 26 | 5.137 |
| PARSE_FAIL | 0 | 0 | 0.0 |
| TECHNICAL_FAILURE | 0 | 0 | 0.0 |

Matched transitions: SIDE_A→SIDE_V 35, SIDE_A→OTHER 15; reverse transitions and all zero PARSE_FAIL cells are retained. Both orders are clustered by item. Video-side gain is 5.8219 pp, OTHER gain 5.1370 pp. Net audio loss does not all become video choice.

Selection reconstruction: 1500 source-panel rows, 900 AV conflicts, 146 eligible, 754 excluded conflicts. Coverage 9.7333% of panel and 16.2222% of AV conflicts. Readability cross-tabs and source-label, trimodal-pattern, speaker/dialogue and video-duration distributions are provided. Only pre-intervention selection is used. No complete whole-panel audio-duration metadata is claimed.

## Interpretation and access

The frozen intervention supports a causal effect of adding audio noise on arbitration under this particular model, prompt, candidates and selected population. The model's audio-only entropy also changes. These are distinct effects: entropy-mediated causation is not identified because noise may affect joint choice through multiple paths. Frozen S7 is an exploratory conditional binary reference, with post-intervention selection, and S8 is association only. No mechanism or effect is generalized to all EmotionTalk, other modalities/datasets/models, or general trimodal composability. Historical R2 and LISTEN negative findings are unchanged.

GitHub includes only audited derived scientific fields, scripts, hashes and reports. No new transcripts, raw generations, media, model weights, credentials or server/personal paths are uploaded. Private full archival copies preserve exact original results and required frozen CPU inputs. Upstream academic availability is recorded, without claiming MIT licenses the dataset or granting blanket public redistribution. Model/media inference cannot be reproduced without authorized source assets; CPU aggregate replay can use the derived scientific projection. Operational backup verification and merge receipts are recorded separately so the scientifically frozen archive is not rewritten after sealing.
