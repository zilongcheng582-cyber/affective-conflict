"""Verify provenance, bounded supplemental protocol identity, then seal quiescent outputs."""
import phase4_transfer as a
import pathlib,json,datetime,collections,subprocess,zipfile
O=a.O;P=a.P;R=a.R
def verify():
 a.verify();nav={x['path']:x for x in a.read(O/'NAVIGATION_MEMORY_UPDATE.json')['updates']};checked=[]
 for name in ['SOURCE_INPUT_LOCK.json','ADDITIONAL_INPUT_LOCK.json','CONSTRUCT_INPUT_LOCK.json','PHASE4_ADDITIONAL_PROTOCOL_LOCK.json']:
  for x in a.read(O/name):
   if x['path'] in nav:
    u=nav[x['path']];assert a.sha(u['backup_path'])==x['sha256'];assert a.sha(x['path'])==u['after_sha256'];status='ORIGINAL_REFERENCE_BACKUP_MATCH_AND_AUTHORIZED_APPEND'
   else:assert a.sha(x['path'])==x['sha256'],x['path'];status='UNCHANGED'
   checked.append({'lock':name,'path':x['path'],'expected_sha256':x['sha256'],'status':status})
 for x in a.read(O/'phase4_numeric/TRANSFER_RESULTS.json')['historical_binding_crosschecks']:assert a.sha(x['path'])==x['sha256']
 pkg=pathlib.Path('/root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1');amend=pkg.parent/'amendment_001/B3_EXECUTION_TECHNICAL_AMENDMENT_001.json';d=a.read(amend)
 assert all(d[k] is False for k in ['scientific_protocol_changed','population_changed','assignment_changed','model_changed','processor_changed','source_model_changed','target_refit_performed','original_package_files_changed'])
 extra=[]
 for name,h in d['unchanged_scientific_and_execution_sha256'].items():
  p=pkg/name;assert p.is_file() and a.sha(p)==h,(name,str(p));n=len(a.read(p)) if p.suffix in ['.csv','.jsonl'] else 'JSON object' if p.suffix=='.json' else 'not row data';extra.append({'path':str(p),'sha256':h,'records':n,'identity_check':'EXACT_AMENDMENT_UNCHANGED_SCIENTIFIC_HASH'})
 raw=a.read(a.B3);assert {x['model_content_sha256'] for x in raw}=={d['unchanged_scientific_and_execution_sha256']['MODEL_FILE_HASH_MANIFEST.csv']};assert {x['processor_content_sha256'] for x in raw}=={d['unchanged_scientific_and_execution_sha256']['PROCESSOR_FILE_HASH_MANIFEST.csv']}
 assert len({x['prompt_hash'] for x in raw})==1
 a.save('PHASE4_SUPPLEMENTAL_EXECUTION_IDENTITY_CHECK.json',{'status':'PASS','amendment_path':str(amend),'amendment_sha256':a.sha(amend),'amendment_kind':d['root_cause_class'],'amendment_bug':d['exact_bug'],'scientific_fields_affected':d['scientific_fields_affected'],'model_content_sha256':next(iter({x['model_content_sha256'] for x in raw})),'processor_content_sha256':next(iter({x['processor_content_sha256'] for x in raw})),'model_revision':sorted({x['model_revision'] for x in raw}),'processor_revision':sorted({x['processor_revision'] for x in raw}),'scoring_implementation_sha256':sorted({x['scoring_code_sha256'] for x in raw}),'additional_frozen_assets':extra})
 reg=O/'04_TRANSFER_FROZEN_EVIDENCE_REGISTER.md';text=reg.read_text()
 if '## Technical Amendment001 and execution identity closure' not in text:
  text+='\n## Technical Amendment001 and execution identity closure\n\nThe actual Amendment001 fixes Windows/Linux `sorted(Path)` inventory-order comparison; it changes only verifier dependency/wrapper, with scientific_fields_affected=[] and frozen population/model/processor/assignment/source model unchanged. Every listed unchanged scientific byte hash was independently rechecked. It is a technical amendment, not a revised Transfer hypothesis or target-fitted model. Corrected model contentSHA8240abe64f8df444e7a4ebbcb636f51e6ef7e6833b62cf60adec0b2d14125a09, processorSHAe471b7e2830ec4f53ee249b2a6707480858e357b30b4dc1616e718ef6fe18d41, model/processorrevisionae9e1690543ffd5c0221dc27f79834d0294cba00. The scoring implementation bindingSHA3246b9ee0fea14948c0ac894181cf513322df7d969b87d6b8af92b17ce120e17 is distinct from scorer module byteSHA; neither is silently substituted.\n\n| path | SHA256 | actual records |\n| --- | --- | --- |\n'+'\n'.join('| '+x['path']+' | '+x['sha256']+' | '+str(x['records'])+' |' for x in extra)+'\n';reg.write_text(text)
 claims=a.read(O/'CLAIM_EVIDENCE_MATRIX.csv');cats={x['category'] for x in claims};assert len(claims)==25 and cats=={'R1 Source Prediction','R2 Compositionality','Frozen Transfer','ERI1 Causal Intervention','Recovered Native Experiments','Transfer Failure Explanation'}
 required=['04_TRANSFER_FROZEN_EVIDENCE_REGISTER.md','04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv','04_TRANSFER_FAILURE_DECOMPOSITION.md','04_TRANSFER_RECOVERED_EVIDENCE_LINKAGE.md','04_TRANSFER_CLAIM_BOUNDARY_MATRIX.md','04_RECOVERED_EVIDENCE_CROSS_STUDY_SYNTHESIS.md','05_CLAIM_EVIDENCE_MATRIX.md','06_QWEN_NEXT_EXPERIMENT_DECISION.md','07_FINAL_SCIENTIFIC_EXECUTIVE_SUMMARY.md']
 for n in required:assert (O/n).stat().st_size>100
 assert len(a.read(O/'04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv'))==18
 assert a.read(O/'phase4_replay_same_seed/PHASE4_REPLAY_CHECK.json')['status']=='PASS'
 # Original replay's three reference mappings must still pass after append-only maintenance.
 q=subprocess.run(['python3',str(O/'replay.py'),str(O/'phase4_original_replay_prepare'),'--prepare-only'],capture_output=True,text=True)
 assert q.returncode==0,q.stderr
 a.save('PHASE4_FINAL_VERIFICATION.json',{'status':'PASS','source_locks_checked':len(checked),'source_inputs':checked,'frozen_git_commit':a.COMMIT,'prediction_rows':9219,'measurement_rows':6354,'reports':18,'strict_linkage_rows':5199,'claim_rows':25,'categories':sorted(cats),'deterministic_repeat_files':6,'original_phase1_3_replay_prepare':'PASS','GPU_execution':False,'model_loading':False,'source_refit':False,'target_refit':False,'frozen_protocol_modified':False,'historical_scientific_inputs_modified':False,'navigation_append_only':True,'required_files':required})
 p=a.read(O/'RUN_PROVENANCE.json');p['phase4']['final_verification']='PHASE4_FINAL_VERIFICATION.json';p['phase4']['code_sha256']['phase4_seal.py']=a.sha(__file__);a.save('RUN_PROVENANCE.json',p)
 print('PHASE4_FINAL_SOURCE_AND_DELIVERABLE_CHECK_PASS',len(checked),len(extra),flush=True)
