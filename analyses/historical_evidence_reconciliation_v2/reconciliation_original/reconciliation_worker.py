import csv,json,hashlib,re,collections,math,zipfile,tarfile
from pathlib import Path
R=Path('/root/autodl-tmp/affective-conflict');E=Path('/root/autodl-tmp/affective-conflict-forensics-expanded-v1');O=Path('/root/autodl-tmp/affective-conflict-reconciliation-v2')
proof={};errors=[]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def register(p,role,records=None):
 p=Path(p);proof[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'records':records,'role':role};return proof[str(p)]['sha256']
def jl(p):
 p=Path(p);rs=[json.loads(l) for l in open(p) if l.strip()];register(p,'historical JSONL input',len(rs));return rs
def tab(p):
 p=Path(p);rs=list(csv.DictReader(open(p)));register(p,'historical CSV input',len(rs));return rs
def save(n,d):(O/n).write_text(json.dumps(d,indent=2,ensure_ascii=False))
def csvsave(n,rs):
 if not rs:return
 with open(O/n,'x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader()
  for r in rs:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
inspect=json.loads((O/'TARGETED_INSPECTION.json').read_text());reg=tab(E/'RECOVERED_EXPERIMENT_EXECUTION_REGISTER.csv')
for name in ['FULL_EXPERIMENT_RECOVERY_REPORT.md','MCR_NATIVE_FOUR_CONDITION_RECOVERY.json']:register(E/name,'expanded forensics priority')
for name in ['AGENTS.md','docs/PROJECT_STATE.md','docs/FILE_MAP.md','docs/DECISIONS.md']:register(R/name,'read-only operating/navigation reference')
# Reconcile exactly the recovered 54 paths; never merge different attempts by last-row overwrite.
actual_reverse=[];runlist=[]
for item in reg:
 rs=jl(item['path']);assert proof[item['path']]['sha256']==item['sha256'];assert len(rs)==int(item['rows'])
 rev=[r for r in rs if any(r.get(k)=='T_THEN_A' for k in ['arm','order','presentation_order','condition'])]
 execution=[r for r in rev if r.get('generation_success') is True or any(r.get(k) for k in ['raw_model_output','raw_generated_sequence','assistant_text'])]
 if rev:actual_reverse.append({'path':item['path'],'sha256':item['sha256'],'rows':len(rs),'reverse_rows':len(rev),'reverse_executed':len(execution),'LISTEN': 'LISTEN' in item['path'] or any(str(r.get('dataset','')).upper()=='LISTEN' for r in rev)})
 if 'LISTEN' in item['path']:
  status='FULL' if len(rs)==1149 else 'PILOT_TECHNICAL_GATE' if len(rs)==6 else 'PLANNED_OR_EMPTY' if not any(r.get('generation_success') or r.get('raw_generated_sequence') for r in rs) else 'PARTIAL'
  runlist.append({'path':item['path'],'sha256':item['sha256'],'records':len(rs),'execution_stage':status,'scientific_role':'SUPERSEDED_DIAGNOSTIC' if 'V3/' in item['path'] else 'SOURCE_ALIGNED_V4' if 'V4' in item['path'] else 'PLAN','reverse_executed':len(execution)})
save('RECOVERED_54_RUN_RECONCILIATION.json',{'paths_verified':len(reg),'reverse_records_by_file':actual_reverse,'listen_run_status':runlist,'listen_executed_reverse_rows':sum(r['reverse_executed'] for r in actual_reverse if r['LISTEN'])})
# Related code/checkpoints already inventoried by expanded forensics, plus its explicit supplement.
sourcehits=[];checkpointresults=[]
paths=[Path(f['path']) for f in inspect['selected_inventory']]+[Path(f['path']) for f in json.loads((E/'OWN_CODE_AND_CHECKPOINT_SUPPLEMENT.json').read_text())['files']]
for p in dict.fromkeys(paths):
 if p.suffix in ['.py','.md','.json','.sh'] and 'LISTEN' in str(p).upper():
  text=p.read_text(errors='replace')
  if 'T_THEN_A' in text:sourcehits.append({'path':str(p),'sha256':register(p,'LISTEN reverse mention source'),'lines':[{'line':i+1,'text':l} for i,l in enumerate(text.splitlines()) if 'T_THEN_A' in l]})
  if p.suffix=='.json' and ('checkpoint' in p.name.lower() or 'results' in p.name.lower()):
   d=json.loads(text);records=d.get('results',[]) if isinstance(d,dict) else d if isinstance(d,list) else []
   checkpointresults.append({'path':str(p),'sha256':register(p,'LISTEN related JSON checkpoint',len(records)),'result_records':len(records),'executed_reverse':sum(isinstance(x,dict) and x.get('presentation_order',x.get('arm'))=='T_THEN_A' for x in records)})
save('LISTEN_CODE_CHECKPOINT_AUDIT_V2.json',{'code_reverse_mentions':sourcehits,'json_checkpoints':checkpointresults})
# Complete answer/letter/option reconstruction and exact V3 -> V4 join.
L4=R/'audit/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED';L3=R/'audit/QWEN25_LISTEN_NATIVE_V3'
can={r['v4_primary_key']:r for r in tab(L4/'LISTEN_V4_CANONICAL_AT_JOIN_V1.csv')};summary={};recovered={};manifests={}
for version,rawp,mp in [('V3',L3/'listen_native_raw_outputs_local_v3.jsonl',L3/'listen_native_manifest_local_v3.csv'),('V4',R/'results/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/listen_native_raw_outputs_source_aligned_v4.jsonl',L4/'listen_native_manifest_source_aligned_v4.csv')]:
 data=jl(rawp);manifest={r['manifest_row_id']:r for r in tab(mp)};manifests[version]=manifest;out=[];counts=collections.defaultdict(collections.Counter)
 for r in data:
  key=r['manifest_row_id'];m=manifest[key];choices=json.loads(r['choices_after_shuffle']);letter=r.get('parsed_letter');label=choices[ord(letter)-65] if letter and 0<=ord(letter)-65<len(choices) else None
  c=can.get(key);identity=bool(c and all(str(r.get(k))==str(manifests.get('V4',manifest).get(key,{}).get(k)) for k in ['condition','dataset_row_index','original_sample_id','audio_hash','transcription_hash'])) if version=='V4' else None
  side='PARSE_FAIL' if label is None else 'SAME_LABEL_MATCH' if c and c['y_A']==c['y_T']==label else 'SIDE_A' if c and label==c['y_A'] else 'SIDE_T' if c and label==c['y_T'] else 'OTHER'
  z={'version':version,'key':key,'condition':r['condition'],'source_id':r['original_sample_id'],'dataset_row_index':r['dataset_row_index'],'audio_sha256':r['audio_hash'],'text_sha256':r['transcription_hash'],'parsed_letter':letter,'parsed_label_recovered':label,'candidate_letter_map':{chr(65+i):x for i,x in enumerate(choices)},'candidate_sequence':choices,'prompt_hash':r['prompt_hash'],'expected_label':r['expected_label'],'source_label_correct':label==r['expected_label'],'raw_model_output':r.get('assistant_text'),'raw_generated_sequence':r.get('raw_generated_sequence'),'outcome_class_against_V4_labels':side,'source_path':str(rawp),'source_sha256':proof[str(rawp)]['sha256']}
  out.append(z);counts[r['condition']]['rows']+=1;counts[r['condition']]['correct']+=z['source_label_correct'];counts[r['condition']][side]+=1;counts[r['condition']]['raw_present']+=bool(r.get('raw_generated_sequence'))
 recovered[version]={r['key']:r for r in out};csvsave('LISTEN_'+version+'_ANSWER_OPTION_RECOVERY_V2.csv',out)
 summary[version]={'by_condition':{k:dict(v) for k,v in counts.items()},'raw_path':str(rawp),'raw_sha256':proof[str(rawp)]['sha256'],'manifest_path':str(mp),'manifest_sha256':proof[str(mp)]['sha256'],'model_revision_values':sorted({str(r.get('model_revision')) for r in data})}
join=[]
for key,z in recovered['V3'].items():
 v=recovered['V4'].get(key);a=manifests['V3'][key];b=manifests['V4'].get(key,{})
 matches={k:str(a.get(k))==str(b.get(k)) for k in ['condition','dataset_row_index','original_sample_id','audio_hash','transcription_hash']};strict=all(matches.values())
 join.append({'v3_key':key,'v4_key':v['key'] if v else None,'strict_source_content_match':strict,'identity_checks':matches,'candidate_sequence_equal':bool(v and z['candidate_sequence']==v['candidate_sequence']),'prompt_hash_equal':bool(v and z['prompt_hash']==v['prompt_hash']),'v3_label':z['parsed_label_recovered'],'v4_label':v['parsed_label_recovered'] if v else None,'scientific_pooling_allowed':False})
csvsave('LISTEN_V3_V4_STRICT_IDENTITY_JOIN_V2.csv',join)
gates=[]
def baseid(s):return re.sub(r'_3[ABC]$','',s)
for version in ['V3','V4']:
 vals=list(recovered[version].values());audio=collections.defaultdict(list);text=collections.defaultdict(list);textlogical=collections.defaultdict(list)
 for r in vals:
  if r['condition']=='3B':audio[(r['audio_sha256'],r['text_sha256'])].append(r)
  if r['condition']=='3A':text[(r['audio_sha256'],r['text_sha256'])].append(r);textlogical[(baseid(r['source_id']),r['text_sha256'])].append(r)
 for r in vals:
  if r['condition']!='3C':continue
  aa=audio[(r['audio_sha256'],r['text_sha256'])];tt=text[(r['audio_sha256'],r['text_sha256'])];tl=textlogical[(baseid(r['source_id']),r['text_sha256'])]
  # A text-only observation never used its accompanying audio: retain this separate validated-input join.
  gate={'version':version,'joint_key':r['key'],'source_id':r['source_id'],'audio_sha256':r['audio_sha256'],'text_sha256':r['text_sha256'],'audio_unique_matches':len(aa),'text_full_content_unique_matches':len(tt),'text_source_id_and_actual_input_matches':len(tl),'audio_correct':aa[0]['source_label_correct'] if len(aa)==1 else None,'text_full_content_correct':tt[0]['source_label_correct'] if len(tt)==1 else None,'text_input_correct':tl[0]['source_label_correct'] if len(tl)==1 else None,'dual_correct_full_content':len(aa)==len(tt)==1 and aa[0]['source_label_correct'] and tt[0]['source_label_correct'],'dual_correct_actual_input':len(aa)==len(tl)==1 and aa[0]['source_label_correct'] and tl[0]['source_label_correct'],'actual_joint_eligibility':'TECHNICAL_GATE_PASS_ONLY','joint_outcome':r['outcome_class_against_V4_labels'],'joint_label':r['parsed_label_recovered']}
  gates.append(gate)
csvsave('LISTEN_UNIMODAL_CORRECTNESS_JOIN_V2.csv',gates)
summary['strict_v3_v4_join']={'rows':len(join),'identity_matched':sum(r['strict_source_content_match'] for r in join),'candidate_sequence_equal':sum(r['candidate_sequence_equal'] for r in join),'prompt_hash_equal':sum(r['prompt_hash_equal'] for r in join),'pooling_allowed':False}
summary['gating']={v:{'joint_rows':sum(r['version']==v for r in gates),'audio_unique':sum(r['version']==v and r['audio_unique_matches']==1 for r in gates),'text_full_content_unique':sum(r['version']==v and r['text_full_content_unique_matches']==1 for r in gates),'text_actual_input_unique':sum(r['version']==v and r['text_source_id_and_actual_input_matches']==1 for r in gates),'dual_correct_full_content':sum(r['version']==v and r['dual_correct_full_content'] for r in gates),'dual_correct_actual_input':sum(r['version']==v and r['dual_correct_actual_input'] for r in gates)} for v in ['V3','V4']}
save('LISTEN_RECONCILIATION_V2.json',summary);print('LISTEN_DONE',summary['strict_v3_v4_join'],summary['gating'],flush=True)
# CA-MER all 6000 scientific keys, raw row references, no last-attempt pooling.
C=R/'audit/QWEN25_CAMER_CONTROLLED_V1';idx=tab(C/'scientific_equivalence_v1/CAMER_CONTROLLED_AVAILABLE_SCIENTIFIC_OUTCOMES_V1.csv');rawp=C/'resource_sweep_v1/qwen25_camer_controlled_resource_sweep_v1.jsonl';raw=jl(rawp);meta={r['sample_id']:r for r in jl(C/'camer_controlled_manifest_v1.jsonl')};cs=collections.defaultdict(collections.Counter);mis=collections.Counter();crows=[];correct=collections.defaultdict(set);oom=collections.defaultdict(set);scorefields=set();seen=set()
for r in idx:
 key=(r['sample_id'],r['arm']);assert key not in seen;seen.add(key);a=r['arm'];s=r['sample_id'];m=meta[s];rr=raw[int(r['resource_sweep_row'])-1]
 for field in ['sample_id','arm','parsed_label']:
  if str(rr.get(field) or '')!=str(r.get(field) or ''):mis['index_raw_'+field]+=1
 if r['original_output_sha256']!=proof[str(rawp)]['sha256']:mis['source_hash']+=1
 for field in ['audio_sha256','silent_video_sha256']:
  if rr.get(field) and rr[field]!=m[field]:mis[field]+=1
 cand=m.get('candidate_order',m.get('candidate_sequence'));mis['candidate_sequence']+=rr.get('candidate_sequence')!=cand
 cs[a]['planned_keys']+=1;cs[a]['generation_success']+=rr.get('generation_status')=='SUCCESS';cs[a]['raw_saved']+=bool(rr.get('raw_model_output'));cs[a]['scientific_available']+=r['scientific_available'].lower()=='true';cs[a]['parser_'+r['parser_status']]+=1;cs[a]['accounting_'+r['accounting_class']]+=1
 if rr.get('cuda_oom') or rr.get('oom_skipped'):oom[a].add(s)
 if a in ['A_ONLY','V_ONLY'] and rr.get('parsed_label')==m['y_A' if a=='A_ONLY' else 'y_V']:correct[a].add(s)
 for k in rr:
  if re.search('logit|logprob|log_prob|probabilit|entropy|candidate_score',k,re.I):scorefields.add(k)
 crows.append({'sample_id':s,'arm':a,'scientific_available':r['scientific_available'],'accounting_class':r['accounting_class'],'generation_status':rr.get('generation_status'),'parse_status':r['parser_status'],'parsed_label':rr.get('parsed_label'),'y_A':m['y_A'],'y_V':m['y_V'],'source_label_correct':rr.get('parsed_label')==m['y_A' if a=='A_ONLY' else 'y_V'] if a in ['A_ONLY','V_ONLY'] else None,'raw_model_output':rr.get('raw_model_output'),'audio_sha256':rr.get('audio_sha256'),'video_sha256':rr.get('silent_video_sha256'),'candidate_sequence':rr.get('candidate_sequence'),'source_row':int(r['resource_sweep_row']),'source_path':str(rawp),'source_sha256':proof[str(rawp)]['sha256'],'raw_run_type':rr.get('run_type'),'raw_scientific_result':rr.get('scientific_result')})
csvsave('CAMER_6000_KEY_RECONCILIATION_V2.csv',crows)
cpairs=[]
for s,m in meta.items():
 cpairs.append({'sample_id':s,'readable_A':s in correct['A_ONLY'],'readable_V':s in correct['V_ONLY'],'dual_readable':s in correct['A_ONLY']&correct['V_ONLY'],'video_and_both_joint_oom':all(s in oom[a] for a in ['V_ONLY','A_THEN_V','V_THEN_A'])})
csvsave('CAMER_UNIMODAL_READABILITY_JOIN_V2.csv',cpairs)
b3p=Path('/root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/outputs/B3_MEASUREMENTS_V1.jsonl');b3=jl(b3p);bc=collections.defaultdict(collections.Counter);berrors=[];brows=[]
for r in b3:
 if r['dataset']!='CA-MER':continue
 a=r['modality'];s=r['stable_dataset_id'];p=r['candidate_probabilities'];lab=r['candidate_labels'];v=r['candidate_log_scores'];h=-sum(x*math.log(x) for x in p if x>0)/math.log(len(p));bc[a]['rows']+=1;bc[a]['seven_candidates']+=len(p)==len(lab)==len(v)==7;bc[a]['sixteen_candidates']+=len(p)==16
 if abs(sum(p)-1)>1e-9 or any(not math.isfinite(x) or x<0 for x in p):berrors.append((s,a,'invalid_probability'))
 if abs(h-r['normalized_entropy'])>1e-9:berrors.append((s,a,'entropy_mismatch'))
 if r['evidence_hash']!=meta[s]['audio_sha256' if a=='A' else 'silent_video_sha256']:berrors.append((s,a,'identity_mismatch'))
 brows.append({'sample_id':s,'modality':a,'candidate_count':len(p),'evidence_sha256':r['evidence_hash'],'normalized_entropy_recomputed_7class':h,'normalized_entropy_saved':r['normalized_entropy'],'source_path':str(b3p),'source_sha256':proof[str(b3p)]['sha256']})
csvsave('CAMER_B3_SEVEN_CLASS_CPU_VERIFICATION_V2.csv',brows)
cam={'scientific_index_path':str(C/'scientific_equivalence_v1/CAMER_CONTROLLED_AVAILABLE_SCIENTIFIC_OUTCOMES_V1.csv'),'unique_keys':len(seen),'arms':{a:dict(v) for a,v in cs.items()},'identity_mismatches':dict(mis),'label_readable_A':len(correct['A_ONLY']),'label_readable_V':len(correct['V_ONLY']),'dual_readable':len(correct['A_ONLY']&correct['V_ONLY']),'oom_by_arm':{a:len(v) for a,v in oom.items()},'same_58_video_joint_oom':oom['V_ONLY']==oom['A_THEN_V']==oom['V_THEN_A'],'generation_score_fields':sorted(scorefields),'corrected_B3':{'path':str(b3p),'sha256':proof[str(b3p)]['sha256'],'all_dataset_rows':len(b3),'arms':{a:dict(v) for a,v in bc.items()},'errors':berrors},'sixteen_class_entropy_cpu_recoverable':False,'reason':'No complete 16-candidate numeric scores/probabilities in recovered generation artifacts; seven-class B3 cannot identify missing candidate mass.'}
save('CAMER_RECONCILIATION_V2.json',cam);print('CAMER_DONE',cam['arms'],flush=True)
# MCR original 1000 native items and actual 909 controlled items, byte hashes and unique source indices.
N=R/'audit/QWEN25_MCR_NATIVE_V1';P=R/'audit/QWEN25_MCR_CONTROLLED_V3';nm=jl(N/'mcr_ser_native_qwen25_manifest_v1.jsonl');nr=jl(N/'full_run/qwen25_mcr_native_full_v1.jsonl');cm=jl(P/'mcr_controlled_arbitration_manifest_v2.jsonl');cr=jl(P/'full_run/qwen25_mcr_controlled_full_v2.jsonl');ng=collections.defaultdict(dict);rg=collections.defaultdict(dict);cg=collections.defaultdict(dict);craw=collections.defaultdict(dict)
for r in nm:assert r['condition'] not in ng[r['source_index']];ng[r['source_index']][r['condition']]=r
for r in nr:assert r['condition'] not in rg[r['source_index']];rg[r['source_index']][r['condition']]=r
for r in cm:assert r['arm'] not in cg[r['source_index']];cg[r['source_index']][r['arm']]=r
for r in cr:assert r['arm'] not in craw[r['source_index']];craw[r['source_index']][r['arm']]=r
conditions={'neutral','faithful','adversarial','irrelevant'};mjoin=[];paired=[];nativecounts=collections.defaultdict(collections.Counter);hashes=collections.Counter();identityerrors=[]
for i,group in ng.items():
 assert set(group)==set(rg[i])==conditions
 ref=group['neutral'];ap=Path(ref['audio_abspath']);ah=sha(ap);register(ap,'targeted original MCR audio byte identity',None);hashes[ah]+=1;ctrl=cg.get(i);match=False;ch=None
 if ctrl:
  ca=ctrl['A_ONLY'];cap=ap.parent.parent/ca['audio'];ch=sha(cap);match=ah==ch and ref['audio_relpath']==ca['audio'] and ref['gt']==ca['y_audio']
  if not match:identityerrors.append(i)
 mjoin.append({'source_index':i,'native_sample_id':ref['sample_id'],'native_audio_path':str(ap),'native_audio_sha256':ah,'native_gt':ref['gt'],'controlled_sample_id':ctrl['A_ONLY']['sample_id'] if ctrl else None,'controlled_audio_sha256':ch,'source_index_path_hash_label_match':match,'controlled_included':bool(ctrl),'native_conditions':sorted(group),'four_native_outputs_present':len(rg[i])==4,'native_adversarial_source_text':group['adversarial']['source_text'],'controlled_text_evidence':ctrl['A_THEN_T']['text_evidence'] if ctrl else None,'native_source_text_sha256':hashlib.sha256(group['adversarial']['source_text'].encode()).hexdigest(),'controlled_text_sha256':hashlib.sha256(ctrl['A_THEN_T']['text_evidence'].encode()).hexdigest() if ctrl else None})
 for condition,m in group.items():
  r=rg[i][condition];assert r['sample_id']==m['sample_id'] and r['audio_abspath']==m['audio_abspath'] and r['gt']==m['gt'];nativecounts[condition]['rows']+=1;nativecounts[condition]['generation_success']+=r['generation_success'] is True;nativecounts[condition]['parse_'+r['parse_status']]+=1;nativecounts[condition]['raw_saved']+=bool(r['raw_model_output'])
  paired.append({'source_index':i,'native_sample_id':ref['sample_id'],'audio_sha256':ah,'condition':condition,'source_text':m['source_text'],'source_text_sha256':hashlib.sha256(m['source_text'].encode()).hexdigest(),'gt':m['gt'],'parsed_label':r['parsed_label'],'parse_status':r['parse_status'],'raw_model_output':r['raw_model_output'],'controlled_population_member':bool(ctrl),'source_record_key':r['record_key'],'source_path':str(N/'full_run/qwen25_mcr_native_full_v1.jsonl'),'source_sha256':proof[str(N/'full_run/qwen25_mcr_native_full_v1.jsonl')]['sha256']})
csvsave('MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.csv',mjoin);csvsave('MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.csv',paired)
mcr={'native_items':len(ng),'native_records':len(nr),'controlled_items':len(cg),'controlled_records':len(cr),'matched_controlled_items':sum(r['source_index_path_hash_label_match'] for r in mjoin),'native_not_controlled':len(set(ng)-set(cg)),'controlled_not_native':len(set(cg)-set(ng)),'distinct_native_audio_hashes':len(hashes),'duplicate_hash_groups':sum(v>1 for v in hashes.values()),'identity_errors':identityerrors,'native_conditions':{a:dict(v) for a,v in nativecounts.items()},'native_four_text_paired_analysis_ready':not identityerrors and len(ng)==1000 and len(nr)==4000,'native_vs_controlled_pooling_allowed':False,'historic_weight_byte_identity':'NOT_PROVEN_BY_SHARED_MODEL_PATH','source_text_examples':{a:ng[min(ng)][a]['source_text'] for a in conditions},'controlled_text_example':cg[min(cg)]['A_THEN_T']['text_evidence'],'exact_native_adversarial_text_equals_controlled':sum(r['native_adversarial_source_text']==r['controlled_text_evidence'] for r in mjoin if r['controlled_included'])}
save('MCR_RECONCILIATION_V2.json',mcr);print('MCR_DONE',mcr['matched_controlled_items'],mcr['distinct_native_audio_hashes'],flush=True)
# Bind every quoted contract and source without running it.
for p,r in inspect['contents'].items():
 if any(x in p for x in ['run_qwen25_mcr_native_v1.py','run_qwen25_mcr_controlled_v3.py','run_listen_local_v3.py','run_listen_source_aligned_v4.py','SCIENTIFIC_EQUIVALENCE','PROVENANCE','qwen25_mcr_native_execution_v1.json','qwen25_mcr_controlled_execution_v1.json','mcr_controlled_arbitration_prompt_v2.json','LISTEN_V3_VS_SOURCE_LAUNCH_AUDIT.md']):register(p,'corresponding code/config/provenance basis')
register(R/'code/run_qwen25_camer_controlled_resource_sweep_v1.py','CA-MER actual resource runner')
save('INPUT_SHA256_RECORD_COUNTS_V2.json',list(proof.values()));save('RECONCILIATION_MACHINE_SUMMARY_V2.json',{'label':'RETROSPECTIVE_EVIDENCE_RECOVERY','LISTEN':summary,'CA-MER':cam,'MCR':mcr,'errors':errors,'gpu_model_loaded':False,'historical_files_modified':False,'directory_rescan':False})
print('RECONCILIATION_WORKER_COMPLETE',len(proof),flush=True)
