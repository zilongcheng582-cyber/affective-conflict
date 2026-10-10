"""POST_HOC_EXPLORATORY. CPU-only frozen replay and failure decomposition."""
import pathlib,json,csv,hashlib,math,collections,datetime,subprocess,sys,shutil
import numpy as np
from scipy.special import expit
from scipy.stats import rankdata
P=pathlib.Path('/root/autodl-tmp/affective-conflict-eri1/repo')
R=pathlib.Path('/root/autodl-tmp/affective-conflict')
O=pathlib.Path('/root/autodl-tmp/affective-conflict-recovered-science-v1')
B3=pathlib.Path('/root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/outputs/B3_MEASUREMENTS_V1.jsonl')
COMMIT='34aa1b0340d906e5d625db7cb4a3def9199fa06e'; TOL=1e-12
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):
 p=pathlib.Path(p)
 if p.suffix=='.csv':return list(csv.DictReader(p.open(encoding='utf-8-sig')))
 if p.suffix=='.jsonl':return [json.loads(x) for x in p.open(encoding='utf8') if x.strip()]
 if p.suffix=='.json':return json.loads(p.read_text(encoding='utf8'))
 return p.read_text(encoding='utf8')
def save(n,d):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def csvsave(n,rows):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);keys=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,tuple)) else v for k,v in r.items()} for r in rows])
def truth(x):return str(x).upper() in ['TRUE','1','YES']
def metric(y,p):
 y=np.array(y,int);p=np.clip(np.array(p,float),1e-12,1-1e-12)
 if not len(y):return {k:None for k in ['AUROC','balanced_accuracy','log_loss','Brier_score']}
 n1=int(y.sum());n0=len(y)-n1
 auc=float((rankdata(p)[y==1].sum()-n1*(n1+1)/2)/(n1*n0)) if n0 and n1 else None
 return {'AUROC':auc,'balanced_accuracy':float(((p[y==1]>=.5).mean()+(p[y==0]<.5).mean())/2) if n0 and n1 else None,'log_loss':float(-(y*np.log(p)+(1-y)*np.log(1-p)).mean()),'Brier_score':float(((y-p)**2).mean())}
def predict(r,model,binding):
 c=binding['models'][model]['parameter_values'];s=binding['scalers'];key='source_probability' if model=='M3a' else 'top1_top2_margin';raw='delta_source_label_probability_raw' if model=='M3a' else 'delta_top1_top2_margin_raw';term='delta_source_label_probability_per_SD' if model=='M3a' else 'delta_top1_top2_margin_per_SD'
 if r[raw] is None:return None
 z=(r[raw]-s[key]['mean'])/s[key]['sd'];e=(r['delta_normalized_entropy_raw']-s['normalized_entropy']['mean'])/s['normalized_entropy']['sd']
 return float(expit(c['intercept_AT']+c.get('pair_'+r['route'],0)+c[term]*z+c['delta_normalized_entropy_per_SD']*e+c['FIRST_IS_MODALITY1']*truth(r['FIRST_IS_MODALITY1'])))
def baseline(r,b):
 c=b['parameters'];return float(expit(c['intercept_AT']+c.get('pair_'+r['route'],0)+c.get('FIRST_IS_MODALITY1',0)*truth(r['FIRST_IS_MODALITY1'])))
def out(r):
 if truth(r['technical_missing']):return 'TECH_MISSING'
 if r['source_relation']!='CONFLICT':return 'SAME_LABEL'
 if not truth(r['observed_outcome_available']):return 'TECH_MISSING'
 v=r['observed_outcome']
 if v in ['SIDE_A','SIDE_T','SIDE_V','PARSE_FAIL']:return v
 if v==r['modality1_source_label']:return 'SIDE_A'
 if v==r['modality2_source_label']:return 'SIDE_V' if r['route']=='AV' else 'SIDE_T'
 return 'OTHER'
