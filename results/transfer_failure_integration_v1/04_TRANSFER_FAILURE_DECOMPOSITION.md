# 04_TRANSFER_FAILURE_DECOMPOSITION

POST_HOC_EXPLORATORY — CPU-only; frozen source models, thresholds, scalers, predictions and raw archives unchanged.

## Replayed frozen routes

Coverage means binary-evaluable / prescribed conflicts, not GPU execution success. Source item IDs repeated across orders are not independent; MCR has909 items/905 distinct audio hashes with residual GT ambiguity; CA full conflict1000 items, support-limited336 items; LISTEN3C378 conflict items, historical mixed519 underlying UID clusters. Unknown CA speaker/source-video dependencies limit item-bootstrap transportability. All frozen CIs below are exact POST_AUDIT intervals, not newly optimized estimates.

| route | planned | conflict | evaluable | A/2/O/PF/TM | AUROC [95CI] | BA | LL | Brier | coverage | M0 LL | M0+ORDER LL | LL−M0 [95CI] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MCR_AT_PRIMARY | 1818 | 1818 | 1734 | 107/1627/84/0/0 | 0.727559 [0.677745,0.776863] | 0.500000 | 0.245884 | 0.058506 | 0.953795 | 0.678181 | 0.668459 | -0.432297 [-0.478847,-0.380386] |
| MCR_AT_MARGIN_SENSITIVITY | 1818 | 1818 | 1734 | 107/1627/84/0/0 | 0.739398 [0.688970,0.788145] | 0.500000 | 0.243253 | 0.058279 | 0.953795 | 0.678181 | 0.668459 | -0.434928 [-0.480903,-0.383241] |
| LISTEN_ALL_MIXED_HISTORICAL | 1149 | 1139 | 518 | 316/202/621/0/0 | 0.522638 [0.454738,0.587010] | 0.489190 | 0.969593 | 0.350150 | 0.454785 | 0.697091 | 0.765037 | 0.272502 [0.193290,0.352542] |
| LISTEN_3C_JOINT_ARBITRATION | 381 | 378 | 167 | 102/65/211/0/0 | 0.605732 [0.514184,0.696893] | 0.515460 | 0.981644 | 0.352787 | 0.441799 | 0.697116 | 0.748593 | 0.284528 [0.168351,0.402273] |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | 1434 | 672 | 416 | 236/180/238/0/18 | 0.686394 [0.617947,0.751111] | 0.595716 | 0.768851 | 0.269759 | 0.619048 | 0.716559 | 0.719741 | 0.052293 [-0.031654,0.136540] |
| CAMER_AV_MARGIN_SENSITIVITY | 3000 | 2000 | 1350 | 754/596/588/0/62 | 0.573999 [0.535149,0.613860] | 0.539941 | 0.800208 | 0.283972 | 0.675000 | 0.714444 | 0.724856 | 0.085764 [0.038995,0.129732] |

## T1. MCR AUROC≈0.73 and BA=0.50

On1734 binary outcomes,107 select audio and1627 text (audio prevalence6.1707%). Frozen M3a selects text at threshold0.5 on all1734: TP0,FP0,FN107,TN1627. Its p(audio) maximum0.405610, median0.012005 and mean0.019427, below observed6.1707%; M3b maximum0.420272 and also no threshold crossings. BA=0.5 follows exactly from zero audio sensitivity and perfect text specificity. It does not imply absence of ranking information or authorize threshold tuning.

Mean M3a logit decomposition: intercept+0.495730, sourceprob+0.289512, H7 term−4.668748, order−0.443343. Mean deltaH7(A−T)=+0.691135; the strongly negative frozen entropy slope maps highly concentrated text-assertion scores and uncertain audio to low audio probabilities. This is an algebraic explanation of the frozen model, not a causal explanation of model behavior. Negative deltaH7 alone has AUROC0.673529; full M3a0.727559.

A_THEN_T:898 binary,22A/876T, within-order AUROC0.699045. T_THEN_A:836 binary,85A/751T, within-order AUROC0.655706. Existing source-only M0+ORDER AUROC0.666403; M3a minus that AUROC+0.061156, paired95CI[+0.009391,+0.111504]. Thus order contributes but does not exhaust the observed ranking association. All source-label and order probability strata are provided in the numeric tables; rare label strata do not support standalone strong conclusions.

