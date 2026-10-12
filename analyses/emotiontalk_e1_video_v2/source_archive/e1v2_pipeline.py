"""CPU gate -> immutable freeze -> independent technical Pilot -> Full -> CPU closure."""
from e1v2_cpu_gate import ROOT,OLD,REPO,R,sha,dump,rows,table
import os,sys,time,json,subprocess,pathlib,traceback,shutil,collections,hashlib
AUDIT=R/'audit/EMOTIONTALK_CONTROLLED_V1'
def state(stage,**kwargs):
 dump(ROOT/'STATUS.json',{'stage':stage,**kwargs});(ROOT/'docs/PROJECT_STATE.md').write_text('# E1 V2 current state\n\n'+json.dumps({'stage':stage,**kwargs},indent=2)+'\n\nHistorical ERI1, E2, Phase 1/2 remain read-only. No GitHub publication.\n');print('PIPELINE_STATE',stage,flush=True)
def run(label,args):
 with open(ROOT/'logs'/(label+'.log'),'ab') as f:q=subprocess.run([sys.executable,'-B',*map(str,args)],cwd=ROOT/'code',stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
 if q.returncode:raise RuntimeError(f'{label} returned {q.returncode}; see logs/{label}.log')
def freeze():
 assert json.loads((ROOT/'01_design/CPU_MEDIA_GATE.json').read_text())['status']=='PASS'
 assert json.loads((ROOT/'code/CPU_STATISTIC_CONTRACT_TEST.json').read_text())['status']=='PASS'
 from src.cross_regime.target_scoring.verify_runtime import verify
 from src.cross_regime.target_scoring.inputs import FrozenInputs
 env=verify(FrozenInputs());assert env['GPU_EXECUTION_ALLOWED']=='YES';dump(ROOT/'01_design/FROZEN_RUNTIME_VERIFY.json',env)
 assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()=='34aa1b0340d906e5d625db7cb4a3def9199fa06e'
 assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True)
 assert shutil.disk_usage(ROOT).free>20*1024**3
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used','--format=csv,noheader'],text=True).strip();assert int(gpu.split(',')[-1].strip().split()[0])<1000,('GPU_OTHER_JOB',gpu)
 spec=json.loads((ROOT/'01_design/DESIGN_SPEC_PRE_MEDIA.json').read_text());sources=json.loads((OLD/'00_gate/00_SOURCE_LOCK.json').read_text())['sources']
 e2cfg=json.loads((OLD/'01_protocol_freeze/E2_FROZEN_PROTOCOL.json').read_text());sources.update(e2cfg['source_files'])
 additional=[OLD/'01_protocol_freeze/E2_FROZEN_PROTOCOL.json',OLD/'03_e2_consistent/trials.jsonl',OLD/'03_e2_consistent/E2_EXECUTION_RECEIPT.json',OLD/'04_cpu_analysis/E2_PRIMARY_ANALYSIS.json',OLD/'05_independent_verification/E2_VERIFICATION_RECEIPT.json',OLD/'06_scientific_closure/E1_E2_SCIENTIFIC_CLOSURE_REPORT.md',AUDIT/'phase1_competence_full_v1_2/emotiontalk_phase1_competence_full_v1_2.jsonl',AUDIT/'phase1_competence_full_v1_2/EMOTIONTALK_PHASE1_COMPETENCE_FULL_V1_2_PROVENANCE.json',AUDIT/'phase2_pairwise_full_v1_attempt_002/emotiontalk_phase2_pairwise_full_v1_attempt_002.jsonl',AUDIT/'phase2_pairwise_full_v1_attempt_002/EMOTIONTALK_PHASE2_PAIRWISE_FULL_V1_ATTEMPT_002_PROVENANCE.json']
 for p in additional:sources[str(p)]={'SHA256':sha(p),'bytes':p.stat().st_size}
 for p,j in sources.items():assert sha(p)==j['SHA256']
 ids=spec['pilot']['IDs'];historical={}
 # Only exact UID-bound raw evidence from verified historical sources is used.
 for path in [additional[-4],additional[-2]]:
  for line in open(path):
   r=json.loads(line)
   if r['utterance_id'] in ids and r['arm'] in ['A_ONLY','V_ONLY','A_THEN_V','V_THEN_A'] and (r.get('pair','AV')=='AV'):
    k=(r['utterance_id'],r['arm']);assert k not in historical;historical[k]={'utterance_id':r['utterance_id'],'arm':r['arm'],'source_path':str(path),'source_sha256':sources[str(path)]['SHA256'],'raw_generation':r['raw_generation'],'parsed_label':r['parsed_label'],'parser_status':r['parser_status'],'candidate_sequence':r['candidate_sequence'],'generation_config':r.get('generation_config'),'input_refs':{k:r.get(k) for k in ['audio_path','silent_video_path','evidence_1_reference','evidence_2_reference']}}
 assert len(historical)==24
 dump(ROOT/'01_design/PILOT_HISTORICAL_CLEAN_REFERENCES.json',list(historical.values()))
 files=list((ROOT/'code').glob('*.py'))+[ROOT/'code/CPU_STATISTIC_CONTRACT_TEST.json']+list((ROOT/'02_media/receipts').glob('*.json'))+[ROOT/'01_design'/x for x in ['DESIGN_SPEC_PRE_MEDIA.json','SOURCE_POPULATION.csv','FULL_MANIFEST.csv','MEDIA_BINDING.csv','PROCESSOR_CODE_CONTRACT.json','CPU_MEDIA_GATE.json','PILOT_HISTORICAL_CLEAN_REFERENCES.json','FROZEN_RUNTIME_VERIFY.json']]
 files.extend(ROOT/x for x in ['tools/ffmpeg','tools/FFMPEG_TOOL_RECEIPT.json','tools/FFMPEG_VERSION.txt','tools/MP4_MUXER_HELP.txt','00_recovery/EXACT_CLOCK_TEST.json'])
 files.extend(REPO/x for x in ['src/emotiontalk/phase1/execution.py','src/emotiontalk/phase2/execution.py','src/emotiontalk/phase2/core.py','src/emotiontalk/runtime.py','src/common/benchmarks/emotiontalk_controlled_parser_v1.py','configs/mainline/b3_runtime.json','configs/mainline/emotiontalk_controlled_prompt_v1.json','protocols/emotiontalk/EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json'])
 spec.update(status='FROZEN_BEFORE_ANY_V2_GPU_CALL',frozen_unix=time.time(),source_code_commit='34aa1b0340d906e5d625db7cb4a3def9199fa06e',model_revision='ae9e1690543ffd5c0221dc27f79834d0294cba00',model_identity=json.loads((REPO/'frozen/identity/model.json').read_text()),processor_identity=json.loads((REPO/'frozen/identity/processor.json').read_text()),GPU=gpu,pilot_ids=ids,locked_files={str(p):sha(p) for p in files},historical_source_files=sources,official_metadata=json.loads((OLD/'00_gate/OFFICIAL_METADATA_SCHEMA.json').read_text()),decoding={'do_sample':False,'max_new_tokens':16,'dtype':'auto (frozen bf16 runtime)','use_audio_in_video':False,'return_audio':False},technical_retry={'max_identical_retries':1,'only_transient_generation_or_OOM':True,'hard_scoring_parser_identity_or_code_error':'STOP_PRESERVE','PARSE_FAIL_OR_OTHER_NOT_RETRIED':True},statistic_definition={'base_seed':2026101103,'endpoint_seed':'base+100+10*fixed_endpoint_index; independent cluster seed+1; signflip seed+2','bootstrap':'numpy linear percentile, 10000 draws; item equal-weight dialogue ratio bootstrap','signflip':'100000 two-sided, plus one correction, equality tolerance 1e-14','primary_alpha':.05,'independent_tolerance':1e-12,'incomplete_ITT':'report worst/best category bounds, complete-case sensitivity; INCONCLUSIVE if primary contrast contains missing generation','scoring_failure_does_not_delete_valid_generation':True})
 target=ROOT/'01_design/RUN_PROTOCOL.json';assert not target.exists();dump(target,spec)
 (ROOT/'01_design/SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in sorted((ROOT/'01_design').glob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'))
 return spec