def lock():
 assert not (O/'PHASE4_EXPLORATORY_PLAN.json').exists()
 paths=[]
 for sub in ['frozen/source_model','results/post_audit/closure_v1','results/post_audit/scientific_analysis_v1','protocols/emotiontalk','frozen/target_scoring']:
  d=P/sub
  if d.exists():paths.extend(p for p in d.rglob('*') if p.is_file() and p.suffix in ['.json','.csv','.md','.py','.txt'])
 paths += [P/'docs/SCIENTIFIC_CLAIM_STATUS_V1.md',P/'evidence/provenance/CROSS_REGIME_ZERO_REFIT_SPEC_V1.json',P/'analyses/post_audit/replay.py',P/'src/cross_regime/zero_refit/metrics.py',P/'src/cross_regime/zero_refit/evaluate.py',P/'RELEASE_MANIFEST_V1.json',P/'POST_AUDIT_REPAIR_MANIFEST_V1.json']
 paths += [P/'manifests'/d/'frozen_joint_outcomes.csv' for d in ['mcr','listen','camer']]
 paths += [P/'evidence/b3/B3_MEASUREMENTS_V1.jsonl',B3]
 paths += [O/n for n in ['03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv','intermediate/CAMER_ITEM_ELIGIBILITY_IDENTITY.csv','intermediate/MCR_NATIVE_CONTROLLED_PER_ITEM_JOIN.csv','numeric/MCR_RESULTS.json','numeric/CAMER_RESULTS.json','numeric/LISTEN_RESULTS.json']]
 paths += [R/'docs'/n for n in ['PROJECT_STATE.md','FILE_MAP.md','DECISIONS.md']]
 sources=[]
 for p in dict.fromkeys(paths):
  assert p.is_file(),str(p);h=sha(p);count=None
  if p.suffix in ['.csv','.jsonl']:count=len(read(p))
  z={'path':str(p),'sha256':h,'bytes':p.stat().st_size,'records':count,'git_blob_check':'NOT_GIT_ASSET'}
  if p.is_relative_to(P):
   v=subprocess.run(['git','-C',str(P),'show',COMMIT+':'+p.relative_to(P).as_posix()],capture_output=True)
   if v.returncode==0:assert hashlib.sha256(v.stdout).hexdigest()==h,str(p);z['git_blob_check']='MATCH_BINDING_COMMIT'
   else:z['git_blob_check']='NOT_IN_BINDING_COMMIT'
  sources.append(z)
 assert sha(P/'evidence/b3/B3_MEASUREMENTS_V1.jsonl')==sha(B3)
 assert subprocess.run(['git','-C',str(P),'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()==COMMIT
 save('PHASE4_SOURCE_LOCK.json',sources)
 save('PHASE4_EXPLORATORY_PLAN.json',{'status':'POST_HOC_EXPLORATORY','registered_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before_new_phase4_numeric_results':True,'prior_route_metrics_already_known':True,'numeric_tolerance':TOL,'probability_sum_tolerance':1e-6,'threshold':.5,'seed':20261010,'new_subgroup_CI':'2000 item-cluster percentile bootstraps; descriptive, not confirmatory; missing one-class replicates disclosed','frozen_CIs':'cite exact POST_AUDIT 2000 paired cluster percentile, seed20261008; do not replace','routes':'MCR primary and margin; LISTEN pooled distinct from3C; CA ontology-supported distinct from fullmargin','decomposition':'outcome/ontology/observed dual-vs-single-vs-neither/unobservable/source-label/order/probability range and threshold confusion; source-only M0+ORDER read frozen existing diagnostic, target oracle diagnostic only','strict_join':'source_item_id and both actual evidence SHA and source labels; include failures in denominator; LISTEN dual requires actual-input and full-content support','native_link':'MCR same909 strict audio identity; native outcomes only interpretation, never transfer replacements','prohibited':'GPU, model loading, source or target refit, scaler/threshold changes, overwriting frozen inputs, push/merge','final_categories':['R1 Source Prediction','R2 Compositionality','Frozen Transfer','ERI1 Causal Intervention','Recovered Native Experiments','Transfer Failure Explanation']})
 print('PHASE4_LOCKED',len(sources),flush=True)
def verify():
 nav=O/'PHASE4_NAVIGATION_MEMORY_UPDATE.json';updates={x['path']:x for x in read(nav)['updates']} if nav.exists() else {}
 for x in read(O/'PHASE4_SOURCE_LOCK.json'):
  if x['path'] in updates:
   u=updates[x['path']];assert sha(u['backup_path'])==x['sha256']==u['before_sha256'];assert sha(x['path'])==u['after_sha256']
  else:assert sha(x['path'])==x['sha256'],x['path']
def load():
 binding=read(P/'frozen/source_model/binding.json');baselines=read(P/'results/post_audit/closure_v1/SOURCE_BASELINE_BINDING_V1.json')
 assert not any(binding[k] for k in ['target_coefficient_fit','target_scaler_fit','target_threshold_tuning']) and binding['threshold']==.5
 for m in baselines.values():assert m['target_fit'] is False and m['threshold']==.5
 raw=read(B3);assert len(raw)==6354;bm={(x['dataset'],x['stable_dataset_id'],x['modality']):x for x in raw};assert len(bm)==6354
 for x in raw:
  assert x['status']=='SUCCESS';assert len(x['candidate_probabilities'])==7;assert abs(sum(x['candidate_probabilities'])-1)<1e-6
  q=x['candidate_probabilities'];ent=-sum(v*math.log(v) for v in q if v)/math.log(7);ss=sorted(q,reverse=True);label=x['raw_source_label'];sp=q[x['candidate_labels'].index(label)] if label in x['candidate_labels'] else None
  assert abs(ent-x['normalized_entropy'])<TOL and abs(ss[0]-ss[1]-x['top1_top2_margin'])<TOL
  assert (sp is None)==(x['source_label_probability'] is None)
  if sp is not None:assert abs(sp-x['source_label_probability'])<TOL
 data={}
 for ds,sub in [('MCR','mcr'),('LISTEN','listen'),('CA-MER','camer')]:
  rows=read(P/'manifests'/sub/'frozen_joint_outcomes.csv');assert len({r['target_record_id'] for r in rows})==len(rows)
  for r in rows:
   a=bm[ds,r['source_item_id'],'A'];b=bm[ds,r['source_item_id'],'V' if ds=='CA-MER' else 'T']
   for x,side in [(a,'modality1'),(b,'modality2')]:assert x['evidence_hash']==r[side+'_evidence_sha256'] and x['raw_source_label']==r[side+'_source_label']
   assert a['candidate_sequence']==b['candidate_sequence']
   for field,k in [('delta_source_label_probability_raw','source_label_probability'),('delta_normalized_entropy_raw','normalized_entropy'),('delta_top1_top2_margin_raw','top1_top2_margin')]:r[field]=a[k]-b[k] if a[k] is not None and b[k] is not None else None
   r['outcome']=out(r);r['ontology_supported']=a['source_label_probability_defined'] and b['source_label_probability_defined']
  data[ds]=rows
 return binding,baselines,data
def spec(data):
 return [('MCR_AT_PRIMARY','MCR','M3a',data['MCR'],'MCR_AT_PRIMARY'),('MCR_AT_MARGIN_SENSITIVITY','MCR','M3b',data['MCR'],'MCR_AT_MARGIN_SENSITIVITY'),('LISTEN_ALL_MIXED_HISTORICAL','LISTEN','M3b',data['LISTEN'],'LISTEN_AT_MARGIN_SENSITIVITY'),('LISTEN_3C_JOINT_ARBITRATION','LISTEN','M3b',[r for r in data['LISTEN'] if r['condition']=='3C'],'LISTEN_AT_MARGIN_SENSITIVITY'),('CAMER_AV_SUPPORT_LIMITED_SOURCEPROB','CA-MER','M3a',[r for r in data['CA-MER'] if r['support_limited_diagnostic_role']=='SUPPLEMENTARY_SUPPORT_LIMITED_DIAGNOSTIC'],'CAMER_AV_SUPPORT_LIMITED_SOURCEPROB'),('CAMER_AV_MARGIN_SENSITIVITY','CA-MER','M3b',data['CA-MER'],'CAMER_AV_MARGIN_SENSITIVITY')]
def describe(rows,model,binding):
 conf=[r for r in rows if r['source_relation']=='CONFLICT'];valid=[r for r in conf if r['outcome'] in ['SIDE_A','SIDE_T','SIDE_V'] and predict(r,model,binding) is not None]
 y=[int(r['outcome']=='SIDE_A') for r in valid];p=[predict(r,model,binding) for r in valid];counts=collections.Counter(r['outcome'] for r in conf)
 z={'planned':len(rows),'conflict':len(conf),'evaluated':len(valid),'SIDE_A':counts['SIDE_A'],'SIDE_2':counts['SIDE_T']+counts['SIDE_V'],'OTHER':counts['OTHER'],'PARSE_FAIL':counts['PARSE_FAIL'],'TECH_MISSING':counts['TECH_MISSING'],'ontology_supported_conflict':sum(r['ontology_supported'] for r in conf),'coverage':len(valid)/len(conf) if conf else None,**metric(y,p),'mean_predicted_p':float(np.mean(p)) if p else None,'observed_audio_fraction':float(np.mean(y)) if y else None,'predicted_audio_N':sum(v>=.5 for v in p),'true_positive':sum(yy and pp>=.5 for yy,pp in zip(y,p)),'false_positive':sum(not yy and pp>=.5 for yy,pp in zip(y,p)),'false_negative':sum(yy and pp<.5 for yy,pp in zip(y,p)),'true_negative':sum(not yy and pp<.5 for yy,pp in zip(y,p)),'probability_quantiles':np.quantile(p,[0,.05,.25,.5,.75,.95,1]).tolist() if p else []}
 if y:z['TARGET_PREVALENCE_ORACLE_DIAGNOSTIC']=metric(y,[np.mean(y)]*len(y))
 return z,valid
def subgroup_ci(rows,model,binding,tag):
 valid=[r for r in rows if r['source_relation']=='CONFLICT' and r['outcome'] in ['SIDE_A','SIDE_T','SIDE_V'] and predict(r,model,binding) is not None]
 if not valid:return {'ci95':None,'defined_bootstraps':0}
 cs=sorted({r['source_item_id'] for r in valid});groups={s:[i for i,r in enumerate(valid) if r['source_item_id']==s] for s in cs};rng=np.random.default_rng(20261010+int(hashlib.sha256(tag.encode()).hexdigest()[:8],16));y=np.array([r['outcome']=='SIDE_A' for r in valid]);p=np.array([predict(r,model,binding) for r in valid]);draw=[]
 for _ in range(2000):
  idx=np.concatenate([groups[cs[j]] for j in rng.integers(0,len(cs),len(cs))]);v=metric(y[idx],p[idx])['AUROC']
  if v is not None:draw.append(v)
 return {'AUROC_CI95':np.quantile(draw,[.025,.975]).tolist() if draw else None,'defined_bootstraps':len(draw),'CI_origin':'POST_HOC_EXPLORATORY conditional evaluable item-cluster percentile; not frozen-route CI'}
def analyze():
 verify();binding,baselines,data=load();predrows=read(P/'results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv');assert len(predrows)==9219
 pm={(r['analysis_role'],r['target_record_id']):r for r in predrows};assert len(pm)==9219
 reports=read(P/'results/post_audit/closure_v1/ZERO_REFIT_BASELINE_COMPARISON_V1.csv');replays=[];routes={};error=0;replayed=set()
 for role,ds,model,rows,predrole in spec(data):
  z,valid=describe(rows,model,binding);routes[role]=z
  for r in rows:
   old=pm[predrole,r['target_record_id']];new=predict(r,model,binding);oldp=float(old['predicted_p_SIDE_A']) if old['predicted_p_SIDE_A'] else None
   assert (new is None)==(oldp is None)
   if new is not None:error=max(error,abs(new-oldp));assert abs(new-oldp)<=TOL
   assert r['source_item_id']==old['source_item_id'] and r['presentation_order']==old['presentation_order']
   assert (old['resolved_side'] or None)==(r['outcome'] if r['outcome'] in ['SIDE_A','SIDE_T','SIDE_V'] else None)
   replayed.add((predrole,r['target_record_id']))
  frozen={}
  for name in ['M0','M0_PLUS_ORDER','FROZEN_POOLED_'+model]:
   ref=next(r for r in reports if r['analysis_role']==role and r['model']==name);y=[r['outcome']=='SIDE_A' for r in valid];p=[predict(r,model,binding) if name.startswith('FROZEN') else baseline(r,baselines[name]) for r in valid];m=metric(y,p)
   identity=hashlib.sha256('\n'.join(r['target_record_id'] for r in valid).encode()).hexdigest();assert identity==ref['evaluated_identity_sha256'];assert len(rows)==int(ref['N_planned']) and z['conflict']==int(ref['N_conflict']) and len(valid)==int(ref['N_evaluated'])
   maxerr=max(abs(m[k]-float(ref[k])) for k in m);assert maxerr<=TOL,(role,name,maxerr)
   row={'analysis_origin':'POST_HOC_EXPLORATORY','route':role,'dataset':ds,'source_model':name,'source_commit':COMMIT,'source_binding_sha256':sha(P/'frozen/source_model/binding.json'),'frozen_features':'delta_sourceprob + delta_H7 + order' if model=='M3a' else 'delta_margin7 + delta_H7 + order','N_planned':len(rows),'N_conflict':z['conflict'],'N_evaluated':len(valid),'SIDE_A':z['SIDE_A'],'SIDE_2':z['SIDE_2'],'OTHER':z['OTHER'],'PARSE_FAIL':z['PARSE_FAIL'],'TECH_MISSING':z['TECH_MISSING'],'coverage':z['coverage'],'evaluated_identity_sha256':identity,'statistical_unit':ref['cluster_definition'],'N_clusters':ref['N_clusters'],'threshold':.5,'max_metric_abs_error':maxerr,'identity_check':'PASS','sample_size_check':'PASS','numeric_check':'PASS','numeric_tolerance':TOL,**m}
   for k in ['AUROC','balanced_accuracy','log_loss','Brier_score','coverage','log_loss_minus_M0','AUROC_minus_M0_PLUS_ORDER']:
    for suf in ['', '_CI_low','_CI_high']:
     if k+suf in ref:row['frozen_'+k+suf]=ref[k+suf]
   replays.append(row);frozen[name]=ref
  z['frozen_baseline_reports']=frozen
 assert len(replayed)==9219;csvsave('04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv',replays)
 # Link recovered discrete/native outcomes without modifying frozen denominators.
 ca={x['sample_id']:x for x in read(O/'intermediate/CAMER_ITEM_ELIGIBILITY_IDENTITY.csv')};li={x['joint_key']:x for x in read(O/'03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv')};mc={x['controlled_sample_id']:x for x in read(O/'intermediate/MCR_NATIVE_CONTROLLED_PER_ITEM_JOIN.csv')}
 links=[]
 for ds,rows in data.items():
  for r in rows:
   if ds=='LISTEN' and r['condition']!='3C':continue
   x=ca[r['source_item_id']] if ds=='CA-MER' else li[r['target_record_id']] if ds=='LISTEN' else mc[r['source_item_id']]
   assert r['modality1_evidence_sha256']==x['audio_sha256']
   if ds=='CA-MER':
    assert r['modality2_evidence_sha256']==x['video_sha256'] and r['modality1_source_label']==x['y_A'] and r['modality2_source_label']==x['y_V'];group=x['eligibility_group'];observed=x[r['presentation_order']];assert observed==r['outcome'] or (r['outcome']=='SAME_LABEL' and observed in ['SAME_LABEL_MATCH','OTHER','TECH_MISSING'])
   elif ds=='LISTEN':
    assert r['modality2_evidence_sha256']==x['text_sha256'] and r['modality1_source_label']==x['y_A'] and r['modality2_source_label']==x['y_T'];group=x['eligibility_group'];assert r['outcome']==x['joint_outcome'] or r['outcome']=='SAME_LABEL';r['strict_content_support']=truth(x['strict_both_content_support'])
   else:
    assert r['modality1_source_label']==x['gt'] and r['modality2_source_label']==x['y_text_adversarial'];label=x['controlled_'+r['presentation_order']];observed='SIDE_A' if label==x['gt'] else 'SIDE_T' if label==x['y_text_adversarial'] else 'OTHER';assert observed==r['outcome'];group='DUAL_MATCH' if x['controlled_A_ONLY']==x['gt'] and x['controlled_T_ONLY']==x['y_text_adversarial'] else 'A_ONLY_MATCH' if x['controlled_A_ONLY']==x['gt'] else 'T_ONLY_MATCH' if x['controlled_T_ONLY']==x['y_text_adversarial'] else 'NEITHER_MATCH'
   r['eligibility_group']=group;r['subset']=x.get('subset','');links.append({'dataset':ds,'record_id':r['target_record_id'],'source_item_id':r['source_item_id'],'audio_sha256':r['modality1_evidence_sha256'],'side2_sha256':r['modality2_evidence_sha256'],'y_A':r['modality1_source_label'],'y_2':r['modality2_source_label'],'outcome':r['outcome'],'eligibility_group':group,'ontology_supported':r['ontology_supported'],'subset':r['subset'],'identity_check':'PASS','strict_content_support':r.get('strict_content_support','NOT_APPLICABLE')})
 csvsave('phase4_numeric/TRANSFER_RECOVERED_ROW_LINKAGE.csv',links)
 groups=[]
 for role,ds,model,rows,predrole in spec(data):
  conf=[r for r in rows if r['source_relation']=='CONFLICT'];parts={'FULL_CONFLICT':conf,'BINARY_EVALUABLE':[r for r in conf if r['outcome'] in ['SIDE_A','SIDE_T','SIDE_V']]}
  if ds!='LISTEN' or role=='LISTEN_3C_JOINT_ARBITRATION':
   for g in ['DUAL_MATCH','A_ONLY_MATCH','V_ONLY_MATCH' if ds=='CA-MER' else 'T_ONLY_MATCH','NEITHER_MATCH','UNOBSERVABLE']:parts[g]=[r for r in conf if r.get('eligibility_group')==g]
   assert sum(len(parts[g]) for g in ['DUAL_MATCH','A_ONLY_MATCH','V_ONLY_MATCH' if ds=='CA-MER' else 'T_ONLY_MATCH','NEITHER_MATCH','UNOBSERVABLE'])==len(conf)
   if ds=='LISTEN':parts['STRICT_DUAL_CONTENT_MATCH']=[r for r in parts['DUAL_MATCH'] if r['strict_content_support']]
  for s in [True,False]:parts['B3_ONTOLOGY_'+str(s)]=[r for r in conf if r['ontology_supported']==s]
  for order in sorted({r['presentation_order'] for r in conf}):parts['ORDER_'+order]=[r for r in conf if r['presentation_order']==order]
  for label in sorted({r['modality1_source_label'] for r in conf}):parts['A_SOURCE_'+label]=[r for r in conf if r['modality1_source_label']==label]
  if ds=='CA-MER':
   for sub in ['audio-aligned','video-aligned','audio_aligned','video_aligned']:
    sel=[r for r in conf if r.get('subset')==sub]
    if sel:
     parts['CONSTRUCT_'+sub]=sel;parts['CONSTRUCT_'+sub+'_DUAL']=[r for r in sel if r['eligibility_group']=='DUAL_MATCH']
  for name,part in parts.items():
   z,valid=describe(part,model,binding);z.update(route=role,group=name,analysis_origin='POST_HOC_EXPLORATORY',selection='Frozen route unchanged; this subgroup diagnostic cannot redefine success')
   for bn,b in baselines.items():z[bn]=metric([r['outcome']=='SIDE_A' for r in valid],[baseline(r,b) for r in valid])
   if name in ['DUAL_MATCH','STRICT_DUAL_CONTENT_MATCH'] and len(valid):z.update(subgroup_ci(part,model,binding,role+name))
   groups.append(z)
 csvsave('phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv',groups)
 # MCR native pairing suggests assertion dependence, never supplies controlled outcomes.
 native={'n':len(mc),'native_adversarial_text_match':sum(x['adversarial']==x['y_text_adversarial'] for x in mc.values()),'native_adversarial_audio_match':sum(x['adversarial']==x['gt'] for x in mc.values()),'controlled_audio_only_source_match':sum(x['controlled_A_ONLY']==x['gt'] for x in mc.values()),'controlled_text_only_text_match':sum(x['controlled_T_ONLY']==x['y_text_adversarial'] for x in mc.values()),'protocol_pooling':False}
 # Frozen coefficient/scaler integrity cross-check against historical report hashes.
 original=read(P/'frozen/source_model/B3_SOURCE_MODEL_BINDING_ORIGINAL.json');assert original['models']==binding['models'] and original['scalers']==binding['scalers']
 resolution=read(P/'frozen/source_model/EMOTIONTALK_PHASE2_SCALER_PROVENANCE_RESOLUTION_V1.json')
 for k in binding['scalers']:
  if isinstance(binding['scalers'][k],dict):assert binding['scalers'][k]['mean']==resolution['fit_time_scalers'][k]['mean'] and binding['scalers'][k]['sd']==resolution['fit_time_scalers'][k]['sd']
 historical_checks=[]
 for a in original['artifacts']:
  suffix=a['artifact_path'].split('historical/original/',1)[-1];p=R/suffix
  if p.is_file():assert sha(p)==a['SHA256'];historical_checks.append({'path':str(p),'sha256':sha(p),'status':'EXACT_ORIGINAL_BINDING_MATCH'})
 save('phase4_numeric/TRANSFER_RESULTS.json',{'routes':routes,'subgroups':groups,'MCR_native_linkage':native,'prediction_rows_replayed':len(replayed),'max_prediction_abs_error':error,'measurement_rows_verified':6354,'metric_reports_checked':len(replays),'strict_recovered_linkage_rows':len(links),'historical_binding_crosschecks':historical_checks,'source_commit':COMMIT,'no_fit':True,'GPU':False})
 verify();save('PHASE4_READ_ONLY_VERIFICATION.json',{'status':'PASS','locked_sources':len(read(O/'PHASE4_SOURCE_LOCK.json')),'all_sha_unchanged':True,'source_commit':COMMIT,'prediction_tolerance':TOL,'metric_tolerance':TOL,'GPU':False,'refit':False});print('PHASE4_NUMERIC_COMPLETE',len(replayed),len(replays),len(links),flush=True)
if __name__=='__main__':
 {'lock':lock,'analyze':analyze}[sys.argv[1]]()
