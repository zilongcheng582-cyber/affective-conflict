# 05_CLAIM_EVIDENCE_MATRIX

POST_HOC_EXPLORATORY — CPU-only; frozen source models, thresholds, scalers, predictions and raw archives unchanged.

Six required research categories are separate. Statuses refer to the precise claim, never an entire dataset. Ranking versus probability-loss conclusions remain distinct. Original sixteen recovered claims are preserved and supplemented by nine Transfer/source/attribution claims.

## R1 Source Prediction

| id | hypothesis | status | sample_size | effect_CI_test_multiplicity | alternatives_not_excluded | source_and_code_trace |
| --- | --- | --- | --- | --- | --- | --- |
| R1_SOURCE | Within-source reliability features predict selected resolved source choices | ALREADY_SUPPORTED | 663rows/274utterances | Existing publication R1 entropy-onlyAUROC.803; no frozen transfer refit | selected DualReadable source population; association not causal mediation | reference R1 report; release results/post_audit/scientific_analysis_v1/R1_MODEL_COMPARISON.csv |

## R2 Compositionality

| id | hypothesis | status | sample_size | effect_CI_test_multiplicity | alternatives_not_excluded | source_and_code_trace |
| --- | --- | --- | --- | --- | --- | --- |
| R2_COMP | TWO_VS_ONE observed pairwise-to-trimodal consistency generalizes beyond item preference | NOT_ESTABLISHED | 402planned/294resolved/268matching;67items×6orders | Resolvedmatch.912; crossfit vsmajoritydelta−.024CI[−.135,.077] | item preference baseline explains primary pattern; ALL_DIFFERENT untested | reference R2 and release POST_AUDIT CPU replay |

## Frozen Transfer

| id | hypothesis | status | sample_size | effect_CI_test_multiplicity | alternatives_not_excluded | source_and_code_trace |
| --- | --- | --- | --- | --- | --- | --- |
| T_MCR_RANK | MCR retains frozen ranking and log-loss benefit against lawful source-fixed M0 | ALREADY_SUPPORTED | 1734/1818;909items | AUROC.727559CI[.677745,.776863];LL−M0−.432297CI[−.478847,−.380386] | later-added assertion regime; order, concentration, class imbalance; BA.5 | 04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv |
| T_LISTEN | Frozen probabilities improve LISTEN3C loss against lawfulM0 | CONTRADICTED | 167/378;381planned | LL−M0+.284528CI[+.168351,+.402273]; modestAUROC.605732 | ontology mismatch, source readability selection, single order, label-specific failures | LISTEN_JOINT_ONLY_REPORT.csv;04_TRANSFER_FAILURE_DECOMPOSITION.md |
| T_CA_SUPPORT | CA ontology-supported sourceprob proves full-target probability transfer | NOT_ESTABLISHED | 416/672;336conflictitems;717total supporteditems | AUROC.686394CI[.617947,.751111];LL−M0+.052293CI[−.031654,+.136540] | support-only supplementary projection; full primaryundefined | 04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv |
| T_CA_MARGIN | Full CA margin probabilities improve lawfulM0 loss | CONTRADICTED | 1350/2000;1000conflictitems | AUROC.573999CI[.535149,.613860];LL−M0+.085764CI[+.038995,+.129732] | weak ranking remains; cannot collapse ranking and calibration into one failure | 04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv |

## ERI1 Causal Intervention

| id | hypothesis | status | sample_size | effect_CI_test_multiplicity | alternatives_not_excluded | source_and_code_trace |
| --- | --- | --- | --- | --- | --- | --- |
| X2 | Audio noise reduces audio-side choice on ERI1eligibleconflicts | ALREADY_SUPPORTED | 146 | −10.96ppCI[−17.47,−4.45]; p=.00172;dialogueCI[−17.69,−4.42] | pipeline/generalnoise effects, partialOTHERmovement, no mediation/symmetry | reference/SCIENTIFIC_CLOSURE_FINAL_REPORT.md |

## Recovered Native Experiments

