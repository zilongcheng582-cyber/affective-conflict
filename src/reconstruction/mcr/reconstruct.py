#!/usr/bin/env python3
"""POSTHOC_RECONSTRUCTION_IMPLEMENTATION

This is a validated post-hoc reconstruction implementation.
It is not claimed to be the original historical producer.
It reconstructs the historical scientific artifact from preserved
authoritative upstream assets and is validated against preserved
authoritative downstream artifacts.

Generation reads raw SER/audio and frozen prompt constants only. Historical
targets and predictions are not generation inputs. Validation is external.
"""
import argparse,collections,csv,hashlib,json,re,wave
from pathlib import Path

RAW_REL='data/MCR-Bench/MCR-Bench/SER/SER.json'
RAW_SHA='58aff644175739b142f46ea9f47c32f9230f3cf7fc033dfdd4e8750ee3e6b880'
LABELS={'sad','happy','fearful','angry','surprised','disgusted','neutral'}
NATIVE_FIELDS=['sample_id','original_record_index','audio','audio_path','audio_sha256','gt','competitor_emotion','competitor_mapping_status','faithful','adversarial','irrelevant','neutral','duplicate_group_status']
MAPPING_FIELDS=['sample_id','gt','adversarial_text','adversarial_description_segment','explicit_competitor_label','mapping_status']
DUP_FIELDS=['duplicate_group_status','audio','record_index_0based','record_index_1based','sample_id','gt','faithful','adversarial','irrelevant','neutral','resolved_audio_path','basename','extension','file_size_bytes','duration_seconds','sha256','audio_identity_exact_within_group','group_size','group_gt_values','neutral_question_equal_within_group','faithful_target_values','adversarial_target_values','irrelevant_description_values','faithful_or_adversarial_speaker_event_marker','audio_multiple_utterance_evidence']

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def description(text):
    if text.count('Description:')!=1:raise ValueError('Description marker must be unique')
    tail=text.split('Description:',1)[1]
    if '\nClassify ' not in tail:raise ValueError('Missing description/instruction boundary')
    return tail.split('\nClassify ',1)[0].strip()
def emotion(text):
    segment=description(text)
    match=re.fullmatch(r'This audio expresses ([a-z]+) emotion\.',segment)
    if not match or match[1] not in LABELS:raise ValueError('Unsupported explicit source emotion')
    return match[1]
def load_raw(root):
    path=root/RAW_REL
    if sha(path)!=RAW_SHA:raise ValueError('Raw source hash differs from frozen binding')
    rows=json.loads(path.read_text())
    if len(rows)!=1000:raise ValueError('Unexpected raw population')
    groups=collections.defaultdict(list)
    for i,row in enumerate(rows):
        if row['gt'] not in LABELS or emotion(row['faithful'])!=row['gt']:raise ValueError('Raw label contract failed')
        ref=Path(row['audio'])
        if ref.is_absolute() or '..' in ref.parts:raise ValueError('Unsafe raw audio reference')
        groups[row['audio']].append(i)
    return rows,dict(groups)
def legacy_ids(raw,groups):
    result={}
    for ref,indices in groups.items():
        for ordinal,i in enumerate(indices,1):
            result[i]=Path(ref).stem+(f'__{ordinal:04d}' if len(indices)>1 else '')
    return result
def duplicate_status(raw,indices):
    if len(indices)==1:return 'UNIQUE'
    # Native consumer enum names differ from the investigation's shorter names.
    # This changes the schema spelling only; classification is still raw-derived.
    return 'SAME_GT_DUPLICATE' if len({raw[i]['gt'] for i in indices})==1 else 'CONFLICTING_GT_DUPLICATE'
