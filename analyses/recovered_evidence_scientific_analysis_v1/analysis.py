"""POST_HOC_EXPLORATORY; stdlib/numpy/scipy only; historical sources read only."""
import csv,json,hashlib,re,itertools,collections,sys,subprocess,platform,datetime
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import binomtest,chi2_contingency
R=Path('/root/autodl-tmp/affective-conflict');Q=Path('/root/autodl-tmp/affective-conflict-reconciliation-v2');E=Path('/root/autodl-tmp/affective-conflict-forensics-expanded-v1');O=Path('/root/autodl-tmp/affective-conflict-recovered-science-v1')
B3=Path('/root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/outputs/B3_MEASUREMENTS_V1.jsonl')
SEED=20261010; BOOT=5000; PERM=19999
CONDS=['neutral','faithful','adversarial','irrelevant']; LABS=['sad','happy','fearful','angry','surprised','disgusted','neutral']; ARMS=['A_ONLY','V_ONLY','A_THEN_V','V_THEN_A']; OUTS=['SIDE_A','SIDE_V','OTHER','PARSE_FAIL','TECH_MISSING','SAME_LABEL_MATCH']
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for s in iter(lambda:f.read(1048576),b''):h.update(s)
 return h.hexdigest()
def read(p):
 p=Path(p)
 if p.suffix=='.csv':return list(csv.DictReader(open(p,encoding='utf-8-sig')))
 if p.suffix=='.jsonl':return [json.loads(s) for s in open(p,encoding='utf8') if s.strip()]
 if p.suffix=='.json':return json.loads(p.read_text())
 return p.read_text()
def save(n,z):
 p=O/n;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(z,ensure_ascii=False,indent=2,allow_nan=False))
