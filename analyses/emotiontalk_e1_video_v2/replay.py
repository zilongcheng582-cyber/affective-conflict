"""CPU-only independent replay from reviewed scientific rows; never loads a model."""
import argparse,csv,json,pathlib,math,hashlib,collections
import numpy as np
ORDERS=['A_THEN_V','V_THEN_A'];TOL=1e-12
def rows(p):
 with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def require(ok,detail):
 if not ok:raise ValueError(detail)
def paired(d,groups,seed):
 d=np.asarray(d,dtype=float);n=len(d);require(n==len(groups),'Cluster/vector length differs')
 rng=np.random.default_rng(seed);ib=rng.integers(n,size=(10000,n));boot=np.mean(d[ib],axis=1)
 names=sorted(set(groups));idx={k:i for i,k in enumerate(names)};sums=np.zeros(len(names));sizes=np.zeros(len(names))
 for value,g in zip(d,groups):sums[idx[g]]+=value;sizes[idx[g]]+=1
 ci=np.random.default_rng(seed+1).integers(len(names),size=(10000,len(names)));cluster=np.sum(sums[ci],axis=1)/np.sum(sizes[ci],axis=1)
 rng=np.random.default_rng(seed+2);exceed=0
 for _ in range(100):
  signs=2*rng.integers(2,size=(1000,n))-1;observed=np.mean(signs*d,axis=1);exceed+=np.count_nonzero(np.abs(observed)>=abs(np.mean(d))-1e-14)
 return {'effect':float(np.mean(d)),'item_ci':np.quantile(boot,[.025,.975]).tolist(),'cluster_ci':np.quantile(cluster,[.025,.975]).tolist(),'p':float(exceed+1)/100001}
def holm(ps):
 order=sorted(range(len(ps)),key=lambda k:ps[k]);out=[None]*len(ps);prior=0.
 for rank,i in enumerate(order):prior=max(prior,min(1.,(len(ps)-rank)*ps[i]));out[i]=prior
 return out
def compare(actual,expected,label,checks):
 a=np.asarray(actual,dtype=float);b=np.asarray(expected,dtype=float);require(a.shape==b.shape,label+' shape differs');delta=float(np.max(np.abs(a-b)));require(np.isfinite(delta) and delta<=TOL,(label,delta,actual,expected));checks.append({'check':label,'max_abs_error':delta})
