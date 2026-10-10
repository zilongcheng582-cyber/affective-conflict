import json,csv,hashlib,collections,re
from pathlib import Path
R=Path('/root/autodl-tmp/affective-conflict');O=Path('/root/autodl-tmp/affective-conflict-reconciliation-v2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
evidence=[];docs={};pools={}
for name in ['MCR_SER_AUDIT.md','MCR_SER_DUPLICATE_AUDIO.md','MCR_SER_FINAL.md','mcr_ser_native_pool_1000.csv','mcr_ser_safe_pool.csv','mcr_ser_arbitration_pool_909.csv','mcr_ser_sensitivity_pool_924.csv']:
 p=R/'audit'/name
 if p.suffix=='.md':docs[str(p)]={'sha256':sha(p),'text':p.read_text()}
 else:
  rs=list(csv.DictReader(open(p)));pools[name]={'rows':len(rs),'fields':list(rs[0]),'source_indices':[int(r['source_index']) for r in rs] if 'source_index' in rs[0] else [],'example':rs[0]}
 evidence.append({'path':str(p),'sha256':sha(p),'records':pools.get(name,{}).get('rows'),'role':'MCR original pool/duplicate-audio audit'})
join=list(csv.DictReader(open(O/'MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.csv')));groups=collections.defaultdict(list)
for r in join:groups[r['native_audio_sha256']].append(r)
excluded=[];conflictinggroups=0
for h,rs in groups.items():
 labels={r['native_gt'] for r in rs};conflictinggroups+=len(labels)>1
 for r in rs:
  if r['controlled_included']=='False':excluded.append({'source_index':int(r['source_index']),'audio_sha256':h,'audio_group_items':len(rs),'audio_group_labels':sorted(labels),'reason_verified_from_hash_group':'CONFLICTING_GT_FOR_IDENTICAL_AUDIO' if len(labels)>1 else 'OTHER_POOL_RULE_REQUIRES_AUDIT'})
out={'pool_evidence':evidence,'pool_schemas':pools,'docs':docs,'conflicting_audio_hash_groups':conflictinggroups,'excluded_91':excluded,'excluded_reason_counts':dict(collections.Counter(r['reason_verified_from_hash_group'] for r in excluded)),'controlled_source_indices_equal_frozen_909':{int(r['source_index']) for r in join if r['controlled_included']=='True'}==set(pools['mcr_ser_arbitration_pool_909.csv']['source_indices'])}
(O/'MCR_POOL_AND_DUPLICATE_AUDIO_AUDIT_V2.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
# Supplemental scalar coverage proof in all previously registered CA-MER rows.
reg=list(csv.DictReader(open('/root/autodl-tmp/affective-conflict-forensics-expanded-v1/RECOVERED_EXPERIMENT_EXECUTION_REGISTER.csv')));score=[]
for f in reg:
 if 'CAMER' not in f['path']:continue
 n=0;raw=0;vectors=0;hints=set()
 for l in open(f['path']):
  if not l.strip():continue
  r=json.loads(l);n+=1;raw+=bool(r.get('raw_model_output'))
  for k,v in r.items():
   if re.search('logit|logprob|log_prob|probabilit|entropy|candidate_score',k,re.I):hints.add(k)
   if isinstance(v,(list,dict)) and len(v)==16 and all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in (v.values() if isinstance(v,dict) else v)):vectors+=1
 score.append({'path':f['path'],'sha256':sha(Path(f['path'])),'records':n,'raw_model_outputs':raw,'score_field_names':sorted(hints),'numeric_16_element_vectors_any_field':vectors})
(O/'CAMER_ALL_RECOVERED_SCORE_ASSET_AUDIT_V2.json').write_text(json.dumps(score,indent=2))
print('POOL_AND_SCORE_AUDIT_DONE',out['excluded_reason_counts'],len(score),sum(r['numeric_16_element_vectors_any_field'] for r in score))
