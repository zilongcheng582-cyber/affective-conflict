from e1e2_common import *
import argparse,time,traceback,gc
def main(exp):
 gate=json.loads((O/'00_gate'/f'{exp}_GATE_REPORT.json').read_text());assert gate['status']=='PASS'
 frozen=O/'01_protocol_freeze';protocol=json.loads((frozen/f'{exp}_FROZEN_PROTOCOL.json').read_text())
 for p,h in protocol['locked_files'].items():assert sha(p)==h,('LOCK_CHANGED',p)
 manifest=rows(frozen/f'{exp}_FULL_MANIFEST.csv');planned={t['trial_id'] for t in manifest};assert len(planned)==len(manifest)
 target=O/('02_e1_video' if exp=='E1' else '03_e2_consistent');attemptdir=target/'attempts';attemptdir.mkdir(exist_ok=True)
 fingerprint=sha(frozen/f'{exp}_FROZEN_PROTOCOL.json');lp=target/'RUN_LOCK.json'
 if lp.exists():assert json.loads(lp.read_text())['fingerprint']==fingerprint
 else:dump(lp,{'fingerprint':fingerprint,'manifest_sha256':sha(frozen/f'{exp}_FULL_MANIFEST.csv'),'created_unix':time.time()})
 attempts=collections.defaultdict(list)
 for p in sorted(attemptdir.glob('*.json')):
  r=json.loads(p.read_text());assert r['trial_id'] in planned and r['run_fingerprint']==fingerprint;attempts[r['trial_id']].append(r)
 for rs in attempts.values():
  rs.sort(key=lambda r:r['attempt']);assert [r['attempt'] for r in rs]==list(range(1,len(rs)+1)) and len(rs)<=2
 from src.emotiontalk.runtime import load
 from src.emotiontalk.phase1 import execution as uni
 from src.emotiontalk.phase2 import execution as joint,core
 torch,process,processor,model=load();parse=core.load_parser();prompt=core.read_json(core.PROMPT_PATH);counter=collections.Counter();start=time.time()
 cache={}
 for t in manifest:
  prev=attempts[t['trial_id']]
  if prev and (not prev[-1]['technical_failure'] or len(prev)==2):continue
  for key in ['audio','video','text']:
   p=t[key+'_path'];st=pathlib.Path(p).stat();info=(st.st_size,st.st_mtime_ns)
   if cache.get(p)!=info:assert sha(p)==t[key+'_sha256'];cache[p]=info
  for attempt in range(len(prev)+1,3):
   if attempt==2 and prev and not prev[-1]['technical_failure']:break
   for p,h in protocol['locked_files'].items():assert sha(p)==h,('LOCK_CHANGED',p)
   obj=inputs(t);began=time.time()
   if t['arm'].endswith('_ONLY'):r=uni.perform_arm(obj,t['arm'],prompt,processor,model,torch,process,parse,counter)
   else:r=joint.execute_pairwise_record(obj,int(t['execution_rank']),processor,model,torch,process,parse,prompt)
   r=core.jsonable(r);technical=not(r.get('generation_success') and r.get('parser_execution'))
   if t['arm'].endswith('_ONLY'):technical=technical or r.get('candidate_scoring_status')!='OK'
   r.update(trial_id=t['trial_id'],experiment=exp,condition=t['condition'],attempt=attempt,run_fingerprint=fingerprint,technical_failure=technical,wall_started_unix=began,wall_finished_unix=time.time(),input_identity={key:{'path':t[key+'_path'],'sha256':t[key+'_sha256']} for key in ['audio','video','text']})
   token=hashlib.sha256(t['trial_id'].encode()).hexdigest();path=attemptdir/f'{token}.attempt{attempt}.json';assert not path.exists();dump(path,r);attempts[t['trial_id']].append(r);prev=attempts[t['trial_id']]
   with (target/'trials.jsonl').open('a') as f:f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
   progress={'experiment':exp,'completed_cells':len(attempts),'planned_cells':len(manifest),'last_trial':t['trial_id'],'technical_failures_all_attempts':sum(x['technical_failure'] for rs in attempts.values() for x in rs),'elapsed_this_session_seconds':time.time()-start}
   dump(target/'PROGRESS.json',progress);print('FULL_CHECKPOINT',json.dumps(progress),flush=True)
   fatal=r.get('fatal_runner_implementation_failure') or r.get('failure_type') in ['FATAL_RUNNER_IMPLEMENTATION_FAILURE','PARSER_EXECUTION_FAILURE']
   if fatal:raise RuntimeError('FULL_BLOCKED_PROTOCOL_CHANGE_REQUIRED: '+str(r.get('failure_message')))
   if not technical:break
   gc.collect();torch.cuda.empty_cache()
   if r.get('failure_type') not in ['CUDA_OOM','GENERATION_FAILURE','GENERATION_OR_SCORING_FAILURE','OOM']:
    raise RuntimeError('UNEXPECTED_EXECUTION_FAILURE_PRESERVED: '+str(r.get('failure_type')))
 for p,h in protocol['locked_files'].items():assert sha(p)==h
 receipt={'status':'COMPLETE','experiment':exp,'logical_cells':len(manifest),'completed_cells':len(attempts),'successful_cells':sum(not v[-1]['technical_failure'] for v in attempts.values()),'technical_missing_cells':sum(v[-1]['technical_failure'] for v in attempts.values()),'technical_failure_attempts':sum(x['technical_failure'] for rs in attempts.values() for x in rs),'retries':sum(len(v)-1 for v in attempts.values()),'session_gpu_runtime_seconds':time.time()-start,'model_revision':protocol['model_revision'],'run_fingerprint':fingerprint,'pilot_executed':False}
 assert len(attempts)==len(manifest);dump(target/f'{exp}_EXECUTION_RECEIPT.json',receipt)
 print('FULL_COMPLETE',json.dumps(receipt),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('experiment',choices=['E1','E2']);a=p.parse_args();main(a.experiment)