Against lawful frozen M0, M3a log loss0.245884 versus0.678181, delta−0.432297 (95CI[−0.478847,−0.380386]); this probability-loss improvement must be reported. The target-prevalence oracle LL0.231639 is a target-informed diagnostic, not an authorized competitor. Its slightly better loss diagnoses average probability mismatch; it cannot erase transferable ranking or redefine the earlier baseline.

On909 strict native-controlled audio/GT matches, controlledT_ONLY follows text909/909, native adversarial text match901/909 and audio match4/909. Native full1000 adversarial follows text988/1000,faithful audio994/1000. These support text-assertion dependence as a plausible protocol explanation, but native fixed candidates/system prompt/generation interface differ from controlled conditions. Native data cannot replace controlled Transfer outcomes or be pooled into its1818 denominator.

## T2. LISTEN probability transfer

Keep1149 historical mixed3A/3B/3C trials (1139conflicts,518binary) distinct from381joint3C trials (378conflicts,167binary,211validOTHER,zero parse/technical failures). Joint binary choices102A/65T mean audio fraction0.610778, but frozen mean p(audio)0.271488;16/167 cross0.5 (TP11,FP5,FN91,TN60). Joint AUROC0.605732 (95CI[0.514184,0.696893]) shows modest ranking association; BA0.515460 and LL0.981644 vs lawfulM0.697116, delta+0.284528 (95CI[+0.168351,+0.402273]), show probability-loss failure against that comparator. Brier0.352787 vsM0.251984 also worsens. The value0.697116 is source-fixed M0, NOT target oracle; target oracle LL is0.668399.

Strict observed dual matching gives22/378 items, all audio source ridicule,21binary with12A/9T and1OTHER. Frozen M3b AUROC0.759259; strict-content subgroup descriptive95CI[0.489796,0.955882], LL0.798549 vs same-subgroupM0.695759. This tiny selected group neither proves an improvement in probability loss nor repairs the original full-population transfer. It is not a new zero-refit success. Common actual-input support242conflicts;136 lack validated unilateral linkage and remain UNOBSERVABLE, never labeled neither-readable. A-only-match71 has58binary (55A/3T); T-only-match46 has24binary allT; neither103 has10binary and93OTHER. These changes in class balance and coverage are selection associations, not causal readability effects.

Literal B3 joint sourceprob support is0/381; the margin route remains computable but measures seven generic emotion candidate scores. Frustration/ridicule/excitement lack direct seven-class counterparts; anger/angry, sadness/sad, happiness/happy etc are not mapped after inspection. Per-modality exact support and native label counts are in `phase4_numeric/LISTEN_NATIVE_LABEL_SUPPORT_AND_OTHER.csv`. Native OTHER labels are valid offered options, including124ridicule/211OTHER; full native choices always include both source labels. In conflict audio-source strata: ridicule140 has32OTHER and108binary (85A/23T); frustration87 has56OTHER; disgust80 has62OTHER; anger58 has48OTHER; sadness13 has13OTHER. Source-label imbalance and uncovered native categories can affect probability transfer interpretation without identifying their causal contributions.

All3C use A_THEN_T; no legitimate item-paired reverse exists in recovered scope. Shared order slope cannot be separated from a route-specific intercept shift in this single-order population. V3 RNG mismatch precludes fabricating counterbalanced evidence. Comparing AUROC after binary or dual selection is exploratory, never general success.

## T3. CA-MER weaker association

The full margin sensitivity evaluates1350/2000 conflicts (754A,596V,588OTHER,62technical slots), while ontology-supported sourceprob uses416/672 conflicts (236A,180V,238OTHER,18technical). The latter is a supplementary diagnostic, not full-target primary;717supported total items include only336conflict items and381consistent. Both16class task labels and seven-class corrected score vectors are preserved as distinct spaces.

