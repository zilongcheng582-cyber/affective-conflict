# 04_TRANSFER_CLAIM_BOUNDARY_MATRIX

POST_HOC_EXPLORATORY — CPU-only; frozen source models, thresholds, scalers, predictions and raw archives unchanged.

| id | category | hypothesis | status | sample_size | effect_CI_test_multiplicity | alternatives_not_excluded | source_and_code_trace |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1_SOURCE | R1 Source Prediction | Within-source reliability features predict selected resolved source choices | ALREADY_SUPPORTED | 663rows/274utterances | Existing publication R1 entropy-onlyAUROC.803; no frozen transfer refit | selected DualReadable source population; association not causal mediation | reference R1 report; release results/post_audit/scientific_analysis_v1/R1_MODEL_COMPARISON.csv |
| R2_COMP | R2 Compositionality | TWO_VS_ONE observed pairwise-to-trimodal consistency generalizes beyond item preference | NOT_ESTABLISHED | 402planned/294resolved/268matching;67items×6orders | Resolvedmatch.912; crossfit vsmajoritydelta−.024CI[−.135,.077] | item preference baseline explains primary pattern; ALL_DIFFERENT untested | reference R2 and release POST_AUDIT CPU replay |
| T_MCR_RANK | Frozen Transfer | MCR retains frozen ranking and log-loss benefit against lawful source-fixed M0 | ALREADY_SUPPORTED | 1734/1818;909items | AUROC.727559CI[.677745,.776863];LL−M0−.432297CI[−.478847,−.380386] | later-added assertion regime; order, concentration, class imbalance; BA.5 | 04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv |
| T_LISTEN | Frozen Transfer | Frozen probabilities improve LISTEN3C loss against lawfulM0 | CONTRADICTED | 167/378;381planned | LL−M0+.284528CI[+.168351,+.402273]; modestAUROC.605732 | ontology mismatch, source readability selection, single order, label-specific failures | LISTEN_JOINT_ONLY_REPORT.csv;04_TRANSFER_FAILURE_DECOMPOSITION.md |
| T_CA_SUPPORT | Frozen Transfer | CA ontology-supported sourceprob proves full-target probability transfer | NOT_ESTABLISHED | 416/672;336conflictitems;717total supporteditems | AUROC.686394CI[.617947,.751111];LL−M0+.052293CI[−.031654,+.136540] | support-only supplementary projection; full primaryundefined | 04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv |
| T_CA_MARGIN | Frozen Transfer | Full CA margin probabilities improve lawfulM0 loss | CONTRADICTED | 1350/2000;1000conflictitems | AUROC.573999CI[.535149,.613860];LL−M0+.085764CI[+.038995,+.129732] | weak ranking remains; cannot collapse ranking and calibration into one failure | 04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv |
| F_MCR_THRESHOLD | Transfer Failure Explanation | MCR BA.5 follows fixed threshold never crossing despite informative ranks | NEW_EXPLORATORY_RESULT | 1734binary | allp<.5;TP0/FN107/TN1627;meanp.019427vs prevalence.061707 | algebraic explanation, not unique causal text-reliability mechanism | phase4_numeric/TRANSFER_RESULTS.json;TRANSFER_FROZEN_LOGIT_DECOMPOSITION.csv |
| F_LISTEN_SELECTION | Transfer Failure Explanation | Strict dual LISTEN AUROC.759 rescues zero-refit probability transfer | NOT_ESTABLISHED | 22selected/21binary allridicule | strictAUROC95CI[.489796,.955882];LL.798549vsM0.695759 | source label restriction, tiny sample, selected coverage, no ontology-supported jointsourceprob | phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv |
| F_CA_ENTROPY | Transfer Failure Explanation | Sixteen-class entropy mismatch fully explains weaker CA association | INSUFFICIENT_EVIDENCE | no16classvectors;fullmargin dual206/216binary | margindualAUROC.573318CI[.477917,.671101];supportedvsoutside.715960/.513616descriptive | selection/construct/source-label readability/true behavior differences not factored | phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv;02_CAMER_UNIMODAL_JOINT_STRUCTURE.md |

## What transferred?

MCR frozen ranking and probability-loss improvement versus lawful source M0; CA supported supplementary ranking/BA association and weak full-margin ranking; modest LISTEN3C ranking association. These are conditional on each frozen projection, not evidence for universal zero-refit calibrated probabilities or a common causal mechanism. MCR remains a later-added exploratory assertion regime.

## What failed to transfer?

LISTEN3C and CAfullmargin probability loss are worse than lawful frozenM0 with positive paired95CIs. CA supported primary probability superiority is not established, rather than proven inferior. MCR frozen0.5threshold fails to recover audio choices (BA.5), despite better loss/ranking. LISTEN primarysourceprob and CAfullprimarysourceprob are structurally unsupported/undefined, not failed executed primary tests. No newly invented binary scientific acceptance rule is applied.

## What remains unidentified?

The relative roles of task ontology, source-label readability, prompt/assertion contracts, selection, order and real dataset behavior. Sixteen-class CA entropy; general non-ridicule LISTEN dual-readable joint response; source-domain versus target probability calibration mechanism; historic native/control exact weight equality; speaker-level independence; causal mediation and video symmetry. Oracle constants and selected-subgroup results cannot remove these gaps.