| id | hypothesis | status | sample_size | effect_CI_test_multiplicity | alternatives_not_excluded | source_and_code_trace |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Native MCR follows explicit conflicting emotion assertions | ALREADY_SUPPORTED | 1000 | 988/1000text match95%CI98.10–99.40%; source match6/1000 | Wrapper, candidate interface, source ambiguity; faithful cannot separate audio/text | rawnativeSHA; analysis.py::mcr |
| M2 | Faithful→adversarial flips almost all item outputs | NEW_EXPLORATORY_RESULT | 1000 | -98.80 pp, 95% CI [-99.49, -98.02] pp;992labelchanges; Holm6p=.0003MCfloor | Emotion assertion changes prescribedtarget; not latent reliability mechanism | 01_MCR_PAIRED_TRANSITIONS.csv; analysis.py::mcr |
| M3 | Irrelevant text leaves behavior unchanged | NOT_ESTABLISHED | 1000 | MatchΔ−1.30ppCI[−5.03,2.51]; Holm6p=.54355;572labelchanges | No equivalence margin; wrapper/content differences | MCRnumeric/secondary |
| M4 | Irrelevant text concentrates predictions on neutral while class effects cancel | NEW_EXPLORATORY_RESULT | 1000 | +35.90 pp, 95% CI [32.16, 39.72] pp;387→746neutral outputs; source-neutral+27.99pp, happy−36.97pp | Classimbalance468neutral, captionsemantics, wrapper, annotation ambiguity, unknown dialogue dependence | diagnostics.py; MCR_SECONDARY_DIAGNOSTICS.json |
| M5 | Native and controlled MCR estimate one poolable protocol | MEASUREMENT_INCOMPATIBLE | 909 | 909strictaudio/labeljoins;0exactfullprompt equality; nativeadv/controlledATagreement875/909 | system/context/order/candidate schedule and weightbyte identity unproven | MCR_NATIVE_CONTROLLED_PER_ITEM_JOIN.csv |
| C1 | 316CAdual matches means316conflicts | NOT_ESTABLISHED | 1500 | 316=108conflict+208consistent; exactly no316conflict claim | Pseudo-labels nottruth; subgroupdefinition | CAMER_ITEM_ELIGIBILITY_IDENTITY.csv |
| C2 | Observed dual source matching is associated with joint binary coverage | NEW_EXPLORATORY_RESULT | 108 | Dual102/108and104/108binary;OTHER6/108CI2.57–11.60%,4/108CI1.45–9.14%; full670/1000,680/1000 | Label/media/confidence selection and sharedscoring definitions; no causal readability manipulation | 02_CAMER_ELIGIBILITY_AND_COVERAGE.csv |
| C3 | Readable CAconflicts show stable global audio dominance/order effect | NOT_ESTABLISHED | 108 | A53/102=51.96%CI42.42–61.76%,55/104=52.88%CI43.27–62.26%; orderΔA+1.85ppCI[−6.48,11.11],Holm6p1 | limitedN/labelmix/speakerdependence | CAMER_RESULTS paired family |
| C4 | Aligned construction remains associated with joint choices on common source-label pairs | NEW_EXPLORATORY_RESULT | 759 | VIDEO−AUDIO SIDE_A−23.92ppCI[−32.84,−15.20]ATV;−28.89ppCI[−37.42,−20.56]VTA;12pointwiseintervals,noadjustedp | Residualsource/media/candidateinteractions; sparse stratum uncertainty | CAMER_LABEL_PAIR_STANDARDIZATION.csv |
| C5 | SevenclassB3 measures16classCAentropy | MEASUREMENT_INCOMPATIBLE | 1500 | 16classconfidenceNOT_MEASURED | Candidateontology & outputinterface mismatch | 00lock/B3hash; no refit |
| L1 | High LISTENOTHER persists afterbothobservedsource matches | NOT_ESTABLISHED | 22 | OTHER1/22=4.55%CI0.81–21.80%; nondual128/220; Δ−53.64ppCI[−63.18,−41.82],Holm3p2.689e−6 | complete label selection; tinyN; no generalization | 03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv |
| L2 | LISTEN supports generalnonridiculedual-readabilityarbitration | INSUFFICIENT_EVIDENCE | 0 | 0/22nonridicule; no rate/test defined | cannot estimate absent-supportbehavior | LISTEN_RESULT bylabel |
| L3 | LISTENOTHER is parsing failure or offered source labelabsence | NEW_EXPLORATORY_RESULT | 378 | 211validOTHER;124/211ridicule; bothsourcelabelsoffered381/381; parsefail0 | Sourceannotation validity, sarcasm/options/letterbias; noobjective correctness adjudication | LISTEN_OTHER_LABEL_DECOMPOSITION.csv |
| L4 | Native LISTENorder effect inferable by V3/V4pooling | NOT_IDENTIFIABLE | 381 | NoexecutedT_THEN_A;1149V3/V4prompt/choicearraysdiffer | versioninterventions confound order | recovered54register andV3/V4strictjoin |

## Transfer Failure Explanation

| id | hypothesis | status | sample_size | effect_CI_test_multiplicity | alternatives_not_excluded | source_and_code_trace |
| --- | --- | --- | --- | --- | --- | --- |
| X1 | Aunifiedcausalreliabilitymechanism transfersacrossdatasets | NOT_IDENTIFIABLE | different | R1AUROC.803entropyonly; correctedMCR.728,LISTEN.523,CA.574sensitivity; no sharedcausalestimand | dataset/prompt/interface/sourceconstruction/modelidentity confounds | 04synthesis/oldreport exactcopies |
| F_MCR_THRESHOLD | MCR BA.5 follows fixed threshold never crossing despite informative ranks | NEW_EXPLORATORY_RESULT | 1734binary | allp<.5;TP0/FN107/TN1627;meanp.019427vs prevalence.061707 | algebraic explanation, not unique causal text-reliability mechanism | phase4_numeric/TRANSFER_RESULTS.json;TRANSFER_FROZEN_LOGIT_DECOMPOSITION.csv |
| F_LISTEN_SELECTION | Strict dual LISTEN AUROC.759 rescues zero-refit probability transfer | NOT_ESTABLISHED | 22selected/21binary allridicule | strictAUROC95CI[.489796,.955882];LL.798549vsM0.695759 | source label restriction, tiny sample, selected coverage, no ontology-supported jointsourceprob | phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv |
| F_CA_ENTROPY | Sixteen-class entropy mismatch fully explains weaker CA association | INSUFFICIENT_EVIDENCE | no16classvectors;fullmargin dual206/216binary | margindualAUROC.573318CI[.477917,.671101];supportedvsoutside.715960/.513616descriptive | selection/construct/source-label readability/true behavior differences not factored | phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv;02_CAMER_UNIMODAL_JOINT_STRUCTURE.md |


