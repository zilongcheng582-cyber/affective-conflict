import pathlib,json,os,hashlib,re
R=pathlib.Path('/root/autodl-tmp/affective-conflict');O=pathlib.Path('/root/autodl-tmp/affective-conflict-forensics-expanded-v1')
s=json.load(open(O/'FULL_EXPERIMENT_SCAN_SUMMARY.json'));roots=[pathlib.Path(p) for p in s['excluded_paths'] if pathlib.Path(p).name=='.ipynb_checkpoints' or pathlib.Path(p).name=='data' and pathlib.Path(p)!=R/'data']
files=[];hits=[]
for root in roots:
 for d,ds,fs in os.walk(root,followlinks=False):
  for n in fs:
   p=pathlib.Path(d,n)
   if p.is_symlink():continue
   e={'path':str(p),'size':p.stat().st_size};files.append(e)
   if p.suffix.lower() in ['.py','.json','.jsonl','.ipynb','.md','.csv','.txt','.sh']:
    h=hashlib.sha256();match=[]
    for i,line in enumerate(p.open('rb'),1):
     h.update(line);text=line.decode(errors='replace')
     if re.search('T_THEN_A|DualReadable|generation_success|raw_model_output|candidate_probabilities',text,re.I) and len(match)<8:match.append({'line':i,'text':text[:1500]})
    e['sha256']=h.hexdigest()
    if match:hits.append(e|{'hits':match})
out={'roots':[str(p) for p in roots],'files':files,'content_hits':hits,'raw_datasets_scanned':False,'note':'Own code/data and notebook checkpoints explicitly supplemented; they are not raw dataset/upstream folders.'}
(O/'OWN_CODE_AND_CHECKPOINT_SUPPLEMENT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('OWN_CODE_SUPPLEMENT_DONE',len(files),len(hits))