def pilot_acceptance():
 cfg=json.loads((ROOT/'01_design/RUN_PROTOCOL.json').read_text());ids=cfg['pilot_ids'];mf=[r for r in rows(ROOT/'01_design/FULL_MANIFEST.csv') if r['utterance_id'] in ids];attempts=[json.loads(p.read_text()) for p in (ROOT/'03_pilot/attempts').glob('*.json')];assert len(attempts)==96 and len({r['trial_id'] for r in attempts})==96 and {r['trial_id'] for r in attempts}=={r['trial_id'] for r in mf}
 final={r['trial_id']:r for r in attempts};history={(r['utterance_id'],r['arm']):r for r in json.loads((ROOT/'01_design/PILOT_HISTORICAL_CLEAN_REFERENCES.json').read_text())};comparisons=[]
 for t in mf:
  r=final[t['trial_id']];assert not r['technical_failure'] and r['candidate_scoring_status']=='OK' and r['run_fingerprint']==sha(ROOT/'01_design/RUN_PROTOCOL.json')
  if t['condition']=='CLEAN':
   h=history[t['utterance_id'],t['arm']];rawmatch=r['raw_generation']==h['raw_generation'];labelmatch=r['parsed_label']==h['parsed_label'] and r['parser_status']==h['parser_status'];seqmatch=t['candidate_sequence']==h['candidate_sequence'];comparisons.append({'utterance_id':t['utterance_id'],'arm':t['arm'],'raw_match':rawmatch,'label_parser_match':labelmatch,'sequence_match':seqmatch,'source_path':h['source_path'],'source_sha256':h['source_sha256']})
 table(ROOT/'03_pilot/CLEAN_HISTORICAL_REPRODUCTION.csv',comparisons)
 passed=all(r['raw_match'] and r['label_parser_match'] and r['sequence_match'] for r in comparisons)
 receipt={'status':'PASS' if passed else 'FAIL','fixed_pilot_ids':ids,'unique_slots':96,'all_generation_parser_candidate_scores':'PASS','actual_consumed_visual_frames':'PASS','checkpoint_resume_no_duplicates':'PASS','clean_historical_comparisons':len(comparisons),'clean_exact_reproduction':'PASS' if passed else 'FAIL','blur_strength_selected_using_outcomes':False,'pilot_pooled_with_full':False,'failure_policy':'any hard failure prevents Full'}
 dump(ROOT/'03_pilot/PILOT_ACCEPTANCE.json',receipt);assert passed,('PILOT_CLEAN_REPRODUCTION_MISMATCH',comparisons)
