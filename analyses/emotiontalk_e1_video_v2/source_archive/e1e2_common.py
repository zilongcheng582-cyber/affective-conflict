import csv,hashlib,json,os,pathlib,sys,collections
sys.dont_write_bytecode=True
R=pathlib.Path('/root/autodl-tmp/affective-conflict')
P=pathlib.Path('/root/autodl-tmp/affective-conflict-eri1/repo')
O=pathlib.Path('/root/autodl-tmp/affective-conflict-e1-video-v2')
sys.path.insert(0,str(P))
os.environ.update(AF_WORK_ROOT=str(R),AF_DATA_ROOT=str(R),AF_MODEL_DIR=str(R/'models/Qwen2.5-Omni-7B'))
for key,sub in [('TMPDIR','tmp'),('NUMBA_CACHE_DIR','numba'),('HF_HOME','hf'),('MPLCONFIGDIR','mpl'),('CUDA_CACHE_PATH','cuda'),('TORCH_HOME','torch'),('XDG_CACHE_HOME','xdg')]:
 p=O/'logs/cache'/sub;p.mkdir(parents=True,exist_ok=True);os.environ[key]=str(p)
os.environ['OMP_NUM_THREADS']='1'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def rows(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def dump(p,x):
 temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');os.replace(temp,p)
def table(p,rs):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def inputs(t):
 from src.emotiontalk.phase2 import core
 seq=t['candidate_sequence'];uid=t['utterance_id']
 sample={'utterance_id':uid,'resource_tier':'FORMAL_FULL','candidate_sequence_id':t['candidate_sequence_id'],'candidate_sequence':seq,'candidate_labels':seq.split('|'),'text':None,'text_json_path':t['text_path'],'text_path':t['text_path'],'audio_path':t['audio_path'],'silent_video_path':t['video_path'],'audio_emotion':t['y_A'],'video_emotion':t['y_V'],'text_emotion':None,'y_M1':t['y_A'],'y_M2':t['y_V'],'labels_by_modality':{'A':t['y_A'],'V':t['y_V']},'video_preflight_error':None,'video_duration':None,'resource_rank_within_pair':None}
 if t['arm'].endswith('_ONLY'):return sample
 order=core.ORDER[t['arm']];refs={'A':t['audio_path'],'V':t['video_path']}
 return {'utterance_id':uid,'pair':'AV','stratum':'conflict' if t['experiment']=='E1' else 'consistent','arm':t['arm'],'evidence_1_modality':order[0],'evidence_1_reference':refs[order[0]],'evidence_2_modality':order[1],'evidence_2_reference':refs[order[1]],'instruction_position':'AFTER_EVIDENCE_2','candidate_sequence_id':t['candidate_sequence_id'],'candidate_sequence':seq,'candidate_labels':seq.split('|'),'y_M1':t['y_A'],'y_M2':t['y_V'],'source_relation':'CONFLICT' if t['experiment']=='E1' else 'CONSISTENT','audio_path':t['audio_path'],'text_path':t['text_path'],'silent_video_path':t['video_path'],'video_duration':None,'resource_proxy':None,'resource_rank_within_pair':None,'sample':sample}
