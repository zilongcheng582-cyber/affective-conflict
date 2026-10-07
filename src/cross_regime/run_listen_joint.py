from src.common.runtime import project_root, external_path, remap_namespace, relocate
#!/usr/bin/env python3
import argparse, re, csv, hashlib, json, os, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = project_root()
AUDIT = ROOT / 'audit/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED'
RESULTS = ROOT / 'results/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED'
MODEL_PATH = ROOT / 'models/Qwen2.5-Omni-7B'
MANIFEST = AUDIT / 'listen_native_manifest_source_aligned_v4.csv'
GATE_MANIFEST = AUDIT / 'listen_technical_gate_manifest_source_aligned_v4.csv'
SYS_PROMPT = 'You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech.'

def now(): return datetime.now(timezone.utc).isoformat()
def sha_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def extract_letter(text, n):
    # Corrected continuation-only parser; not a recertification of native V4.
    if not isinstance(text, str) or not 1 <= n <= 26: return None
    text = text.strip().upper()
    if text == 'OTHER': return None
    valid = {chr(65+i) for i in range(n)}
    # Standalone choice tokens only; words such as ANSWER cannot supply A.
    matches = re.findall(r'(?<![A-Z0-9])[A-Z](?![A-Z0-9])', text)
    choices = set(matches) & valid
    return next(iter(choices)) if len(choices) == 1 else None

def decode_continuation(output, inputs, processor):
    import torch
    input_ids = inputs['input_ids']
    input_length = input_ids.shape[1]
    if output.shape[1] < input_length or not torch.equal(output[:, :input_length], input_ids):
        raise ValueError('generated sequence does not contain the exact input prefix')
    continuation_ids = output[:, input_length:]
    decoded = processor.batch_decode(continuation_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    return decoded[0].strip() if decoded else ''

def load_rows(path):
    with open(path, encoding='utf-8', newline='') as f: return list(csv.DictReader(f))
def load_model():
    import torch
    from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
    from qwen_omni_utils import process_mm_info
    model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
        str(MODEL_PATH), torch_dtype=torch.bfloat16, device_map='auto', attn_implementation='flash_attention_2')
    processor = Qwen2_5OmniProcessor.from_pretrained(str(MODEL_PATH))
    return model, processor, process_mm_info
def run_one(row, model, processor, process_mm_info, manifest_hash):
    import numpy as np
    import soundfile as sf
    import torch
    t0=time.time(); rec={
        'run_id':'LISTEN_CONTINUATION_CORRECTED_PATCH_V1', 'manifest_row_id':row['manifest_row_id'],
        'condition':row['condition'], 'input_mode':row['input_mode'], 'dataset_row_index':int(row['dataset_row_index']),
        'original_sample_id':row['original_sample_id'], 'prompt_hash':row['prompt_hash'],
        'expected_letter':row['expected_letter'], 'expected_label':row['expected_label'],
        'choices_after_shuffle':row['choices_after_shuffle'], 'audio_hash':row['audio_hash'],
        'transcription_hash':row['transcription_hash'], 'manifest_hash':manifest_hash,
        'start_time':now(), 'model_revision':str(MODEL_PATH), 'technical_status':'FAIL',
        'scientific_output_evaluated':False, 'raw_generated_sequence':None, 'assistant_text':None,
        'parsed_letter':None, 'parse_status':'NOT_RUN', 'error_type':None, 'error_message':None,
    }
    try:
        if torch.cuda.is_available(): torch.cuda.reset_peak_memory_stats()
        mode=row['input_mode']
        if mode in ('audio','audio_and_text'):
            audio, sr = sf.read(row['audio_path'], dtype='float32', always_2d=False)
            if audio.ndim > 1: audio = np.mean(audio, axis=1).astype(np.float32)
            rec['audio_source_sampling_rate']=int(sr); rec['audio_num_samples']=int(audio.shape[0]); rec['audio_enabled']=True
            if mode == 'audio': user_text=row['prompt']
            else: user_text=f"Transcription: {row['transcription']}\n\n{row['prompt']}"
            messages=[{'role':'system','content':[{'type':'text','text':SYS_PROMPT}]}, {'role':'user','content':[{'type':'audio','audio':audio},{'type':'text','text':user_text}]}]
            text=processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            audios, images, videos = process_mm_info(messages, use_audio_in_video=True)
            inputs=processor(text=text,audio=audios,images=images,videos=videos,return_tensors='pt',padding=True,use_audio_in_video=True)
            inputs=inputs.to(model.device)
            output=model.generate(**inputs,use_audio_in_video=True,return_audio=False,max_new_tokens=3,do_sample=False,num_beams=1,pad_token_id=processor.tokenizer.eos_token_id)
        elif mode == 'text':
            rec['audio_enabled']=False
            messages=[{'role':'system','content':[{'type':'text','text':SYS_PROMPT}]}, {'role':'user','content':[{'type':'text','text':f"Transcription: {row['transcription']}\n\n{row['prompt']}"}]}]
            text=processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            audios, images, videos = process_mm_info(messages, use_audio_in_video=False)
            inputs=processor(text=text,audio=audios,images=images,videos=videos,return_tensors='pt',padding=True,use_audio_in_video=False)
            inputs=inputs.to(model.device)
            output=model.generate(**inputs,use_audio_in_video=False,return_audio=False,max_new_tokens=3)
        else: raise ValueError(f'unknown input_mode {mode}')
        decoded=processor.batch_decode(output,skip_special_tokens=True,clean_up_tokenization_spaces=False)
        full=decoded[0] if decoded else ''
        assistant=decode_continuation(output, inputs, processor)
        choices=json.loads(row['choices_after_shuffle']); parsed=extract_letter(assistant,len(choices))
        rec.update({'raw_generated_sequence':full,'assistant_text':assistant,'parsed_letter':parsed,'parse_status':'VALID' if parsed else ('OTHER' if assistant.upper() == 'OTHER' else 'PARSE_FAIL'), 'parser_version':'CONTINUATION_ONLY_PATCH_V1', 'raw_full_text_role':'LEGACY_DIAGNOSTIC','technical_status':'PASS','generation_success':True})
    except Exception as e:
        rec.update({'generation_success':False,'error_type':type(e).__name__,'error_message':str(e),'traceback':traceback.format_exc()})
    finally:
        if torch.cuda.is_available():
            rec['peak_gpu_memory_allocated_mb']=torch.cuda.max_memory_allocated()/1024**2
            rec['peak_gpu_memory_reserved_mb']=torch.cuda.max_memory_reserved()/1024**2
        rec['wall_time_sec']=time.time()-t0; rec['end_time']=now()
    return rec
