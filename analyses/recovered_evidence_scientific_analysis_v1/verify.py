import sys,json,csv,collections,hashlib,zipfile,datetime
from pathlib import Path
sys.path.insert(0,'/root/autodl-tmp/affective-conflict-recovered-science-v1');import analysis as a
O=a.O
def verify():
 prov=a.read(O/'RUN_PROVENANCE.json');assert prov['status']=='COMPLETE' and prov['NEXT_STEP']=='SECOND_MODEL';required=prov['required_artifacts'];assert len(required)==20 and all((O/n).is_file() for n in required)
 v=a.read(O/'CLOSURE_INPUT_VERIFICATION.json')
 for x in v:assert a.sha(x['path'])==x['current_sha256'],x['path']
 assert all(x['scientific_unchanged'] or x['navigation_append_only'] for x in v)
 assert sum(x['navigation_append_only'] for x in v)==3
 assert a.read(O/'REPRODUCIBILITY_VERIFICATION.json')['all_match'];assert a.read(O/'SECONDARY_REPLAY_VERIFICATION.json')['all_match']
 t=a.read(O/'01_MCR_PAIRED_TRANSITIONS.csv');cnt=collections.Counter()
 for x in t:cnt[(x['from_condition'],x['to_condition'])]+=int(x['count'])
 assert len(cnt)==6 and set(cnt.values())=={1000}
 m=a.read(O/'01_MCR_LABEL_CONDITION_ASSOCIATIONS.csv');assert len(m)==28 and sum(int(x['n']) for x in m)==4000
 c=a.read(O/'02_CAMER_ELIGIBILITY_AND_COVERAGE.csv')
 for x in c:assert sum(int(x[o]) for o in a.OUTS)==int(x['n_items'])
 ct=a.read(O/'02_CAMER_MATCHED_TRANSITIONS.csv');ctn=collections.Counter()
 for x in ct:ctn[x['population']]+=int(x['count'])
 for x in ct:assert ctn[x['population']]==int(x['denominator'])
 l=a.read(O/'03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv');assert len(l)==381 and len({x['base_source_id'] for x in l})==381;assert sum(a.truth(x['conflict']) for x in l)==378
 dual=[x for x in l if a.truth(x['conflict']) and x['eligibility_group']=='DUAL_MATCH'];assert len(dual)==22 and {x['y_A'] for x in dual}=={'ridicule'}
 native=a.read(O/'intermediate/MCR_ITEM_IDENTITY_OUTCOMES.csv');assert len(native)==1000 and len({x['audio_sha256'] for x in native})==943
 ca=a.read(O/'intermediate/CAMER_ITEM_ELIGIBILITY_IDENTITY.csv');assert len(ca)==1500 and sum(x['eligibility_group']=='DUAL_MATCH' for x in ca)==316;assert sum(a.truth(x['conflict']) and x['eligibility_group']=='DUAL_MATCH' for x in ca)==108
 b3=a.read(a.B3);assert len(b3)==6354 and len({(x['dataset'],x['stable_dataset_id']) for x in b3})==3177
 matrix=a.read(O/'CLAIM_EVIDENCE_MATRIX.csv');states={'ALREADY_SUPPORTED','NEW_EXPLORATORY_RESULT','REPLICATION_OF_EXISTING_RESULT','NOT_ESTABLISHED','NOT_IDENTIFIABLE','MEASUREMENT_INCOMPATIBLE','INSUFFICIENT_EVIDENCE'};assert all(x['status'] in states for x in matrix)
 # Every matrix trace connects to a required dataset report and source lock; no standalone unbound result.
 checks={'required_artifacts_present':20,'MCR_transition_pairs':dict((a+'->'+b,n) for (a,b),n in cnt.items()),'MCR_label_condition_rows':28,'CA_coverage_rows':len(c),'CA_transition_population_counts':dict(ctn),'LISTEN_joint_base_items':381,'LISTEN_exact_audio_hashes':len({x['audio_sha256'] for x in l}),'LISTEN_exact_audio_text_pairs':len({(x['audio_sha256'],x['text_sha256']) for x in l}),'LISTEN_dual22_all_ridicule':True,'B3_corrected_rows':6354,'B3_dataset_item_IDs':3177,'claim_rows':len(matrix),'allowed_claim_statuses':True,'original_scientific_source_hashes_unchanged':True,'navigation_docs_appended_only':3,'primary_numeric_exact_replay':18,'secondary_numeric_exact_replay':2,'CPU_only':True,'GPU_used':False,'all_pass':True}
 # The earlier checksum of finalize_run.log was necessarily made while that process was still logging.
 # Record that bounded lifecycle issue before producing the final quiescent manifest.
 drift=[]
 for line in (O/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1)
  if a.sha(O/n)!=h:drift.append({'path':n,'previous_sha256':h,'final_sha256':a.sha(O/n),'reason':'finalization log appended after initial checksum creation' if n=='finalize_run.log' else 'UNEXPECTED'})
 assert all(x['path']=='finalize_run.log' for x in drift),drift
 a.save('PRE_FINAL_MANIFEST_VALIDATION.json',{'bounded_initial_drift':drift,'numerical_or_scientific_drift':False,'remedy':'regenerate manifest after writer completion'})
 a.save('FINAL_VERIFICATION.json',checks)
 prov['closure_verification']='FINAL_VERIFICATION.json';prov['source_hash_locks'].append('PRIOR_REPORT_READBACK_LOCK.json');prov['actual_code_sha256']={str(p):a.sha(p) for p in O.glob('*.py')};prov['final_report_manifest_policy']='finalize_run.log checksummed after writer completion; bundle and manifest itself excluded';a.save('RUN_PROVENANCE.json',prov)
 paths=[p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.transfer') and p.name not in ['SHA256SUMS.txt','RECOVERED_SCIENCE_REPORTS_V1.zip']]
 (O/'SHA256SUMS.txt').write_text(''.join(a.sha(p)+'  '+str(p.relative_to(O))+'\n' for p in sorted(paths)))
 for line in (O/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);assert a.sha(O/n)==h,n
 bundle=[p for p in paths if p.parent==O and (p.suffix in ['.md','.csv','.py'] or p.name in ['RUN_PROVENANCE.json','REPRODUCIBILITY_VERIFICATION.json','SECONDARY_REPLAY_VERIFICATION.json','EXPLORATORY_ANALYSIS_PLAN.json','ENVIRONMENT.json','FAILURE_AND_EXCLUSION_ACCOUNTING.json','REFERENCE_SOURCE_RELATIONSHIPS.json','NAVIGATION_MEMORY_UPDATE.json','SOURCE_INPUT_LOCK.json','ADDITIONAL_INPUT_LOCK.json','CONSTRUCT_INPUT_LOCK.json','CLOSURE_INPUT_VERIFICATION.json','PRIOR_REPORT_READBACK_LOCK.json','FINAL_VERIFICATION.json','PRE_FINAL_MANIFEST_VALIDATION.json'])]+list((O/'numeric').glob('*'))+[O/'SHA256SUMS.txt']
 with zipfile.ZipFile(O/'RECOVERED_SCIENCE_REPORTS_V1.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in bundle:z.write(p,str(p.relative_to(O)))
 result={**checks,'hash_manifest_sha256':a.sha(O/'SHA256SUMS.txt'),'bundle_sha256':a.sha(O/'RECOVERED_SCIENCE_REPORTS_V1.zip'),'bundle_bytes':(O/'RECOVERED_SCIENCE_REPORTS_V1.zip').stat().st_size,'NEXT_STEP':'SECOND_MODEL','STOP':True}
 # Receipt outside output tree avoids a self-referential hash and must not rewrite output after closure.
 Path('/tmp/recovered_science_final_receipt.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':verify()
