"""Frozen generation kernels, additional frozen candidate scorer, append-only attempts."""
from e1v2_cpu_gate import ROOT,OLD,REPO,R,sha,dump,rows
from e1e2_common import inputs
import collections,argparse,time,gc,json,hashlib,os,traceback,math
def check_lock(cfg):
 for p,h in cfg['locked_files'].items():assert sha(p)==h,('LOCK_CHANGED',p)
def load_attempts(target,mf,fingerprint):
 by=collections.defaultdict(list);planned={t['trial_id'] for t in mf}
 for p in (target/'attempts').glob('*.json'):
  r=json.loads(p.read_text());assert r['trial_id'] in planned and r['run_fingerprint']==fingerprint;by[r['trial_id']].append(r)
 for rs in by.values():
  rs.sort(key=lambda r:r['attempt']);assert [r['attempt'] for r in rs]==list(range(1,len(rs)+1)) and len(rs)<=2
 # Repair only missing journal entries from immutable per-attempt records; reject duplicates.
 journal=target/'trials.jsonl';seen=set()
 if journal.exists():
  for line in journal.read_text().splitlines():
   r=json.loads(line);key=(r['trial_id'],r['attempt']);assert key not in seen;seen.add(key);assert r in by[r['trial_id']]
 with journal.open('a') as f:
  for rs in by.values():
   for r in rs:
    key=(r['trial_id'],r['attempt'])
    if key not in seen:f.write(json.dumps(r,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno());seen.add(key)
 return by
def main(phase,max_slots=None):
 cfg=json.loads((ROOT/'01_design/RUN_PROTOCOL.json').read_text());check_lock(cfg);fingerprint=sha(ROOT/'01_design/RUN_PROTOCOL.json')
 mf=rows(ROOT/'01_design/FULL_MANIFEST.csv')
 if phase=='pilot':mf=[t for t in mf if t['utterance_id'] in cfg['pilot_ids']]
 assert len(mf)==(96 if phase=='pilot' else 2336)
 target=ROOT/('03_pilot' if phase=='pilot' else '04_full');(target/'attempts').mkdir(exist_ok=True)
 lp=target/'RUN_LOCK.json';lock={'fingerprint':fingerprint,'phase':phase,'manifest_sha256':sha(ROOT/'01_design/FULL_MANIFEST.csv'),'planned_slots':len(mf)}
 if lp.exists():assert json.loads(lp.read_text())==lock
 else:dump(lp,lock)
 by=load_attempts(target,mf,fingerprint)
 pending=[t for t in mf if not by.get(t['trial_id']) or by[t['trial_id']][-1]['technical_failure'] and len(by[t['trial_id']])<2]
 if not pending:
  print('RESUME_NOOP_LOCK_PASS',phase,flush=True);return
 if phase=='full':assert json.loads((ROOT/'03_pilot/PILOT_ACCEPTANCE.json').read_text())['status']=='PASS'
 from src.emotiontalk.runtime import load
 from src.emotiontalk.phase1 import execution as uni
 from src.emotiontalk.phase2 import execution as joint,core
 torch,process,processor,model=load();parse=core.load_parser();prompt=core.read_json(core.PROMPT_PATH);counter=collections.Counter();start=time.time();did=0
 for t in pending:
  if max_slots is not None and did>=max_slots:break
  check_lock(cfg)
  for k in ['audio','video','text']:assert sha(t[k+'_path'])==t[k+'_sha256']
  for attempt in range(len(by[t['trial_id']])+1,3):
   obj=inputs(t);began=time.time();actual_visual=[]
   def checked_process(messages,**kwargs):
    result=process(messages,**kwargs)
    if t['arm']=='A_ONLY':assert not result[2]
    else:
     tensors=[]
     def walk(x):
      if torch.is_tensor(x) and x.ndim==4:tensors.append(x)
      elif isinstance(x,(list,tuple)):
       for y in x:walk(y)
      elif isinstance(x,dict):
       for y in x.values():walk(y)
     walk(result[2]);assert len(tensors)==1,('UNEXPECTED_VISUAL_TENSOR_COUNT',len(tensors))
     v=tensors[0];identity={'shape':list(v.shape),'sha256':hashlib.sha256(v.cpu().numpy().tobytes()).hexdigest()}
     physical=json.loads((ROOT/'02_media/receipts'/(t['utterance_id']+'.json')).read_text());expected=next(x for x in physical['physical'] if x['condition']==t['condition']);assert identity=={'shape':expected['model_frame_shape'],'sha256':expected['model_frames_sha256']},('ACTUAL_CONSUMED_FRAMES_CHANGED',t['trial_id']);actual_visual.append(identity)
    return result
   if t['arm'].endswith('_ONLY'):r=uni.perform_arm(obj,t['arm'],prompt,processor,model,torch,checked_process,parse,counter)
   else:
    r=joint.execute_pairwise_record(obj,int(t['execution_rank']),processor,model,torch,checked_process,parse,prompt)
    # Scoring is separate from generation. Use the same joint rendered prefix; V_ONLY
    # only selects the source-label metadata returned by the existing scorer.
    r['candidate_scoring_status']='NOT_ATTEMPTED';r['joint_score_reference_modality']='V'
    if r.get('generation_success') and r.get('parser_execution'):
     x=None
     try:
      messages=core.build_messages(obj,prompt);rendered,_=uni.normalize_template_result(processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True));aud,ims,vids=checked_process(messages,use_audio_in_video=False)
      x=processor(text=rendered,audio=aud,images=ims,videos=vids,return_tensors='pt',padding=True,use_audio_in_video=False).to(model.device).to(model.dtype)
      r.update(uni.score_candidate_strings(rendered,x,obj['sample'],'V_ONLY',processor,model,torch));r['scoring_prefix_contract']='FULL_JOINT_PREFIX_NOT_UNIMODAL_PROMPT'
     except Exception as e:r.update(candidate_scoring_status='FAILED',scoring_error=repr(e),scoring_traceback=traceback.format_exc())
     finally:x=None;gc.collect();torch.cuda.empty_cache()
   r=core.jsonable(r);r['actual_consumed_visual_frames']=actual_visual
   generation_failure=not(r.get('generation_success') and r.get('parser_execution') and r.get('parser_status') in ['OK','PARSE_FAIL'])
   scoring_failure=r.get('candidate_scoring_status')!='OK'
   if not scoring_failure:
    ps=[s['probability_mean_score_primary'] for s in r['candidate_scores'].values()];en=r['candidate_entropy_primary']['normalized_by_log7'];assert len(ps)==7 and all(math.isfinite(v) and 0<=v<=1 for v in ps) and abs(sum(ps)-1)<1e-8 and 0<=en<=1+1e-8
   r.update(trial_id=t['trial_id'],phase=phase,experiment='E1V2',condition=t['condition'],attempt=attempt,run_fingerprint=fingerprint,generation_technical_failure=generation_failure,scoring_technical_failure=scoring_failure,technical_failure=generation_failure or scoring_failure,wall_started_unix=began,wall_finished_unix=time.time(),input_identity={k:{'path':t[k+'_path'],'sha256':t[k+'_sha256']} for k in ['audio','video','text']})
   dest=target/'attempts'/(hashlib.sha256(t['trial_id'].encode()).hexdigest()+f'.attempt{attempt}.json');assert not dest.exists();dump(dest,r);by[t['trial_id']].append(r)
   with (target/'trials.jsonl').open('a') as f:f.write(json.dumps(r,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
   dump(target/'PROGRESS.json',{'phase':phase,'completed_slots':len(by),'planned_slots':len(mf),'attempts':sum(len(rs) for rs in by.values()),'technical_failure_attempts':sum(x['technical_failure'] for rs in by.values() for x in rs),'elapsed_this_session_seconds':time.time()-start,'last_trial':t['trial_id']});print('CHECKPOINT',phase,len(by),len(mf),t['trial_id'],flush=True)
   if not r['technical_failure']:break
   if phase=='pilot' or (scoring_failure and not generation_failure) or r.get('failure_type') not in ['CUDA_OOM','GENERATION_FAILURE','GENERATION_OR_SCORING_FAILURE']:raise RuntimeError('HARD_ERROR_PRESERVED_STOP: '+str(r.get('failure_type') or r.get('scoring_error')))
   if attempt==2:raise RuntimeError('REPEATED_TECHNICAL_FAILURE_PRESERVED_STOP')
   gc.collect();torch.cuda.empty_cache()
  did+=1
 check_lock(cfg)
 record={'phase':phase,'planned_slots':len(mf),'completed_slots':len(by),'all_attempts':sum(len(rs) for rs in by.values()),'technical_failure_attempts':sum(x['technical_failure'] for rs in by.values() for x in rs),'retries':sum(len(rs)-1 for rs in by.values()),'session_active_model_seconds':time.time()-start,'candidate_scoring_forward_calls':sum(x.get('candidate_scoring_forward_calls',0) for rs in by.values() for x in rs),'generation_calls':sum(bool(x.get('generation_attempted')) for rs in by.values() for x in rs),'run_fingerprint':fingerprint,'status':'COMPLETE' if len(by)==len(mf) else 'PARTIAL'}
 dump(target/f'EXECUTION_SESSION_{os.getpid()}.json',record)
 if len(by)==len(mf):dump(target/'EXECUTION_RECEIPT.json',record)
 print('RUNNER_RETURN',json.dumps(record),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['pilot','full'],required=True);p.add_argument('--max-slots',type=int);a=p.parse_args();main(a.phase,a.max_slots)
