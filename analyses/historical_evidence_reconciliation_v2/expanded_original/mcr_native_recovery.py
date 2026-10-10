import json,re,hashlib,collections
from pathlib import Path
R=Path('/root/autodl-tmp/affective-conflict');O=Path('/root/autodl-tmp/affective-conflict-forensics-expanded-v1')
p=R/'audit/QWEN25_MCR_NATIVE_V1/full_run/qwen25_mcr_native_full_v1.jsonl';examples={};keys=collections.Counter();ids=collections.defaultdict(set)
for l in open(p):
 r=json.loads(l);a=r['condition'];keys.update(r.keys());ids[a].add(r['sample_id'])
 if a not in examples:examples[a]=r
q=R/'code/run_qwen25_mcr_native_v1.py';source=q.read_text(errors='replace');ls=source.splitlines();snips=[]
for i,l in enumerate(ls):
 if re.search(r'faithful|irrelevant|neutral|adversarial|messages|content|conditions',l,re.I):snips.append({'line':i+1,'text':'\n'.join(ls[max(0,i-2):i+4])})
d={'label':'RETROSPECTIVE_EVIDENCE_RECOVERY','path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'unique_items_by_condition':{a:len(v) for a,v in ids.items()},'same_items_across_four_conditions':len(set.intersection(*ids.values())),'fields':list(keys),'examples':examples,'runner_path':str(q),'runner_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'source_snippets':snips,'runner_executed_now':False}
(O/'MCR_NATIVE_FOUR_CONDITION_RECOVERY.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print('MCR_NATIVE_RECOVERED',d['unique_items_by_condition'],d['same_items_across_four_conditions'])
