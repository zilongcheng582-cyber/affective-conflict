from e1e2_common import *
import numpy as np,math,time
SEED=2026101110;BOOT=10000;SIGN=100000
def estimate(d,clusters,seed):
 d=np.asarray(d,dtype=float);rng=np.random.default_rng(seed)
 boot=np.mean(d[rng.integers(0,len(d),size=(BOOT,len(d)))],axis=1)
 names=sorted(set(clusters));sums=np.array([sum(d[i] for i,k in enumerate(clusters) if k==name) for name in names]);sizes=np.array([clusters.count(name) for name in names]);idx=np.random.default_rng(seed+1).integers(0,len(names),size=(BOOT,len(names)));cb=sums[idx].sum(axis=1)/sizes[idx].sum(axis=1)
 signs=np.random.default_rng(seed+2);exceed=0
 for _ in range(100):
  draws=signs.integers(0,2,size=(SIGN//100,len(d)))*2-1;exceed+=int((np.abs((draws*d).mean(axis=1))>=abs(d.mean())-1e-14).sum())
 return {'estimate':float(d.mean()),'item_ci95':np.quantile(boot,[.025,.975]).tolist(),'dialogue_cluster_ci95':np.quantile(cb,[.025,.975]).tolist(),'two_sided_signflip_p':(1+exceed)/(SIGN+1),'items':len(d),'dialogue_clusters':len(names),'seed':seed,'bootstrap_replicates':BOOT,'signflip_replicates':SIGN}
def outcome(t,r):
 if r['technical_failure']:return 'TECH_FAILURE'
 if r.get('parser_status')=='PARSE_FAIL' or r.get('parsed_label') is None:return 'PARSE_FAIL'
 label=r['parsed_label']
 if t['experiment']=='E1':return 'SIDE_A' if label==t['y_A'] else ('SIDE_V' if label==t['y_V'] else 'OTHER')
 return 'SHARED_LABEL' if label==t['y_A'] else 'OTHER'
def analyze(exp,output):
 f=O/'01_protocol_freeze';mf=rows(f/f'{exp}_FULL_MANIFEST.csv');protocol=json.loads((f/f'{exp}_FROZEN_PROTOCOL.json').read_text());run=O/('02_e1_video' if exp=='E1' else '03_e2_consistent')
 for p,h in protocol['locked_files'].items():assert sha(p)==h
 by=collections.defaultdict(list)
 for p in (run/'attempts').glob('*.json'):
  r=json.loads(p.read_text());by[r['trial_id']].append(r)
 assert set(by)=={t['trial_id'] for t in mf}
 final={k:sorted(v,key=lambda r:r['attempt'])[-1] for k,v in by.items()};uids=sorted({t['utterance_id'] for t in mf});joint=[t for t in mf if not t['arm'].endswith('_ONLY')]
 cells={};out=[]
 for t in mf:
  r=final[t['trial_id']];oc=outcome(t,r);en=r.get('candidate_entropy_primary',{}).get('normalized_by_log7')
  row={**t,'outcome':oc,'parsed_label':r.get('parsed_label') or '', 'technical_failure':r['technical_failure'],'attempt_count':len(by[t['trial_id']]),'entropy_normalized':en if en is not None else ''};out.append(row);cells[t['utterance_id'],t['condition'],t['arm']]=row
 table(output/f'{exp}_FULL_OUTCOMES.csv',out)
 orders=['A_THEN_V','V_THEN_A'];conditions=sorted({t['condition'] for t in mf});base='V_RECODE' if exp=='E1' else 'A_RECODE';high='V_BLUR_HIGH' if exp=='E1' else 'A_SNR00';clean='V_CLEAN' if exp=='E1' else 'A_CLEAN';primary_target='SIDE_V' if exp=='E1' else 'SHARED_LABEL'
 clusters=[cells[u,base,orders[0]]['dialogue_id'] for u in uids]
 def vector(cond,category):return np.array([sum(cells[u,cond,o]['outcome']==category for o in orders)/2 for u in uids])
 d=vector(high,primary_target)-vector(base,primary_target)+vector(high,'TECH_FAILURE');primary=estimate(d,clusters,SEED+(0 if exp=='E1' else 100))
 # Conservative versus negative H1: high technical missing=success, baseline missing=failure.
 low=[];upper=[];complete=[]
 for u in uids:
  b=[cells[u,base,o] for o in orders];h=[cells[u,high,o] for o in orders]
  bv=sum(r['outcome']==primary_target for r in b)/2;hv=sum(r['outcome']==primary_target for r in h)/2;bm=sum(r['outcome']=='TECH_FAILURE' for r in b)/2;hm=sum(r['outcome']=='TECH_FAILURE' for r in h)/2
  low.append(hv-bv-bm);upper.append(hv+hm-bv)
  if not(bm+hm):complete.append(hv-bv)
 primary.update(ITT_denominator_items=len(uids),joint_primary_cells=len(uids)*4,technical_missing_ITT_rule='NEGATIVE_H1_CONSERVATIVE_HIGH_SUCCESS_BASELINE_FAILURE',technical_failure_conservative_effect_bounds=[float(np.mean(low)),float(np.mean(upper))],complete_case_items=len(complete),complete_case_effect=float(np.mean(complete)) if complete else None,post_treatment_selection=False)
 cats=['SIDE_A','SIDE_V','OTHER','PARSE_FAIL','TECH_FAILURE'] if exp=='E1' else ['SHARED_LABEL','OTHER','PARSE_FAIL','TECH_FAILURE']
 secondary=[]
 for ci,cat in enumerate(cats):
  if cat!=primary_target:secondary.append({'endpoint':cat+'_HIGH_MINUS_RECODE',**estimate(vector(high,cat)-vector(base,cat),clusters,SEED+300+ci)})
 secondary.append({'endpoint':'CLEAN_MINUS_RECODE_PIPELINE',**estimate(vector(clean,primary_target)-vector(base,primary_target),clusters,SEED+400)})
 od=np.array([(int(cells[u,high,orders[0]]['outcome']==primary_target)-int(cells[u,base,orders[0]]['outcome']==primary_target))-(int(cells[u,high,orders[1]]['outcome']==primary_target)-int(cells[u,base,orders[1]]['outcome']==primary_target)) for u in uids]);secondary.append({'endpoint':'ORDER_INTERACTION',**estimate(od,clusters,SEED+500)})
 inter=[x for x in conditions if x not in [clean,base,high]]
 for i,cond in enumerate(inter):secondary.append({'endpoint':cond+'_MINUS_RECODE',**estimate(vector(cond,primary_target)-vector(base,primary_target),clusters,SEED+600+i)})
 # Linear within-item slope over pre-frozen ordinal intervention intensity (recode + 3 levels).
 doseconds=['V_RECODE','V_BLUR_LOW','V_BLUR_MED','V_BLUR_HIGH'] if exp=='E1' else ['A_RECODE','A_SNR20','A_SNR10','A_SNR00'];dv=np.column_stack([vector(c,primary_target) for c in doseconds]);slope=((dv-dv.mean(axis=1,keepdims=True))*np.array([-1.5,-.5,.5,1.5])).sum(axis=1)/5
 secondary.append({'endpoint':'ORDINAL_DOSE_RESPONSE',**estimate(slope,clusters,SEED+700)})
 unimodal='V_ONLY' if exp=='E1' else 'A_ONLY';match=[];entropy=[]
 for u in uids:
  a=cells[u,base,unimodal];b=cells[u,high,unimodal];label=a['y_V'] if exp=='E1' else a['y_A'];match.append(float(b['parsed_label']==label)-float(a['parsed_label']==label))
  if a['entropy_normalized']!='' and b['entropy_normalized']!='':entropy.append((u,float(b['entropy_normalized'])-float(a['entropy_normalized'])))
 secondary.append({'endpoint':'UNIMODAL_SOURCE_LABEL_MATCH',**estimate(match,clusters,SEED+800)})
 if len(entropy)==len(uids):secondary.append({'endpoint':'UNIMODAL_ENTROPY',**estimate([v for u,v in entropy],clusters,SEED+900)})
 ranked=sorted(range(len(secondary)),key=lambda i:secondary[i]['two_sided_signflip_p']);running=0
 for rank,i in enumerate(ranked):running=max(running,min(1,(len(ranked)-rank)*secondary[i]['two_sided_signflip_p']));secondary[i]['holm_p']=running
 transitions=[]
 for cond in conditions:
  if cond==base:continue
  for arm in orders:
   counts=collections.Counter((cells[u,base,arm]['outcome'],cells[u,cond,arm]['outcome'],cells[u,base,arm]['parsed_label'],cells[u,cond,arm]['parsed_label']) for u in uids)
   for (a,b,la,lb),n in sorted(counts.items()):transitions.append({'condition':cond,'arm':arm,'from':a,'to':b,'from_label':la,'to_label':lb,'n':n})
 table(output/f'{exp}_MATCHED_TRANSITIONS.csv',transitions)
 accounting=[]
 for cond in conditions:
  for arm in orders+[unimodal]:
   for cat in cats:accounting.append({'condition':cond,'arm':arm,'outcome':cat,'n':sum(cells[u,cond,arm]['outcome']==cat for u in uids),'denominator':len(uids)})
 table(output/f'{exp}_OUTCOME_ACCOUNTING.csv',accounting)
 strata=[]
 for field in ['stratum','y_A','dialogue_id']:
  for val in sorted({cells[u,base,orders[0]][field] for u in uids}):
   indices=[i for i,u in enumerate(uids) if cells[u,base,orders[0]][field]==val];strata.append({'grouping':field,'value':val,'items':len(indices),'effect':float(d[indices].mean()),'role':'PREDEFINED_DESCRIPTIVE'})
 for baseline in ['BOTH_CORRECT','ONE_CORRECT','NONE_CORRECT']:
  indices=[i for i,u in enumerate(uids) if ['NONE_CORRECT','ONE_CORRECT','BOTH_CORRECT'][int(2*vector(base,primary_target)[i])]==baseline]
  if indices:strata.append({'grouping':'RECODE_BASELINE_STATUS','value':baseline,'items':len(indices),'effect':float(d[indices].mean()),'role':'DESCRIPTIVE_POST_TREATMENT_NOT_PRIMARY_SELECTION'})
 table(output/f'{exp}_DESCRIPTIVE_STRATA.csv',strata)
 verdict='SUPPORTED' if primary['estimate']<0 and primary['two_sided_signflip_p']<.05 and primary['item_ci95'][1]<0 else 'NOT_SUPPORTED'
 if primary['technical_failure_conservative_effect_bounds'][0]!=primary['technical_failure_conservative_effect_bounds'][1]:verdict='INCONCLUSIVE'
 result={'primary':primary,'secondary':secondary,'scientific_ruling':verdict,'missing_entropies':len(uids)-len(entropy),'complete_population':len(uids),'all_attempts':sum(len(v) for v in by.values()),'technical_failure_attempts':sum(r['technical_failure'] for v in by.values() for r in v),'retained_technical_missing':sum(r['technical_failure'] for r in final.values()),'retries':sum(len(v)-1 for v in by.values()),'scientific_scope':'E1 video arbitration response; E2 shared-label retention on a different fixed population; no entropy mediation or randomized cross-population interaction'}
 dump(output/f'{exp}_PRIMARY_ANALYSIS.json',result)
 check='VONLY' if exp=='E1' else 'AONLY';(output/f'{exp}_{check}_MANIPULATION_CHECK.md').write_text('# Frozen full manipulation check\n\n'+json.dumps([s for s in secondary if s['endpoint'].startswith('UNIMODAL')],indent=2)+'\n\nNo selection using these post-intervention measurements. Entropy is teacher-forced seven-candidate scoring only.\n')
 (output/f'{exp}_SCIENTIFIC_REPORT.md').write_text(f'# {exp} prospective full scientific report\n\nRuling: {verdict}. Primary effect {primary["estimate"]*100:.6f} pp; item CI {primary["item_ci95"]}; dialogue CI {primary["dialogue_cluster_ci95"]}; two-sided sign-flip p {primary["two_sided_signflip_p"]}.\n\nAll planned items retained. See PRIMARY_ANALYSIS, OUTCOME_ACCOUNTING, MATCHED_TRANSITIONS and DESCRIPTIVE_STRATA for full results. E2 cannot identify which modality produced a shared label. Physical intensities are not calibrated equivalent to ERI1. No entropy mediation claim. Confirmation awaits independent verification.\n')
 return result
if __name__=='__main__':
 import sys
 exp=sys.argv[1];output=pathlib.Path(sys.argv[2]);output.mkdir(parents=True,exist_ok=True);print(json.dumps(analyze(exp,output)['primary']))