Observed16class unilateral source matching:1000 conflict items split108dual,273A-only,244V-only,343neither,32unobservable. Two joint orders yield216dual trials,206binary and10OTHER; margin AUROC0.573318 (descriptive95CI[0.477917,0.671101]), LL0.842310 vs same-subgroupM0.706205. Thus high95.37% dual binary coverage does not rescue margin prediction. Seven-supported dual has31items/62trials,54binary, sourceprob AUROC0.710165; selecting it changes both ontology and population and cannot redefine success.

For the same frozen M3b margin equation, ontology-supported conflicts have AUROC0.715960 (416binary/672), versus0.513616 outside joint support (934binary/1328). This is a descriptive selection pattern, not an isolated causal ontology effect or a formally tested difference. Full audio-aligned1000trials yield695binary, AUROC0.509993 and audio fraction0.738129; video-aligned1000yield655binary, AUROC0.569317 and audio fraction0.367939. These constructed populations differ in labels, source-match selection and missingness. In dual-only subsets, audio-aligned111binary AUROC0.540028, video-aligned95binary0.499542. No common human ground truth or source-cluster structure is established.

Four causes remain distinct: seven-vs-sixteen measurement-space mismatch; unilateral source-label unreadability; conditional selection and changing label prevalence; true cross-dataset model behavior. Present evidence documents the first three constraints and protocol-specific behavior but cannot attribute the entire association decline to any one cause. Cross-domain AUROC differences against selected EmotionTalkR1 do not identify mechanism strength. Missing16class continuous vectors prevent a full entropy-transfer explanation; recovering discrete A_ONLY/V_ONLY does not supply them.

## All conditional diagnostics

No target/source refit here, no calibration fit, no threshold optimization. New subgroup intervals are descriptive2000-bootstrap item intervals and not multiplicity-adjusted confirmatory tests. Some one-class groups have undefined AUROC/BA; all group denominators and failure classes are retained. The broader item latent dependence remains unidentified.

