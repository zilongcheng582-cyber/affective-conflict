"""Independent CPU reconstruction: no import of primary analysis or runner."""
import pathlib,csv,json,hashlib,collections,itertools,numpy as np
ROOT=pathlib.Path('/root/autodl-tmp/affective-conflict-e1-video-v2');REPO=pathlib.Path('/root/autodl-tmp/affective-conflict-eri1/repo')
def csvrows(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def independent_stats(values,groups,seed):
 n=len(values);values=np.array(values,float);random=np.random.default_rng(seed);boot=[]
 for _ in range(10000):boot.append(float(np.mean(values[random.integers(0,n,n)])))
 keys=sorted(set(groups));inds=[[i for i,g in enumerate(groups) if g==k] for k in keys];random=np.random.default_rng(seed+1);cluster=[]
 for _ in range(10000):
  draws=random.integers(0,len(keys),len(keys));numerator=sum(sum(values[i] for i in inds[j]) for j in draws);denominator=sum(len(inds[j]) for j in draws);cluster.append(numerator/denominator)
 random=np.random.default_rng(seed+2);extreme=0;observed=abs(sum(values)/n)
 for _ in range(100):
  null=(random.integers(0,2,(1000,n))*2-1).dot(values)/n;extreme+=int(np.count_nonzero(abs(null)>=observed-1e-14))
 return {'effect':float(sum(values)/n),'utterance_ci95':np.quantile(boot,[.025,.975]).tolist(),'dialogue_cluster_ci95':np.quantile(cluster,[.025,.975]).tolist(),'p_two_sided':(extreme+1)/100001}
def main():
 cfg=json.loads((ROOT/'01_design/RUN_PROTOCOL.json').read_text());fingerprint=digest(ROOT/'01_design/RUN_PROTOCOL.json');checks=[]
 for p,h in cfg['locked_files'].items():assert digest(p)==h,('CODE_OR_DESIGN_CHANGED',p)
 for p,rec in cfg['historical_source_files'].items():assert digest(p)==rec['SHA256'],('HISTORICAL_ARTIFACT_CHANGED',p)
 mf=csvrows(ROOT/'01_design/FULL_MANIFEST.csv');assert len(mf)==2336 and len({t['trial_id'] for t in mf})==2336
 plan=json.loads((REPO/'manifests/emotiontalk/EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json').read_text());uids=sorted(plan['pairs']['AV']['conflict_utterance_ids']);assert len(uids)==146 and {t['utterance_id'] for t in mf}==set(uids)
 by=collections.defaultdict(list)
 for p in (ROOT/'04_full/attempts').glob('*.json'):
  r=json.loads(p.read_text());assert r['phase']=='full' and r['run_fingerprint']==fingerprint;by[r['trial_id']].append(r)
 assert set(by)=={t['trial_id'] for t in mf}
 journal=[json.loads(x) for x in (ROOT/'04_full/trials.jsonl').read_text().splitlines()];assert len({(r['trial_id'],r['attempt']) for r in journal})==len(journal)==sum(len(rs) for rs in by.values())
 for r in journal:assert r in by[r['trial_id']]
 lock=json.loads((ROOT/'04_full/RUN_LOCK.json').read_text());assert lock['fingerprint']==fingerprint and lock['manifest_sha256']==digest(ROOT/'01_design/FULL_MANIFEST.csv')
 cells={};hashes={};projected={r['trial_id']:r for r in csvrows(ROOT/'05_analysis/FULL_OUTCOMES.csv')}
 for t in mf:
  rs=sorted(by[t['trial_id']],key=lambda r:r['attempt']);assert [r['attempt'] for r in rs] in [[1],[1,2]];r=rs[-1]
  for k in ['audio','video','text']:
   p=t[k+'_path'];expected=t[k+'_sha256'];assert r['input_identity'][k]=={'path':p,'sha256':expected}
   if p not in hashes:hashes[p]=digest(p)
   assert hashes[p]==expected
  if r['generation_technical_failure']:out='TECHNICAL_FAILURE'
  elif r.get('parser_status')!='OK' or r.get('parsed_label') is None:out='PARSE_FAIL'
  else:out='SIDE_V' if r['parsed_label']==t['y_V'] else 'SIDE_A' if r['parsed_label']==t['y_A'] else 'OTHER'
  pr=projected[t['trial_id']];assert pr['outcome']==out and pr['parsed_label']==(r.get('parsed_label') or '')
  cells[t['utterance_id'],t['condition'],t['arm']]={'out':out,'label':r.get('parsed_label') or '', 'cluster':t['dialogue_id'],'entropy':r.get('candidate_entropy_primary',{}).get('normalized_by_log7'),'y_V':t['y_V']}
  if t['arm']!='A_ONLY' and r.get('generation_success'):
   expected=json.loads((ROOT/'02_media/receipts'/(t['utterance_id']+'.json')).read_text());physical=next(x for x in expected['physical'] if x['condition']==t['condition']);assert all(x=={'shape':physical['model_frame_shape'],'sha256':physical['model_frames_sha256']} for x in r['actual_consumed_visual_frames']) and r['actual_consumed_visual_frames']
  if not r['scoring_technical_failure']:
   scores=r['candidate_scores'];assert set(scores)==set(t['candidate_sequence'].split('|'));ps=[v['probability_mean_score_primary'] for v in scores.values()];assert abs(sum(ps)-1)<1e-8 and all(0<=v<=1 for v in ps)
 clusters=[cells[u,'CLEAN','A_THEN_V']['cluster'] for u in uids];assert len(set(clusters))==134
 official=cfg['official_metadata'];assert digest(official['path'])==official['SHA256'];mapping={pathlib.PurePosixPath(r['file_name']).stem:pathlib.PurePosixPath(r['file_name']).parts[1] for r in csvrows(official['path'])};assert all(mapping[u]==c for u,c in zip(uids,clusters))
 order=['A_THEN_V','V_THEN_A'];categories=['SIDE_V','SIDE_A','OTHER'];conditions=['CLEAN','RECODE','BLUR_L1','BLUR_L2','BLUR_L3']
 def rates(cond,cat):return [sum(cells[u,cond,o]['out']==cat for o in order)/2 for u in uids]
 vectors={}
 for cat in categories:vectors[cat+'_L3_MINUS_RECODE']=[a-b for a,b in zip(rates('BLUR_L3',cat),rates('RECODE',cat))]
 for cat in categories:vectors[cat+'_CLEAN_MINUS_RECODE']=[a-b for a,b in zip(rates('CLEAN',cat),rates('RECODE',cat))]
 for cat in categories:
  ys=[rates(c,cat) for c in conditions[1:]];vectors[cat+'_ORDINAL_DOSE_SLOPE']=[sum((j-1.5)*ys[j][i] for j in range(4))/5 for i in range(146)]
 for cat in categories:vectors[cat+'_ORDER_INTERACTION']=[(int(cells[u,'BLUR_L3',order[0]]['out']==cat)-int(cells[u,'RECODE',order[0]]['out']==cat))-(int(cells[u,'BLUR_L3',order[1]]['out']==cat)-int(cells[u,'RECODE',order[1]]['out']==cat)) for u in uids]
 vectors['V_ONLY_CORRECTNESS_L3_MINUS_RECODE']=[int(cells[u,'BLUR_L3','V_ONLY']['label']==cells[u,'BLUR_L3','V_ONLY']['y_V'])-int(cells[u,'RECODE','V_ONLY']['label']==cells[u,'RECODE','V_ONLY']['y_V']) for u in uids]
 if all(cells[u,c,'V_ONLY']['entropy'] is not None for u in uids for c in ['RECODE','BLUR_L3']):vectors['V_ONLY_NORMALIZED_ENTROPY_L3_MINUS_RECODE']=[cells[u,'BLUR_L3','V_ONLY']['entropy']-cells[u,'RECODE','V_ONLY']['entropy'] for u in uids]
 report=json.loads((ROOT/'05_analysis/SCIENTIFIC_RESULTS.json').read_text());recomputed=[]
 for family in ['primary','secondary']:
  records=report[family];pvalues=[]
  for r in records:
   independent=independent_stats(vectors[r['endpoint']],clusters,r['seed']);pvalues.append(independent['p_two_sided'])
   for key,v in independent.items():
    error=float(np.max(np.abs(np.asarray(v)-np.asarray(r[key]))));assert error<=1e-12,(r['endpoint'],key,error);checks.append({'endpoint':r['endpoint'],'check':key,'max_abs_error':error,'tolerance':1e-12,'status':'PASS'})
  sort=sorted(range(len(records)),key=lambda i:pvalues[i]);prev=0
  for j,i in enumerate(sort):prev=max(prev,min(1,pvalues[i]*(len(records)-j)));assert abs(prev-records[i]['p_holm'])<=1e-12
 transitions=csvrows(ROOT/'05_analysis/ALL_CATEGORY_TRANSITIONS.csv');labels=csvrows(ROOT/'05_analysis/ALL_LABEL_TRANSITIONS.csv')
 for a,b in itertools.permutations(conditions,2):
  for arm in ['V_ONLY']+order:
   expected=collections.Counter((cells[u,a,arm]['out'],cells[u,b,arm]['out']) for u in uids);reported={(x['from'],x['to']):int(x['n']) for x in transitions if x['from_condition']==a and x['to_condition']==b and x['arm']==arm};assert sum(reported.values())==146 and all(reported[k]==expected[k] for k in reported)
   label=lambda x:x['out'] if x['out'] in ['PARSE_FAIL','TECHNICAL_FAILURE'] else x['label'];lc=collections.Counter((label(cells[u,a,arm]),label(cells[u,b,arm])) for u in uids);lr={(x['from_label'],x['to_label']):int(x['n']) for x in labels if x['from_condition']==a and x['to_condition']==b and x['arm']==arm};assert sum(lr.values())==146 and all(lr[k]==lc[k] for k in lr)
 for p in (ROOT/'05_analysis').glob('*'):
  if p.is_file():assert digest(p)==digest(ROOT/'05_analysis/repeat'/p.name),('CPU_REPEAT_DIFF',p.name)
 checks.extend({'endpoint':'INTEGRITY','check':k,'max_abs_error':0,'tolerance':0,'status':'PASS'} for k in ['2336_UNIQUE_SLOTS','146_FROZEN_UIDS','134_OFFICIAL_DIALOGUE_CLUSTERS','ALL_MEDIA_HASHES','ACTUAL_MODEL_CONSUMED_FRAMES','GENERATION_PARSE_SCORE_STATUSES','IMMUTABLE_ATTEMPTS_JOURNAL','ALL_CATEGORY_AND_LABEL_TRANSITIONS','PRIMARY_AND_SECONDARY_HOLM','DETERMINISTIC_CPU_REPEAT','HISTORICAL_ARTIFACTS_UNCHANGED'])
 output=ROOT/'06_verification';output.mkdir(exist_ok=True)
 with open(output/'INDEPENDENT_RECOMPUTATION.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
 (output/'VERIFICATION_RECEIPT.json').write_text(json.dumps({'status':'PASS','checks':len(checks),'planned_slots':2336,'fixed_ITT_items':146,'CPU_only':True,'independent_statistics_implementation':True,'max_abs_error':max(x['max_abs_error'] for x in checks)},indent=2)+'\n');print('E1V2_INDEPENDENT_CPU_VERIFICATION_PASS',flush=True)
if __name__=='__main__':main()
