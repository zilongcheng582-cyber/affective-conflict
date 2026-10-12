"""Independent primary recomputation. Does not import primary analysis module."""
import csv,json,hashlib,pathlib,collections,numpy as np,sys
ROOT=pathlib.Path('/root/autodl-tmp/affective-conflict-e1-e2-full-v1')
REPO=pathlib.Path('/root/autodl-tmp/affective-conflict-eri1/repo')
def readcsv(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main(exp):
 mf=readcsv(ROOT/'01_protocol_freeze'/f'{exp}_FULL_MANIFEST.csv');cfg=json.loads((ROOT/'01_protocol_freeze'/f'{exp}_FROZEN_PROTOCOL.json').read_text())
 for p,h in cfg['locked_files'].items():assert digest(p)==h
 for p,identity in cfg['source_files'].items():assert digest(p)==identity['SHA256'],('HISTORICAL_FROZEN_SOURCE_CHANGED',p)
 plan=json.loads((REPO/'manifests/emotiontalk/EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json').read_text());expected=set(plan['pairs']['AV']['conflict_utterance_ids' if exp=='E1' else 'consistent_utterance_ids']);assert {t['utterance_id'] for t in mf}==expected
 assert len(mf)==len(expected)*15 and len({t['trial_id'] for t in mf})==len(mf)
 clean='V_CLEAN' if exp=='E1' else 'A_CLEAN';base='V_RECODE' if exp=='E1' else 'A_RECODE';high='V_BLUR_HIGH' if exp=='E1' else 'A_SNR00';target='SIDE_V' if exp=='E1' else 'SHARED_LABEL';orders=['A_THEN_V','V_THEN_A'];u=sorted(expected)
 primary=json.loads((ROOT/'04_cpu_analysis'/f'{exp}_PRIMARY_ANALYSIS.json').read_text())['primary'];projections=readcsv(ROOT/'04_cpu_analysis'/f'{exp}_FULL_OUTCOMES.csv');assert {t['trial_id'] for t in projections}=={t['trial_id'] for t in mf}
 by=collections.defaultdict(list);run=ROOT/('02_e1_video' if exp=='E1' else '03_e2_consistent')
 fingerprint=digest(ROOT/'01_protocol_freeze'/f'{exp}_FROZEN_PROTOCOL.json');lock=json.loads((run/'RUN_LOCK.json').read_text());assert lock['fingerprint']==fingerprint and lock['manifest_sha256']==digest(ROOT/'01_protocol_freeze'/f'{exp}_FULL_MANIFEST.csv')
 for p in (run/'attempts').glob('*.json'):
  r=json.loads(p.read_text());assert r['run_fingerprint']==fingerprint;by[r['trial_id']].append(r)
 assert set(by)=={t['trial_id'] for t in mf};final={k:sorted(rs,key=lambda r:r['attempt'])[-1] for k,rs in by.items()};cells={}
 for t in mf:
  r=final[t['trial_id']];assert [x['attempt'] for x in sorted(by[t['trial_id']],key=lambda r:r['attempt'])] in [[1],[1,2]]
  for kind in ['audio','video','text']:
   assert r['input_identity'][kind]['sha256']==t[kind+'_sha256'] and digest(t[kind+'_path'])==t[kind+'_sha256']
  if r['technical_failure']:out='TECH_FAILURE'
  elif r.get('parser_status')=='PARSE_FAIL' or not r.get('parsed_label'):out='PARSE_FAIL'
  elif exp=='E2':out='SHARED_LABEL' if r['parsed_label']==t['y_A'] else 'OTHER'
  else:out='SIDE_A' if r['parsed_label']==t['y_A'] else ('SIDE_V' if r['parsed_label']==t['y_V'] else 'OTHER')
  cells[t['utterance_id'],t['condition'],t['arm']]=(out,r.get('parsed_label') or '',t['dialogue_id'])
  pr=next(x for x in projections if x['trial_id']==t['trial_id']);assert pr['outcome']==out and pr['parsed_label']==(r.get('parsed_label') or '')
 differences=[];clusters=[]
 for uid in u:
  a=sum(cells[uid,high,o][0] in [target,'TECH_FAILURE'] for o in orders);b=sum(cells[uid,base,o][0]==target for o in orders);differences.append((a-b)/2);clusters.append(cells[uid,base,orders[0]][2])
 d=np.asarray(differences);seed=2026101110+(0 if exp=='E1' else 100);rng=np.random.default_rng(seed);boot=[]
 for _ in range(10000):indices=rng.integers(0,len(u),size=len(u));boot.append(sum(d[i] for i in indices)/len(u))
 names=sorted(set(clusters));groups=[[i for i,c in enumerate(clusters) if c==name] for name in names];rng=np.random.default_rng(seed+1);cb=[]
 for _ in range(10000):
  indices=rng.integers(0,len(names),size=len(names));num=sum(sum(d[i] for i in groups[k]) for k in indices);den=sum(len(groups[k]) for k in indices);cb.append(num/den)
 rng=np.random.default_rng(seed+2);exceed=0
 for _ in range(100):
  sign=rng.integers(0,2,size=(1000,len(u)))*2-1;null=sign.dot(d)/len(u);exceed+=int((np.abs(null)>=abs(sum(d)/len(u))-1e-14).sum())
 recompute={'estimate':sum(d)/len(u),'item_ci95':np.quantile(boot,[.025,.975]).tolist(),'dialogue_cluster_ci95':np.quantile(cb,[.025,.975]).tolist(),'two_sided_signflip_p':(1+exceed)/100001};checks=[]
 for key,value in recompute.items():
  error=float(np.max(np.abs(np.asarray(value)-np.asarray(primary[key]))));assert error<=1e-12,(key,error);checks.append({'experiment':exp,'check':key,'max_absolute_error':error,'tolerance':1e-12,'status':'PASS'})
 transitions=readcsv(ROOT/'04_cpu_analysis'/f'{exp}_MATCHED_TRANSITIONS.csv');conditions=sorted({t['condition'] for t in mf})
 for cond in conditions:
  if cond==base:continue
  for o in orders:
   cnt=collections.Counter((cells[uid,base,o][0],cells[uid,cond,o][0],cells[uid,base,o][1],cells[uid,cond,o][1]) for uid in u);reported={(x['from'],x['to'],x['from_label'],x['to_label']):int(x['n']) for x in transitions if x['condition']==cond and x['arm']==o};assert dict(cnt)==reported
 for p in (ROOT/'04_cpu_analysis').glob(exp+'_*'):
  repeat=ROOT/'04_cpu_analysis/repeat'/p.name;assert repeat.exists() and digest(p)==digest(repeat),('CPU_REPEAT_DIFF',p.name)
 checks.extend({'experiment':exp,'check':key,'max_absolute_error':0,'tolerance':0,'status':'PASS'} for key in ['FROZEN_SOURCE_POPULATION','ALL_MEDIA_HASHES','ALL_LOGICAL_CELLS','PARSE_ATTEMPT_ACCOUNTING','ALL_PAIRED_TRANSITIONS','OFFICIAL_CLUSTER_JOIN','NO_POST_TREATMENT_SELECTION','FROZEN_PROTOCOL_UNCHANGED','DETERMINISTIC_CPU_REPEAT'])
 # Official directories, not UID truncation.
 schema=json.loads((ROOT/'00_gate/OFFICIAL_METADATA_SCHEMA.json').read_text());official={pathlib.PurePosixPath(r['file_name']).stem:pathlib.PurePosixPath(r['file_name']).parts[1] for r in readcsv(schema['path'])};assert all(official[uid]==cl for uid,cl in zip(u,clusters))
 output=ROOT/'05_independent_verification'/f'{exp}_INDEPENDENT_RECOMPUTATION.csv'
 with output.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
 (ROOT/'05_independent_verification'/f'{exp}_VERIFICATION_RECEIPT.json').write_text(json.dumps({'status':'PASS','checks':len(checks),'population_items':len(u),'cells':len(mf),'CPU_only':True,'independent_primary_implementation':True},indent=2)+'\n');print('INDEPENDENT_VERIFICATION_PASS',exp)
if __name__=='__main__':main(sys.argv[1])
