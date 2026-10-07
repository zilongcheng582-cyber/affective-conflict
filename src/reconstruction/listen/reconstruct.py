#!/usr/bin/env python3
"""POSTHOC_RECONSTRUCTION_IMPLEMENTATION

This is a validated post-hoc reconstruction implementation.
It is not claimed to be the original historical producer.
It reconstructs the historical scientific artifact from preserved
authoritative upstream assets and is validated against preserved
authoritative downstream artifacts.

CPU-only raw parquet replay of official experiment/choice control flow.
No checkpoint, prediction, downstream manifest or join is read.
"""
import argparse,csv,hashlib,json,os,random,sys
from pathlib import Path
import pyarrow.parquet as pq
ADDITIONAL=['neutral','sadness','surprise','happiness','fear','anger','excitement','frustration']
SYSTEM='You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech.'
SHAS=['f6ceaeb135f8338346ad6ce105cb48ed4863fb92e87b822964372280f5eb6475','f721d9528f07dd21052443f3a356ac01a2d0949cb7e5056fc3e7e5bd2e6df811','6d102f09616fee959ab52009618b5ecf79fd7c6e19f835937ac478dfc0ef3470']
def sha_text(s):return hashlib.sha256(s.encode()).hexdigest()
def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def prompt(row,mode,choices):
    head={'text':'Read the transcription and classify the emotion.','audio':'Listen to the audio and classify the emotion.','audio_and_text':'Listen to the audio and read the transcription, then classify the emotion.'}[mode]
    opts='\n'.join(f'{chr(65+i)}. {c}' for i,c in enumerate(choices))
    letters=', '.join(chr(65+i) for i in range(len(choices)))
    return f'{head}\n\n{row["question"]}\n\n{opts}\n\nRespond with only the letter ({letters}):'
def shuffle(row,condition,mode):
    choices=list(row.get('choices') or [])
    correct=row.get('explicit_emotion',row['answer']) if mode=='text' and condition in ['2A','3A'] else row['answer']
    if not correct or not correct.strip():return None
    all_choices=list(set(choices+ADDITIONAL)) if condition in ['3A','3B','3C'] else choices
    if correct not in all_choices:return None
    position=all_choices.index(correct);indices=list(range(len(all_choices)));random.shuffle(indices)
    return choices,[all_choices[k] for k in indices],correct,chr(65+indices.index(position))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--reconstruct',required=True,action='store_true');args=ap.parse_args()
    if os.environ.get('PYTHONHASHSEED')!='42' or sys.version_info[:2]!=(3,12):raise RuntimeError('Historical set ordering requires Python 3.12 and process-start PYTHONHASHSEED=42')
    by_type={};index=0
    files=sorted((args.root/'data/LISTEN/data').glob('train-*.parquet'))
    if len(files)!=3:raise ValueError('Expected exactly three train shards')
    columns=['id','question','answer','choices','transcription','experiment_type','explicit_emotion']
    for file,expected in zip(files,SHAS):
        if sha_file(file)!=expected:raise ValueError('Raw parquet binding mismatch')
        pf=pq.ParquetFile(file)
        for rg in range(pf.num_row_groups):
            metadata=pf.read_row_group(rg,columns=columns).to_pylist()
            selected={j for j,r in enumerate(metadata) if r['experiment_type'] in ['3A','3B']}
            audio_hashes={};offset=0
            # Bound CPU memory: never materialize a complete audio row group.
            if selected:
                for batch in pf.iter_batches(row_groups=[rg],columns=['audio'],batch_size=64):
                    for local,audio in enumerate(batch.column('audio').to_pylist()):
                        j=offset+local
                        if j not in selected:continue
                        b=(audio or {}).get('bytes') or b''
                        if not b:raise ValueError('Selected row missing raw media bytes')
                        audio_hashes[j]=hashlib.sha256(b).hexdigest()
                    offset+=batch.num_rows
            for j,row in enumerate(metadata):
                row=dict(row);typ=row['experiment_type'];row['_index']=index;row['_file']=str(file);row['_rg']=rg;row['_j']=j
                if typ in ['3A','3B']:
                    row['_audio_hash']=audio_hashes[j]
                by_type.setdefault(typ,[]).append(row);index+=1
    if index!=11507:raise ValueError('Source train population changed')
    random.seed(42);records=[];counts={};pre=0
    stream=[('1','text'),('1','audio'),('1','audio_and_text'),('2A','text'),('2B','audio'),('2C','audio_and_text'),('3A','text'),('3B','audio'),('3C','audio_and_text')]
    for condition,mode in stream:
        source=by_type['2B' if condition=='2C' else '3B' if condition=='3C' else condition];n=0
        for i,row in enumerate(source):
            shuffled=shuffle(row,condition,mode)
            if shuffled is None:
                if condition in ['3A','3B','3C']:raise ValueError('Unexpected skip in documented complete population')
                continue
            n+=1
            if condition not in ['3A','3B','3C']:pre+=1;continue
            before,after,correct,letter=shuffled;ah=row['_audio_hash'];text=str(row.get('transcription','') or '');p=prompt(row,mode,after)
            # Cache filename is derived from authoritative embedded media, never target IDs.
            audio_path=args.root/'audit/QWEN25_LISTEN_NATIVE_V3/input_audio'/f'{ah}.wav'
            if not audio_path.is_file() or sha_file(audio_path)!=ah:raise ValueError('Preserved raw-media cache does not match embedded audio')
            records.append(dict(manifest_row_id=f'{condition}_{i:04d}',condition=condition,input_mode=mode,condition_index=i,dataset_row_index=row['_index'],original_sample_id=str(row['id']),audio_path=str(audio_path),audio_hash=ah,transcription=text,transcription_hash=sha_text(text),question=str(row['question']),choices_before_shuffle=json.dumps(before,ensure_ascii=False,separators=(',',':')),choices_after_shuffle=json.dumps(after,ensure_ascii=False,separators=(',',':')),expected_label=correct,expected_letter=letter,prompt=p,prompt_hash=sha_text(p),system_prompt=SYSTEM,system_prompt_hash=sha_text(SYSTEM),source_parquet=row['_file'],source_row_group=row['_rg'],source_row_in_group=row['_j'],dataset_revision='f6397b5bfedd85ae41b80dac13e95bb55adf0a35',repo_commit='32966584488bd3b3c67a150bd55f1f18ca09ef76',PYTHONHASHSEED='42',python_random_seed=42))
        counts[condition+'_'+mode]=n
    if pre!=17190 or len(records)!=1149:raise ValueError('Official full-stream shuffle/population contract differs')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    print(json.dumps(dict(gap_id='G10',rows=len(records),SHA256=sha_file(args.output),preceding_valid_shuffles=pre,experiment_counts=counts,python=sys.version,hashseed=os.environ['PYTHONHASHSEED'])))
if __name__=='__main__':main()
