import csv,json,hashlib,collections,re
from pathlib import Path
R=Path('/root/autodl-tmp/affective-conflict');O=Path('/root/autodl-tmp/affective-conflict-reconciliation-v2');P=json.loads((O/'MCR_POOL_AND_DUPLICATE_AUDIO_AUDIT_V2.json').read_text())
for name,info in P['pool_schemas'].items():
 rs=list(csv.DictReader(open(R/'audit'/name,encoding='utf-8-sig')))
 field=next(k for k in ['source_index','original_record_index','record_index_0based'] if k in rs[0])
 info['source_indices']=[int(r[field]) for r in rs];info['source_index_field']=field
sens=set(P['pool_schemas']['mcr_ser_sensitivity_pool_924.csv']['source_indices'])
for r in P['excluded_91']:r['frozen_pool_reason']='SAME_GT_DUPLICATE_REPRESENTATIVE_REMOVED' if r['source_index'] in sens else 'CONFLICTING_GT_AUDIO_GROUP_EXCLUDED'
P['frozen_exclusion_reason_counts']=dict(collections.Counter(r['frozen_pool_reason'] for r in P['excluded_91']))
join=list(csv.DictReader(open(O/'MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.csv')));ctrl=[r for r in join if r['controlled_included']=='True'];P['controlled_distinct_audio_paths']=len({r['native_audio_path'] for r in ctrl});P['controlled_distinct_audio_hashes']=len({r['native_audio_sha256'] for r in ctrl});P['native_distinct_audio_paths']=len({r['native_audio_path'] for r in join})
P['controlled_source_indices_equal_frozen_909']={int(r['source_index']) for r in ctrl}==set(P['pool_schemas']['mcr_ser_arbitration_pool_909.csv']['source_indices'])
byindex={int(r['source_index']):r for r in join};P['frozen_pool_hash_checks']={}
for name in ['mcr_ser_native_pool_1000.csv','mcr_ser_arbitration_pool_909.csv','mcr_ser_sensitivity_pool_924.csv']:
 rs=list(csv.DictReader(open(R/'audit'/name,encoding='utf-8-sig')));key=P['pool_schemas'][name]['source_index_field']
 P['frozen_pool_hash_checks'][name]={'rows':len(rs),'stored_distinct_audio_hashes':len({r['audio_sha256'] for r in rs}),'stored_hash_matches_current':sum(r['audio_sha256']==byindex[int(r[key])]['native_audio_sha256'] for r in rs)}
(O/'MCR_POOL_AND_DUPLICATE_AUDIO_AUDIT_V2.json').write_text(json.dumps(P,indent=2,ensure_ascii=False))
plans=[]
for relative in ['audit/QWEN25_LISTEN_NATIVE_V1/listen_native_manifest.csv','audit/QWEN25_LISTEN_NATIVE_V2_CURRENT_RELEASE/listen_current_release_manifest_v2.csv','audit/listen_pilot_100.csv']:
 p=R/relative
 if not p.exists():continue
 with open(p) as f:rows=list(csv.DictReader(f))
 plans.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'physical_csv_rows':len(rows),'records':sum(bool(r.get('condition') or r.get('sample_id')) for r in rows),'stage':'BLOCKED_PLACEHOLDER_NOT_TRIAL' if len(rows)==1 and rows[0].get('manifest_status') else 'PLANNED_NOT_EXECUTION_EVIDENCE','conditions':dict(collections.Counter(r.get('condition',r.get('experiment_type')) for r in rows)),'placeholder_example':rows[0] if len(rows)==1 else None})
(O/'LISTEN_PLANNED_VERSUS_EXECUTED_STAGE_V2.json').write_text(json.dumps(plans,indent=2))
print('SCOPE_FINISH',P['frozen_exclusion_reason_counts'],'PATHS_HASHES',P['native_distinct_audio_paths'],P['controlled_distinct_audio_paths'],P['controlled_distinct_audio_hashes'],'LISTEN_PLANS',[(Path(r['path']).name,r['records']) for r in plans])
