"""E1 V2 CPU recovery and media validation. Never loads model or uses GPU."""
import os,sys,pathlib,json,hashlib,csv,subprocess,time,traceback,inspect,shutil
sys.dont_write_bytecode=True
ROOT=pathlib.Path('/root/autodl-tmp/affective-conflict-e1-video-v2')
OLD=pathlib.Path('/root/autodl-tmp/affective-conflict-e1-e2-full-v1')
REPO=pathlib.Path('/root/autodl-tmp/affective-conflict-eri1/repo')
R=pathlib.Path('/root/autodl-tmp/affective-conflict')
FFMPEG=ROOT/'tools/ffmpeg'
os.environ.update(AF_WORK_ROOT=str(R),AF_DATA_ROOT=str(R),AF_MODEL_DIR=str(R/'models/Qwen2.5-Omni-7B'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
for key,sub in [('TMPDIR','tmp'),('NUMBA_CACHE_DIR','numba'),('HF_HOME','hf'),('MPLCONFIGDIR','mpl'),('CUDA_CACHE_PATH','cuda'),('TORCH_HOME','torch'),('XDG_CACHE_HOME','xdg')]:
 p=ROOT/'logs/cache'/sub;p.mkdir(parents=True,exist_ok=True);os.environ[key]=str(p)
sys.path.insert(0,str(REPO))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+f'.{os.getpid()}.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');os.replace(tmp,p)
def rows(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def table(p,rs):
 with open(p,'w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def cmd(args):return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT)
def probe(p):
 j=json.loads(cmd(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]));v=[x for x in j['streams'] if x['codec_type']=='video'];assert len(v)==1 and not any(x['codec_type']=='audio' for x in j['streams']);return v[0]
def timestamps(p):return [float(x['best_effort_timestamp_time']) for x in json.loads(cmd(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(p)]))['frames']]
def prepare():
 for d in ['00_recovery','01_design','02_media','03_pilot','04_full','05_analysis','06_verification','07_closure','code','docs','logs']: (ROOT/d).mkdir(parents=True,exist_ok=True)
 assert not (ROOT/'04_full/trials.jsonl').exists()
 # Preserve old artifacts by byte-copy to a new evidence area only.
 recovered={}
 for rel in ['00_gate/E1_GATE_REPORT.json','00_gate/00_SOURCE_LOCK.json','00_gate/SOURCE_POPULATION_WITH_CLUSTERS.csv','00_gate/MEDIA_PROCESSOR_CONTRACT.json','logs/media_gate.log','code/e1e2_media_gate.py','code/e1e2_full_runner.py','code/e1e2_common.py','01_protocol_freeze/E2_FROZEN_PROTOCOL.json','03_e2_consistent/E2_EXECUTION_RECEIPT.json','06_scientific_closure/E1_E2_SCIENTIFIC_CLOSURE_REPORT.md']:
  p=OLD/rel;dest=ROOT/'00_recovery'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():assert sha(dest)==sha(p)
  else:shutil.copyfile(p,dest)
  recovered[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
 original_log=(OLD/'logs/media_gate.log').read_text();stderr=[x for x in original_log.splitlines() if 'Unrecognized option' in x or 'Error splitting' in x];assert "Unrecognized option 'fps_mode'." in stderr
 ff=cmd(['ffmpeg','-version']);gblur=cmd(['ffmpeg','-hide_banner','-h','filter=gblur']);assert 'Gaussian Blur' in gblur
 (ROOT/'00_recovery/FFMPEG_VERSION.txt').write_text(ff);(ROOT/'00_recovery/GBLUR_HELP.txt').write_text(gblur)
 from importlib import metadata
 env={'python_executable':sys.executable,'python_version':sys.version,'packages':{d.metadata['Name']:d.version for d in metadata.distributions() if d.metadata.get('Name')},'ffmpeg_version':ff.splitlines()[0],'code_commit':cmd(['git','-C',str(REPO),'rev-parse','HEAD']).strip(),'git_status':cmd(['git','-C',str(REPO),'status','--porcelain'])}
 assert env['code_commit']=='34aa1b0340d906e5d625db7cb4a3def9199fa06e' and not env['git_status']
 for role in ['model','processor']:
  p=REPO/'frozen/identity'/(role+'.json');env[role+'_identity']=json.loads(p.read_text());env[role+'_identity_sha256']=sha(p)
 dump(ROOT/'00_recovery/ENVIRONMENT_LOCK.json',env)
 source=[r for r in rows(OLD/'00_gate/SOURCE_POPULATION_WITH_CLUSTERS.csv') if r['experiment']=='E1'];assert len(source)==146 and len({s['utterance_id'] for s in source})==146 and len({s['dialogue_id'] for s in source})==134
 oldlock=json.loads((OLD/'00_gate/00_SOURCE_LOCK.json').read_text())
 for p,rec in oldlock['sources'].items():assert sha(p)==rec['SHA256'],p
 for s in source:
  for k in ['audio','video','text']:assert sha(s[k+'_path'])==s[k+'_sha256'],(s['utterance_id'],k)
 table(ROOT/'01_design/SOURCE_POPULATION.csv',source)
 spec={'experiment':'EMOTIONTALK_E1_VIDEO_DEGRADATION_EXECUTION_V2','source_items':146,'dialogue_clusters':134,'slots':2336,'conditions':['CLEAN','RECODE','BLUR_L1','BLUR_L2','BLUR_L3'],'blur':{'algorithm':'FFmpeg gblur','sigma_native_short_side_fractions':[0.01,0.04,0.12],'steps':3,'planes':15,'sigmaV':'same as sigma','parameters_selected_before_pilot':True},'encoding':{'codec':'libx264','crf':0,'pixel_format':'yuv420p','preset':'fast','threads':1,'timestamp_preservation':'-copyts -vsync 0; original video_track_timescale','audio_tracks':0,'no_crop_or_resize_or_fps_reduction':True},'calls':'146 x (5 x (V_ONLY + A_THEN_V + V_THEN_A) + A_ONLY CLEAN); candidate scoring additional forwards counted separately','primary':{'contrast':'BLUR_L3 minus RECODE','endpoints':['SIDE_V','SIDE_A','OTHER'],'weights':'equal utterance weight, average two presentation orders','multiplicity':'Holm across three primary two-sided paired sign-flip tests','bootstrap_replicates':10000,'signflip_replicates':100000,'seed':2026101103,'unit':'utterance paired; official dialogue cluster percentile bootstrap also reported','fixed_ITT':146,'technical_missing':'retain every item and report category-wise worst/best effect bounds; complete-case sensitivity secondary; no positive claim unless robust to conservative bounds','PARSE_FAIL':'separate category, never dropped'},'secondary':{'family':'one Holm family for CLEAN-RECODE three category effects, three category ordinal dose slopes, three category order interactions, V_ONLY correctness and entropy L3-RECODE','dose_scores':{'RECODE':0,'BLUR_L1':1,'BLUR_L2':2,'BLUR_L3':3},'transitions':'all category matrices by each order and condition; no outcome-based filtering'},'scoring':'seven frozen candidate sequence teacher-forced probabilities and normalized entropy on every planned slot, preserving generation/scoring/parse as separate statuses; no entropy mediation claim','pilot':{'items':'first six sorted frozen utterance IDs','IDs':sorted(s['utterance_id'] for s in source)[:6],'slots':96,'independent_directory':True,'resume_check':'run first subset then same-lock resume, followed by no-op resume; all 96 unique','pass':'source and input contract identical, clean historical raw answer and parsed result equality when generation contract identical, scoring finite probabilities sum 1, entropy [0,1], no hard errors; no selection of blur by outcome'},'full_order':'fixed numpy PCG64 permutation seed 2026101103 after all media bound','historical_results_readonly':True,'no_gpu_yet':True}
 spec['encoding']['encoder_time_base']='original stream time_base; prevents default frame-rate clock rounding for nonzero source PTS'
 tool=json.loads((ROOT/'tools/FFMPEG_TOOL_RECEIPT.json').read_text());assert tool['status']=='PASS' and sha(FFMPEG)==tool['binary_sha256']
 assert json.loads((ROOT/'00_recovery/EXACT_CLOCK_TEST.json').read_text())['status']=='PASS'
 spec['encoding'].update(ffmpeg_binary=str(FFMPEG),ffmpeg_sha256=sha(FFMPEG),ffmpeg_version=tool['ffmpeg_version'],movie_timescale='original stream time_base denominator; exact MP4 edit-list clock',timestamp_preservation='-copyts -vsync 0 -enc_time_base original -video_track_timescale original denominator -movie_timescale original denominator')
 spec['physical_proxy_policy']='all fixed Gaussian sigma parameters and command identities validated; actual consumed frames must differ from RECODE; Laplacian sharpness and gradient energy reported descriptively, nonmonotone proxies flagged, never used to tune sigma'
 p=ROOT/'01_design/DESIGN_SPEC_PRE_MEDIA.json'
 if p.exists():assert json.loads(p.read_text())==spec
 else:dump(p,spec)
 dump(ROOT/'00_recovery/RECOVERY_RECEIPT.json',{'status':'READ_ONLY_RECOVERY_PASS','original_stderr':stderr,'failure':'FFmpeg 4.4.2 rejected unsupported output option -fps_mode before media encoding; zero prior E1 media or model results','minimal_repair':'isolated verified FFmpeg; -vsync 0 and original encoder/video-track/movie clocks; strict timestamp and actual processor frame validation; no tolerance or blur changes','active_ffmpeg_tool':tool,'cpu_regression_evidence':str(ROOT/'00_recovery/EXACT_CLOCK_TEST.json'),'sources':recovered,'source_lock_sha256':sha(OLD/'00_gate/00_SOURCE_LOCK.json'),'design_spec_sha256':sha(p),'historical_media_count':len(list((OLD/'media/E1').glob('*/*'))),'GPU_executed':False})
 (ROOT/'00_recovery/FAILURE_AND_REPAIR.md').write_text('# E1 V2 failure recovery\n\nOriginal stderr: '+repr(stderr)+'\n\nNative FFmpeg rejected -fps_mode. The first compatibility repair exposed encoder time-base rounding; preserving encoder time-base then exposed millisecond MP4 edit-list rounding. The isolated SHA256-verified FFmpeg binary supports movie_timescale. Preserve native encoder, video-track and movie clocks; do not relax timestamp tolerances. EXACT_CLOCK_TEST.json records the CPU-only regression proof for three original clips and all four derived conditions. Gaussian fractions 0.01/0.04/0.12 remain unchanged before any Pilot. Actual model frame and processor contract validation across all 146 items remains mandatory. Historical E1, E2 and ERI1 remain read-only.\n')
 for name,text in [('PROJECT_STATE.md','E1 V2 CPU media validation in progress. GPU enabled but not yet used; Pilot and Full not started. E2 remains complete, immutable.'),('FILE_MAP.md','00_recovery: original failure evidence, engineering attempts and environment lock; tools: isolated verified FFmpeg; 01_design: fixed population and pre-media design; 02_media: derived video and per-item physical receipts; 03_pilot and 04_full: currently empty.'),('DECISIONS.md','E1 V2 authorized by user. Isolated FFmpeg plus original encoder, track and movie clocks requires strict physical and processor identity checks. 2336 formal slots; independent 6-item Pilot required. Three primary endpoints use Holm. No post-treatment selection. No changes to historical frozen artifacts.')]: (ROOT/'docs'/name).write_text(text+'\n')
 print('RECOVERY_AND_PREMEDIA_DESIGN_PASS',flush=True)
def gate():
 tool=json.loads((ROOT/'tools/FFMPEG_TOOL_RECEIPT.json').read_text());assert tool['status']=='PASS' and sha(FFMPEG)==tool['binary_sha256']
 import numpy as np,torch
 from qwen_omni_utils import vision_process as vision,process_mm_info
 from transformers import Qwen2_5OmniProcessor
 from src.emotiontalk.phase2 import core
 from src.emotiontalk.phase1 import execution as uni
 # Recover the exact functions actually used by process_mm_info, not a guessed video reader.
 import qwen_omni_utils
 fetch=vision.fetch_video;reader=vision.VIDEO_READER_BACKENDS[vision.get_video_reader_backend()]
 dump(ROOT/'01_design/PROCESSOR_CODE_CONTRACT.json',{'fetch_source':inspect.getsource(fetch),'reader_source':inspect.getsource(reader),'smart_nframes_source':inspect.getsource(vision.smart_nframes),'vision_module':vision.__file__,'vision_module_sha256':sha(vision.__file__),'process_mm_info_source':inspect.getsource(process_mm_info)})
 processor=Qwen2_5OmniProcessor.from_pretrained(str(R/'models/Qwen2.5-Omni-7B'),local_files_only=True);prompt=core.read_json(core.PROMPT_PATH)
 # Local copy of prior frozen input builder; only output/cache root changes.
 sys.path.insert(0,str(ROOT/'code'));from e1e2_common import inputs
 source=rows(ROOT/'01_design/SOURCE_POPULATION.csv');manifest=[];bindings=[]
 worker=int(os.environ.get('E1V2_CPU_WORKER','-1'));workers=int(os.environ.get('E1V2_CPU_WORKERS','1'))
 for n,s in enumerate(source,1):
  if worker>=0 and (n-1)%workers!=worker:continue
  receipt=ROOT/'02_media/receipts'/(s['utterance_id']+'.json')
  if receipt.exists():
   r=json.loads(receipt.read_text());assert r['status']=='PASS'
   for t in r['bindings']:assert sha(t['video_path'])==t['video_sha256']
   bindings.extend(r['bindings']);print('CPU_RESUME_ITEM',n,flush=True);continue
  vp=s['video_path'];meta=probe(vp);basepts=timestamps(vp);clean=fetch({'video':vp});base_shape=list(clean.shape);sharp_prev=None;recode=None;bs=[];physical=[]
  # Match the reader's actual linspace selection and explicitly link to decoded PTS.
  sampled,reader_meta,sample_fps=reader({'video':vp});indices=[int(i) for i in reader_meta['frames_indices']];total=reader_meta['total_num_frames'];assert len(basepts)==total and len(indices)==clean.shape[0]
  del sampled
  for cond,fraction in zip(['CLEAN','RECODE','BLUR_L1','BLUR_L2','BLUR_L3'],[0,0,.01,.04,.12]):
   t={**s,'condition':cond,'sigma_native':fraction*min(int(meta['width']),int(meta['height'])),'sigma_native_short_side_fraction':fraction}
   command=None
   if cond!='CLEAN':
    dst=ROOT/'02_media/videos'/cond/(s['utterance_id']+'.mp4');dst.parent.mkdir(parents=True,exist_ok=True)
    command=[str(FFMPEG),'-nostdin','-v','error','-copyts','-i',vp,'-map','0:v:0','-an']
    if fraction:command+=['-vf',f'gblur=sigma={t["sigma_native"]}:sigmaV={t["sigma_native"]}:steps=3:planes=15']
    command+=['-c:v','libx264','-preset','fast','-crf','0','-pix_fmt','yuv420p','-threads','1','-vsync','0','-enc_time_base',meta['time_base'],'-video_track_timescale',meta['time_base'].split('/')[1],'-movie_timescale',meta['time_base'].split('/')[1],str(dst)]
    cp=ROOT/'02_media/commands'/cond/(s['utterance_id']+'.json')
    if dst.exists():
     assert cp.exists(),('UNBOUND_EXISTING_MEDIA_REQUIRES_REVIEW',str(dst));prior=json.loads(cp.read_text());assert prior['command']==command and prior['returncode']==0
     if prior.get('output_sha256'):assert sha(dst)==prior['output_sha256']
    else:
     run=subprocess.run(command,capture_output=True,text=True);dump(cp,{'command':command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'output_sha256':sha(dst) if run.returncode==0 else None});assert run.returncode==0,run.stderr
    t.update(video_path=str(dst),video_sha256=sha(dst))
   newmeta=probe(t['video_path']);newpts=timestamps(t['video_path']);delta=max(abs(a-b) for a,b in zip(newpts,basepts));assert len(newpts)==len(basepts) and delta<=1e-6,('PTS_MISMATCH',s['utterance_id'],cond,len(basepts),len(newpts),delta,basepts[:3],newpts[:3])
   for k in ['width','height','r_frame_rate','nb_frames']:assert newmeta.get(k)==meta.get(k),(cond,k)
   assert abs(float(newmeta['duration'])-float(meta['duration']))<=1e-6
   sampled,new_reader_meta,new_sample_fps=reader({'video':t['video_path']});assert [int(i) for i in new_reader_meta['frames_indices']]==indices and new_reader_meta['total_num_frames']==total and abs(new_sample_fps-sample_fps)<1e-12;del sampled
   v=fetch({'video':t['video_path']});assert list(v.shape)==base_shape
   a=v.numpy();grey=a.astype('float64').mean(axis=1);lap=-4*grey+np.roll(grey,1,1)+np.roll(grey,-1,1)+np.roll(grey,1,2)+np.roll(grey,-1,2);sharp=float(lap[:,1:-1,1:-1].var())
   if cond=='RECODE':recode=v;sharp_prev=sharp
   elif fraction:assert float((v-recode).abs().mean())>0
   m={'condition':cond,'command':command,'original_stream':meta,'stream':newmeta,'all_decoded_frame_pts':newpts,'sampled_frame_indices':indices,'sample_fps':sample_fps,'model_sampled_timestamps':[newpts[i] for i in indices],'model_frame_shape':base_shape,'model_frames_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'sharpness_physical_proxy':sharp,'sharpness_proxy_nonmonotone':bool(fraction and sharp>=sharp_prev),'spatial_gradient_energy':float(np.mean(np.diff(grey,axis=1)**2)+np.mean(np.diff(grey,axis=2)**2)),'processor':{}}
   if fraction:sharp_prev=sharp
   for arm in ['V_ONLY','A_THEN_V','V_THEN_A']:
    obj=inputs({**t,'arm':arm})
    messages=uni.build_messages(obj,arm,prompt)[0] if arm=='V_ONLY' else core.build_messages(obj,prompt)
    aud,ims,vids=process_mm_info(messages,use_audio_in_video=False);rendered,_=uni.normalize_template_result(processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True));x=processor(text=rendered,audio=aud,images=ims,videos=vids,return_tensors='pt',padding=True,use_audio_in_video=False)
    m['processor'][arm]={'tokens':int(x.input_ids.shape[-1]),'video_grid_thw':x['video_grid_thw'].tolist(),'visual_tensor_sha256':hashlib.sha256(x['pixel_values_videos'].numpy().tobytes()).hexdigest(),'visual_tensor_shape':list(x['pixel_values_videos'].shape),'audio_input_count':0 if arm=='V_ONLY' else 1}
    del x,aud,ims,vids
   physical.append(m);bs.append(t)
  for arm in ['V_ONLY','A_THEN_V','V_THEN_A']:
   ref=physical[0]['processor'][arm]
   for m in physical[1:]:
    x=m['processor'][arm];assert x['tokens']==ref['tokens'] and x['video_grid_thw']==ref['video_grid_thw'] and x['visual_tensor_shape']==ref['visual_tensor_shape']
  dump(receipt,{'status':'PASS','utterance_id':s['utterance_id'],'bindings':bs,'physical':physical});bindings.extend(bs)
  dump(ROOT/'02_media'/('PROGRESS.json' if worker<0 else f'WORKER_{worker}_PROGRESS.json'),{'completed_receipts':len(list((ROOT/'02_media/receipts').glob('*.json'))),'planned_items':146,'last_uid':s['utterance_id'],'GPU_used':False});print('CPU_MEDIA_ITEM_PASS',n,s['utterance_id'],flush=True)
 if worker>=0:
  dump(ROOT/'02_media'/f'WORKER_{worker}_DONE.json',{'status':'PASS','worker':worker});return
 for t in bindings:
  for arm in ['V_ONLY','A_THEN_V','V_THEN_A']:manifest.append({**t,'arm':arm,'trial_id':f'E1V2|{t["utterance_id"]}|{t["condition"]}|{arm}'})
 for s in source:manifest.append({**s,'condition':'CLEAN','sigma_native':0,'sigma_native_short_side_fraction':0,'arm':'A_ONLY','trial_id':f'E1V2|{s["utterance_id"]}|CLEAN|A_ONLY'})
 rng=np.random.Generator(np.random.PCG64(2026101103));manifest=[{**manifest[i],'execution_rank':rank} for rank,i in enumerate(rng.permutation(len(manifest)),1)];assert len(manifest)==2336 and len({r['trial_id'] for r in manifest})==2336
 table(ROOT/'01_design/FULL_MANIFEST.csv',manifest);table(ROOT/'01_design/MEDIA_BINDING.csv',bindings)
 dump(ROOT/'01_design/CPU_MEDIA_GATE.json',{'status':'PASS','source_items':146,'physical_video_conditions':730,'slots':2336,'media_hashes':'PASS','timestamps_and_model_sampling':'PASS','all_three_video_arm_processor_contracts':'PASS','GPU_executed':False,'protocol_freeze':'PENDING_RUNNER_AND_ANALYSIS_CODE_LOCK','pilot':'NOT_STARTED'})
 print('CPU_MEDIA_GATE_PASS',flush=True)
if __name__=='__main__':
 try:
  if 'E1V2_CPU_WORKER' not in os.environ:prepare()
  gate()
 except Exception as e:
  dump(ROOT/'01_design/CPU_MEDIA_GATE.json',{'status':'FAIL','error':repr(e),'traceback':traceback.format_exc(),'GPU_executed':False});raise
