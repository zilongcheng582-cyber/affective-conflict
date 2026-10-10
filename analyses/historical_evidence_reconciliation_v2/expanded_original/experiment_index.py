import json,csv,collections,re,hashlib
from pathlib import Path
R=Path('/root/autodl-tmp/affective-conflict');O=Path('/root/autodl-tmp/affective-conflict-forensics-expanded-v1')
inv=json.load(open(O/'EXPANDED_FILE_INVENTORY.json'));docs='\n'.join(p.read_text(errors='replace') for p in [R/'AGENTS.md',R/'docs/PROJECT_STATE.md',R/'docs/FILE_MAP.md',R/'docs/DECISIONS.md'])
index=[]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
for f in inv:
 p=Path(f['path']);rel=str(p.relative_to(R));low=rel.lower()
 if not (rel.startswith(('audit/','results/','logs/')) or '\\' in rel):continue
 if p.suffix!='.jsonl' or 'manifest' in low or 'text_evidence' in low:continue
 if f['size']>200000000:continue
 n=bad=raw=genok=genfail=0;keys=collections.Counter();conditions=collections.Counter();statuses=collections.defaultdict(collections.Counter);ex=[];ids=set()
 with p.open(errors='replace') as fh:
  for line in fh:
   if not line.strip():continue
   try:r=json.loads(line)
   except Exception:bad+=1;continue
   if not isinstance(r,dict):continue
   n+=1;keys.update(r.keys())
   sid=r.get('sample_id',r.get('original_sample_id',r.get('trial_id',r.get('utterance_id'))))
   if sid is not None:ids.add(str(sid))
   conditions[str(r.get('arm',r.get('condition',r.get('order','UNKNOWN'))))]+=1
   raw+=any(r.get(k) is not None for k in ['raw_model_output','raw_generated_sequence','prediction_raw','raw_generation','assistant_text','raw_response','generated_text'])
   genok+=r.get('generation_success') is True or r.get('generation_status')=='SUCCESS'
   genfail+=r.get('generation_success') is False or r.get('generation_status') in ['FAIL','FAILED']
   for k in ['parse_status','parser_status_raw','technical_status','generation_status','status','error_type','run_type','scoring_status','failure_type']:
    if k in r:statuses[k][str(r[k])]+=1
   if len(ex)<1:ex.append({k:r[k] for k in r if k in ['run_id','runner_version','model_revision','model_identity','protocol_version','start_time','started_utc','timestamp','scientific_result','formal_full_run','sample_id','generation_success','status']})
 hash=sha(p);skeleton=any(x in low for x in ['skeleton','reconstruction']) and not raw
 if raw or genok or genfail:kind='EXECUTION_RECORDS'
 elif skeleton:kind='CPU_RECONSTRUCTION_NOT_NEW_INFERENCE'
 else:kind='PLAN_OR_DERIVED_OR_UNKNOWN'
 index.append({'path':str(p),'relative_path':rel,'sha256':hash,'size':f['size'],'rows':n,'unique_items':len(ids),'bad_rows':bad,'raw_output_present':raw,'generation_success_explicit':genok,'generation_failure_explicit':genfail,'conditions':dict(conditions),'statuses':{k:dict(v) for k,v in statuses.items()},'keys':list(keys),'example':ex,'evidence_kind':kind,'filename_explicit_in_core_docs':p.name in docs,'directory_explicit_in_core_docs':str(p.parent.relative_to(R)) in docs})
groups=collections.defaultdict(list)
for r in index:groups[r['sha256']].append(r['path'])
for r in index:r['identical_byte_paths']=groups[r['sha256']]
(O/'EXPERIMENT_EXECUTION_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2))
summary={'total_jsonl_files':len(index),'execution_record_files':sum(r['evidence_kind']=='EXECUTION_RECORDS' for r in index),'unique_execution_byte_artifacts':len({r['sha256'] for r in index if r['evidence_kind']=='EXECUTION_RECORDS'}),'execution_files_not_named_in_core_docs':[r for r in index if r['evidence_kind']=='EXECUTION_RECORDS' and not r['filename_explicit_in_core_docs']],'scope':'audit/results/logs/anomalous paths only; excludes upstream repository and raw datasets; filenames absent does not mean experiment wholly undocumented'}
(O/'EXPERIMENT_INDEX_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print('EXPERIMENT_INDEX_DONE',len(index),summary['execution_record_files'],len(summary['execution_files_not_named_in_core_docs']))
