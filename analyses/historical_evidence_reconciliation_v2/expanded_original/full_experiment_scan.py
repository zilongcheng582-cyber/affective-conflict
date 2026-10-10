import os,json,hashlib,zipfile,tarfile,re,collections,time
from pathlib import Path
R=Path('/root/autodl-tmp/affective-conflict');O=Path('/root/autodl-tmp/affective-conflict-forensics-expanded-v1')
skip={'data','models','envs','.git','.venv','node_modules','hf-cache','.ipynb_checkpoints','third_party','external','source_clone','source_audit','source'}
text_ext={'.py','.pyi','.sh','.json','.jsonl','.csv','.tsv','.md','.txt','.log','.out','.err','.yaml','.yml','.ipynb','.ini','.toml','.cfg'}
pattern=re.compile(r'T_THEN_A|DualReadable|dual_readable|selected_sample_ids|joint_eligible|candidate_probabilities|candidate_log_scores|logits|UNIMODAL_SOURCE_LABEL_MATCH',re.I)
inventory=[];hits=[];archives=[];excluded=[];errors=[];raw_candidates=[]
def stream_scan(name,fh):
 h=hashlib.sha256();n=0;matched=[];armcounts=collections.Counter();datasets=collections.Counter();rawcount=0
 for line in fh:
  h.update(line);n+=1;text=line.decode('utf-8',errors='replace')
  if pattern.search(text) and len(matched)<12:matched.append({'line':n,'text':text[:1600]})
  if name.endswith('.jsonl'):
   try:r=json.loads(text)
   except Exception:continue
   if isinstance(r,dict):
    if any(k in r for k in ['raw_model_output','raw_generated_sequence','prediction_raw','assistant_text','generation_success']):
     rawcount+=1;armcounts[str(r.get('arm',r.get('condition',r.get('order','UNKNOWN'))))]+=1;datasets[str(r.get('dataset',r.get('regime','UNKNOWN')))]+=1
 digest=h.hexdigest()
 if matched:hits.append({'path':name,'sha256':digest,'lines':n,'hits':matched})
 if rawcount:raw_candidates.append({'path':name,'sha256':digest,'rows_with_execution_fields':rawcount,'conditions':dict(armcounts),'datasets':dict(datasets)})
 return digest,n
for d,ds,fs in os.walk(R,followlinks=False):
 for n in list(ds):
  if n in skip:excluded.append(str(Path(d,n)))
 ds[:]=[n for n in ds if n not in skip and not Path(d,n).is_symlink()]
 for n in fs:
  p=Path(d,n)
  if p.is_symlink():inventory.append({'path':str(p),'kind':'SYMLINK','target':os.readlink(p)});continue
  st=p.stat();entry={'path':str(p),'size':st.st_size,'mtime':st.st_mtime,'kind':'METADATA_ONLY'};inventory.append(entry)
  if re.search(r'credential|secret|keys?\.env|id_rsa|id_ed25519',n,re.I):entry['kind']='SENSITIVE_CONTENT_SKIPPED';continue
  try:
   if p.suffix.lower() in text_ext or not p.suffix and st.st_size<1000000:
    with p.open('rb') as f:entry['sha256'],entry['lines']=stream_scan(str(p),f)
    entry['kind']='FULL_STREAM_TEXT_SCAN'
   if p.suffix.lower()=='.zip':
    with zipfile.ZipFile(p) as z:
     archive={'path':str(p),'members':[]};archives.append(archive)
     for m in z.infolist():
      member={'name':m.filename,'size':m.file_size};archive['members'].append(member)
      if any(x in m.filename.split('/') for x in ['data','models','envs','.git','third_party','external','source_clone']):continue
      if Path(m.filename).suffix.lower() in text_ext:
       try:
        with z.open(m) as f:member['sha256'],member['lines']=stream_scan(str(p)+'::'+m.filename,f)
       except Exception as e:errors.append([str(p)+'::'+m.filename,str(e)])
   elif n.endswith(('.tar.gz','.tgz','.tar')):
    with tarfile.open(p,'r:*') as z:
     archive={'path':str(p),'members':[]};archives.append(archive)
     for m in z:
      member={'name':m.name,'size':m.size};archive['members'].append(member)
      if any(x in m.name.split('/') for x in ['data','models','envs','.git','third_party','external','source_clone']):continue
      if m.isfile() and Path(m.name).suffix.lower() in text_ext:
       with z.extractfile(m) as f:member['sha256'],member['lines']=stream_scan(str(p)+'::'+m.name,f)
  except Exception as e:errors.append([str(p),str(e)])
summary={'label':'RETROSPECTIVE_EVIDENCE_RECOVERY','root':str(R),'files':len(inventory),'fully_streamed_text_files':sum(r['kind']=='FULL_STREAM_TEXT_SCAN' for r in inventory),'metadata_only_non_text_files':sum(r['kind']=='METADATA_ONLY' for r in inventory),'archives':len(archives),'execution_candidates_including_duplicates':len(raw_candidates),'exclusion_names':sorted(skip),'excluded_paths':excluded,'errors':errors,'gpu_loaded':False,'old_runners_executed':False,'finished_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
for name,data in [('FULL_EXPERIMENT_SCAN_SUMMARY.json',summary),('FULL_EXPERIMENT_FILE_INVENTORY.json',inventory),('FULL_EXPERIMENT_CONTENT_HITS.json',hits),('FULL_EXPERIMENT_ARCHIVE_INDEX.json',archives),('FULL_EXPERIMENT_EXECUTION_CANDIDATES.json',raw_candidates)]:
 with open(O/name,'x') as f:json.dump(data,f,ensure_ascii=False,indent=2)
print('FULL_EXPERIMENT_SCAN_DONE',summary['files'],summary['fully_streamed_text_files'],len(archives),len(raw_candidates),len(errors))