def csvsave(n,rows):
 p=O/n;p.parent.mkdir(exist_ok=True,parents=True)
 keys=list(dict.fromkeys(k for r in rows for k in r))
 assert keys,n
 with open(p,'w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})
def truth(v):return str(v).lower()=='true'
def wilson(k,n):
 if not n:return [None,None]
 p=k/n;z=1.959963984540054;d=1+z*z/n;c=(p+z*z/(2*n))/d;w=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return [float(c-w),float(c+w)]
def cluster_ci(values,clusters,tag,equal_cluster=False):
 v=np.asarray(values,float); cs=sorted(set(clusters));idx={c:i for i,c in enumerate(cs)}; sums=np.zeros(len(cs));sizes=np.zeros(len(cs))
 for x,c in zip(v,clusters):sums[idx[c]]+=x;sizes[idx[c]]+=1
 if equal_cluster:sums=sums/sizes;sizes=np.ones(len(cs))
 rng=np.random.default_rng(SEED+int(hashlib.sha256(tag.encode()).hexdigest()[:8],16)); draws=[]
 for _ in range(BOOT//250):
  j=rng.integers(0,len(cs),(250,len(cs)));draws.extend((sums[j].sum(axis=1)/sizes[j].sum(axis=1)).tolist())
 return {'estimate':float(sums.sum()/sizes.sum()),'ci95':np.quantile(draws,[.025,.975]).tolist(),'n_items':len(v),'n_clusters':len(cs),'unit':'audio_sha256' if tag.startswith('MCR') else 'item'}
def paired(v,clusters,tag,cluster_null=False):
 z=cluster_ci(v,clusters,tag)
 if cluster_null:
  d=collections.defaultdict(float)
  for x,c in zip(v,clusters):d[c]+=x
  s=np.array(list(d.values()));rng=np.random.default_rng(SEED+int(hashlib.sha256((tag+'null').encode()).hexdigest()[:8],16));obs=abs(s.sum());extreme=0
  for j in range(0,PERM,500):
   signs=rng.choice([-1,1],(min(500,PERM-j),len(s)));extreme+=int((np.abs(signs@s)>=obs-1e-10).sum())
  z['p_value']=(extreme+1)/(PERM+1);z['test']='audio-SHA cluster sign-flip Monte Carlo, exchangeability sensitivity'
 else:
  plus=sum(x>0 for x in v);minus=sum(x<0 for x in v);z['p_value']=float(binomtest(plus,plus+minus).pvalue) if plus+minus else 1.;z['test']='exact paired discordance test';z['discordant_plus']=plus;z['discordant_minus']=minus
 return z
def holm(rows,key='p_value'):
 order=sorted(range(len(rows)),key=lambda i:rows[i][key]);running=0
 for rank,i in enumerate(order):running=max(running,min(1,(len(rows)-rank)*rows[i][key]));rows[i]['p_holm']=running
 return rows
def outcomes(rows,label='SIDE_V'):
 c=collections.Counter(rows);n=len(rows);binary=c['SIDE_A']+c[label]
 return {'n':n,'counts':{x:c[x] for x in OUTS+(['SIDE_T'] if label=='SIDE_T' else [])},'binary_n':binary,'binary_coverage':binary/n if n else None,'binary_audio_share':c['SIDE_A']/binary if binary else None,'binary_audio_wilson95':wilson(c['SIDE_A'],binary),'other_rate':c['OTHER']/n if n else None,'other_wilson95':wilson(c['OTHER'],n)}
def lock():
 paths=[R/'AGENTS.md',R/'docs/PROJECT_STATE.md',R/'docs/FILE_MAP.md',R/'docs/DECISIONS.md',E/'RECOVERED_EXPERIMENT_EXECUTION_REGISTER.csv',E/'FULL_EXPERIMENT_RECOVERY_REPORT.md',E/'MCR_NATIVE_FOUR_CONDITION_RECOVERY.json']
 names=['HISTORICAL_EVIDENCE_RECONCILIATION_V2.md','THREE_DATASET_HISTORICAL_EVIDENCE_MATRIX_V2.csv','INPUT_SHA256_RECORD_COUNTS_V2.json','LISTEN_RECONCILIATION_V2.json','MCR_RECONCILIATION_V2.json','CAMER_RECONCILIATION_V2.json','MCR_TEXT_AND_MODEL_CONTRACT_AUDIT_V2.json','MCR_POOL_AND_DUPLICATE_AUDIO_AUDIT_V2.json','MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.csv','MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.csv','CAMER_6000_KEY_RECONCILIATION_V2.csv','LISTEN_UNIMODAL_CORRECTNESS_JOIN_V2.csv','LISTEN_V4_ANSWER_OPTION_RECOVERY_V2.csv','LISTEN_V3_V4_STRICT_IDENTITY_JOIN_V2.csv','RECOVERED_54_RUN_RECONCILIATION.json']
 paths += [Q/n for n in names]
 paths += [R/'audit/QWEN25_MCR_NATIVE_V1/full_run/qwen25_mcr_native_full_v1.jsonl',R/'audit/QWEN25_MCR_NATIVE_V1/mcr_ser_native_qwen25_manifest_v1.jsonl',R/'audit/QWEN25_MCR_NATIVE_V1/scoring/mcr_qwen25_native_metrics_v1.json',R/'audit/QWEN25_MCR_CONTROLLED_V3/full_run/qwen25_mcr_controlled_full_v2.jsonl',R/'audit/QWEN25_MCR_CONTROLLED_V3/mcr_controlled_arbitration_manifest_v2.jsonl',R/'audit/QWEN25_CAMER_CONTROLLED_V1/camer_controlled_manifest_v1.jsonl',R/'audit/QWEN25_CAMER_CONTROLLED_V1/resource_sweep_v1/qwen25_camer_controlled_resource_sweep_v1.jsonl',R/'audit/QWEN25_CAMER_CONTROLLED_V1/scientific_equivalence_v1/CAMER_CONTROLLED_AVAILABLE_SCIENTIFIC_OUTCOMES_V1.csv',R/'audit/QWEN25_CAMER_CONTROLLED_V1/scientific_equivalence_v1/CAMER_RESOURCE_SWEEP_SCIENTIFIC_EQUIVALENCE_V1.json',R/'results/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/listen_native_raw_outputs_source_aligned_v4.jsonl',R/'audit/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/LISTEN_V4_CANONICAL_AT_JOIN_V1.csv',R/'audit/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/listen_native_manifest_source_aligned_v4.csv',B3]
 for n in ['run_qwen25_mcr_native_v1.py','run_qwen25_mcr_controlled_v3.py','run_qwen25_camer_controlled_resource_sweep_v1.py']:
  paths.append(R/'code'/n)
 ins=read(Q/'TARGETED_INSPECTION.json')
 paths += [Path(p) for p in ins['contents'] if any(s in p for s in ['CAMER_DATA','CAMER_SOURCE','CAMER_CONTROLLED_PROTOCOL','MCR_SER_FINAL','mcr_native_execution','mcr_controlled_execution','mcr_controlled_arbitration_prompt','SOURCE_LAUNCH_AUDIT','run_listen_source_aligned']) and Path(p).is_file()]
 paths += list((O/'reference').glob('*'))
 source=[]
 for p in dict.fromkeys(paths):
  assert p.is_file(),str(p)
  z=read(p) if p.suffix in ['.csv','.jsonl'] else None
  source.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'records':len(z) if z is not None else None,'unique_samples':len({str(x.get('sample_id',x.get('native_sample_id',x.get('source_id',x.get('authoritative_listen_item_id',''))))) for x in z}) if z is not None and z else None,'role':'FROZEN_REFERENCE_COPY' if '/reference/' in str(p) else 'READ_ONLY_SOURCE'})
 csvsave('SOURCE_INPUT_LOCK.csv',source)
 save('SOURCE_INPUT_LOCK.json',source)
 plan={'status':'POST_HOC_EXPLORATORY','registered_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before_new_numeric_results':True,'seed':SEED,'bootstrap':BOOT,'sign_flip_draws':PERM,'MCR':{'denominator':1000,'unit':'released sample ID; audio-SHA cluster CI and paired sign flip','contrasts':'six condition pairs: source-label match, second minus first; Holm family 6','rates':'four full-denominator audio-source match; explicit emotion assertion only faithful/adversarial; OTHER means valid label neither audio nor defined text; neutral/irrelevant OTHER means valid non-source label','secondary':'all-four invariance, pair transitions, seven source-label strata descriptively; equal-SHA weighting and exclusion of entire conflicting-GT hash groups; complete-case irrelevant parse sensitivity; controlled909 protocol kept separate'},'CAMER':{'denominator':'1500 planned items,1000 conflict,500consistent','groups':'dual source-label match / A-only / V-only / neither when both scientifically observable; unobservable separately, never call technical missing neither','family':'paired order effects on SIDE_A,SIDE_V,OTHER in full conflict and conflict dual group; Holm 6','construct':'audio-aligned/video-aligned/consistent full and dual; label-pair/candidate-position support; item bootstrap only, no unverified speaker/video cluster','additional':'persistent OTHER, source-label strata, fixed exact label-pair standardization of construct contrasts when common support exists; descriptive 95CI not simultaneous'},'LISTEN':{'no_repeat':'read and cite frozen R3 full findings, no target refit','new':'common-input/conflict support, posthoc observed dual match, full outcome and label subgroups; recovered OTHER choices and raw responses','family':'dual vs nondual on common support: SIDE_A,SIDE_T,OTHER; Holm3 Fisher exact, selection association only','intervals':'Wilson item-proportion CIs, bootstrap ratio for conditional choices where possible; limited source dependence unknown; tiny subgroups explicitly insufficient'},'cross_study':'no pooled rates or unified causal mechanism; no invented labels or official dialogue groups','failures':'full planned denominators; parse and technical missing explicit; missing media limits support','replay':'same script/sources/seed to alternate output dir, compare deterministic numeric hashes','prohibited':'GPU,weight loading,new generation,history changes,refit frozen transfer,push/merge'}
 save('EXPLORATORY_ANALYSIS_PLAN.json',plan)
 save('ENVIRONMENT.json',{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'git_stdout':subprocess.run(['git','-C',str(R),'rev-parse','HEAD'],capture_output=True,text=True).stdout,'git_stderr':subprocess.run(['git','-C',str(R),'rev-parse','HEAD'],capture_output=True,text=True).stderr,'source_script_sha256':sha(__file__)})
 # Read actual contracts before defining any estimand; preserve excerpts and full paths/hashes.
 texts={str(p):p.read_text() for p in paths if p.suffix in ['.py','.md'] and ('/code/' in str(p) or 'PROTOCOL' in str(p) or 'SOURCE_LAUNCH' in str(p))}
 save('INPUT_CONSTRUCTION_CONTRACTS.json',texts)
 print('LOCK_REGISTERED',len(source),flush=True)
