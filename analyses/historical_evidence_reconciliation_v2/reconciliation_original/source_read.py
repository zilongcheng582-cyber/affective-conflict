import json,re
from pathlib import Path
O=Path('/root/autodl-tmp/affective-conflict-reconciliation-v2');d=json.loads((O/'TARGETED_INSPECTION.json').read_text());out={}
for p,r in d['contents'].items():
 if any(p.endswith(x) for x in ['run_qwen25_mcr_native_v1.py','run_qwen25_mcr_controlled_v3.py','qwen25_mcr_native_execution_v1.json','qwen25_mcr_controlled_execution_v1.json','mcr_controlled_arbitration_prompt_v2.json','MCR_CONTROLLED_FULL_V2_PROVENANCE.json','LISTEN_V3_VS_SOURCE_LAUNCH_AUDIT.md','LISTEN_V4_CANONICAL_AT_JOIN_PROVENANCE_V1.json','CAMER_RESOURCE_SWEEP_SCIENTIFIC_EQUIVALENCE_V1.json','LISTEN_PHASE1_POOL.md','LISTEN_NATIVE_PROTOCOL_V1.json']):
  if p.endswith('.py'):
   ls=r['text'].splitlines();ix=set()
   for i,l in enumerate(ls):
    if re.search(r'messages|content|candidate|model_path|model_revision|from_pretrained|generate\(|system_text|processor|text_evidence|source_text|hash',l,re.I):ix.update(range(max(0,i-3),min(len(ls),i+7)))
   out[p]={'sha256':r['sha256'],'excerpts':[{'line':i+1,'text':ls[i]} for i in sorted(ix)]}
  else:out[p]=r
S=Path('/root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/outputs/B3_MEASUREMENTS_V1.jsonl')
if S.exists():out['B3_example']=json.loads(next(l for l in open(S) if l.strip()))
(O/'SOURCE_CONTRACT_READBACK.json').write_text(json.dumps(out,indent=2,ensure_ascii=False));print('SOURCE_CONTRACT_READBACK_DONE',len(out))
