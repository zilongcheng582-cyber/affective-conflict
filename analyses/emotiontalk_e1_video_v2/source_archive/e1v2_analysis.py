"""Frozen item-paired analysis; never selects items using intervention outcomes."""
from e1v2_cpu_gate import ROOT,OLD,REPO,R,sha,dump,rows,table
import numpy as np,collections,json,pathlib,itertools,math,sys
CATS=['SIDE_V','SIDE_A','OTHER','PARSE_FAIL','TECHNICAL_FAILURE'];CONDS=['CLEAN','RECODE','BLUR_L1','BLUR_L2','BLUR_L3'];ORDERS=['A_THEN_V','V_THEN_A'];SEED=2026101103
def stats(d,clusters,seed):
 d=np.asarray(d,dtype=float);n=len(d);boot=d[np.random.default_rng(seed).integers(n,size=(10000,n))].mean(axis=1)
 names=sorted(set(clusters));sums=np.array([sum(d[i] for i,c in enumerate(clusters) if c==k) for k in names]);sizes=np.array([clusters.count(k) for k in names]);idx=np.random.default_rng(seed+1).integers(len(names),size=(10000,len(names)));cb=sums[idx].sum(axis=1)/sizes[idx].sum(axis=1)
 rng=np.random.default_rng(seed+2);exceed=0
 for _ in range(100):exceed+=int((np.abs(((rng.integers(2,size=(1000,n))*2-1)*d).mean(axis=1))>=abs(d.mean())-1e-14).sum())
 return {'effect':float(d.mean()),'utterance_ci95':np.quantile(boot,[.025,.975]).tolist(),'dialogue_cluster_ci95':np.quantile(cb,[.025,.975]).tolist(),'p_two_sided':(exceed+1)/100001,'seed':seed,'items':n,'clusters':len(names)}
def holm(rs):
 rank=sorted(range(len(rs)),key=lambda i:rs[i]['p_two_sided']);running=0
 for j,i in enumerate(rank):running=max(running,min(1,(len(rs)-j)*rs[i]['p_two_sided']));rs[i]['p_holm']=running
def classify(t,r):
 if r['generation_technical_failure']:return 'TECHNICAL_FAILURE'
 if r.get('parser_status')!='OK' or r.get('parsed_label') is None:return 'PARSE_FAIL'
 return 'SIDE_V' if r['parsed_label']==t['y_V'] else 'SIDE_A' if r['parsed_label']==t['y_A'] else 'OTHER'