def native(root,raw,groups):
    hashes={ref:sha(root/Path(RAW_REL).parent/ref) for ref in groups}
    out=[]
    for i,row in enumerate(raw):
        out.append(dict(sample_id=f'MCR_SER_{i}',original_record_index=i,audio=row['audio'],audio_path=str(root/Path(RAW_REL).parent/row['audio']),audio_sha256=hashes[row['audio']],gt=row['gt'],competitor_emotion=emotion(row['adversarial']),competitor_mapping_status='EXACT',**{k:row[k] for k in ['faithful','adversarial','irrelevant','neutral']},duplicate_group_status=duplicate_status(raw,groups[row['audio']])))
    return out
def mapping(raw,groups):
    ids=legacy_ids(raw,groups)
    return [dict(sample_id=ids[i],gt=r['gt'],adversarial_text=r['adversarial'],adversarial_description_segment=description(r['adversarial']),explicit_competitor_label=emotion(r['adversarial']),mapping_status='EXACT') for i,r in enumerate(raw)]
def duplicates(root,raw,groups):
    out=[];ids=legacy_ids(raw,groups)
    for ref,indices in sorted(groups.items()):
        if len(indices)==1:continue
        p=root/Path(RAW_REL).parent/ref
        with wave.open(str(p),'rb') as wav:duration=wav.getnframes()/wav.getframerate()
        gt=sorted({raw[i]['gt'] for i in indices});faith=sorted({emotion(raw[i]['faithful']) for i in indices});adv=sorted({emotion(raw[i]['adversarial']) for i in indices});irrelevant=sorted({description(raw[i]['irrelevant']) for i in indices})
        # Explicit source emotion templates contain no speaker/event claim.
        marker=any(re.search(r'\b(speaker|speaking|man|woman|person|event)\b',description(raw[i][k]),re.I) is not None for i in indices for k in ['faithful','adversarial'])
        for i in indices:
            r=raw[i];out.append(dict(duplicate_group_status='SAME_GT' if len(gt)==1 else 'CONFLICTING_GT',audio=ref,record_index_0based=i,record_index_1based=i+1,sample_id=ids[i],gt=r['gt'],**{k:r[k] for k in ['faithful','adversarial','irrelevant','neutral']},resolved_audio_path=str(p),basename=p.name,extension=p.suffix,file_size_bytes=p.stat().st_size,duration_seconds=duration,sha256=sha(p),audio_identity_exact_within_group=True,group_size=len(indices),group_gt_values='|'.join(gt),neutral_question_equal_within_group=len({raw[j]['neutral'] for j in indices})==1,faithful_target_values='|'.join(faith),adversarial_target_values='|'.join(adv),irrelevant_description_values=' || '.join(irrelevant),faithful_or_adversarial_speaker_event_marker=bool(marker),audio_multiple_utterance_evidence='UNRESOLVED_FROM_METADATA'))
    return out
def arbitration(root,raw,groups):
    selected={min(indices) for indices in groups.values() if len({raw[i]['gt'] for i in indices})==1}
    out=[]
    for i,r in enumerate(native(root,raw,groups)):
        if i not in selected:continue
        if len(groups[r['audio']])>1:r['duplicate_group_status']='SAME_GT_REPRESENTATIVE'
        out.append(r)
    if len(out)!=909:raise ValueError('Documented arbitration population changed')
    return out
def write_csv(path,rows,fields):
    with path.open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--gap',choices=['G04','G05','G06','G07'],required=True);ap.add_argument('--reconstruct',action='store_true',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True);raw,groups=load_raw(args.root)
    funcs={'G04':(lambda:native(args.root,raw,groups),NATIVE_FIELDS),'G05':(lambda:mapping(raw,groups),MAPPING_FIELDS),'G06':(lambda:duplicates(args.root,raw,groups),DUP_FIELDS),'G07':(lambda:arbitration(args.root,raw,groups),NATIVE_FIELDS)}
    fun,fields=funcs[args.gap];rows=fun()
    if fields:write_csv(args.output,rows,fields)
    else:
        with args.output.open('x',encoding='utf-8') as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
    print(json.dumps({'gap_id':args.gap,'rows':len(rows),'SHA256':sha(args.output),'status':'GENERATED'}))
if __name__=='__main__':main()