| route | group | conflict | evaluable | A/2/O/TM | AUROC | BA | LL | M0 LL | coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LISTEN_3C_JOINT_ARBITRATION | DUAL_MATCH | 22 | 21 | 12/9/1/0 | 0.759259 | 0.527778 | 0.798549 | 0.695759 | 0.954545 |
| LISTEN_3C_JOINT_ARBITRATION | A_ONLY_MATCH | 71 | 58 | 55/3/13/0 | 0.381818 | 0.545455 | 1.371559 | 0.708755 | 0.816901 |
| LISTEN_3C_JOINT_ARBITRATION | T_ONLY_MATCH | 46 | 24 | 0/24/22/0 | UNDEFINED | UNDEFINED | 0.270138 | 0.676053 | 0.521739 |
| LISTEN_3C_JOINT_ARBITRATION | NEITHER_MATCH | 103 | 10 | 4/6/93/0 | 0.291667 | 0.416667 | 0.890960 | 0.689847 | 0.097087 |
| LISTEN_3C_JOINT_ARBITRATION | UNOBSERVABLE | 136 | 54 | 31/23/82/0 | 0.586255 | 0.521038 | 0.967070 | 0.695850 | 0.397059 |
| LISTEN_3C_JOINT_ARBITRATION | STRICT_DUAL_CONTENT_MATCH | 22 | 21 | 12/9/1/0 | 0.759259 | 0.527778 | 0.798549 | 0.695759 | 0.954545 |
| LISTEN_3C_JOINT_ARBITRATION | B3_ONTOLOGY_True | 0 | 0 | 0/0/0/0 | UNDEFINED | UNDEFINED | UNDEFINED | UNDEFINED | UNDEFINED |
| LISTEN_3C_JOINT_ARBITRATION | B3_ONTOLOGY_False | 378 | 167 | 102/65/211/0 | 0.605732 | 0.515460 | 0.981644 | 0.697116 | 0.441799 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | DUAL_MATCH | 62 | 54 | 28/26/8/0 | 0.710165 | 0.634615 | 0.694182 | 0.704821 | 0.870968 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | A_ONLY_MATCH | 152 | 121 | 115/6/31/0 | 0.730435 | 0.726087 | 0.928956 | 0.808730 | 0.796053 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | V_ONLY_MATCH | 168 | 142 | 16/126/26/0 | 0.659722 | 0.568948 | 0.493484 | 0.607179 | 0.845238 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | NEITHER_MATCH | 270 | 97 | 75/22/173/0 | 0.432727 | 0.426061 | 1.013600 | 0.766094 | 0.359259 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | UNOBSERVABLE | 20 | 2 | 2/0/0/18 | UNDEFINED | UNDEFINED | 0.779418 | 0.820661 | 0.100000 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | B3_ONTOLOGY_True | 672 | 416 | 236/180/238/18 | 0.686394 | 0.595716 | 0.768851 | 0.716559 | 0.619048 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | B3_ONTOLOGY_False | 0 | 0 | 0/0/0/0 | UNDEFINED | UNDEFINED | UNDEFINED | UNDEFINED | UNDEFINED |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | CONSTRUCT_audio-aligned | 270 | 160 | 131/29/108/2 | 0.632272 | 0.577652 | 0.887562 | 0.777053 | 0.592593 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | CONSTRUCT_audio-aligned_DUAL | 30 | 23 | 14/9/7/0 | 0.539683 | 0.523810 | 0.773213 | 0.726516 | 0.766667 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | CONSTRUCT_video-aligned | 402 | 256 | 105/151/130/16 | 0.677452 | 0.565878 | 0.694657 | 0.678750 | 0.636816 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | CONSTRUCT_video-aligned_DUAL | 32 | 31 | 14/17/1/0 | 0.802521 | 0.642857 | 0.635545 | 0.688724 | 0.968750 |
| CAMER_AV_MARGIN_SENSITIVITY | DUAL_MATCH | 216 | 206 | 108/98/10/0 | 0.573318 | 0.557918 | 0.842310 | 0.706205 | 0.953704 |
| CAMER_AV_MARGIN_SENSITIVITY | A_ONLY_MATCH | 546 | 450 | 435/15/96/0 | 0.510651 | 0.485057 | 0.834121 | 0.812641 | 0.824176 |
| CAMER_AV_MARGIN_SENSITIVITY | V_ONLY_MATCH | 488 | 419 | 34/385/69/0 | 0.517800 | 0.489037 | 0.659325 | 0.599593 | 0.858607 |
| CAMER_AV_MARGIN_SENSITIVITY | NEITHER_MATCH | 686 | 273 | 175/98/413/0 | 0.429155 | 0.435102 | 0.929125 | 0.734295 | 0.397959 |
| CAMER_AV_MARGIN_SENSITIVITY | UNOBSERVABLE | 64 | 2 | 2/0/0/62 | UNDEFINED | UNDEFINED | 0.751346 | 0.820661 | 0.031250 |
| CAMER_AV_MARGIN_SENSITIVITY | B3_ONTOLOGY_True | 672 | 416 | 236/180/238/18 | 0.715960 | 0.612665 | 0.722501 | 0.716559 | 0.619048 |
| CAMER_AV_MARGIN_SENSITIVITY | B3_ONTOLOGY_False | 1328 | 934 | 518/416/350/44 | 0.513616 | 0.508868 | 0.834819 | 0.713502 | 0.703313 |
| CAMER_AV_MARGIN_SENSITIVITY | CONSTRUCT_audio-aligned | 1000 | 695 | 513/182/285/20 | 0.509993 | 0.508729 | 0.843793 | 0.757657 | 0.695000 |
| CAMER_AV_MARGIN_SENSITIVITY | CONSTRUCT_audio-aligned_DUAL | 120 | 111 | 69/42/9/0 | 0.540028 | 0.542961 | 0.794429 | 0.729626 | 0.925000 |
| CAMER_AV_MARGIN_SENSITIVITY | CONSTRUCT_video-aligned | 1000 | 655 | 241/414/303/42 | 0.569317 | 0.528199 | 0.753962 | 0.668593 | 0.655000 |
| CAMER_AV_MARGIN_SENSITIVITY | CONSTRUCT_video-aligned_DUAL | 96 | 95 | 39/56/1/0 | 0.499542 | 0.509844 | 0.898254 | 0.678839 | 0.989583 |

