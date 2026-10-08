"""Content-based validation, independent of historical path-based sample selection."""
import argparse,csv,hashlib
from collections import defaultdict
from pathlib import Path

def content_groups(records):
    groups=defaultdict(list)
    for row in records:
        digest=row.get('actual_audio_sha256') or row.get('audio_sha256')
        if not digest or len(digest)!=64:raise ValueError('Verified audio SHA256 required')
        groups[digest].append(row)
    result=[]
    for digest,group in sorted(groups.items()):
        if len(group)<2:continue
        labels=sorted({r['gt'] for r in group})
        paths={r.get('audio_relative_path',r.get('audio','')) for r in group}
        for row in group:
            result.append({**row,'content_duplicate_group_sha256':digest,'group_size':len(group),
                           'group_gt_values':'|'.join(labels),'conflicting_GT':len(labels)>1,
                           'different_paths_same_content':len(paths)>1,
                           'warning':'CONFLICTING_GT_CONTENT_DUPLICATE' if len(labels)>1 else 'SAME_GT_CONTENT_DUPLICATE',
                           'historical_sample_removed':False,'analysis_origin':'POST_AUDIT_REANALYSIS'})
    return result

def audit_audio_files(raw,audio_root):
    records=[];root=Path(audio_root).resolve()
    for index,row in enumerate(raw):
        p=(root/row['audio']).resolve()
        if not p.is_relative_to(root):raise ValueError('Unsafe audio reference')
        h=hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
        records.append({'sample_id':f'MCR_SER_{index}','gt':row['gt'],'audio_relative_path':row['audio'],
                        'actual_audio_sha256':h.hexdigest(),'hash_basis':'RECOMPUTED_WAV_BYTES'})
    return content_groups(records)

def write_audit(path,rows):
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        fields=list(dict.fromkeys(k for r in rows for k in r)) or ['sample_id','content_duplicate_group_sha256','warning']
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--identity-csv',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with a.identity_csv.open(encoding='utf-8-sig',newline='') as f:records=list(csv.DictReader(f))
    write_audit(a.output,content_groups(records))
if __name__=='__main__':main()