def closure():
 cfg=json.loads((ROOT/'01_design/RUN_PROTOCOL.json').read_text());verification=json.loads((ROOT/'06_verification/VERIFICATION_RECEIPT.json').read_text());assert verification['status']=='PASS'
 results=json.loads((ROOT/'05_analysis/SCIENTIFIC_RESULTS.json').read_text());e2=json.loads((OLD/'04_cpu_analysis/E2_PRIMARY_ANALYSIS.json').read_text());execution=json.loads((ROOT/'04_full/EXECUTION_RECEIPT.json').read_text());assert execution['completed_slots']==2336
 for p,rec in cfg['historical_source_files'].items():assert sha(p)==rec['SHA256']
 sessions=[json.loads(p.read_text()) for p in (ROOT/'04_full').glob('EXECUTION_SESSION_*.json')];raw=[json.loads(p.read_text()) for p in (ROOT/'04_full/attempts').glob('*.json')];resource={'gpu':cfg['GPU'],'formal_active_model_seconds':sum(x['session_active_model_seconds'] for x in sessions),'formal_generation_calls':sum(bool(x.get('generation_attempted')) for x in raw),'formal_candidate_scoring_forward_calls':sum(x.get('candidate_scoring_forward_calls',0) for x in raw),'pilot_separately_accounted':True,'initial_model_loading_and_release_verification_excluded_from_active_model_seconds':True}
 dump(ROOT/'07_closure/RESOURCE_ACCOUNTING.json',resource)
 comparison={'role':'EXPLORATORY_PARALLEL_COMPARISON_NOT_SYMMETRY_TEST','ERI1_frozen':{'items':146,'SIDE_A_SNR00_minus_RECODE':-.1095890410958904,'SIDE_V':.05821917808219178,'OTHER':.05136986301369863,'source':str(REPO.parent/'closure_v1/github_evidence/ERI1_PRIMARY_RESULTS_V1.csv')},'E1_V2':results['primary'],'E2_frozen':e2['primary'],'boundaries':['E1 and ERI1 share frozen conflict population but interventions are not calibrated equivalent','E2 uses 225 distinct consistent items','No percentage-difference proof of symmetry or asymmetry','No entropy causal mediation','No response-guided sigma change']}
 dump(ROOT/'07_closure/CROSS_EXPERIMENT_COMPARISON.json',comparison)
 text='# E1 video degradation V2 scientific closure\n\nFULL_COMPLETE; INDEPENDENT_CPU_REPLAY_PASS. 2336 formal slots; all 146 frozen items retained.\n\n'+json.dumps(results,indent=2)+'\n\n## Comparison and limits\n\n'+json.dumps(comparison,indent=2)+'\n\nHistorical results unchanged. Negative and non-significant findings use the same reporting standard. No further model, intervention or GitHub merge initiated.\n'
 (ROOT/'07_closure/SCIENTIFIC_CLOSURE_REPORT.md').write_text(text);(ROOT/'07_closure/CLAIM_EVIDENCE_MATRIX.md').write_text('# E1 V2 claim evidence\n\n| Claim | Evidence | Boundary |\n|---|---|---|\n| Video degradation changes choice | three frozen primary endpoints and Holm | fixed 146-item conflict ITT |\n| V_ONLY readability changes | correctness and normalized entropy | manipulation measure, no mediation |\n| Presentation order moderates response | three Holm-adjusted interactions | report adjusted evidence |\n| Audio/video symmetry | not identified by percentage differences | doses not calibrated equivalent |\n| Conflict specificity | not identified by E1/E2 population contrast | E2 population distinct |\n| Frozen ERI1/E2 revision | none | source hashes unchanged |\n')
 dump(ROOT/'07_closure/RUN_PROVENANCE.json',{'source_code_commit':cfg['source_code_commit'],'model_revision':cfg['model_revision'],'run_fingerprint':sha(ROOT/'01_design/RUN_PROTOCOL.json'),'manifest_sha256':sha(ROOT/'01_design/FULL_MANIFEST.csv'),'pilot':json.loads((ROOT/'03_pilot/PILOT_ACCEPTANCE.json').read_text()),'execution':execution,'verification':verification,'historical_artifacts_unchanged':True,'restricted_media_and_raw_outputs_local_only':True})
 paths=[p for folder in ['01_design','03_pilot','04_full','05_analysis','06_verification','07_closure','code'] for p in (ROOT/folder).rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt']
 (ROOT/'07_closure/SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT).as_posix()}\n' for p in sorted(paths)))
 state('SCIENTIFIC_CLOSURE_COMPLETE_STOP',formal_slots=2336,fixed_ITT_items=146,independent_replay='PASS',historical_artifacts_unchanged=True)
 (ROOT/'docs/FILE_MAP.md').write_text('00_recovery: original failure and pre-freeze engineering attempts; 01_design: immutable protocol and media manifest; 02_media: V2 derived videos and physical receipts; 03_pilot: separate 96-slot technical Pilot; 04_full: 2336-slot formal immutable attempts; 05_analysis: frozen CPU tables and repeat; 06_verification: independent reconstruction; 07_closure: bounded science, comparison, provenance, resources and SHA256SUMS; code: frozen execution/replay. No raw data publication.\n')
