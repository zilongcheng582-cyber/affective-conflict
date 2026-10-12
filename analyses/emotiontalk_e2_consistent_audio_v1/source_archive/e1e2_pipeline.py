"""Authorized Gate -> freeze -> Full -> CPU -> independent closure supervisor."""
from e1e2_common import *
import subprocess,time,traceback,shutil
def run(label,args):
 with (O/'logs'/f'{label}.log').open('a') as f:
  result=subprocess.run([sys.executable,*args],stdout=f,stderr=subprocess.STDOUT,env=os.environ.copy())
 if result.returncode:raise RuntimeError(f'{label} exited {result.returncode}; see logs/{label}.log')
def freeze(exp):
 gate=json.loads((O/'00_gate'/f'{exp}_GATE_REPORT.json').read_text());assert gate['status']=='PASS'
 mf=O/'01_protocol_freeze'/f'{exp}_FULL_MANIFEST.csv';trials=rows(mf);assert len(trials)==(2190 if exp=='E1' else 3375)
 for s in rows(O/'00_gate/SOURCE_POPULATION_WITH_CLUSTERS.csv'):
  for key in ['audio','video','text']:assert sha(s[key+'_path'])==s[key+'_sha256']
 sources=json.loads((O/'00_gate/00_SOURCE_LOCK.json').read_text())['sources']
 C=P.parent/'closure_v1/github_evidence'
 for name in ['SCIENTIFIC_CLOSURE_FINAL_REPORT.md','ERI1_PRIMARY_RESULTS_V1.csv','ERI1_FULL_OUTCOME_ACCOUNTING_V1.csv','ERI1_ELIGIBILITY_CHARACTERISTICS_V1.csv','DIALOGUE_CLUSTER_MAP_V1.csv','ERI1_PROVENANCE_V1.json']:
  path=C/name;sources[str(path)]={'SHA256':sha(path),'bytes':path.stat().st_size}
 original=rows(C/'ERI1_PRIMARY_RESULTS_V1.csv');historical={r['endpoint']:r for r in original};assert abs(float(historical['PRIMARY_dSIDE_A_SNR00_minus_RECODE']['estimate'])+.1095890410958904)<1e-12
 for p,x in sources.items():assert sha(p)==x['SHA256']
 assert shutil.disk_usage(O).free>20*1024**3
 gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used','--format=csv,noheader'],text=True).strip();assert int(gpu.split(',')[-1].strip().split()[0])<1000,('OTHER_GPU_JOB',gpu)
 files=[mf,O/'00_gate/SOURCE_POPULATION_WITH_CLUSTERS.csv',O/'00_gate'/f'{exp}_MEDIA_BINDING.csv',P/'configs/mainline/b3_runtime.json',P/'configs/mainline/emotiontalk_controlled_prompt_v1.json',P/'protocols/emotiontalk/EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json',P/'src/emotiontalk/reliability_v1/audio.py']+list((O/'code').glob('*.py'))
 files.extend(P/p for p in ['src/emotiontalk/phase1/execution.py','src/emotiontalk/phase2/execution.py','src/emotiontalk/phase2/core.py','src/emotiontalk/runtime.py','src/common/benchmarks/emotiontalk_controlled_parser_v1.py'])
 protocol={'experiment':exp,'status':'PROSPECTIVE_FROZEN_BEFORE_ANY_GPU_TRIAL','frozen_unix':time.time(),'model_revision':'ae9e1690543ffd5c0221dc27f79834d0294cba00','source_code_commit':'34aa1b0340d906e5d625db7cb4a3def9199fa06e','model_identity':json.loads((P/'frozen/identity/model.json').read_text()),'processor_identity':json.loads((P/'frozen/identity/processor.json').read_text()),'gpu':gpu,'runtime_config':json.loads((P/'configs/mainline/b3_runtime.json').read_text()),'source_files':sources,'locked_files':{str(p):sha(p) for p in files},'source_population':'EXACT_FROZEN_ERI1_146' if exp=='E1' else 'EXACT_FROZEN_PHASE2_AV_CONSISTENT_225','pre_intervention_qualification':'HISTORICAL_DUALREADABLE_AV','joint_cells':1460 if exp=='E1' else 2250,'unimodal_cells':730 if exp=='E1' else 1125,'historical_cells_reused':0,'reuse_decision':'No historical generation reused without a complete per-cell current-interface input identity receipt. All current matched controls measured fresh.','execution_order_seed':2026101101 if exp=='E1' else 2026101102,'condition_order':'PCG64_PERMUTATION_OF_ALL_LOGICAL_CELLS','decoding':{'do_sample':False,'max_new_tokens':16,'use_audio_in_video':False,'return_audio':False,'audio_provided_once':True},'candidate_order':'SOURCE_UID_BOUND_PIPE_SEQUENCE_UNCHANGED','primary':'P(SIDE_V|V_BLUR_HIGH)-P(SIDE_V|V_RECODE)' if exp=='E1' else 'P(pred==shared|A_SNR00)-P(pred==shared|A_RECODE)','estimand':'ALL_PRESELECTED_ITEMS_EQUAL_WEIGHT_TWO_ORDERS_AVERAGED','primary_expected_direction':'NEGATIVE','technical_missing_primary_ITT':'HIGH=SUCCESS_BASELINE=FAILURE_CONSERVATIVE_AGAINST_NEGATIVE_H1','parse_fail_primary_success':False,'missing_bounds':'ALL_HIGH_FAILURE_BASE_SUCCESS_TO_ALL_HIGH_SUCCESS_BASE_FAILURE','bootstrap':{'items':10000,'dialogue_clusters':10000,'item_weighted_cluster_ratio':True,'quantile':'numpy_linear','seed':2026101110+(0 if exp=='E1' else 100)},'test':{'type':'PAIRED_ITEM_TWO_SIDED_SIGNFLIP','draws':100000,'plus_one_correction':True,'ties_tolerance':1e-14,'seed_offset':2},'secondary_family':'ONE_HOLM_FAMILY: other outcomes, clean-recode, order interaction, low/medium contrasts, ordinal slope, unimodal match, legitimate entropy','dose_response':'WITHIN_ITEM_EQUAL_STEP_ORDINAL_SLOPE_NOT_PHYSICALLY_EQUAL_STRENGTH','primary_alpha':.05,'ruling_rule':'SUPPORTED iff negative primary, item CI upper<0, p<.05, no unresolved missing effect bounds and independent verification PASS; otherwise NOT_SUPPORTED or INCONCLUSIVE; no p-value-dependent resampling','joint_claim_FWER':{'E1_plus_ERI1':'HOLM_TWO_PRIMARY_P_VALUES_AT_0.05_WITH_PRESPECIFIED_NEGATIVE_DIRECTIONS','E1_E2_independent_questions':'Separate primary questions; any combined confirmatory statement must pass Holm across the two primaries. E2 is not modality competition.'},'technical_retry':{'max_identical_retries':1,'allowed':'CUDA cleanup and one identical execution for OOM/transient generation failure','forbidden':'precision/media sampling/prompt/model/ontology/selection changes','fatal_code_or_identity_failure':'STOP_BLOCKED_PRESERVE_ATTEMPT'},'checkpoint':'ATOMIC_PER_TRIAL_ATTEMPT_FILES_WITH_FSYNC_JSONL_LEDGER','resume':'EXACT_RUN_LOCK_MATCH_SKIP_SUCCESS_NO_DOUBLE_COUNT','independent_tolerance':1e-12,'same_input_CPU_repeats':2,'baseline_strata':'ALL_SAME,A_EQ_V_NE_T,label,dialogue; CLEAN/RECODE correctness descriptive only; never primary selection','cross_population_label':'EXPLORATORY_CROSS_POPULATION_COMPARISON','scientific_boundaries':['No causal entropy mediation','No audio/video physical dose equivalence','No randomized conflict-by-noise interaction across distinct populations','E2 cannot distinguish audio from video reliance','OTHER and PARSE_FAIL retained distinct from technical missing'],'pilot_executed':False}
 dest=O/'01_protocol_freeze'/f'{exp}_FROZEN_PROTOCOL.json';assert not dest.exists();dump(dest,protocol)
 dump(O/'00_gate/GATE_SOURCE_LOCK.json',{'files':sources,'model_revision':protocol['model_revision'],'GPU_performed_before_freeze':False})
 gatepaths=list((O/'00_gate').glob('*.json'))+list((O/'00_gate').glob('*.csv'))+[mf,dest]
 (O/'00_gate/GATE_SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(O).as_posix()}\n' for p in sorted(gatepaths)))
 return protocol