def seal():
 assert a.read(O/'PHASE4_FINAL_VERIFICATION.json')['status']=='PASS'
 rows=[]
 for p in sorted(O.rglob('*')):
  if not p.is_file() or p.name=='SHA256SUMS.txt' or p.suffix in ['.zip','.transfer','.pyc'] or '__pycache__' in p.parts:continue
  rows.append((a.sha(p),p.relative_to(O).as_posix()))
 (O/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for h,n in rows))
 assert all(a.sha(O/n)==h for h,n in rows)
 # Compact final bundle: reports, numeric tables/locks, replay scripts and receipts; exclude raw media/model/log payloads.
 names=[p for p in O.iterdir() if p.is_file() and (p.suffix in ['.md','.csv','.json','.py'] or p.name=='SHA256SUMS.txt') and not p.name.startswith(('INPUT_CONSTRUCTION','CONSTRUCT_AND_RUNTIME_FOCUS'))]
 names += [p for p in (O/'phase4_numeric').iterdir() if p.is_file()]
 names += [O/'phase4_replay_same_seed/PHASE4_REPLAY_CHECK.json']
 bundle=O/'PHASE4_INTEGRATED_VERIFIED_REPORTS.zip'
 with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in names:z.write(p,p.relative_to(O).as_posix())
 receipt={'status':'COMPLETE','manifest_path':str(O/'SHA256SUMS.txt'),'manifest_sha256':a.sha(O/'SHA256SUMS.txt'),'manifest_file_count':len(rows),'bundle_path':str(bundle),'bundle_sha256':a.sha(bundle),'bundle_bytes':bundle.stat().st_size,'bundle_files':len(names),'source_commit':a.COMMIT,'predictions_replayed':9219,'GPU':False,'STOP':True}
 # External transfer receipt is not part of the sealed analysis directory.
 print('PHASE4_SEAL_RECEIPT='+json.dumps(receipt),flush=True)
if __name__=='__main__':{'verify':verify,'seal':seal}[__import__('sys').argv[1]]()