def replay(directory,experiment):
 full=rows(directory/'full_outcomes.csv');plan=rows(directory/'manifest.csv');attempts=rows(directory/'attempts.csv');reference=json.loads((directory/'scientific_results.json').read_text());checks=[]
 total=2336 if experiment=='E1' else 3375;population=146 if experiment=='E1' else 225
 require(len(full)==total and len({r['trial_id'] for r in full})==total,'Incomplete/duplicate formal rows');require(len(plan)==total and {r['trial_id'] for r in plan}=={r['trial_id'] for r in full},'Manifest differs from results')
 require({r['trial_id'] for r in attempts}=={r['trial_id'] for r in full},'Attempts differ from manifest');require(all(r['phase']=='full' for r in attempts),'Pilot pooled into formal rows')
 uids=sorted({r['utterance_id'] for r in full});require(len(uids)==population,'Population size differs');cells={(r['utterance_id'],r['condition'],r['arm']):r for r in full};require(len(cells)==total,'Duplicate condition/arm cells')
 base='RECODE' if experiment=='E1' else 'A_RECODE';high='BLUR_L3' if experiment=='E1' else 'A_SNR00';clean='CLEAN' if experiment=='E1' else 'A_CLEAN';groups=[cells[u,base,ORDERS[0]]['dialogue_id'] for u in uids];require(len(set(groups))==(134 if experiment=='E1' else 177),'Official cluster count differs')
 def vec(c,k):return np.array([sum(cells[u,c,o]['outcome']==k for o in ORDERS)/2 for u in uids])
 def delta(k):return vec(high,k)-vec(base,k)
 def interaction(k):return np.array([(int(cells[u,high,ORDERS[0]]['outcome']==k)-int(cells[u,base,ORDERS[0]]['outcome']==k))-(int(cells[u,high,ORDERS[1]]['outcome']==k)-int(cells[u,base,ORDERS[1]]['outcome']==k)) for u in uids])
 def slope(k):
  conditions=['RECODE','BLUR_L1','BLUR_L2','BLUR_L3'] if experiment=='E1' else ['A_RECODE','A_SNR20','A_SNR10','A_SNR00'];a=np.column_stack([vec(c,k) for c in conditions]);return ((a-a.mean(axis=1,keepdims=True))*np.array([-1.5,-.5,.5,1.5])).sum(axis=1)/5
 arm='V_ONLY' if experiment=='E1' else 'A_ONLY';labelkey='y_V' if experiment=='E1' else 'y_A'
 correct=np.array([int(cells[u,high,arm]['parsed_label']==cells[u,high,arm][labelkey])-int(cells[u,base,arm]['parsed_label']==cells[u,base,arm][labelkey]) for u in uids])
 entropy=np.array([float(cells[u,high,arm]['entropy_normalized'])-float(cells[u,base,arm]['entropy_normalized']) for u in uids])
 estimates=[];primary=[];secondary=[]
 if experiment=='E1':
  cats=['SIDE_V','SIDE_A','OTHER'];vectors={k+'_L3_MINUS_RECODE':delta(k) for k in cats}
  for k in cats:vectors[k+'_CLEAN_MINUS_RECODE']=vec(clean,k)-vec(base,k);vectors[k+'_ORDINAL_DOSE_SLOPE']=slope(k);vectors[k+'_ORDER_INTERACTION']=interaction(k)
  vectors['V_ONLY_CORRECTNESS_L3_MINUS_RECODE']=correct;vectors['V_ONLY_NORMALIZED_ENTROPY_L3_MINUS_RECODE']=entropy
  family=[('primary',reference['primary']),('secondary',reference['secondary'])]
 else:
  target='SHARED_LABEL';vectors={'PRIMARY':delta(target)};cats=['SHARED_LABEL','OTHER','PARSE_FAIL','TECH_FAILURE']
  for k in cats:
   if k!=target:vectors[k+'_HIGH_MINUS_RECODE']=delta(k)
  vectors['CLEAN_MINUS_RECODE_PIPELINE']=vec(clean,target)-vec(base,target);vectors['ORDER_INTERACTION']=interaction(target)
  for c in ['A_SNR10','A_SNR20']:vectors[c+'_MINUS_RECODE']=vec(c,target)-vec(base,target)
  vectors['ORDINAL_DOSE_RESPONSE']=slope(target);vectors['UNIMODAL_SOURCE_LABEL_MATCH']=correct;vectors['UNIMODAL_ENTROPY']=entropy
  family=[('primary',[{'endpoint':'PRIMARY',**reference['primary']}]),('secondary',reference['secondary'])]
 for kind,records in family:
  computed=[]
  for ref in records:
   name=ref['endpoint'];r=paired(vectors[name],groups,int(ref['seed']));effectkey='effect' if experiment=='E1' else 'estimate';itemkey='utterance_ci95' if experiment=='E1' else 'item_ci95';pkey='p_two_sided' if experiment=='E1' else 'two_sided_signflip_p'
   compare(r['effect'],ref[effectkey],name+':effect',checks);compare(r['item_ci'],ref[itemkey],name+':item_CI',checks);compare(r['cluster_ci'],ref['dialogue_cluster_ci95'],name+':dialogue_CI',checks);compare(r['p'],ref[pkey],name+':p',checks);computed.append((ref,r));estimates.append({'endpoint':name,'family':kind,**r})
  if kind=='secondary' or experiment=='E1':
   adjusted=holm([r['p'] for ref,r in computed]);key='p_holm' if experiment=='E1' else 'holm_p'
   for (ref,r),p in zip(computed,adjusted):compare(p,ref[key],ref['endpoint']+':Holm',checks)
 if experiment=='E1':
  original=json.loads((directory/'order_effects.json').read_text())
  for ref in original:
   order=ref['arm'];cat=ref['category'];d=[int(cells[u,high,order]['outcome']==cat)-int(cells[u,base,order]['outcome']==cat) for u in uids];r=paired(d,groups,ref['seed'])
   for field,target in [('effect','effect'),('item_ci','utterance_ci95'),('cluster_ci','dialogue_cluster_ci95'),('p','p_two_sided')]:compare(r[field],ref[target],f'{order}:{cat}:{field}',checks)
 # Recompute all category transitions from the complete scientific population.
 transitionfile=directory/'category_transitions.csv'
 if transitionfile.exists():
  for row in rows(transitionfile):
   a=row.get('from_condition',base);b=row.get('to_condition',row.get('condition'));o=row['arm'];n=sum(cells[u,a,o]['outcome']==row['from'] and cells[u,b,o]['outcome']==row['to'] for u in uids)
   # E2 source table subdivides a category cell by parsed labels.
   if 'from_label' in row:n=sum(cells[u,a,o]['outcome']==row['from'] and cells[u,b,o]['outcome']==row['to'] and cells[u,a,o]['parsed_label']==row['from_label'] and cells[u,b,o]['parsed_label']==row['to_label'] for u in uids)
   require(n==int(row['n']),('TRANSITION_COUNT_DIFFERS',row))
 probabilities=rows(directory/'candidate_probabilities.csv');by=collections.defaultdict(list)
 for r in probabilities:by[r['trial_id']].append(r)
 expected={r['trial_id'] for r in full if experiment=='E1' or r['arm']=='A_ONLY'};require(set(by)==expected,'Candidate probability coverage differs')
 final={r['trial_id']:r for r in full}
 for uid,rs in by.items():
  ps=[float(r['probability_mean_score_primary']) for r in rs];require(len(ps)==7 and len({r['label'] for r in rs})==7 and all(math.isfinite(p) and 0<=p<=1 for p in ps) and abs(sum(ps)-1)<1e-8,'Invalid candidate distribution');h=-sum(p*math.log(p) for p in ps if p>0)/math.log(7);compare(h,float(final[uid]['entropy_normalized']),uid+':entropy',checks)
 return {'status':'PASS','experiment':experiment,'formal_trials':total,'items':population,'dialogue_clusters':len(set(groups)),'checks':len(checks),'max_abs_error':max((r['max_abs_error'] for r in checks),default=0),'bootstrap_replicates':10000,'signflip_replicates':100000,'CI_REPRODUCIBILITY':'PUBLIC_PROJECTION_REPLAY_PASS','GPU_calls':0,'refits':0,'post_treatment_filtering':False,'estimates':estimates}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--repo-root',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);parser.add_argument('--experiment',choices=['E1','E2','both'],default='both');args=parser.parse_args();result={'status':'PASS','numpy_version':np.__version__}
 for experiment,folder in [('E1','emotiontalk_e1_video_v2'),('E2','emotiontalk_e2_consistent_audio_v1')]:
  if args.experiment in [experiment,'both']:result[experiment]=replay(args.repo_root/'results'/folder,experiment)
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:({x:v[x] for x in ['status','formal_trials','checks','max_abs_error']} if isinstance(v,dict) else v) for k,v in result.items()}))
if __name__=='__main__':main()
