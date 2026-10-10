import sys,json,re,collections
from pathlib import Path
sys.path.insert(0,'/root/autodl-tmp/affective-conflict-recovered-science-v1');import analysis as a
I=a.read(a.Q/'TARGETED_INSPECTION.json'); texts={};locks=[];warnings=[]
for p in I['contents']:
 if 'CAMER' not in p.upper() or 'BYTECODE' in p or 'candidate_snapshot' in p:continue
 if Path(p).suffix not in ['.md','.json','.py']:continue
 if Path(p).stat().st_size>2_000_000:continue
 data=Path(p).read_bytes()
 try:t=data.decode('utf8')
 except UnicodeDecodeError as ex:
  warnings.append({'path':p,'sha256':a.sha(p),'issue':'historical contract text not UTF-8; replacement decoding for navigation excerpts only','error':str(ex)});t=data.decode('utf8',errors='replace')
 if any(s in t for s in ['audio-aligned','video-aligned','final_label']):
  lines=t.splitlines();idx=[i for i,s in enumerate(lines) if any(k in s for k in ['audio-aligned','video-aligned','ground truth','final_label','human'])];take=sorted({j for i in idx for j in range(max(0,i-2),min(len(lines),i+3))});texts[p]='\n'.join(f'{i+1}: {lines[i]}' for i in take);locks.append({'path':p,'sha256':a.sha(p),'bytes':Path(p).stat().st_size})
for name,p in [('LISTEN',a.R/'results/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/listen_native_raw_outputs_source_aligned_v4.jsonl'),('CAMER',a.R/'audit/QWEN25_CAMER_CONTROLLED_V1/resource_sweep_v1/qwen25_camer_controlled_resource_sweep_v1.jsonl')]:
 counts=collections.defaultdict(collections.Counter)
 with open(p) as f:
  for line in f:
   x=json.loads(line)
   for k,v in x.items():
    if any(s in k.lower() for s in ['model','processor','revision','prompt','retry','attempt','status']) and k not in ['raw_model_output']:counts[k][str(v)]+=1
 texts[name+'_metadata']={k:dict(v) for k,v in counts.items()}
a.save('CONSTRUCT_AND_RUNTIME_FOCUS.json',texts);a.save('CONSTRUCT_INPUT_LOCK.json',locks);a.save('CONTRACT_TEXT_WARNINGS.json',warnings);print('CONTRACT_FOCUS_DONE')
