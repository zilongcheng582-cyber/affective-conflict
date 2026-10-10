import json,csv,hashlib,re,zipfile,tarfile,collections
from pathlib import Path
R=Path('/root/autodl-tmp/affective-conflict');E=Path('/root/autodl-tmp/affective-conflict-forensics-expanded-v1');O=Path('/root/autodl-tmp/affective-conflict-reconciliation-v2')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def jl(p):return [json.loads(l) for l in open(p) if l.strip()]
entries=json.loads((E/'FULL_EXPERIMENT_ARCHIVE_INDEX.json').read_text());archives=[Path(r['path']) for r in entries];archives.append(R/'source/LISTEN.zip');findings=[];errors=[];known={r['sha256']:r['path'] for r in csv.DictReader(open(E/'RECOVERED_EXPERIMENT_EXECUTION_REGISTER.csv'))}
for p in archives:
 z=zipfile.ZipFile(p) if zipfile.is_zipfile(p) else tarfile.open(p)
 names=z.namelist() if isinstance(z,zipfile.ZipFile) else [m.name for m in z.getmembers() if m.isfile()]
 result={'path':str(p),'sha256':sha(p),'all_members':len(names),'reviewed_members':[]}
 for name in names:
  if not re.search('listen|camer|mcr',name,re.I) or Path(name).suffix.lower() not in ['.py','.json','.jsonl','.csv','.md','.sh']:continue
  try:
   data=z.read(name) if isinstance(z,zipfile.ZipFile) else z.extractfile(name).read();text=data.decode('utf-8',errors='replace');mh=hashlib.sha256(data).hexdigest();item={'name':name,'bytes':len(data),'sha256':mh,'duplicate_registered_path':known.get(mh)}
   if Path(name).suffix.lower() in ['.json','.jsonl']:
    d=json.loads(text) if name.endswith('.json') else [json.loads(l) for l in text.splitlines() if l.strip()]
    rs=d if isinstance(d,list) else d.get('results',[]) if isinstance(d,dict) else []
    rs=[r for r in rs if isinstance(r,dict)];item['records']=len(rs);item['raw_execution_records']=sum(bool(r.get('raw_model_output') or r.get('raw_generated_sequence') or r.get('assistant_text')) for r in rs);item['executed_reverse']=sum(any(r.get(k)=='T_THEN_A' for k in ['arm','presentation_order','order','condition']) and bool(r.get('generation_success') or r.get('raw_model_output') or r.get('raw_generated_sequence')) for r in rs)
    vectors=[]
    for r in rs:
     for k in ['candidate_probabilities','candidate_log_scores','candidate_scores','logits','probabilities']:
      v=r.get(k)
      if isinstance(v,(list,dict)) and len(v)==16 and all(isinstance(x,(int,float)) for x in (v.values() if isinstance(v,dict) else v)):vectors.append(k)
    item['numeric_16_candidate_vectors']=len(vectors)
   if 'T_THEN_A' in text:item['reverse_text_lines']=[{'line':i+1,'text':l[:500]} for i,l in enumerate(text.splitlines()) if 'T_THEN_A' in l][:20]
   result['reviewed_members'].append(item)
  except Exception as ex:errors.append({'path':str(p),'member':name,'error':str(ex)})
 z.close();findings.append(result)
(O/'INDEXED_ARCHIVE_RECONCILIATION_V2.json').write_text(json.dumps({'method':'existing expanded archive paths; selected dataset-named members only; no extraction into historical dirs','archives':findings,'errors':errors},indent=2))
# Native descriptions actually used, not the condition names alone.
native=jl(R/'audit/QWEN25_MCR_NATIVE_V1/mcr_ser_native_qwen25_manifest_v1.jsonl');ctrl=jl(R/'audit/QWEN25_MCR_CONTROLLED_V3/mcr_controlled_arbitration_manifest_v2.jsonl');cm={r['source_index']:r for r in ctrl if r['arm']=='A_THEN_T'};nc=collections.Counter();faithful=collections.Counter();claimmatches=0;excluded=[]
for r in native:
 if r['condition'] not in ['adversarial','faithful']:continue
 m=re.search(r'Description: (.*?)\nClassify',r['source_text'],re.S);desc=m.group(1) if m else None;lab=re.search(r'This audio expresses (\w+) emotion\.',desc or '');label=lab.group(1) if lab else None
 if r['condition']=='faithful':faithful['claim_extracted']+=label is not None;faithful['claim_matches_gt']+=label==r['gt']
 else:
  nc['claim_extracted']+=label is not None;nc['claim_equals_audio_label']+=label==r['gt'];nc['claim_differs_audio_label']+=label is not None and label!=r['gt']
  if r['source_index'] in cm:claimmatches+=desc==cm[r['source_index']]['text_evidence']
  else:excluded.append({'source_index':r['source_index'],'audio_gt':r['gt'],'adversarial_claim_label':label,'reason':'SAME_LABEL' if label==r['gt'] else 'UNRESOLVED'})
inspection=json.loads((O/'TARGETED_INSPECTION.json').read_text());model=[]
for p,r in inspection['contents'].items():
 if 'MCR' in p.upper() and ('PROVENANCE' in p.upper() or 'FULL_RUN' in p.upper() or 'EXECUTION' in p.upper()):
  lines=[{'line':i+1,'text':l[:1000]} for i,l in enumerate(r['text'].splitlines()) if re.search(r'model|processor|weight|revision|sha256|command|audio.root',l,re.I)]
  if lines:model.append({'path':p,'sha256':r['sha256'],'identity_excerpts':lines})
(O/'MCR_TEXT_AND_MODEL_CONTRACT_AUDIT_V2.json').write_text(json.dumps({'adversarial_claims':dict(nc),'faithful_claims':dict(faithful),'controlled_description_exact_matches':claimmatches,'excluded_native_items':excluded,'model_identity_sources':model,'weight_byte_equivalence':'NOT_ESTABLISHED_BY_PATH_AND_CONFIG_ALONE'},indent=2))
print('ARCHIVE_CONTRACT_AUDIT_COMPLETE',len(findings),len(errors),'MCR_DESCRIPTION_MATCHES',claimmatches,'EXCLUDED_REASONS',dict(collections.Counter(r['reason'] for r in excluded)))
