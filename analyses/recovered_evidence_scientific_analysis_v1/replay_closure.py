import sys,json,hashlib,zipfile
from pathlib import Path
O=Path('/root/autodl-tmp/affective-conflict-recovered-science-v1');sys.path.insert(0,str(O));import analysis as a
# Before updating only replay documentation/packaging, ensure the prior sealed archive is intact.
for line in (O/'SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ',1);assert a.sha(O/n)==h,n
import replay
mapping=replay.prepare(O/'replay_after_navigation_validation')
assert len(mapping)==3
a.O=O
p=O/'REPLAY_INSTRUCTIONS.md';old=p.read_bytes();(O/'REPLAY_INSTRUCTIONS_BEFORE_NAVIGATION_FIX.md').write_bytes(old)
text=p.read_text();start=text.index('mkdir replay_new');end=text.index("python3 -c 'import hashlib",start)
text=text[:start]+'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 replay.py '+str(O)+'/replay_new > replay_new.log 2>&1\n'+text[end:]
text+='\nAfter the authorized three navigation-only appends, `replay.py` maps exactly those references to saved byte-identical original docs. It verifies before/after hashes and never restores/rewrites the historical docs. All scientific inputs retain their original paths/hashes. The underlying statistical code, support sets and seeds are unchanged. `replay.py PATH --prepare-only` validated all original input bytes after this mapping; primary18/secondary2 numeric repeat checks remain valid.\n'
p.write_text(text)
prov=a.read(O/'RUN_PROVENANCE.json');prov['replay_after_navigation_validation']={'passed':True,'byte_identical_references':mapping,'statistical_code_modified':False,'numeric_definitions_or_outputs_modified':False};prov['actual_code_sha256']={str(p):a.sha(p) for p in O.glob('*.py')};a.save('RUN_PROVENANCE.json',prov)
ver=a.read(O/'FINAL_VERIFICATION.json');ver['replay_after_navigation_original_bytes_pass']=True;a.save('FINAL_VERIFICATION.json',ver)
paths=[p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.transfer') and p.name not in ['SHA256SUMS.txt','RECOVERED_SCIENCE_REPORTS_V1.zip','REPLAY_CLOSURE_DELTA.zip']]
(O/'SHA256SUMS.txt').write_text(''.join(a.sha(p)+'  '+str(p.relative_to(O))+'\n' for p in sorted(paths)))
for line in (O/'SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ',1);assert a.sha(O/n)==h,n
# Repackage exact same previously delivered members plus the validated replay driver/closure code.
oldzip=O/'RECOVERED_SCIENCE_REPORTS_V1.zip'
with zipfile.ZipFile(oldzip) as z:names=z.namelist()
names=list(dict.fromkeys(names+['replay.py','replay_closure.py','REPLAY_INSTRUCTIONS_BEFORE_NAVIGATION_FIX.md']))
with zipfile.ZipFile(oldzip,'w',zipfile.ZIP_DEFLATED) as z:
 for n in names:z.write(O/n,n)
receipt=json.loads(Path('/tmp/recovered_science_final_receipt.json').read_text());receipt.update({'hash_manifest_sha256':a.sha(O/'SHA256SUMS.txt'),'bundle_sha256':a.sha(oldzip),'bundle_bytes':oldzip.stat().st_size,'replay_after_navigation_original_bytes_pass':True})
Path('/tmp/recovered_science_final_receipt.json').write_text(json.dumps(receipt,indent=2))
delta=['replay.py','replay_closure.py','REPLAY_INSTRUCTIONS.md','REPLAY_INSTRUCTIONS_BEFORE_NAVIGATION_FIX.md','RUN_PROVENANCE.json','FINAL_VERIFICATION.json','SHA256SUMS.txt']
with zipfile.ZipFile(O/'REPLAY_CLOSURE_DELTA.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in delta:z.write(O/n,n)
print('REPLAY_AFTER_NAVIGATION_CLOSURE_PASS',json.dumps(receipt))
