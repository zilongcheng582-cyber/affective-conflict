"""Integrate mandatory Phase4; update only independent reports and navigation memory."""
import phase4_transfer as a
import pathlib,json,csv,shutil,datetime,subprocess
O=a.O;P=a.P;R=a.R
HEADER='POST_HOC_EXPLORATORY — CPU-only; frozen source models, thresholds, scalers, predictions and raw archives unchanged.\n\n'
def md(n,s):(O/n).write_text('# '+n.removesuffix('.md')+'\n\n'+HEADER+s+'\n',encoding='utf8')
def f(v):return 'UNDEFINED' if v is None else f'{float(v):.6f}'
def table(rows,keys):
 return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(str(r.get(k,'')) for k in keys)+' |' for r in rows)+'\n'
def main():
 a.verify();z=a.read(O/'phase4_numeric/TRANSFER_RESULTS.json');rep=a.read(O/'04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv');sg=z['subgroups'];locks=a.read(O/'PHASE4_SOURCE_LOCK.json')+a.read(O/'PHASE4_ADDITIONAL_PROTOCOL_LOCK.json');binding=a.read(P/'frozen/source_model/binding.json');base=a.read(P/'results/post_audit/closure_v1/SOURCE_BASELINE_BINDING_V1.json')
 repeat=a.read(O/'phase4_replay_same_seed/PHASE4_REPLAY_CHECK.json');assert repeat['status']=='PASS'
 old=['04_RECOVERED_EVIDENCE_CROSS_STUDY_SYNTHESIS.md','05_CLAIM_EVIDENCE_MATRIX.md','CLAIM_EVIDENCE_MATRIX.csv','06_QWEN_NEXT_EXPERIMENT_DECISION.md','07_FINAL_SCIENTIFIC_EXECUTIVE_SUMMARY.md','RUN_PROVENANCE.json','REPLAY_INSTRUCTIONS.md','NAVIGATION_MEMORY_UPDATE.json','SHA256SUMS.txt','FINAL_VERIFICATION.json']
 backup=O/'phase4_before_update';backup.mkdir(exist_ok=False)
 for n in old:shutil.copy2(O/n,backup/n)
 registry=[]
 for x in locks:
  row=dict(x);p=pathlib.Path(x['path'])
  if x.get('records') is None and p.suffix=='.json':
   d=a.read(p);row['records']='JSON object' if isinstance(d,dict) else len(d)
  elif x.get('records') is None:row['records']='not row data'
  registry.append(row)
 for x in z['historical_binding_crosschecks']:registry.append({**x,'records':len(a.read(x['path'])) if x['path'].endswith('.csv') else 'bound historical source','git_blob_check':'ORIGINAL_BINDING_EXACT_HASH'})
 reg='''## Frozen chain and version resolution

Authoritative release checkout: `/root/autodl-tmp/affective-conflict-eri1/repo`, binding commit `34aa1b0340d906e5d625db7cb4a3def9199fa06e`. Every locked release asset was checked against `git show COMMIT:path`, not merely the working file name. The historical root has no Git runtime identity; original report/scaler/consumer hashes were separately matched to the binding. No fetch/reset/checkout or branch mutation was performed.

Source chain: Phase2 attempt002 2132 records →696 conflict order records→663 resolved source-fit records, 274 utterances (AT116/61, AV284/146, VT263/139 rows/utterances). The frozen pooled M3a/M3b use pair intercepts and shared strength/entropy/order slopes. They are not separately fitted AT or AV models. Later R1 publication cross-validation and posthoc entropy-only fits do not replace these historical transfer parameters. Source fitting/scaling used663 order rows; inference uncertainties cluster the underlying source item. R1 within-source prediction is not an external-transfer validation.

Original `protocols/emotiontalk/CROSS_REGIME_TRANSFER_SPEC_V1.*` names LISTEN and CA-MER; MCR enters the later zero-refit spec and remains a later-added exploratory label-assertion regime. The original zero-refit spec's displayed scaler values are superseded by the executed fit-time scaler provenance resolution. Replay uses the exact frozen binding and fit-time 663-row population, never its broader diagnostic population scalers. The model-freeze prose describes pair-specific order but the authoritative executed coefficient/consumer binding uses a shared order coefficient; this previously resolved distinction is explicitly retained.

Corrected measurement protocol, sequence assignment, evaluation plan and technical Amendment001 are registered below. They identify6354 scientific measurements/5515 acquired forwards. No16class target probabilities are present. The corrected B3 seven-class teacher-forced scores are distinct from discrete task generation and from historical stale feature columns. Both raw corrected JSONL copies match SHA256 `0ad7785530a52923dabdf3ec6b3c5afe27e68d87be61e1b5f4465fde79fad450`.

POST_AUDIT closure provides9219 row predictions and source-fixed comparisons with paired cluster percentile CIs (seed20261008,2000 replicates). Its scientific ruling is `REQUIRES_INTERPRETATION`: an executable binary acceptance rule was not predeclared. Historical `SURVIVES_WITH_CORRECTION` author interpretation is not recast as a confirmatory decision. This analysis reports metric-specific conclusions against lawful M0.

## Frozen coefficients, scalers and baselines

```json
'''+json.dumps({'models':binding['models'],'scalers':binding['scalers'],'baselines':base},indent=2)+'\n```\n\n'
 reg+='M0 is the earlier frozen source preference. M0+ORDER is the existing POST_AUDIT source-only fit on663 source records; its coefficients are read unchanged, not refitted here. Target-prevalence oracle constants are new diagnostics and are never lawful zero-refit competitors. Threshold0.5 and all inclusion rules remain fixed.\n\n## Exact evidence register\n\n'+table(registry,['path','sha256','records','git_blob_check'])
 md('04_TRANSFER_FROZEN_EVIDENCE_REGISTER.md',reg)
 rows=[]
 for role,v in z['routes'].items():
  rr=v['frozen_baseline_reports'];m=next(x for k,x in rr.items() if k.startswith('FROZEN'))
  rows.append({'route':role,'planned':v['planned'],'conflict':v['conflict'],'evaluable':v['evaluated'],'A/2/O/PF/TM':f"{v['SIDE_A']}/{v['SIDE_2']}/{v['OTHER']}/{v['PARSE_FAIL']}/{v['TECH_MISSING']}",'AUROC [95CI]':f"{f(v['AUROC'])} [{f(m['AUROC_CI_low'])},{f(m['AUROC_CI_high'])}]",'BA':f(v['balanced_accuracy']),'LL':f(v['log_loss']),'Brier':f(v['Brier_score']),'coverage':f(v['coverage']),'M0 LL':f(rr['M0']['log_loss']),'M0+ORDER LL':f(rr['M0_PLUS_ORDER']['log_loss']),'LL−M0 [95CI]':f"{f(m['log_loss_minus_M0'])} [{f(m['log_loss_minus_M0_CI_low'])},{f(m['log_loss_minus_M0_CI_high'])}]"})
 route_table=table(rows,list(rows[0]))
 selected=[]
 for x in sg:
  if x['route'] in ['LISTEN_3C_JOINT_ARBITRATION','CAMER_AV_MARGIN_SENSITIVITY','CAMER_AV_SUPPORT_LIMITED_SOURCEPROB'] and (x['group'] in ['DUAL_MATCH','STRICT_DUAL_CONTENT_MATCH','A_ONLY_MATCH','V_ONLY_MATCH','T_ONLY_MATCH','NEITHER_MATCH','UNOBSERVABLE','B3_ONTOLOGY_True','B3_ONTOLOGY_False'] or x['group'].startswith('CONSTRUCT_')):
   selected.append({'route':x['route'],'group':x['group'],'conflict':x['conflict'],'evaluable':x['evaluated'],'A/2/O/TM':f"{x['SIDE_A']}/{x['SIDE_2']}/{x['OTHER']}/{x['TECH_MISSING']}",'AUROC':f(x['AUROC']),'BA':f(x['balanced_accuracy']),'LL':f(x['log_loss']),'M0 LL':f(x['M0']['log_loss']),'coverage':f(x['coverage'])})
 failure='''## Replayed frozen routes

Coverage means binary-evaluable / prescribed conflicts, not GPU execution success. Source item IDs repeated across orders are not independent; MCR has909 items/905 distinct audio hashes with residual GT ambiguity; CA full conflict1000 items, support-limited336 items; LISTEN3C378 conflict items, historical mixed519 underlying UID clusters. Unknown CA speaker/source-video dependencies limit item-bootstrap transportability. All frozen CIs below are exact POST_AUDIT intervals, not newly optimized estimates.

'''+route_table+'''
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

'''+table(selected,list(selected[0]))
 md('04_TRANSFER_FAILURE_DECOMPOSITION.md',failure)
 linkage='''## Strict linkage and outcome preservation

`phase4_numeric/TRANSFER_RECOVERED_ROW_LINKAGE.csv`:5199 linked trial rows = MCR1818 + CA3000 + LISTEN381. Source item identity, both frozen evidence hashes/source labels where provided, and recovered observed outcomes are checked. MCR controlled-media textSHA comes from its frozen corrected measurement/outcome chain; native shares exact audio/GT only and has a different fullprompt. Native prompt mismatch is preserved, not bypassed.

MCR pairs909controlled items with native four conditions; no rerun needed for text-dependence characterization. CA joins1500 items' recovered raw6000keys, unilateral correctness-based source matches and original two joint arms; technical missing stays explicit. LISTEN joins381actual3C records to native choices, letter mapping, exact input hashes and observed unilateral matches; full-content strict dual22 is separately marked. Historical pooled rows are replayed but never converted into joint outcomes.

The previous reconciliation and recovered-science locks remain the provenance for raw original archives and code. New inference is not new evidence simply because an existing archive is newly projected. The original freeze contains stale embedded continuous features; all transfer features are recomputed from canonical corrected B3 raw vectors, with exact identity and seven-candidate order alignment.

## Replay checks

6354corrected measurements independently recomputed (H7,margin,source-label probability); probability sum tolerance1e−6. 9219frozen predictions matched maximum absolute error1.6653345369377348e−16 within1e−12. Six route/projection populations ×3models/baselines =18reports checked against exact identity SHA, N and metric tolerance1e−12. Every released locked asset matches its binding Git blob. Existing POST_AUDIT CIs retain seed20261008 and2000paired cluster draws; no scientific acceptance criterion is invented.

Independent repeat uses `phase4_replay.py NEW_DIRECTORY`: six deterministic numeric/table outputs exact SHA256match, including subgroup bootstrap projections. The five original source coefficient/scaler/consumer assets match the historical binding hashes. Record counts and exact source paths are in the evidence register; output identities are in SHA256SUMS.

## Non-poolable links and unresolved identity

Native MCR4000 and controlled3636generations use differing contracts; no common statistical denominator. LISTENV3 andV4 have incompatible random candidate schedules; no reverse-order join. CA discrete16class outputs are not correctedB3seven-class probabilities. Historical weight equality for native/controlled MCR cannot be asserted beyond recovered metadata/model path; the correctedB3content identity is separately bound. None of these gaps is repaired by substituting another version.
'''
 md('04_TRANSFER_RECOVERED_EVIDENCE_LINKAGE.md',linkage)
 claimrows=[
 {'id':'R1_SOURCE','category':'R1 Source Prediction','hypothesis':'Within-source reliability features predict selected resolved source choices','status':'ALREADY_SUPPORTED','sample_size':'663rows/274utterances','effect_CI_test_multiplicity':'Existing publication R1 entropy-onlyAUROC.803; no frozen transfer refit','alternatives_not_excluded':'selected DualReadable source population; association not causal mediation','source_and_code_trace':'reference R1 report; release results/post_audit/scientific_analysis_v1/R1_MODEL_COMPARISON.csv'},
 {'id':'R2_COMP','category':'R2 Compositionality','hypothesis':'TWO_VS_ONE observed pairwise-to-trimodal consistency generalizes beyond item preference','status':'NOT_ESTABLISHED','sample_size':'402planned/294resolved/268matching;67items×6orders','effect_CI_test_multiplicity':'Resolvedmatch.912; crossfit vsmajoritydelta−.024CI[−.135,.077]','alternatives_not_excluded':'item preference baseline explains primary pattern; ALL_DIFFERENT untested','source_and_code_trace':'reference R2 and release POST_AUDIT CPU replay'},
 {'id':'T_MCR_RANK','category':'Frozen Transfer','hypothesis':'MCR retains frozen ranking and log-loss benefit against lawful source-fixed M0','status':'ALREADY_SUPPORTED','sample_size':'1734/1818;909items','effect_CI_test_multiplicity':'AUROC.727559CI[.677745,.776863];LL−M0−.432297CI[−.478847,−.380386]','alternatives_not_excluded':'later-added assertion regime; order, concentration, class imbalance; BA.5','source_and_code_trace':'04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv'},
 {'id':'T_LISTEN','category':'Frozen Transfer','hypothesis':'Frozen probabilities improve LISTEN3C loss against lawfulM0','status':'CONTRADICTED','sample_size':'167/378;381planned','effect_CI_test_multiplicity':'LL−M0+.284528CI[+.168351,+.402273]; modestAUROC.605732','alternatives_not_excluded':'ontology mismatch, source readability selection, single order, label-specific failures','source_and_code_trace':'LISTEN_JOINT_ONLY_REPORT.csv;04_TRANSFER_FAILURE_DECOMPOSITION.md'},
 {'id':'T_CA_SUPPORT','category':'Frozen Transfer','hypothesis':'CA ontology-supported sourceprob proves full-target probability transfer','status':'NOT_ESTABLISHED','sample_size':'416/672;336conflictitems;717total supporteditems','effect_CI_test_multiplicity':'AUROC.686394CI[.617947,.751111];LL−M0+.052293CI[−.031654,+.136540]','alternatives_not_excluded':'support-only supplementary projection; full primaryundefined','source_and_code_trace':'04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv'},
 {'id':'T_CA_MARGIN','category':'Frozen Transfer','hypothesis':'Full CA margin probabilities improve lawfulM0 loss','status':'CONTRADICTED','sample_size':'1350/2000;1000conflictitems','effect_CI_test_multiplicity':'AUROC.573999CI[.535149,.613860];LL−M0+.085764CI[+.038995,+.129732]','alternatives_not_excluded':'weak ranking remains; cannot collapse ranking and calibration into one failure','source_and_code_trace':'04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv'},
 {'id':'F_MCR_THRESHOLD','category':'Transfer Failure Explanation','hypothesis':'MCR BA.5 follows fixed threshold never crossing despite informative ranks','status':'NEW_EXPLORATORY_RESULT','sample_size':'1734binary','effect_CI_test_multiplicity':'allp<.5;TP0/FN107/TN1627;meanp.019427vs prevalence.061707','alternatives_not_excluded':'algebraic explanation, not unique causal text-reliability mechanism','source_and_code_trace':'phase4_numeric/TRANSFER_RESULTS.json;TRANSFER_FROZEN_LOGIT_DECOMPOSITION.csv'},
 {'id':'F_LISTEN_SELECTION','category':'Transfer Failure Explanation','hypothesis':'Strict dual LISTEN AUROC.759 rescues zero-refit probability transfer','status':'NOT_ESTABLISHED','sample_size':'22selected/21binary allridicule','effect_CI_test_multiplicity':'strictAUROC95CI[.489796,.955882];LL.798549vsM0.695759','alternatives_not_excluded':'source label restriction, tiny sample, selected coverage, no ontology-supported jointsourceprob','source_and_code_trace':'phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv'},
 {'id':'F_CA_ENTROPY','category':'Transfer Failure Explanation','hypothesis':'Sixteen-class entropy mismatch fully explains weaker CA association','status':'INSUFFICIENT_EVIDENCE','sample_size':'no16classvectors;fullmargin dual206/216binary','effect_CI_test_multiplicity':'margindualAUROC.573318CI[.477917,.671101];supportedvsoutside.715960/.513616descriptive','alternatives_not_excluded':'selection/construct/source-label readability/true behavior differences not factored','source_and_code_trace':'phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv;02_CAMER_UNIMODAL_JOINT_STRUCTURE.md'}]
 original=a.read(backup/'CLAIM_EVIDENCE_MATRIX.csv')
 for x in original:x['category']='ERI1 Causal Intervention' if x['id']=='X2' else 'Transfer Failure Explanation' if x['id']=='X1' else 'Recovered Native Experiments';x['analysis_origin']='POST_HOC_EXPLORATORY'
 for x in claimrows:
  x['analysis_origin']='POST_HOC_EXPLORATORY';x['previously_reported']='Frozen numerical results cited; new explanatory projections explicitly labeled';x['exploratory_selection']='Original frozen populations unchanged; subgroup evidence does not replace primary';x['new_experiment_needed']='See06_QWEN_NEXT_EXPERIMENT_DECISION.md'
 allclaims=original+claimrows;a.csvsave('CLAIM_EVIDENCE_MATRIX.csv',allclaims)
 text='Six required research categories are separate. Statuses refer to the precise claim, never an entire dataset. Ranking versus probability-loss conclusions remain distinct. Original sixteen recovered claims are preserved and supplemented by nine Transfer/source/attribution claims.\n\n'
 for category in ['R1 Source Prediction','R2 Compositionality','Frozen Transfer','ERI1 Causal Intervention','Recovered Native Experiments','Transfer Failure Explanation']:
  text+='## '+category+'\n\n'+table([x for x in allclaims if x['category']==category],['id','hypothesis','status','sample_size','effect_CI_test_multiplicity','alternatives_not_excluded','source_and_code_trace'])+'\n'
 md('05_CLAIM_EVIDENCE_MATRIX.md',text)
 md('04_TRANSFER_CLAIM_BOUNDARY_MATRIX.md',table(claimrows,['id','category','hypothesis','status','sample_size','effect_CI_test_multiplicity','alternatives_not_excluded','source_and_code_trace'])+'''
## What transferred?

MCR frozen ranking and probability-loss improvement versus lawful source M0; CA supported supplementary ranking/BA association and weak full-margin ranking; modest LISTEN3C ranking association. These are conditional on each frozen projection, not evidence for universal zero-refit calibrated probabilities or a common causal mechanism. MCR remains a later-added exploratory assertion regime.

## What failed to transfer?

LISTEN3C and CAfullmargin probability loss are worse than lawful frozenM0 with positive paired95CIs. CA supported primary probability superiority is not established, rather than proven inferior. MCR frozen0.5threshold fails to recover audio choices (BA.5), despite better loss/ranking. LISTEN primarysourceprob and CAfullprimarysourceprob are structurally unsupported/undefined, not failed executed primary tests. No newly invented binary scientific acceptance rule is applied.

## What remains unidentified?

The relative roles of task ontology, source-label readability, prompt/assertion contracts, selection, order and real dataset behavior. Sixteen-class CA entropy; general non-ridicule LISTEN dual-readable joint response; source-domain versus target probability calibration mechanism; historic native/control exact weight equality; speaker-level independence; causal mediation and video symmetry. Oracle constants and selected-subgroup results cannot remove these gaps.
''')
 synthesis='''## Integrated evidence architecture

R1 is source-domain conditional prediction, R2 is TWO_VS_ONE consistency with a strong item-preference alternative, Frozen Transfer tests the same historical pooled equations on distinct target protocols, ERI1 supplies a selected-panel audio-noise causal intervention, and recovered native experiments expose protocol/label/readability behavior. Failure decomposition connects those lines without merging populations or identifying a common mechanism.

'''+route_table+'''
## Recovered native evidence and transfer explanation

MCR four-text native1000 has994faithful source matches versus6adversarial source matches and988adversarial text matches; this helps interpret the controlled transfer's text-heavy outcomes, but prompt/system/candidate interfaces differ. CA recovered discrete unilateral source matches explain major coverage/label changes while seven-class continuous features remain a separate construct; dual binary coverage improves without rescuing margin probability loss. LISTEN validOTHER choices and ridicule-only dual support make full3C and selected binary populations scientifically different. No unrun native experiment is inferred from an absent old scientific projection.

ERI1:2336trials/146selected items, source-side choice SNR00−RECODE−10.9589pp (95CI[−17.4658,−4.4521]),signflip p.001720; source entropy manipulation+.060772. No new ERI1 computation or frozen result modification. The intervention establishes a bounded audio-input effect, not mediation, universal transport, visual symmetry or conflict specificity. R1 source predictability and MCR target sorting do not make those stronger causal claims valid.

## Three separate closure conclusions

**What transferred?** Protocol-specific ranking information and, on MCR, a substantial loss improvement relative to source-fixedM0. CA supported diagnostic and LISTEN3C retain ranking association under their restrictions.

**What failed to transfer?** LISTEN3C and fullCA margin probability loss relative to lawfulM0; MCR fixed-threshold audio recall. CA support-only probability superiority remains unestablished. Undefined primary routes are not fabricated successful or failed tests.

**What remains unidentified?** Ontology/readability/selection/order/contract causal decomposition, missingCA16classcontinuous vectors, non-ridiculeLISTEN dual support, latent independence and unified reliability mechanism. The failures motivate prospective measurement validation, not retrospective optimization.

The final matrix separates all six mandatory categories and preserves negative evidence. The previous defaultSECOND_MODEL recommendation is superseded for the transfer-explanation objective by CPU measurement-design priority; a bounded descriptive manuscript may still stop Qwen acquisition and choose independent replication. See06forgoal-specific decisions. No experiment was designed or launched here.
'''
 md('04_RECOVERED_EVIDENCE_CROSS_STUDY_SYNTHESIS.md',synthesis)
 decision='''**NEXT_STEP = CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION** (recommendation only; no design or GPU execution in this task).

The completed Phase4 changes the reason for prioritization. Source-to-target ranking and probability loss separate; CA dual matching does not repair margin loss, while same-equation ontology-supported versus unsupported AUROC differs descriptively(.715960 vs.513616). LISTEN selected22ridicule cases cannot establish general transport and have no directsourceprob support. The previous defaultSECOND_MODEL is therefore superseded for explaining transfer failure: multiplying models before validating target measurement space can reproduce an unidentified construct mismatch.

No new Qwen GPU is required to report the present bounded evidence. If the next separately authorized objective is failure identification, the first action is a CPU-only prospective contract/identity/measurement design freeze. Do not assume3000newforwards; verify cached identity, requiredmodality/item coverage and correct16classcandidate interface before sizing any acquisition. No target refit, threshold adjustment or retrospective population selection is an admissible solution.

| Qwen priority | Existing candidate | Question resolved / useful null | What it still cannot resolve |
| --- | --- | --- | --- |
|1|B:CA-MER16classcontinuous measurement|Directly tests whether task-aligned probabilities change the weakseven-class feature association; a null result rejects that narrow measurement explanation|Discrete source matches already recovered; scorer versus JSONgeneration interface and sourcepseudo-label truth remain. Requires newCPUfreeze; noacquisitionauthorized|
|2|D:LISTENreverse, conditional on prospective ontology/readability support|Separates within-item order from fixed intercept if original fullidentity/choices held; null order contrast is informative|Standalone reversal of22ridicule-selected cases cannot cureontology/support mismatch or establish generalprobabilitytransfer. CPU feasibility/support comesfirst|
|3|C:EmotionTalkconsistentcontrol|Tests conflict-specific intervention response beyond currentselectedconflictERI1claim; a null interaction narrows specificity|Doesnotidentifyexternaltargetfailure;225consistent and146selectedconflict are different populations, baselineceiling andsourceoverlap requireCPUdesign|
|4|A:E1visualdegradation|Tests directional visual susceptibility/asymmetry|DoesnotaddressCA16classmeasurement orLISTENontology directly; doseequivalence/mediation undefined|

SECOND_MODEL remains useful for a different objective: testing whether the already qualified protocol-specific patterns recur across models. For a bounded manuscript without stronger transfer-mechanism claims, STOP Qwen acquisition and prioritize second-model replication when separately authorized. For failure attribution, validate measurement/support first. Neither branch is automatically executed.

Negative results have high decision value: if task-aligned CA confidence is still weak, wrong candidate ontology alone is insufficient; if a supported LISTEN counterbalance leaves probability loss worse, order alone is insufficient. Present observational subgroup numbers do not prove either causal explanation. Do not optimize for expected significance.
'''
 md('06_QWEN_NEXT_EXPERIMENT_DECISION.md',decision)
 summary='''强制 Phase4已完成，新增分析均为POST_HOC_EXPLORATORY。没有GPU、模型加载、重拟合、阈值调整、冻结结果修改或GitHub合并。

- 6354条corrected测量独立复核；9219条冻结预测全部匹配，最大绝对误差1.6653e−16；18组路线/基线报告的身份、样本数和指标通过1e−12容差；5199条恢复记录严格链接；6个CPU重放产物逐文件SHA一致。
- MCR：AUROC.727559，BA.50源于1734个预测全部低于.5；logloss.245884优于合法源固定M0.678181，不能将它概括为“迁移完全失败”。排序、概率损失和阈值分类分别报告。
- LISTEN3C：167/378二元可评估，211OTHER；AUROC.605732但logloss.981644差于合法M0.697116，差+.284528，95CI[+.168351,+.402273]。该M0不是targetoracle。双侧严格匹配仅22条、全部ridicule，选后AUROC.759259不能宣称新迁移成功。
- CA：支持本体诊断AUROC.686394但概率优势未建立；完整marginAUROC.573999且logloss差于M0。双侧匹配206/216可评估仍未挽救margin概率表现。七类与十六类测量不匹配、单模态源标签读出失败、选后总体变化和真实行为差异仍需分开，未保存十六类概率意味着完整熵解释未识别。

**What transferred：**有限的外部排序信息，及MCR相对合法M0的概率损失改善。

**What failed to transfer：**LISTEN3C和CA完整margin的概率损失优势；MCR固定阈值下音频召回。支持限定或结构未定义的路线不能冒充完整目标成功。

**What remains unidentified：**本体、可读性、顺序、输入契约、选择性覆盖和跨域行为各自的因果贡献；CA十六类连续特征、LISTEN非ridicule双侧支持等。

综合矩阵现分列R1、R2、FrozenTransfer、ERI1、RecoveredNative、FailureExplanation六类。若下一目标是解释迁移失败，优先建议CPU测量/支持方案冻结，潜在QwenGPU首位为CA十六类连续评分验证，LISTEN反序须先解决本体和支持；若仅写有限结论论文，可停止新增Qwen并另行考虑第二模型。未自动开始任何后续工作。

完整证据路径、SHA、记录数见04_TRANSFER_FROZEN_EVIDENCE_REGISTER.md；全部最终产物见SHA256SUMS.txt。本轮原始归档与冻结结果保持只读；仅按AGENTS既有授权追加三个导航docs，旧结论和修订前报告保留快照。
'''
 md('07_FINAL_SCIENTIFIC_EXECUTIVE_SUMMARY.md',summary)
 # Verify all frozen scientific sources before the already-authorized navigation append.
 a.verify()
 for x in a.read(O/'PHASE4_ADDITIONAL_PROTOCOL_LOCK.json'):assert a.sha(x['path'])==x['sha256']
 nav=[]
 for n in ['PROJECT_STATE.md','FILE_MAP.md','DECISIONS.md']:
  p=R/'docs'/n;b=backup/'docs'/n;b.parent.mkdir(exist_ok=True);shutil.copy2(p,b);before=a.sha(p)
  note='\n\n## Mandatory frozen Transfer integration — 2026-10-10\n\nPOST_HOC_EXPLORATORY Phase4 complete at '+str(O)+'. Frozen commit '+a.COMMIT+';6354measurements/9219predictions/18route-baselinechecks/5199strictlinks; CPU-only and6deterministicreplayhashmatches. MCRranking+source-fixedM0lossbenefit retained despiteBA.5; LISTEN3CprobabilitylossworseM0; CAfullmarginlossworseM0, support-limitedrankingnotfullprimarysuccess. LISTENdual22allridicule cannot rescuezero-refit; CAdual206/216binarydoesnotrescueprobabilities;16classcontinuousscoresmissing. Finalmatrixsixcategories; five04_TRANSFER_*deliverables andintegrated04/05/06/07reports. Fortransferfailureidentification NEXT_STEP=CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION, potentialQwenpriorityCA16classmeasurement thenLISTENorderconditionalonsupport; previousSECOND_MODELdefault supersededforthisobjective, stillappropriateforboundedreplicationgoal. NoGPU/refit/frozenchange/push/merge. Olddecisionspreserved; originalreportsbackedupinphase4_before_update.\n'
  p.write_text(p.read_text()+note,encoding='utf8');nav.append({'path':str(p),'backup_path':str(b),'before_sha256':before,'after_sha256':a.sha(p)})
 a.save('PHASE4_NAVIGATION_MEMORY_UPDATE.json',{'mode':'APPEND_ONLY_AUTHORIZED_BY_AGENTS','updates':nav})
 prior=a.read(O/'NAVIGATION_MEMORY_UPDATE.json')
 for x in prior['updates']:x['after_sha256']=next(u['after_sha256'] for u in nav if u['path']==x['path']);x['phase4_before_sha256']=next(u['before_sha256'] for u in nav if u['path']==x['path'])
 a.save('NAVIGATION_MEMORY_UPDATE.json',prior)
 provenance=a.read(O/'RUN_PROVENANCE.json');provenance['phase4']={'status':'COMPLETE','analysis_origin':'POST_HOC_EXPLORATORY','source_commit':a.COMMIT,'measurements':6354,'predictions':9219,'route_baseline_reports':18,'strict_links':5199,'repeat':repeat,'NEXT_STEP':'CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION','bounded_manuscript_alternative':'SECOND_MODEL_WITHOUT_ADDITIONAL_QWEN','GPU':False,'refit':False,'code_sha256':{n:a.sha(O/n) for n in ['phase4_transfer.py','phase4_supplement.py','phase4_replay.py','phase4_finalize.py']},'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};provenance['NEXT_STEP']='CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION';provenance['mandatory_phase4_complete']=True;a.save('RUN_PROVENANCE.json',provenance)
 inst=(O/'REPLAY_INSTRUCTIONS.md').read_text()+'\n\n## Mandatory Phase4 replay\n\nRun `python3 '+str(O/'phase4_replay.py')+' NEW_EMPTY_DIRECTORY`. It reads frozen release/archival assets, uses exact pre-append navigation backups, repeats fixed-coefficient prediction and descriptive subgroup calculations, then checks six deterministic outputs against SHA256. It never refits any model. Source locks and the navigation update records must remain present. Previous Phase1–3 replay remains valid with original byte-identical reference backups.\n';(O/'REPLAY_INSTRUCTIONS.md').write_text(inst)
 a.save('PHASE4_COMPLETION_RECEIPT.json',{'status':'COMPLETE','all_claim_categories_present':sorted({x['category'] for x in allclaims}),'claim_count':len(allclaims),'GPU':False,'frozen_results_modified':False,'historical_archive_modified':False,'navigation_only_history_changes':nav,'target_fit':False,'pilot_pooled':False,'source_commit':a.COMMIT,'NEXT_STEP':'CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION'})
 print('PHASE4_REPORTS_AND_NAVIGATION_COMPLETE',len(allclaims),flush=True)
if __name__=='__main__':main()
