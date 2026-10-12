"""Read-only historical source gate. Writes exclusively to new E1/E2 root."""
import csv,hashlib,json,os,pathlib,subprocess,sys,collections,time
sys.dont_write_bytecode=True
R=pathlib.Path('/root/autodl-tmp/affective-conflict')
P=pathlib.Path('/root/autodl-tmp/affective-conflict-eri1/repo')
O=pathlib.Path('/root/autodl-tmp/affective-conflict-e1-e2-full-v1')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def rows(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def table(p,rs):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def yes(x):return str(x).upper()=='TRUE'
def main():
 assert O.is_dir() and (O/'00_gate').is_dir()
 sys.path.insert(0,str(P))
 os.environ.update(AF_WORK_ROOT=str(R),AF_DATA_ROOT=str(R),AF_MODEL_DIR=str(R/'models/Qwen2.5-Omni-7B'),PYTHONDONTWRITEBYTECODE='1')
 lock=json.loads((P.parent/'runs/full_v1/RUN_LOCK.json').read_text())
 source={}
 def identity(p,expected=None):
  h=sha(p);source[str(p)]={'SHA256':h,'bytes':p.stat().st_size}
  if expected:assert h==expected,(str(p),h,expected)
  return h
 identity(P/'experiments/emotiontalk_reliability_v1/FROZEN_TRIAL_MANIFEST_V1.csv','09a755ac00b5cc8a31ed94612c0d5eb6cf43f79eaba2edf2788cb7ae010afae4')
 identity(P/'experiments/emotiontalk_reliability_v1/AUDIO_INTERVENTION_BINDING_V1.csv','3afa4c2531c917fb679ad914cee278ddf17fb143c978f2c50ce2a95f177e4190')
 identity(P.parent/'runs/full_v1/trials.jsonl','cdcef4a7ae8be49d9da47040d6aa2504384c9bc6cade83765e3611c4777a0eba')
 commit=subprocess.check_output(['git','-C',str(P),'rev-parse','HEAD'],text=True).strip();assert commit=='34aa1b0340d906e5d625db7cb4a3def9199fa06e'
 for rel,h in lock['code_sha256'].items():identity(P/rel,h)
 for rel in ['src/emotiontalk/reliability_v1/audio.py','experiments/emotiontalk_reliability_v1/ANALYSIS_PLAN_V1.md','experiments/emotiontalk_reliability_v1/PRE_EXECUTION_AMENDMENT_001.md','experiments/emotiontalk_reliability_v1/BINDING_RECORD_V1.json','frozen/identity/model.json','frozen/identity/processor.json','protocols/emotiontalk/EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json']:identity(P/rel)
 for name in ['AGENTS.md','docs/PROJECT_STATE.md','docs/FILE_MAP.md','docs/DECISIONS.md']:identity(R/name)
 for name in ['source_measurements.csv','EMOTIONTALK_MASTER_PANEL_V1.csv','EMOTIONTALK_MEDIA_MANIFEST_V1.csv','EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json']:identity(P/'manifests/emotiontalk'/name)
 panel={r['utterance_id']:r for r in rows(P/'manifests/emotiontalk/EMOTIONTALK_MASTER_PANEL_V1.csv')}
 meas={r['utterance_id']:r for r in rows(P/'manifests/emotiontalk/source_measurements.csv')}
 media={r['utterance_id']:r for r in rows(P/'manifests/emotiontalk/EMOTIONTALK_MEDIA_MANIFEST_V1.csv')}
 plan=json.loads((P/'manifests/emotiontalk/EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json').read_text())
 identity(P/'manifests/emotiontalk/EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json','0363b012bf5ce083854efa210d2b739c04a10262136ba6abc81e3d7438d05e20')
 binding={r['utterance_id']:r for r in rows(P/'experiments/emotiontalk_reliability_v1/AUDIO_INTERVENTION_BINDING_V1.csv') if r['condition']=='CLEAN'}
 a=sorted(binding);b=sorted(plan['pairs']['AV']['consistent_utterance_ids'])
 assert len(a)==146 and len(b)==225 and not(set(a)&set(b))
 assert set(a)==set(plan['pairs']['AV']['conflict_utterance_ids'])
 responses=[json.loads(l) for l in open(P/'evidence/emotiontalk/phase2_observed_responses.jsonl')]
 identity(P/'evidence/emotiontalk/phase2_observed_responses.jsonl','4fc584c9a9af341f2db4bbdbe84437587187fa870dda9b6cb0417ba7a1782b87')
 observed={(r['utterance_id'],r['arm']):r for r in responses if r['pair']=='AV'}
 seqs={s['candidate_sequence_id']:s['pipe'] for s in json.loads((P/'protocols/emotiontalk/EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json').read_text())['sequences']}
 # Official metadata pathname is located within the existing upstream checkout only.
 official=list((R/'external/EmotionTalk').glob('**/mm-process/mm.csv'))
 assert len(official)==1,official
 identity(official[0],'ad791bd276b2fdd519ffb4a27d215f9e2ffa06f4acbe36445eecb77206543a03')
 official_rows=rows(official[0]);print('OFFICIAL_FIELDS',list(official_rows[0]),flush=True)
 # Freeze metadata now; subsequent cluster construction must use its actual fields.
 dump(O/'00_gate/OFFICIAL_METADATA_SCHEMA.json',{'path':str(official[0]),'SHA256':sha(official[0]),'fields':list(official_rows[0]),'first_row':official_rows[0]})
 from src.common.runtime import external_path
 out=[]
 for exp,ids in [('E1',a),('E2',b)]:
  for uid in ids:
   p,m,md=panel[uid],meas[uid],media[uid]
   assert yes(m['DualReadable_AV']) and yes(m['Readable_A']) and yes(m['Readable_V'])
   assert (m['y_A']!=m['y_V'])==(exp=='E1')
   assert p['audio_emotion']==m['y_A'] and p['video_emotion']==m['y_V'] and p['text_emotion']==m['y_T']
   assert p['candidate_sequence']==m['candidate_sequence']==seqs[p['candidate_sequence_id']]
   for order in ['A_THEN_V','V_THEN_A']:
    h=observed[uid,order];assert h['candidate_sequence']==p['candidate_sequence'] and h['y_M1']==m['y_A'] and h['y_M2']==m['y_V']
   ap=external_path(p['audio_path']);vp=external_path(md['silent_video_path'])
   assert md['validation_status']=='PASS' and int(md['silent_audio_stream_count'])==0
   ah=sha(ap);vh=sha(vp);assert vh==md['silent_video_sha256']
   if exp=='E1':assert ah==binding[uid]['source_audio_sha256'] and vh==binding[uid]['silent_video_sha256']
   tp=R/'data/EmotionTalk/extracted/Text/json'/uid.split('_')[0]/'_'.join(uid.split('_')[:2])/'_'.join(uid.split('_')[:3])/(uid+'.json')
   assert json.loads(tp.read_text())['content']==p['text']
   out.append({'experiment':exp,'utterance_id':uid,'y_A':m['y_A'],'y_V':m['y_V'],'y_T':m['y_T'],'stratum':'CONFLICT' if exp=='E1' else ('ALL_SAME' if m['y_A']==m['y_T'] else 'A_EQ_V_NE_T'),'candidate_sequence_id':p['candidate_sequence_id'],'candidate_sequence':p['candidate_sequence'],'audio_path':str(ap),'audio_sha256':ah,'video_path':str(vp),'video_sha256':vh,'text_path':str(tp),'text_sha256':sha(tp),'speaker_id':p['speaker_id'],'qualification':'FROZEN_PRE_INTERVENTION_DUALREADABLE_AV'})
  print('SOURCE_ITEMS_OK',exp,len(ids),flush=True)
 assert collections.Counter(x['stratum'] for x in out if x['experiment']=='E2')=={'ALL_SAME':127,'A_EQ_V_NE_T':98}
 table(O/'00_gate/SOURCE_POPULATION.csv',out)
 hist=[observed[uid,arm] for uid in b for arm in ['A_THEN_V','V_THEN_A']]
 assert sum(r['joint_outcome']=='SHARED_LABEL' for r in hist)==448
 result={'source_identity':'PASS','E1_items':146,'E2_items':225,'E2_strata':{'ALL_SAME':127,'A_EQ_V_NE_T':98},'historical_E2_shared':448,'historical_E2_denominator':450,'historical_clean_reused_as_current_control':False,'code_commit':commit,'sources':source,'GPU_executed':False,'gate_status':'SOURCE_ONLY_NOT_FULL_GATE'}
 dump(O/'00_gate/00_SOURCE_LOCK.json',result)
 print('SOURCE_GATE_PASS',json.dumps({k:v for k,v in result.items() if k!='sources'}),flush=True)
if __name__=='__main__':main()