def analyze(output):
 output=pathlib.Path(output);output.mkdir(parents=True,exist_ok=True);cfg=json.loads((ROOT/'01_design/RUN_PROTOCOL.json').read_text());fp=sha(ROOT/'01_design/RUN_PROTOCOL.json')
 for p,h in cfg['locked_files'].items():assert sha(p)==h
 mf=rows(ROOT/'01_design/FULL_MANIFEST.csv');assert len(mf)==2336 and len({t['trial_id'] for t in mf})==2336
 by=collections.defaultdict(list)
 for p in (ROOT/'04_full/attempts').glob('*.json'):
  r=json.loads(p.read_text());assert r['run_fingerprint']==fp and r['phase']=='full';by[r['trial_id']].append(r)
 assert set(by)=={t['trial_id'] for t in mf};final={k:sorted(v,key=lambda r:r['attempt'])[-1] for k,v in by.items()};cells={};projection=[];probability=[]
 for t in mf:
  r=final[t['trial_id']];oc=classify(t,r);en=r.get('candidate_entropy_primary',{}).get('normalized_by_log7')
  x={**t,'outcome':oc,'parsed_label':r.get('parsed_label') or '', 'generation_technical_failure':r['generation_technical_failure'],'scoring_technical_failure':r['scoring_technical_failure'],'attempts':len(by[t['trial_id']]),'entropy':en if en is not None else ''};projection.append(x);cells[t['utterance_id'],t['condition'],t['arm']]=x
  for label,score in r.get('candidate_scores',{}).items():probability.append({'trial_id':t['trial_id'],'condition':t['condition'],'arm':t['arm'],'label':label,**{k:v for k,v in score.items() if not isinstance(v,(dict,list))}})
 table(output/'FULL_OUTCOMES.csv',projection)
 if probability:table(output/'CANDIDATE_PROBABILITIES.csv',probability)
 uids=sorted({t['utterance_id'] for t in mf});assert len(uids)==146;clusters=[cells[u,'CLEAN','A_THEN_V']['dialogue_id'] for u in uids];assert len(set(clusters))==134
 def vec(cond,cat):return np.array([sum(cells[u,cond,o]['outcome']==cat for o in ORDERS)/2 for u in uids])
 tests=[];primary=[];secondary=[]
 def add(name,d,group):
  seed=SEED+100+len(tests)*10;rec={'endpoint':name,'family':group,**stats(d,clusters,seed)};tests.append({'endpoint':name,'family':group,'seed':seed,'differences':d.tolist()});return rec
 for cat in CATS[:3]:
  d=vec('BLUR_L3',cat)-vec('RECODE',cat);r=add(cat+'_L3_MINUS_RECODE',d,'PRIMARY_3_HOLM');r['ITT_denominator']=146
  lower=d-vec('RECODE','TECHNICAL_FAILURE');upper=d+vec('BLUR_L3','TECHNICAL_FAILURE');r['technical_missing_effect_bounds']=[float(lower.mean()),float(upper.mean())]
  cc=[i for i,u in enumerate(uids) if all(cells[u,c,o]['outcome']!='TECHNICAL_FAILURE' for c in ['RECODE','BLUR_L3'] for o in ORDERS)];r['complete_case_items']=len(cc);r['complete_case_effect']=float(d[cc].mean()) if cc else None;primary.append(r)
 for cat in CATS[:3]:secondary.append(add(cat+'_CLEAN_MINUS_RECODE',vec('CLEAN',cat)-vec('RECODE',cat),'SECONDARY_HOLM'))
 for cat in CATS[:3]:
  a=np.column_stack([vec(c,cat) for c in CONDS[1:]]);slope=((a-a.mean(axis=1,keepdims=True))*np.array([-1.5,-.5,.5,1.5])).sum(axis=1)/5;secondary.append(add(cat+'_ORDINAL_DOSE_SLOPE',slope,'SECONDARY_HOLM'))
 for cat in CATS[:3]:
  d=np.array([(int(cells[u,'BLUR_L3',ORDERS[0]]['outcome']==cat)-int(cells[u,'RECODE',ORDERS[0]]['outcome']==cat))-(int(cells[u,'BLUR_L3',ORDERS[1]]['outcome']==cat)-int(cells[u,'RECODE',ORDERS[1]]['outcome']==cat)) for u in uids]);secondary.append(add(cat+'_ORDER_INTERACTION',d,'SECONDARY_HOLM'))
 correct=np.array([int(cells[u,'BLUR_L3','V_ONLY']['parsed_label']==cells[u,'BLUR_L3','V_ONLY']['y_V'])-int(cells[u,'RECODE','V_ONLY']['parsed_label']==cells[u,'RECODE','V_ONLY']['y_V']) for u in uids]);secondary.append(add('V_ONLY_CORRECTNESS_L3_MINUS_RECODE',correct,'SECONDARY_HOLM'))
 entropy=[]
 for u in uids:
  a=cells[u,'RECODE','V_ONLY']['entropy'];b=cells[u,'BLUR_L3','V_ONLY']['entropy'];entropy.append(float(b)-float(a) if a!='' and b!='' else None)
 if all(x is not None for x in entropy):secondary.append(add('V_ONLY_NORMALIZED_ENTROPY_L3_MINUS_RECODE',np.array(entropy),'SECONDARY_HOLM'))
 holm(primary);holm(secondary)
 accounting=[]
 for cond in CONDS:
  for arm in ['V_ONLY']+ORDERS:
   for cat in CATS:accounting.append({'condition':cond,'arm':arm,'category':cat,'n':sum(cells[u,cond,arm]['outcome']==cat for u in uids),'denominator':146})
 for cat in CATS:accounting.append({'condition':'CLEAN','arm':'A_ONLY','category':cat,'n':sum(cells[u,'CLEAN','A_ONLY']['outcome']==cat for u in uids),'denominator':146})
 table(output/'OUTCOME_ACCOUNTING.csv',accounting)
 transitions=[];labeltrans=[]
 labels=sorted(set(mf[0]['candidate_sequence'].split('|')))+['PARSE_FAIL','TECHNICAL_FAILURE']
 def lab(x):return x['outcome'] if x['outcome'] in CATS[3:] else x['parsed_label']
 for base,cond in itertools.permutations(CONDS,2):
  for arm in ['V_ONLY']+ORDERS:
   counter=collections.Counter((cells[u,base,arm]['outcome'],cells[u,cond,arm]['outcome']) for u in uids);lc=collections.Counter((lab(cells[u,base,arm]),lab(cells[u,cond,arm])) for u in uids)
   for a,b in itertools.product(CATS,repeat=2):transitions.append({'from_condition':base,'to_condition':cond,'arm':arm,'from':a,'to':b,'n':counter[a,b],'denominator':146})
   for a,b in itertools.product(labels,repeat=2):labeltrans.append({'from_condition':base,'to_condition':cond,'arm':arm,'from_label':a,'to_label':b,'n':lc[a,b],'denominator':146})
 table(output/'ALL_CATEGORY_TRANSITIONS.csv',transitions);table(output/'ALL_LABEL_TRANSITIONS.csv',labeltrans)
 trajectory=[]
 for cond in CONDS:
  for cat in CATS:trajectory.append({'condition':cond,'category':cat,'rate_equal_item_mean_two_orders':float(vec(cond,cat).mean()),'items':146,'joint_slots':292,'V_ONLY_correctness':sum(cells[u,cond,'V_ONLY']['parsed_label']==cells[u,cond,'V_ONLY']['y_V'] for u in uids)/146})
 table(output/'DOSE_TRAJECTORY.csv',trajectory)
 # Per-order effects are descriptive paired estimates with intervals, not another
 # unadjusted inferential family. Interaction tests above carry adjusted p values.
 orders=[]
 for oi,o in enumerate(ORDERS):
  for ci,cat in enumerate(CATS[:3]):
   d=np.array([int(cells[u,'BLUR_L3',o]['outcome']==cat)-int(cells[u,'RECODE',o]['outcome']==cat) for u in uids]);orders.append({'arm':o,'category':cat,**stats(d,clusters,SEED+900+oi*30+ci*10),'role':'DESCRIPTIVE_ORDER_EFFECT'})
 dump(output/'ORDER_EFFECTS.json',orders)
 for rec in primary:
  missing=rec['technical_missing_effect_bounds'][0]!=rec['technical_missing_effect_bounds'][1];rec['ruling']='INCONCLUSIVE_TECHNICAL_MISSING' if missing else ('DECREASE' if rec['effect']<0 else 'INCREASE') if rec['p_holm']<.05 else 'NOT_STATISTICALLY_DETECTED'
 result={'status':'ANALYSIS_COMPLETE_AWAITING_INDEPENDENT_VERIFICATION','fixed_ITT_items':146,'dialogue_clusters':134,'planned_slots':2336,'all_attempts':sum(len(v) for v in by.values()),'technical_failure_attempts':sum(x['technical_failure'] for rs in by.values() for x in rs),'generation_missing_final':sum(r['generation_technical_failure'] for r in final.values()),'scoring_missing_final':sum(r['scoring_technical_failure'] for r in final.values()),'retries':sum(len(rs)-1 for rs in by.values()),'primary':primary,'secondary':secondary,'post_treatment_selection':False,'run_fingerprint':fp}
 dump(output/'SCIENTIFIC_RESULTS.json',result);dump(output/'PAIRED_STATISTIC_VECTORS.json',{'uids':uids,'clusters':clusters,'tests':tests})
 report='# E1 V2 frozen scientific analysis\n\nAll 146 frozen utterances retained; 134 official dialogue clusters. Primary contrast BLUR_L3 minus RECODE, averaged over both orders. Three primary two-sided paired sign-flip tests use Holm correction.\n\n'+json.dumps(result,indent=2)+'\n\nNo causal entropy mediation claim. Audio remains unchanged. This conflict population differs from E2 consistent population; percentage differences do not prove symmetry or asymmetry. Ordinal blur strengths are not physically equivalent to audio SNR doses. Historical ERI1 and E2 remain immutable. Independent verification is required before final closure.\n'
 (output/'SCIENTIFIC_REPORT.md').write_text(report)
 return result
if __name__=='__main__':print(json.dumps(analyze(sys.argv[1])['primary']))
