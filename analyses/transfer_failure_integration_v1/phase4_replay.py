"""CPU-only repeat to a new directory; immutable references, no model fits."""
import sys,json,shutil,pathlib
BASE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(BASE));import phase4_transfer as a;import phase4_supplement as b
target=pathlib.Path(sys.argv[1]);assert not target.exists();target.mkdir()
for n in ['PHASE4_SOURCE_LOCK.json','03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv','intermediate/CAMER_ITEM_ELIGIBILITY_IDENTITY.csv','intermediate/MCR_NATIVE_CONTROLLED_PER_ITEM_JOIN.csv']:
 p=target/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/n,p)
nav=BASE/'PHASE4_NAVIGATION_MEMORY_UPDATE.json'
if nav.exists():
 updates={x['path']:x for x in json.loads(nav.read_text())['updates']};locks=json.loads((target/'PHASE4_SOURCE_LOCK.json').read_text())
 for x in locks:
  if x['path'] in updates:
   u=updates[x['path']];assert a.sha(u['backup_path'])==x['sha256'];assert a.sha(x['path'])==u['after_sha256'];x['path']=u['backup_path']
 (target/'PHASE4_SOURCE_LOCK.json').write_text(json.dumps(locks,indent=2))
a.O=target;a.analyze();b.main()
files=['04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv','phase4_numeric/TRANSFER_RESULTS.json','phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv','phase4_numeric/TRANSFER_RECOVERED_ROW_LINKAGE.csv','phase4_numeric/TRANSFER_FROZEN_LOGIT_DECOMPOSITION.csv','phase4_numeric/LISTEN_NATIVE_LABEL_SUPPORT_AND_OTHER.csv']
checks=[{'path':n,'first_sha256':a.sha(BASE/n),'replay_sha256':a.sha(target/n),'match':a.sha(BASE/n)==a.sha(target/n)} for n in files]
assert all(x['match'] for x in checks)
(target/'PHASE4_REPLAY_CHECK.json').write_text(json.dumps({'status':'PASS','CPU_only':True,'files':checks},indent=2))
print('PHASE4_REPEAT_EXACT_HASH_PASS',len(checks),flush=True)