def write_jsonl(path, recs):
    with open(path,'w',encoding='utf-8') as f:
        for r in recs: f.write(json.dumps(r,ensure_ascii=False,default=str)+'\n')
def configure_paths(args):
    global ROOT, AUDIT, RESULTS, MODEL_PATH, MANIFEST, GATE_MANIFEST
    ROOT = args.data_root.resolve()
    AUDIT = args.output.resolve() / 'audit'
    RESULTS = args.output.resolve() / 'results'
    MODEL_PATH = args.model_path or ROOT / 'models/Qwen2.5-Omni-7B'
    if not args.input: raise ValueError('--input must explicitly select the frozen gate/full manifest')
    MANIFEST = GATE_MANIFEST = args.input

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--gate-only',action='store_true'); ap.add_argument('--full',action='store_true')
    ap.add_argument('--data-root',type=Path,default=ROOT); ap.add_argument('--model-path',type=Path)
    ap.add_argument('--input',type=Path); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    configure_paths(args)
    if args.gate_only == args.full: raise SystemExit('choose exactly one of --gate-only or --full')
    AUDIT.mkdir(parents=True,exist_ok=True); RESULTS.mkdir(parents=True,exist_ok=True); mh=sha_file(MANIFEST)
    rows=load_rows(GATE_MANIFEST if args.gate_only else MANIFEST)
    if args.gate_only and len(rows)!=6: raise SystemExit(f'gate manifest rows={len(rows)}')
    if args.full:
        gate=json.load(open(AUDIT/'technical_gate_summary_source_aligned_v4.json'))
        if gate.get('status')!='PASS': raise SystemExit('technical gate is not PASS; full run refused')
        if len(rows)!=1149: raise SystemExit(f'full manifest rows={len(rows)}')
    model, processor, pmm = load_model()
    out=[]
    for i,row in enumerate(rows):
        print(f'RUN {i+1}/{len(rows)} {row["manifest_row_id"]}',flush=True)
        r=run_one(row,model,processor,pmm,mh); out.append(r)
        target=RESULTS/'technical_gate_outputs_source_aligned_v4.jsonl' if args.gate_only else RESULTS/'listen_native_raw_outputs_source_aligned_v4.jsonl'
        with open(target,'a' if i else 'w',encoding='utf-8') as f: f.write(json.dumps(r,ensure_ascii=False,default=str)+'\n')
        if args.gate_only: print(json.dumps({'id':r['manifest_row_id'],'status':r['technical_status'],'error':r['error_message']},ensure_ascii=False),flush=True)
    if args.gate_only:
        passed=all(r.get('technical_status')=='PASS' and r.get('generation_success') for r in out)
        summary={'status':'PASS' if passed else 'FAIL','records':len(out),'successful':sum(bool(r.get('generation_success')) for r in out),'parser_executed':sum(r.get('parse_status')!='NOT_RUN' for r in out),'created_at':now(),'manifest_hash':mh,'scientific_output_evaluated':False}
        with open(AUDIT/'technical_gate_summary_source_aligned_v4.json','w') as f: json.dump(summary,f,indent=2)
        print(json.dumps(summary,indent=2),flush=True)
    else:
        summary={'status':'COMPLETE' if len(out)==1149 and all(r.get('technical_status')=='PASS' for r in out) else 'PARTIAL_OR_FAILED','records':len(out),'successful':sum(bool(r.get('generation_success')) for r in out),'parse_valid':sum(r.get('parse_status')=='VALID' for r in out),'created_at':now(),'manifest_hash':mh,'scientific_output_evaluated':False}
        with open(AUDIT/'listen_execution_summary_local_v3.json','w') as f: json.dump(summary,f,indent=2)
        print(json.dumps(summary,indent=2),flush=True)
remap_namespace(globals())

if __name__=='__main__': main()