def main():
 try:
  state('WAIT_CPU_MEDIA_GATE',pilot='NOT_STARTED',full='NOT_STARTED')
  while not (ROOT/'01_design/CPU_MEDIA_GATE.json').exists():time.sleep(20)
  assert json.loads((ROOT/'01_design/CPU_MEDIA_GATE.json').read_text())['status']=='PASS'
  state('DESIGN_AND_RUNTIME_FREEZE');freeze();state('TECHNICAL_PILOT_RUNNING')
  runner=ROOT/'code/e1v2_runner.py';run('PILOT_FIRST16',[runner,'--phase','pilot','--max-slots','16']);run('PILOT_RESUME',[runner,'--phase','pilot'])
  before={p.name:sha(p) for p in (ROOT/'03_pilot/attempts').glob('*.json')};run('PILOT_NOOP_RESUME',[runner,'--phase','pilot']);assert before=={p.name:sha(p) for p in (ROOT/'03_pilot/attempts').glob('*.json')};pilot_acceptance()
  state('FULL_RUNNING',pilot='PASS',planned_slots=2336);run('FULL',[runner,'--phase','full'])
  state('CPU_ANALYSIS_RUNNING');run('CPU_ANALYSIS',[ROOT/'code/e1v2_analysis.py',ROOT/'05_analysis']);run('CPU_ANALYSIS_REPEAT',[ROOT/'code/e1v2_analysis.py',ROOT/'05_analysis/repeat']);state('INDEPENDENT_CPU_VERIFICATION_RUNNING');run('INDEPENDENT_CPU_VERIFY',[ROOT/'code/e1v2_verify.py']);closure()
 except Exception as e:
  state('BLOCKED_PRESERVE_ALL_EVIDENCE',error=repr(e),traceback=traceback.format_exc(),full_not_authorized_unless_pilot_pass=True);raise
if __name__=='__main__':main()