def validate_inputs():
 for r in read(O/'SOURCE_INPUT_LOCK.json'):assert sha(r['path'])==r['sha256'],r['path']
def mcr():
 rows=read(Q/'MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.csv'); ids=read(Q/'MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.csv'); raw=read(R/'audit/QWEN25_MCR_NATIVE_V1/full_run/qwen25_mcr_native_full_v1.jsonl');manifest=read(R/'audit/QWEN25_MCR_NATIVE_V1/mcr_ser_native_qwen25_manifest_v1.jsonl')
 rawmap={(str(x['source_index']),x['condition']):x for x in raw};manmap={(str(x['source_index']),x['condition']):x for x in manifest};g=collections.defaultdict(dict)
 for x in rows:
  key=(x['source_index'],x['condition']);a=rawmap[key];b=manmap[key]
  assert a['parsed_label']==(x['parsed_label'] or None) and a['gt']==x['gt'] and a['parse_status']==x['parse_status'] and a['raw_model_output']==x['raw_model_output'];assert b['source_text']==x['source_text'] and a['audio_abspath']==b['audio_abspath'];assert truth(a['generation_success']);g[x['source_index']][x['condition']]=x
 assert len(rawmap)==len(manmap)==4000 and len(g)==1000
 ident={x['source_index']:x for x in ids};item=[];hashlabels=collections.defaultdict(set)
 for i in sorted(g,key=int):
  z=g[i];assert set(z)==set(CONDS) and len({x['audio_sha256'] for x in z.values()})==1
  ref=z['neutral'];yT=re.search(r'Description: This audio expresses (\w+) emotion\.',z['adversarial']['source_text']).group(1);assert yT in LABS and yT!=ref['gt'];assert 'This audio expresses '+ref['gt']+' emotion.' in z['faithful']['source_text']
  a={'source_index':i,'sample_id':ref['native_sample_id'],'audio_sha256':ref['audio_sha256'],'gt':ref['gt'],'y_text_adversarial':yT,'controlled_member':truth(ident[i]['controlled_included'])}
  assert sha(ident[i]['native_audio_path'])==a['audio_sha256']
  for c in CONDS:a[c]=z[c]['parsed_label'] if z[c]['parse_status']=='PARSE_OK' else 'PARSE_FAIL'
  a['all_four_same_valid']=all(a[c] in LABS for c in CONDS) and len({a[c] for c in CONDS})==1;a['any_change_including_failure']=len({a[c] for c in CONDS})>1;item.append(a);hashlabels[a['audio_sha256']].add(a['gt'])
 conflicts={h for h,l in hashlabels.items() if len(l)>1}; clusters=[x['audio_sha256'] for x in item];condition=[]
 for c in CONDS:
  match=[int(x[c]==x['gt']) for x in item];text=[int(x[c]==(x['gt'] if c=='faithful' else x['y_text_adversarial'])) for x in item] if c in ['faithful','adversarial'] else None;other=[int(x[c] in LABS and x[c]!=x['gt'] and (c!='adversarial' or x[c]!=x['y_text_adversarial'])) for x in item]
  condition.append({'condition':c,'n':1000,'audio_match_n':sum(match),'audio_match':cluster_ci(match,clusters,'MCRrate'+c),'text_match_n':sum(text) if text else None,'text_match':cluster_ci(text,clusters,'MCRtext'+c) if text else 'NOT_DEFINED','other_n':sum(other),'other_rate':sum(other)/1000,'parse_fail_n':sum(x[c]=='PARSE_FAIL' for x in item),'technical_failure_n':0})
 contrasts=[];trans=[]
 for a,b in itertools.combinations(CONDS,2):
  v=[int(x[b]==x['gt'])-int(x[a]==x['gt']) for x in item];z=paired(v,clusters,'MCR'+a+b,True);z.update({'from':a,'to':b,'changed_labels_or_parse':sum(x[a]!=x[b] for x in item),'estimand':'audio-source-label match difference, to minus from'});contrasts.append(z)
  cnt=collections.Counter((x[a],x[b]) for x in item)
  for la in LABS+['PARSE_FAIL']:
   for lb in LABS+['PARSE_FAIL']:trans.append({'from_condition':a,'to_condition':b,'from_label':la,'to_label':lb,'count':cnt[(la,lb)],'full_pair_denominator':1000})
 holm(contrasts);csvsave('01_MCR_PAIRED_TRANSITIONS.csv',trans)
 strata=[]
 for label in LABS:
  ii=[x for x in item if x['gt']==label]
  for c in CONDS:
   vals=[int(x[c]==label) for x in ii];s=cluster_ci(vals,[x['audio_sha256'] for x in ii],'MCRlabel'+label+c);strata.append({'gt':label,'condition':c,'n':len(ii),'source_match_n':sum(vals),'source_match_rate':s['estimate'],'ci_low':s['ci95'][0],'ci_high':s['ci95'][1],'audio_hash_clusters':s['n_clusters'],'text_assertion_match_n':sum(x[c]==x['y_text_adversarial'] for x in ii) if c=='adversarial' else sum(vals) if c=='faithful' else None,'hypothesis_test':'DESCRIPTIVE_NOT_MULTIPLICITY_ADJUSTED'})
 csvsave('01_MCR_LABEL_CONDITION_ASSOCIATIONS.csv',strata);csvsave('intermediate/MCR_ITEM_IDENTITY_OUTCOMES.csv',item)
 sens=[]
 for name,ii in [('released1000',item),('controlled_members909',[x for x in item if x['controlled_member']]),('exclude_all_conflicting_GT_hashes',[x for x in item if x['audio_sha256'] not in conflicts])]:
  for a,b in [('faithful','adversarial'),('neutral','irrelevant')]:
   v=[int(x[b]==x['gt'])-int(x[a]==x['gt']) for x in ii];cs=[x['audio_sha256'] for x in ii]
   for equal in [False,True]:
    s=cluster_ci(v,cs,'MCRsensitivity'+name+a+b+str(equal),equal);sens.append({'population':name,'contrast':b+'-'+a,'weighting':'equal_audio_hash' if equal else 'released_item','n':len(ii),**s})
 nofail=[x for x in item if x['irrelevant']!='PARSE_FAIL'];v=[int(x['irrelevant']==x['gt'])-int(x['neutral']==x['gt']) for x in nofail];sens.append({'population':'irrelevant_parse_complete_case','contrast':'irrelevant-neutral',**cluster_ci(v,[x['audio_sha256'] for x in nofail],'MCRparsecomplete')})
 cr=read(R/'audit/QWEN25_MCR_CONTROLLED_V3/full_run/qwen25_mcr_controlled_full_v2.jsonl');cm=read(R/'audit/QWEN25_MCR_CONTROLLED_V3/mcr_controlled_arbitration_manifest_v2.jsonl');cg=collections.defaultdict(dict);cmeta={(str(x['source_index']),x['arm']):x for x in cm}
 for x in cr:cg[str(x['source_index'])][x['arm']]=x
 comparison=[]
 for x in item:
  if not x['controlled_member']:continue
  i=x['source_index'];c=cg[i];assert set(c)=={'A_ONLY','T_ONLY','A_THEN_T','T_THEN_A'} and truth(ident[i]['source_index_path_hash_label_match']);assert all(t['y_audio']==x['gt'] and t['y_text']==x['y_text_adversarial'] for t in c.values())
  row={**x,'controlled_sample_id':ident[i]['controlled_sample_id'],'identity_match':True,'native_prompt_equals_controlled_text':ident[i]['native_adversarial_source_text']==ident[i]['controlled_text_evidence']}
  for arm in c:row['controlled_'+arm]=c[arm]['parsed_label'];row['same_native_adv_'+arm]=x['adversarial']==c[arm]['parsed_label']
  row['controlled_candidate_order']=c['A_THEN_T']['candidate_sequence'];comparison.append(row)
 csvsave('intermediate/MCR_NATIVE_CONTROLLED_PER_ITEM_JOIN.csv',comparison)
 dup=[{'audio_sha256':h,'items':[x['sample_id'] for x in item if x['audio_sha256']==h],'labels':sorted(hashlabels[h]),'controlled_items':[x['sample_id'] for x in item if x['audio_sha256']==h and x['controlled_member']]} for h in sorted(hashlabels) if sum(x['audio_sha256']==h for x in item)>1]
 save('intermediate/MCR_DUPLICATE_DIAGNOSTICS.json',dup)
 z={'conditions':condition,'paired_contrasts':contrasts,'invariance':{'all_four_same_valid':sum(x['all_four_same_valid'] for x in item),'any_change_including_failure':sum(x['any_change_including_failure'] for x in item),'all_four_valid':sum(all(x[c] in LABS for c in CONDS) for x in item),'faithful_to_adv_changed':sum(x['faithful']!=x['adversarial'] for x in item)},'source_label_strata':strata,'duplicate':{'native_items':1000,'native_hashes':len(hashlabels),'conflicting_hash_groups':len(conflicts),'conflicting_items':sum(x['audio_sha256'] in conflicts for x in item),'controlled_items':len(comparison),'controlled_hashes':len({x['audio_sha256'] for x in comparison}),'controlled_conflicting_hash_items':[x for x in dup if x['controlled_items'] and len(x['labels'])>1]},'sensitivities':sens,'native_controlled_comparison':{a:{'same_label_n':sum(x['same_native_adv_'+a] for x in comparison),'n':909,'native_audio_match_n':sum(x['adversarial']==x['gt'] for x in comparison),'controlled_audio_match_n':sum(x['controlled_'+a]==x['gt'] for x in comparison),'controlled_text_match_n':sum(x['controlled_'+a]==x['y_text_adversarial'] for x in comparison)} for a in ['A_ONLY','T_ONLY','A_THEN_T','T_THEN_A']},'model_bytes_cross_protocol':'NOT_PROVEN','official_dialogue_cluster':'NOT_VERIFIED; filename-derived cluster not treated as official','native_existing_metrics':read(R/'audit/QWEN25_MCR_NATIVE_V1/scoring/mcr_qwen25_native_metrics_v1.json')}
 save('numeric/MCR_RESULTS.json',z);print('MCR_SCIENCE_DONE',flush=True);return z
