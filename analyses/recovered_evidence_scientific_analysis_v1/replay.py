"""CPU replay with byte-identical original navigation references after append-only maintenance."""
import sys,json,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE));import analysis as a
def prepare(target):
 target=Path(target);assert not target.exists(),str(target);target.mkdir(parents=True)
 locks=json.loads((BASE/'SOURCE_INPUT_LOCK.json').read_text());updates={x['path']:x for x in json.loads((BASE/'NAVIGATION_MEMORY_UPDATE.json').read_text())['updates']};mapped=[]
 for r in locks:
  if r['path'] in updates:
   u=updates[r['path']];backup=Path(u['backup_path']);assert a.sha(backup)==r['sha256']==u['before_sha256'];assert a.sha(r['path'])==u['after_sha256'];mapped.append({'original_path':r['path'],'replay_path':str(backup),'same_original_sha256':r['sha256']});r['path']=str(backup)
 assert len(mapped)==3
 (target/'SOURCE_INPUT_LOCK.json').write_text(json.dumps(locks,ensure_ascii=False,indent=2));(target/'REPLAY_REFERENCE_MAPPING.json').write_text(json.dumps(mapped,indent=2));a.O=target;a.validate_inputs();return mapped
if __name__=='__main__':
 mapped=prepare(sys.argv[1]);print('BYTE_IDENTICAL_NAVIGATION_REFERENCE_MAPPING_PASS',len(mapped),flush=True)
 if len(sys.argv)<3 or sys.argv[2]!='--prepare-only':a.analyze()