def closure(states):
 source=json.loads((O/'00_gate/00_SOURCE_LOCK.json').read_text())['sources'];unchanged=all(sha(p)==x['SHA256'] for p,x in source.items());assert unchanged
 results={};valid={};counts={'GPU_INFERENCE_COMPLETED':0,'TECHNICAL_FAILURES':0}
 for exp in ['E1','E2']:
  ap=O/'04_cpu_analysis'/f'{exp}_PRIMARY_ANALYSIS.json';vp=O/'05_independent_verification'/f'{exp}_VERIFICATION_RECEIPT.json';runpath=O/('02_e1_video' if exp=='E1' else '03_e2_consistent');receipt=runpath/f'{exp}_EXECUTION_RECEIPT.json'
  if ap.exists():results[exp]=json.loads(ap.read_text())
  if vp.exists():valid[exp]=json.loads(vp.read_text())['status']
  if receipt.exists():r=json.loads(receipt.read_text());counts['GPU_INFERENCE_COMPLETED']+=r['successful_cells'];counts['TECHNICAL_FAILURES']+=r['technical_failure_attempts']
  else:
   rs=[json.loads(p.read_text()) for p in (runpath/'attempts').glob('*.json')];final={r['trial_id']:r for r in sorted(rs,key=lambda r:r['attempt'])};counts['GPU_INFERENCE_COMPLETED']+=sum(not r['technical_failure'] for r in final.values());counts['TECHNICAL_FAILURES']+=sum(r['technical_failure'] for r in rs)
  if states[exp]['gate']=='FAIL':
   (runpath/f'{exp}_SCIENTIFIC_REPORT.md').write_text('# Experiment blocked before Full\n\nCPU media/environment gate FAIL. No inference, no scientific effect estimate. See 00_gate/'+exp+'_GATE_REPORT.json. This is a technical pre-execution block, not a negative scientific outcome.\n')
 summary={**states,**counts,'INDEPENDENT_REPLAY':'PASS' if all(valid.get(exp)=='PASS' for exp in results) and results else 'PARTIAL','FROZEN_ERI1_UNCHANGED':'YES','PILOT_EXECUTED':'NO','scientific_closure':'COMPLETE_WITH_E1_GATE_BLOCK' if valid.get('E2')=='PASS' and states['E1']['gate']=='FAIL' else ('COMPLETE' if len(valid)==2 else 'BLOCKED'),'results':results}
 out=O/'06_scientific_closure';dump(out/'E1_E2_FULL_RUN_PROVENANCE.json',summary)
 text='# E1/E2 scientific closure\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\nE1 cannot establish video response or symmetry when Gate FAIL. E2 answers only shared-label retention in the frozen consistent population. No causal entropy mediation, no claim that physical intensities are equivalent, no randomized cross-population comparison. ERI1 frozen SIDE_A -10.9589 pp, SIDE_V +5.8219 pp, OTHER +5.1370 pp remain unchanged. Negative results and positive results use the same rule. No additional model, dataset, optimization or GitHub publication initiated.\n'
 (out/'E1_E2_SCIENTIFIC_CLOSURE_REPORT.md').write_text(text)
 (out/'E1_E2_CROSS_EXPERIMENT_COMPARISON.md').write_text('# Cross-experiment comparison\n\nEXPLORATORY_CROSS_POPULATION_COMPARISON.\n\n'+text)
 (out/'E1_E2_CLAIM_EVIDENCE_MATRIX.md').write_text('# Claim–Evidence Matrix\n\n|Claim|Status|Evidence|\n|---|---|---|\n|E1 video reliability response|'+states['E1']['scientific_ruling']+'|E1 gate/primary|\n|E2 shared-label degradation|'+states['E2']['scientific_ruling']+'|E2 primary, transitions, manipulation check|\n|Directional audio/video symmetry|NOT_IDENTIFIED if E1 blocked; otherwise Holm-defined direction comparison only|Frozen ERI1 + E1|\n|Entropy causal mediation|NOT_ESTABLISHED|No mediator randomization|\n|General versus conflict-specific impairment|NOT_FULLY_IDENTIFIED|E2 uses a distinct fixed population|\n|Frozen ERI1 revision|NONE|Original source SHA256 unchanged|\n')
 checks=[]
 for exp in valid:checks+=rows(O/'05_independent_verification'/f'{exp}_INDEPENDENT_RECOMPUTATION.csv')
 if checks:table(out/'E1_E2_INDEPENDENT_RECOMPUTATION.csv',checks)
 for p in (O/'04_cpu_analysis').glob('*'):
  if p.is_file() and p.name.startswith(('E1_','E2_')):shutil.copyfile(p,O/('02_e1_video' if p.name.startswith('E1_') else '03_e2_consistent')/p.name)
 (O/'docs/PROJECT_STATE.md').write_text(text);(O/'docs/FILE_MAP.md').write_text('# E1/E2 output map\n\n00_gate: actual source/media/environment checks; 01_protocol_freeze: exact manifest and pre-GPU protocol; 02_e1_video and 03_e2_consistent: attempts, outputs and reports; 04_cpu_analysis: primary CPU and repeat; 05_independent_verification: separate implementation; 06_scientific_closure: bounded integrated conclusions. Code and replay via code/e1e2_pipeline.py. Restricted media, raw answers and complete logs stay local.\n');(O/'docs/DECISIONS.md').write_text('# Prospective decisions\n\nAll samples recovered from frozen pre-intervention identities. No Pilot. E1 Gate FAIL stops E1. E2 independent. Technical missing negative-H1-conservative, paired item inference and official dialogue cluster robustness, pre-GPU secondary Holm family. No post-treatment primary selection. No historical writes or GitHub publication.\n')
 paths=[p for p in O.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt' and '.transfer' not in p.name and 'cache' not in p.parts]
 (O/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(O).as_posix()}\n' for p in sorted(paths)))
 print('SCIENTIFIC_CLOSURE',json.dumps({k:v for k,v in summary.items() if k!='results'}),flush=True)
def main():
 states={exp:{'gate':'PENDING','full':'NOT_STARTED','scientific_ruling':'BLOCKED'} for exp in ['E1','E2']}
 # Wait for CPU gates only. No model is loaded before every relevant gate is finalized.
 while not all((O/'00_gate'/f'{exp}_GATE_REPORT.json').exists() for exp in ['E1','E2']):time.sleep(20)
 for exp in ['E1','E2']:states[exp]['gate']=json.loads((O/'00_gate'/f'{exp}_GATE_REPORT.json').read_text())['status']
 dump(O/'00_gate/00_GATE_RESULTS.json',{exp:json.loads((O/'00_gate'/f'{exp}_GATE_REPORT.json').read_text()) for exp in ['E1','E2']})
 (O/'00_gate/00_GATE_SUMMARY.md').write_text('# Pre-GPU Gate result\n\n'+json.dumps(states,indent=2)+'\n')
 table(O/'00_gate/00_FULL_EXECUTION_PLAN.csv',[{'experiment':exp,'items':146 if exp=='E1' else 225,'joint_trials':1460 if exp=='E1' else 2250,'unimodal_trials':730 if exp=='E1' else 1125,'gate':states[exp]['gate'],'authorized_execution':states[exp]['gate']=='PASS'} for exp in ['E1','E2']])
 for exp in ['E1','E2']:
  states[exp]['gate']=json.loads((O/'00_gate'/f'{exp}_GATE_REPORT.json').read_text())['status']
  if states[exp]['gate']!='PASS':states[exp]['full']='BLOCKED';continue
  try:
   freeze(exp);states[exp]['full']='RUNNING';dump(O/'PIPELINE_STATUS.json',states)
   run(exp+'_full',[str(O/'code/e1e2_full_runner.py'),exp]);states[exp]['full']='COMPLETE'
   run(exp+'_analysis',[str(O/'code/e1e2_analysis.py'),exp,str(O/'04_cpu_analysis')]);run(exp+'_analysis_repeat',[str(O/'code/e1e2_analysis.py'),exp,str(O/'04_cpu_analysis/repeat')]);run(exp+'_independent',[str(O/'code/e1e2_verify.py'),exp]);states[exp]['scientific_ruling']=json.loads((O/'04_cpu_analysis'/f'{exp}_PRIMARY_ANALYSIS.json').read_text())['scientific_ruling']
  except Exception as e:
   if states[exp]['full']!='COMPLETE':states[exp]['full']='PARTIAL' if list((O/('02_e1_video' if exp=='E1' else '03_e2_consistent')/'attempts').glob('*.json')) else 'BLOCKED'
   states[exp]['error']=repr(e);states[exp]['traceback']=traceback.format_exc();states[exp]['scientific_ruling']='BLOCKED'
  dump(O/'PIPELINE_STATUS.json',states)
 closure(states)
if __name__=='__main__':main()