def camer():
 rec=read(Q/'CAMER_6000_KEY_RECONCILIATION_V2.csv');meta={x['sample_id']:x for x in read(R/'audit/QWEN25_CAMER_CONTROLLED_V1/camer_controlled_manifest_v1.jsonl')};raw=read(R/'audit/QWEN25_CAMER_CONTROLLED_V1/resource_sweep_v1/qwen25_camer_controlled_resource_sweep_v1.jsonl');idx=read(R/'audit/QWEN25_CAMER_CONTROLLED_V1/scientific_equivalence_v1/CAMER_CONTROLLED_AVAILABLE_SCIENTIFIC_OUTCOMES_V1.csv');im={(x['sample_id'],x['arm']):x for x in idx};g=collections.defaultdict(dict);account=[]
 for x in rec:
  rr=raw[int(x['source_row'])-1];mm=meta[x['sample_id']];assert rr['sample_id']==x['sample_id'] and rr['arm']==x['arm'] and (rr.get('parsed_label') or '')==x['parsed_label'];assert rr['candidate_sequence']==mm['candidate_order'];assert truth(x['scientific_available'])==truth(im[(x['sample_id'],x['arm'])]['scientific_available']);g[x['sample_id']][x['arm']]=x
 assert len(rec)==len(raw)==len(im)==6000 and len(g)==1500
 for a in ARMS:
  rs=[x for x in rec if x['arm']==a];account.append({'arm':a,'planned':1500,'generation_success':sum(x['generation_status']=='SUCCESS' for x in rs),'scientific_available':sum(truth(x['scientific_available']) for x in rs),'technical_missing':sum(x['generation_status']!='SUCCESS' for x in rs),'parse_failed':sum(x['generation_status']=='SUCCESS' and not truth(x['scientific_available']) for x in rs)})
 items=[]
 for s in sorted(g):
  rs=g[s];m=meta[s];assert set(rs)==set(ARMS);a=rs['A_ONLY'];v=rs['V_ONLY'];ao=truth(a['scientific_available']);vo=truth(v['scientific_available']);am=ao and a['parsed_label']==m['y_A'];vm=vo and v['parsed_label']==m['y_V'];group='UNOBSERVABLE' if not (ao and vo) else 'DUAL_MATCH' if am and vm else 'A_ONLY_MATCH' if am else 'V_ONLY_MATCH' if vm else 'NEITHER_MATCH'
  row={'sample_id':s,'subset':m['subset'],'conflict':m['y_A']!=m['y_V'],'y_A':m['y_A'],'y_V':m['y_V'],'observed_A':ao,'observed_V':vo,'match_A':am,'match_V':vm,'eligibility_group':group,'audio_sha256':m['audio_sha256'],'video_sha256':m['silent_video_sha256'],'candidate_sequence':m['candidate_order'],'audio_candidate_position':m['candidate_order'].index(m['y_A']),'video_candidate_position':m['candidate_order'].index(m['y_V'])}
  for arm in ['A_THEN_V','V_THEN_A']:
   x=rs[arm];lab=x['parsed_label'];cl='TECH_MISSING' if x['generation_status']!='SUCCESS' else 'PARSE_FAIL' if not truth(x['scientific_available']) else 'SAME_LABEL_MATCH' if lab==m['y_A']==m['y_V'] else 'SIDE_A' if lab==m['y_A'] else 'SIDE_V' if lab==m['y_V'] else 'OTHER';row[arm]=cl;row[arm+'_label']=lab
  items.append(row)
 assert sum(x['match_A'] and x['match_V'] for x in items)==316
 csvsave('intermediate/CAMER_ITEM_ELIGIBILITY_IDENTITY.csv',items)
 groups={'FULL_CONFLICT':[x for x in items if x['conflict']],'FULL_CONSISTENT':[x for x in items if not x['conflict']]}
 for grp in ['DUAL_MATCH','A_ONLY_MATCH','V_ONLY_MATCH','NEITHER_MATCH','UNOBSERVABLE']:groups['CONFLICT_'+grp]=[x for x in items if x['conflict'] and x['eligibility_group']==grp]
 for sub in sorted({x['subset'] for x in items}):
  groups['CONSTRUCT_'+sub]=[x for x in items if x['subset']==sub];groups['CONSTRUCT_'+sub+'_DUAL']=[x for x in items if x['subset']==sub and x['eligibility_group']=='DUAL_MATCH']
 coverage=[];summary={};trans=[];contrasts=[]
 for name,ii in groups.items():
  summary[name]={'n_items':len(ii),'source_match_A_n':sum(x['match_A'] for x in ii),'source_match_V_n':sum(x['match_V'] for x in ii),'dual_n':sum(x['eligibility_group']=='DUAL_MATCH' for x in ii)}
  for arm in ['A_THEN_V','V_THEN_A']:
   s=outcomes([x[arm] for x in ii]);summary[name][arm]=s
   # ratio CI resamples complete items, retaining the varying binary denominator.
   if ii and s['binary_n']:
    rng=np.random.default_rng(SEED+int(hashlib.sha256((name+arm).encode()).hexdigest()[:8],16));num=np.array([x[arm]=='SIDE_A' for x in ii]);den=np.array([x[arm] in ['SIDE_A','SIDE_V'] for x in ii]);j=rng.integers(0,len(ii),(BOOT,len(ii)));dd=den[j].sum(axis=1);valid=dd>0;s['binary_audio_item_bootstrap95']=np.quantile(num[j].sum(axis=1)[valid]/dd[valid],[.025,.975]).tolist();s['zero_binary_bootstrap_draws']=int((~valid).sum())
   coverage.append({'population':name,'arm':arm,'n_items':len(ii),**{k:v for k,v in s.items() if k!='counts'},**s['counts']})
  cnt=collections.Counter((x['A_THEN_V'],x['V_THEN_A']) for x in ii)
  for a,b in itertools.product(OUTS,repeat=2):trans.append({'population':name,'from_order':'A_THEN_V','to_order':'V_THEN_A','from_outcome':a,'to_outcome':b,'count':cnt[(a,b)],'denominator':len(ii)})
  if name in ['FULL_CONFLICT','CONFLICT_DUAL_MATCH']:
   for out in ['SIDE_A','SIDE_V','OTHER']:
    d=[int(x['V_THEN_A']==out)-int(x['A_THEN_V']==out) for x in ii];z=paired(d,[x['sample_id'] for x in ii],'CAMER'+name+out);z.update({'population':name,'outcome':out,'contrast':'V_THEN_A minus A_THEN_V','planned_missing_in_denominator':True});contrasts.append(z)
 holm(contrasts);csvsave('02_CAMER_ELIGIBILITY_AND_COVERAGE.csv',coverage);csvsave('02_CAMER_MATCHED_TRANSITIONS.csv',trans)
 persist={}
 for name,ii in groups.items():
  oa=sum(x['A_THEN_V']=='OTHER' for x in ii);both=sum(x['A_THEN_V']==x['V_THEN_A']=='OTHER' for x in ii);persist[name]={'first_order_other':oa,'both_order_other':both,'persistence_given_first_other':both/oa if oa else None,'wilson95':wilson(both,oa)}
 # Full fixed label-pair overlap and candidate support: no forced adjustment without common support.
 conf=groups['FULL_CONFLICT'];subs=sorted({x['subset'] for x in conf});lp={sub:collections.Counter((x['y_A'],x['y_V']) for x in conf if x['subset']==sub) for sub in subs};common=set(lp[subs[0]])&set(lp[subs[1]]);support=[];standard=[]
 for sub in subs:
  for labels,n in sorted(lp[sub].items()):support.append({'subset':sub,'y_A':labels[0],'y_V':labels[1],'n':n,'common_construct_label_pair':labels in common})
 for dual in [False,True]:
  ss={sub:[x for x in conf if x['subset']==sub and (not dual or x['eligibility_group']=='DUAL_MATCH')] for sub in subs};common2=set((x['y_A'],x['y_V']) for x in ss[subs[0]])&set((x['y_A'],x['y_V']) for x in ss[subs[1]])
  for arm in ['A_THEN_V','V_THEN_A']:
   for out in ['SIDE_A','SIDE_V','OTHER']:
    if not common2:standard.append({'dual_only':dual,'arm':arm,'outcome':out,'status':'NOT_IDENTIFIABLE_NO_COMMON_LABEL_PAIR'});continue
    strata=sorted(common2);total={k:sum((x['y_A'],x['y_V'])==k for sub in subs for x in ss[sub]) for k in strata};weights={k:total[k]/sum(total.values()) for k in strata};rng=np.random.default_rng(SEED+int(hashlib.sha256((str(dual)+arm+out).encode()).hexdigest()[:8],16));ests=[];boots=np.zeros(BOOT)
    for sub,sign in [(subs[0],-1),(subs[1],1)]:
     est=0
     for k in strata:
      z=np.array([int(x[arm]==out) for x in ss[sub] if (x['y_A'],x['y_V'])==k]);est+=weights[k]*z.mean();j=rng.integers(0,len(z),(BOOT,len(z)));boots+=sign*weights[k]*z[j].mean(axis=1)
     ests.append(est)
    standard.append({'dual_only':dual,'arm':arm,'outcome':out,'contrast':subs[1]+' minus '+subs[0],'estimate':ests[1]-ests[0],'ci95':np.quantile(boots,[.025,.975]).tolist(),'common_label_pairs':len(common2),'support_by_construct':{s:sum((x['y_A'],x['y_V']) in common2 for x in ss[s]) for s in subs},'status':'DESCRIPTIVE_COMMON_LABEL_PAIR_STANDARDIZATION_NOT_CAUSAL'})
 csvsave('intermediate/CAMER_LABEL_PAIR_CONSTRUCT_SUPPORT.csv',support);csvsave('intermediate/CAMER_LABEL_PAIR_STANDARDIZATION.csv',standard)
 candidate=[]
 for grp in ['ALL','DUAL_MATCH']:
  for sub in subs:
   ii=[x for x in conf if x['subset']==sub and (grp=='ALL' or x['eligibility_group']==grp)];candidate.append({'group':grp,'subset':sub,'n':len(ii),'audio_position_mean':float(np.mean([x['audio_candidate_position'] for x in ii])) if ii else None,'video_position_mean':float(np.mean([x['video_candidate_position'] for x in ii])) if ii else None,'y_A_distribution':dict(collections.Counter(x['y_A'] for x in ii)),'y_V_distribution':dict(collections.Counter(x['y_V'] for x in ii))})
 csvsave('intermediate/CAMER_CANDIDATE_LABEL_CONFOUNDING.csv',candidate)
 save('numeric/CAMER_RESULTS.json',{'arm_accounting':account,'groups':summary,'paired_order_contrasts':contrasts,'other_persistence':persist,'label_pair_standardization':standard,'candidate_confounding':candidate,'source_subset_semantics':{sub:{'y_A_semantics':meta[next(x['sample_id'] for x in items if x['subset']==sub)]['y_A_semantics'],'y_V_semantics':meta[next(x['sample_id'] for x in items if x['subset']==sub)]['y_V_semantics']} for sub in sorted({x['subset'] for x in items})},'audio_hashes':len({x['audio_sha256'] for x in items}),'video_hashes':len({x['video_sha256'] for x in items}),'source_cluster':'NOT_VERIFIED; item-bootstrap not robust to latent source dependencies','entropy16':'NOT_MEASURED','new_forward_required_for_discrete_analysis':False});print('CAMER_SCIENCE_DONE',flush=True)
