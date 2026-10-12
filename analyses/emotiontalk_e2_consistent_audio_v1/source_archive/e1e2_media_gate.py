"""CPU physical/environment gate; never imports or loads the Qwen model."""
from e1e2_common import *
import subprocess,time,traceback,inspect,importlib.metadata,math
import numpy as np
def probe(p):
 j=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
 vs=[s for s in j['streams'] if s['codec_type']=='video'];assert len(vs)==1 and not any(s['codec_type']=='audio' for s in j['streams'])
 return vs[0]
def pts(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(p)]))['frames']
def metrics(v):
 a=v.cpu().numpy();grey=a.mean(axis=1).astype('float64')
 lap=-4*grey+np.roll(grey,1,1)+np.roll(grey,-1,1)+np.roll(grey,1,2)+np.roll(grey,-1,2)
 return {'shape':list(a.shape),'frame_tensor_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'sharpness_laplacian_variance':float(lap[:,1:-1,1:-1].var()),'pixel_mean':float(a.mean())}
def main():
 from src.cross_regime.target_scoring.verify_runtime import verify
 from src.cross_regime.target_scoring.inputs import FrozenInputs
 env=verify(FrozenInputs());dump(O/'00_gate/ENVIRONMENT_GATE.json',env)
 assert env['GPU_EXECUTION_ALLOWED']=='YES',env
 from transformers import Qwen2_5OmniProcessor
 from qwen_omni_utils import process_mm_info,vision_process as vision
 from src.emotiontalk.reliability_v1 import audio,design
 from src.emotiontalk.phase2 import core
 from src.emotiontalk.phase1 import execution as uni
 processor=Qwen2_5OmniProcessor.from_pretrained(str(R/'models/Qwen2.5-Omni-7B'),local_files_only=True)
 prompt=core.read_json(core.PROMPT_PATH)
 identity={'model_revision':'ae9e1690543ffd5c0221dc27f79834d0294cba00','model_and_processor':'FROZEN_RUNTIME_VERIFY_PASS','vision_module':vision.__file__,'vision_module_sha256':sha(vision.__file__),'vision_fetch_source':inspect.getsource(vision.fetch_video),'processor_config':processor.video_processor.to_dict() if hasattr(processor,'video_processor') else processor.image_processor.to_dict(),'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]}
 dump(O/'00_gate/MEDIA_PROCESSOR_CONTRACT.json',identity)
 source=rows(O/'00_gate/SOURCE_POPULATION.csv')
 schema=json.loads((O/'00_gate/OFFICIAL_METADATA_SCHEMA.json').read_text());official=rows(schema['path']);omap={pathlib.PurePosixPath(r['file_name']).stem:r['file_name'] for r in official};assert len(omap)==len(official)
 for s in source:
  parts=pathlib.PurePosixPath(omap[s['utterance_id']]).parts
  assert len(parts)==4 and parts[:3]==tuple(pathlib.Path(s['audio_path']).parts[-4:-1])
  s['dialogue_id']=parts[1]
 assert len({s['dialogue_id'] for s in source if s['experiment']=='E1'})==134
 table(O/'00_gate/SOURCE_POPULATION_WITH_CLUSTERS.csv',source)
 previous={design.noise_seed(s['utterance_id']) for s in source if s['experiment']=='E1'}
 e2seeds={s['utterance_id']:design.derived_seed('E2_AV_CONSISTENT_AUDIO_DEGRADATION_CONTROL_V1',s['utterance_id'],'AUDIO_WHITE_NOISE_V1') for s in source if s['experiment']=='E2'}
 assert len(set(e2seeds.values()))==225 and not(set(e2seeds.values())&previous)
 all_manifests={};physical=[];gates={}
 for exp in ['E1','E2']:
  trials=[];condition_rows=[]
  try:
   for n,s in enumerate(x for x in source if x['experiment']==exp):
    uid=s['utterance_id'];base=dict(s);vclean=None
    if exp=='E1':
     meta=probe(s['video_path']);vclean=vision.fetch_video({'video':s['video_path']});cm=metrics(vclean);frame_pts=pts(s['video_path'])
     conditions=['V_CLEAN','V_RECODE','V_BLUR_LOW','V_BLUR_MED','V_BLUR_HIGH'];sigmas=[0,0,.01,.04,.12]
    else:conditions=['A_CLEAN','A_RECODE','A_SNR20','A_SNR10','A_SNR00']
    compare_video=None;recode_audio=None
    for i,cond in enumerate(conditions):
     t=dict(base);t['condition']=cond;t['noise_seed']=e2seeds.get(uid,'');t['sigma_native']='';t['sigma_visible_target']='';t['target_snr_db']=''
     m={'experiment':exp,'utterance_id':uid,'condition':cond}
     if exp=='E1' and i:
      dst=O/'media/E1'/cond/(uid+'.mp4');dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists()
      visible_short=min(vclean.shape[-2:]);native_short=min(int(meta['height']),int(meta['width']));sigma=sigmas[i]*native_short
      t.update(sigma_native=sigma,sigma_visible_target=sigmas[i]*visible_short)
      cmd=['ffmpeg','-nostdin','-v','error','-copyts','-i',s['video_path'],'-map','0:v:0','-an']
      if sigma:cmd+=['-vf',f'gblur=sigma={sigma}:steps=3']
      cmd+=['-c:v','libx264','-preset','fast','-crf','0','-pix_fmt','yuv420p','-threads','2','-fps_mode','passthrough','-video_track_timescale',meta['time_base'].split('/')[1],str(dst)]
      subprocess.run(cmd,check=True);newmeta=probe(dst)
      for k in ['width','height','nb_frames','r_frame_rate']:assert newmeta.get(k)==meta.get(k),(uid,cond,k,newmeta.get(k),meta.get(k))
      newpts=pts(dst);assert len(newpts)==len(frame_pts) and all(abs(float(a['best_effort_timestamp_time'])-float(b['best_effort_timestamp_time']))<=1e-6 for a,b in zip(newpts,frame_pts))
      assert abs(float(newmeta['duration'])-float(meta['duration']))<=1e-6
      t.update(video_path=str(dst),video_sha256=sha(dst));v=vision.fetch_video({'video':str(dst)});m.update(metrics(v));assert tuple(v.shape)==tuple(vclean.shape)
      if i==1:compare_video=v;last_sharp=m['sharpness_laplacian_variance']
      else:
       difference=float((v-compare_video).abs().mean());m['mean_absolute_difference_from_recode']=difference;assert difference>0,(uid,cond,'NO_VISIBLE_CHANGE')
       # Sharpness proxy is physical only, never model emotion performance.
       assert m['sharpness_laplacian_variance']<last_sharp,(uid,cond,'NON_MONOTONE_SHARPNESS')
       last_sharp=m['sharpness_laplacian_variance']
      m.update(sigma_native=sigma,sigma_visible_target=t['sigma_visible_target'],original_stream=meta,processed_stream=newmeta,timestamps_sha256=hashlib.sha256(json.dumps(newpts,sort_keys=True).encode()).hexdigest())
     elif exp=='E1':m.update(cm)
     elif i:
      dst=O/'media/E2'/cond/(uid+'.wav');dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();snr={2:20,3:10,4:0}.get(i)
      data,am=audio.make_variant(pathlib.Path(s['audio_path']).read_bytes(),e2seeds[uid],snr);dst.write_bytes(data);t.update(audio_path=str(dst),audio_sha256=sha(dst),target_snr_db='' if snr is None else snr);m.update(am)
      from scipy.io import wavfile
      sr,w=wavfile.read(dst);assert sr==16000 and w.ndim==1 and w.dtype==np.float32
      if i==1:recode_audio=w
      else:
       assert len(w)==len(recode_audio);noise=w.astype('float64')-recode_audio.astype('float64');actual=10*np.log10(np.mean(recode_audio.astype('float64')**2)/np.mean(noise**2));assert abs(actual-snr)<1e-4;m['readback_snr_db']=float(actual)
     assert sha(t['audio_path'])==t['audio_sha256'] and sha(t['video_path'])==t['video_sha256']
     # Decode once per physical cell; run exact processor for both presentation orders.
     for arm in ['A_THEN_V','V_THEN_A']:
      test={**t,'arm':arm};rec=inputs(test);messages=core.build_messages(rec,prompt)
      aud,ims,vids=process_mm_info(messages,use_audio_in_video=False)
      rendered,_=uni.normalize_template_result(processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True))
      processed=processor(text=rendered,audio=aud,images=ims,videos=vids,return_tensors='pt',padding=True,use_audio_in_video=False)
      assert sum(c['type']=='audio' for c in messages[0]['content'])==1 and sum(c['type']=='video' for c in messages[0]['content'])==1
      m['processor_'+arm]={'input_token_count':int(processed.input_ids.shape[-1]),'video_grid':processed.get('video_grid_thw').tolist() if processed.get('video_grid_thw') is not None else None}
      del processed,aud,ims,vids
     physical.append(m);condition_rows.append(t)
     for arm in ['A_THEN_V','V_THEN_A','V_ONLY' if exp=='E1' else 'A_ONLY']:
      trials.append({**t,'arm':arm,'trial_id':f'{exp}|{uid}|{cond}|{arm}'})
    print('MEDIA_CPU_ITEM_PASS',exp,n+1,uid,flush=True)
   seed=2026101101 if exp=='E1' else 2026101102;rng=np.random.default_rng(seed);order=rng.permutation(len(trials))
   trials=[{**trials[idx],'execution_rank':rank} for rank,idx in enumerate(order,1)]
   assert len(trials)==(2190 if exp=='E1' else 3375) and len({t['trial_id'] for t in trials})==len(trials)
   table(O/'01_protocol_freeze'/f'{exp}_FULL_MANIFEST.csv',trials);table(O/'00_gate'/f'{exp}_MEDIA_BINDING.csv',condition_rows)
   gates[exp]={'status':'PASS','source_items':146 if exp=='E1' else 225,'joint_cells':1460 if exp=='E1' else 2250,'unimodal_cells':730 if exp=='E1' else 1125,'model_processor_gate':'PASS','all_joint_order_processor_parses':'PASS','physical_cell_count':len(condition_rows),'GPU_executed':False}
  except Exception as e:
   gates[exp]={'status':'FAIL','error':repr(e),'traceback':traceback.format_exc(),'GPU_executed':False};print('GATE_FAIL',exp,repr(e),flush=True)
  dump(O/'00_gate'/f'{exp}_GATE_REPORT.json',gates[exp]);dump(O/'00_gate/MEDIA_PHYSICAL_CHECKS.json',physical)
 dump(O/'00_gate/00_GATE_RESULTS.json',gates);print('MEDIA_GATES_DONE',json.dumps(gates),flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  for exp in ['E1','E2']:dump(O/'00_gate'/f'{exp}_GATE_REPORT.json',{'status':'FAIL','scope':'SHARED_ENVIRONMENT_OR_IDENTITY','error':repr(e),'traceback':traceback.format_exc(),'GPU_executed':False})
  raise
