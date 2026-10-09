"""CPU-only scientific projection replay. No model, media, GPU or frozen analysis functions.

python recompute.py --evidence results/eri1_scientific_closure_v1 --output NEW.json
"""
import argparse,collections,csv,json,pathlib
import numpy as np
SEED=20261009;B=10000;P=100000
def rows(p):
 with pathlib.Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ci(x,seed):
 x=np.asarray(x,float);rng=np.random.default_rng(seed)
 means=x[rng.integers(len(x),size=(B,len(x)))].mean(1)
 return {'estimate':float(x.mean()),'CI_low':float(np.quantile(means,.025)),'CI_high':float(np.quantile(means,.975))}
def pvalue(x,seed):
 x=np.asarray(x,float);rng=np.random.default_rng(seed);hits=0
 for _ in range(P//5000):
  flips=rng.choice((-1.,1.),size=(5000,len(x)))
  hits+=int((np.abs((flips*x).mean(1))>=abs(x.mean())-1e-15).sum())
 return (hits+1)/(P+1)
def recompute(evidence):
 r=rows(evidence/'ERI1_SCIENTIFIC_TRIAL_PROJECTION_V1.csv')
 assert len(r)==2336 and len({x['trial_id'] for x in r})==2336
 assert all(x['phase']=='full' and x['attempt']=='1' and x['technical_failure'].lower()=='false' for x in r)
 items=sorted({x['item_id'] for x in r});assert len(items)==146
 assert set(collections.Counter(x['item_id'] for x in r).values())=={16}
 cells={(x['item_id'],x['condition'],x['order_or_arm']):x for x in r};assert len(cells)==2336
 orders=('A_THEN_V','V_THEN_A')
 def side(uid,cond,arm):
  x=cells[uid,cond,arm]
  # Recover audio-side binary outcome independently from parsed label/source label.
  value=int(x['parsed_emotion_label']==x['source_audio_label'])
  assert value==int(x['outcome_class']=='SIDE_A')
  return value
 d=np.array([np.mean([side(uid,'SNR00',o) for o in orders])-np.mean([side(uid,'RECODE',o) for o in orders]) for uid in items])
 dh=np.array([float(cells[uid,'SNR00','A_ONLY']['normalized_entropy_unimodal'])-float(cells[uid,'RECODE','A_ONLY']['normalized_entropy_unimodal']) for uid in items])
 primary=ci(d,SEED);primary['p_two_sided_signflip']=pvalue(d,SEED+1)
 entropy=ci(dh,SEED+2);entropy['p_two_sided_signflip']=pvalue(dh,SEED+3)
 clusters=collections.defaultdict(list)
 for i,uid in enumerate(items):clusters[cells[uid,'CLEAN','V_ONLY']['dialogue_id']].append(i)
 names=sorted(clusters);sizes=np.array([len(clusters[k]) for k in names]);sums=np.array([d[clusters[k]].sum() for k in names])
 indices=np.random.default_rng(SEED+101).integers(0,len(names),(B,len(names)));draw=sums[indices].sum(1)/sizes[indices].sum(1)
 dialogue={'analysis_label':'POST_HOC_ROBUSTNESS_V1','dialogue_count':len(names),'max_cluster_items':int(sizes.max()),'estimate':float(d.mean()),'CI_low':float(np.quantile(draw,.025)),'CI_high':float(np.quantile(draw,.975)),'bootstrap_seed':SEED+101,'estimand':'item-weighted pooled mean under dialogue resampling'}
 transitions=collections.Counter((cells[uid,'RECODE',o]['outcome_class'],cells[uid,'SNR00',o]['outcome_class']) for uid in items for o in orders)
 fixed=rows(evidence/'ERI1_SELECTION_ROW_PROJECTION_V1.csv');assert len(fixed)==1500 and len({x['item_id'] for x in fixed})==1500
 selection={'source_panel':len(fixed),'AV_conflict':sum(x['AV_source_conflict'].lower()=='true' for x in fixed),'eligible':sum(x['eligible'].lower()=='true' for x in fixed)}
 assert selection=={'source_panel':1500,'AV_conflict':900,'eligible':146}
 reference=json.loads((evidence/'ERI1_FROZEN_ANALYSIS_RESULTS_V1.json').read_text())
 for independent,key in [(primary,'PRIMARY_dSIDE_A_SNR00_minus_RECODE'),(entropy,'S1_dEntropyA_SNR00_minus_RECODE')]:
  for metric,value in independent.items():assert abs(value-reference[key][metric])<1e-12,(key,metric)
 return {'status':'PASS','CPU_only':True,'items':146,'trials':2336,'primary':primary,'entropy':entropy,'dialogue':dialogue,'transitions':[{'from':a,'to':b,'n':n} for (a,b),n in sorted(transitions.items())],'selection':selection,'independent_comparison_tolerance':1e-12,'scope':'Frozen primary/S1 verification; clustering/transitions/selection POST_HOC_ROBUSTNESS_V1; no mediation inference'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 result=recompute(a.evidence)
 with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
 print(json.dumps({'status':result['status'],'primary':result['primary'],'dialogue':result['dialogue']}))