def listen():
 from scipy.stats import fisher_exact
 gates=[x for x in read(Q/'LISTEN_UNIMODAL_CORRECTNESS_JOIN_V2.csv') if x['version']=='V4'];can={x['v4_primary_key']:x for x in read(R/'audit/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/LISTEN_V4_CANONICAL_AT_JOIN_V1.csv')};answer={x['key']:x for x in read(Q/'LISTEN_V4_ANSWER_OPTION_RECOVERY_V2.csv')};raw=read(R/'results/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/listen_native_raw_outputs_source_aligned_v4.jsonl');rawmap={x['manifest_row_id']:x for x in raw};allrows=[]
 for z in gates:
  k=z['joint_key'];c=can[k];a=answer[k];rr=rawmap[k];assert rr['audio_hash']==z['audio_sha256']==c['audio_evidence_sha256'];assert rr['transcription_hash']==z['text_sha256']==c['text_evidence_sha256'];assert a['parsed_label_recovered']==c['observed_v4_choice']==z['joint_label'];options=json.loads(a['candidate_sequence']);letter=a['parsed_letter'];assert options[ord(letter)-65]==a['parsed_label_recovered'];assert a['raw_model_output']==rr['assistant_text']
  observable=int(z['audio_unique_matches'])==int(z['text_source_id_and_actual_input_matches'])==1;group='UNOBSERVABLE' if not observable else 'DUAL_MATCH' if truth(z['dual_correct_actual_input']) else 'A_ONLY_MATCH' if truth(z['audio_correct']) else 'T_ONLY_MATCH' if truth(z['text_input_correct']) else 'NEITHER_MATCH'
  allrows.append({'joint_key':k,'base_source_id':re.sub(r'_3[ABC]$','',z['source_id']),'audio_sha256':z['audio_sha256'],'text_sha256':z['text_sha256'],'conflict':c['y_A']!=c['y_T'],'y_A':c['y_A'],'y_T':c['y_T'],'common_input_support':observable,'strict_both_content_support':int(z['text_full_content_unique_matches'])==1,'match_A':truth(z['audio_correct']),'match_T':truth(z['text_input_correct']),'eligibility_group':group,'joint_outcome':z['joint_outcome'],'joint_label':z['joint_label'],'parsed_letter':letter,'candidate_sequence':options,'source_A_in_options':c['y_A'] in options,'source_T_in_options':c['y_T'] in options,'raw_answer':a['raw_model_output'],'joint_raw_output_key':k})
 csvsave('03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv',allrows)
 conf=[x for x in allrows if x['conflict']];common=[x for x in conf if x['common_input_support']];dual=[x for x in common if x['eligibility_group']=='DUAL_MATCH'];othercommon=[x for x in common if x['eligibility_group']!='DUAL_MATCH'];groups={'COMMON_CONFLICT':common,'DUAL_MATCH_CONFLICT':dual,'COMMON_NON_DUAL':othercommon,'NO_TEXT_IDENTITY': [x for x in conf if not x['common_input_support']]}
 for g in ['A_ONLY_MATCH','T_ONLY_MATCH','NEITHER_MATCH']:groups[g]=[x for x in common if x['eligibility_group']==g]
 for g in ['COMMON_CONFLICT','DUAL_MATCH_CONFLICT']:
  for rid in [True,False]:groups[g+('_RIDICULE' if rid else '_NON_RIDICULE')]=[x for x in groups[g] if (x['y_A']=='ridicule')==rid]
 summary={g:outcomes([x['joint_outcome'] for x in ii],'SIDE_T') for g,ii in groups.items()}
 tests=[]
 for out in ['SIDE_A','SIDE_T','OTHER']:
  d=sum(x['joint_outcome']==out for x in dual);nd=sum(x['joint_outcome']==out for x in othercommon);p=float(fisher_exact([[d,len(dual)-d],[nd,len(othercommon)-nd]]).pvalue);rng=np.random.default_rng(SEED+int(hashlib.sha256(('LISTEN'+out).encode()).hexdigest()[:8],16));a=np.array([x['joint_outcome']==out for x in dual],float);b=np.array([x['joint_outcome']==out for x in othercommon],float);j=rng.integers(0,len(a),(BOOT,len(a)));k=rng.integers(0,len(b),(BOOT,len(b)));bs=a[j].mean(1)-b[k].mean(1);tests.append({'outcome':out,'contrast':'posthoc dual minus common nondual','estimate':float(a.mean()-b.mean()),'ci95':np.quantile(bs,[.025,.975]).tolist(),'p_value':p,'test':'Fisher exact selection association, not causal','dual_n':len(a),'nondual_n':len(b)})
 holm(tests)
 decom=[]
 for name,ii in [('ALL_3C_CONFLICT',conf),('COMMON_CONFLICT',common),('DUAL_MATCH_CONFLICT',dual)]:
  for label,count in sorted(collections.Counter(x['joint_label'] for x in ii if x['joint_outcome']=='OTHER').items()):decom.append({'population':name,'OTHER_selected_label':label,'count':count,'population_n':len(ii),'other_n':sum(x['joint_outcome']=='OTHER' for x in ii),'interpretation':'valid offered native emotion label outside both source labels'})
 csvsave('intermediate/LISTEN_OTHER_LABEL_DECOMPOSITION.csv',decom)
 labs=[]
 for label in sorted({x['y_A'] for x in common}):
  for name,ii in [('common',[x for x in common if x['y_A']==label]),('dual',[x for x in dual if x['y_A']==label])]:labs.append({'group':name,'audio_source_label':label,**outcomes([x['joint_outcome'] for x in ii],'SIDE_T')})
 csvsave('intermediate/LISTEN_ELIGIBILITY_BY_NATIVE_LABEL.csv',labs)
 # Validate corrected B3 evidence by dataset stable identity, never stale embedded features.
 b3=[x for x in read(B3) if x['dataset']=='LISTEN'];bm={(x['stable_dataset_id'],x['modality']):x for x in b3};support=[]
 for x in allrows:
  c=can[x['joint_key']];ident=c['authoritative_listen_item_id'];r={k:x[k] for k in ['joint_key','y_A','y_T','audio_sha256','text_sha256']}
  for mod,label,h in [('A',x['y_A'],x['audio_sha256']),('T',x['y_T'],x['text_sha256'])]:
   candidates=[v for (sid,m),v in bm.items() if m==mod and v['evidence_hash']==h]
   # Multiple sequence-specific source IDs are not silently collapsed.
   exact=[v for v in candidates if v['stable_dataset_id']==ident];vals=exact or candidates
   r[mod+'_matched_B3_rows']=len(vals);r[mod+'_literal_label_supported']=bool(vals) and all(label in v['candidate_labels'] for v in vals);r[mod+'_native_label']=label
  support.append(r)
 csvsave('intermediate/LISTEN_CORRECTED_B3_ONTOLOGY_SUPPORT.csv',support)
 save('numeric/LISTEN_RESULTS.json',{'joint_rows':len(allrows),'conflict_rows':len(conf),'common_conflict_n':len(common),'dual_conflict_n':len(dual),'strict_content_dual_n':sum(x['conflict'] and x['strict_both_content_support'] and x['eligibility_group']=='DUAL_MATCH' for x in allrows),'groups':summary,'selection_tests':tests,'by_label':labs,'OTHER_selected_labels':decom,'all_source_labels_in_candidate_options':all(x['source_A_in_options'] and x['source_T_in_options'] for x in allrows),'dual_ridicule_n':sum(x['y_A']=='ridicule' for x in dual),'dual_audio_choices_ridicule_n':sum(x['y_A']=='ridicule' and x['joint_outcome']=='SIDE_A' for x in dual),'b3_literal_joint_support_n':sum(x['A_literal_label_supported'] and x['T_literal_label_supported'] for x in support),'reverse_executed':'NOT_FOUND_IN_RECOVERED_EVIDENCE','pool_V3_V4':False});print('LISTEN_SCIENCE_DONE',flush=True)
def analyze():
 validate_inputs();mcr();camer();listen();validate_inputs();save('ANALYSIS_COMPLETE.json',{'status':'NUMERIC_ANALYSIS_COMPLETE','seed':SEED,'CPU_only':True,'historical_unchanged_hash_verification':True});print('ALL_CPU_NUMERIC_DONE',flush=True)
if __name__=='__main__':
 if len(sys.argv)>2:O=Path(sys.argv[2])
 if sys.argv[1]=='lock':lock()
 elif sys.argv[1]=='analyze':analyze()
