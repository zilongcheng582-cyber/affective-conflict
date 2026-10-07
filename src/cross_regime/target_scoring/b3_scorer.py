"""Patched B3 source-compatible scorer. Import and CPU tests never load Qwen.

No GPU execution CLI is provided while authoritative inputs are unresolved.
The scoring callable is ready for the separately authorized remote harness.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import b3_protocol as protocol
import source_teacher_forcing as source

ARMS={'A':'A_ONLY','T':'T_ONLY','V':'V_ONLY'}


def implementation_sha256():
    return protocol.object_sha256({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in (Path(__file__),Path(source.__file__),Path(protocol.__file__))})


def score_evidence(task, evidence, prompt, processor, model, torch, process_mm_info):
    """Only teacher-forced candidate scoring; no generation/evaluation methods."""
    identity=protocol.cache_identity(task)
    manifest_sha256=protocol.require_sha(task['manifest_sha256'])
    if task['scoring_code_sha256']!=implementation_sha256():
        raise ValueError('Scoring implementation hash mismatch')
    if protocol.object_sha256(prompt)!=task['prompt_content_sha256']:
        raise ValueError('Prompt template content mismatch')
    evidence=verify_evidence(task,evidence,evidence.get('dataset_root','.'))
    if set(task['candidate_sequence'])!=set(source.ONTOLOGY):
        raise ValueError('Assigned sequence differs from frozen source ontology')
    labels=list(task['candidate_sequence'])
    sample={'candidate_labels':labels,'candidate_sequence':labels,
            'candidate_sequence_id':task['candidate_sequence_id'],
            'text':evidence.get('text',''),'text_json_path':evidence.get('locator',''),
            'audio_path':evidence.get('audio_path',''),'silent_video_path':evidence.get('video_path',''),
            # Frozen source scorer requires a supported measurement label after
            # scoring. Its auxiliary sourceprob is discarded. Raw target label
            # is used only by the downstream measurement join, never in prompt.
            'text_emotion':source.ONTOLOGY[0],'audio_emotion':source.ONTOLOGY[0],
            'video_emotion':source.ONTOLOGY[0]}
    arm=ARMS[task['modality']]
    messages,_,_=source.build_messages(sample,arm,prompt)
    rendered,_=source.normalize_template_result(processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True))
    audios,images,videos=process_mm_info(messages,use_audio_in_video=False)
    inputs=processor(text=rendered,audio=audios,images=images,videos=videos,return_tensors='pt',padding=True,use_audio_in_video=False)
    inputs=inputs.to(model.device).to(model.dtype)
    scored=source.score_candidate_strings(rendered,inputs,sample,arm,processor,model,torch)
    by_label=scored['candidate_scores']
    probabilities=[by_label[x]['probability_mean_score_primary'] for x in labels]
    protocol.features(labels,probabilities,None)
    return {'status':'SUCCESS','inference_cache_key':identity['cache_key'],'cache_identity':identity['identity'],
            'manifest_sha256':manifest_sha256,
            'candidate_labels':labels,'candidate_sequence':labels,
            'candidate_sequence_id':task['candidate_sequence_id'],
            'candidate_probabilities':probabilities,
            'candidate_log_scores':[by_label[x]['mean_token_log_probability'] for x in labels],
            'candidate_sum_log_scores':[by_label[x]['sum_log_probability'] for x in labels],
            'candidate_probabilities_sum_sensitivity':[by_label[x]['probability_sum_score_sensitivity'] for x in labels],
            'normalized_entropy':scored['candidate_entropy_primary']['normalized_by_log7'],
            'top1_top2_margin':scored['candidate_top1_top2_margin_primary'],
            'model_generate_called':False}


def verify_evidence(task, evidence, dataset_root):
    """Resolve only an explicit evidence path, never guess or remap media."""
    if task['modality']=='T':
        actual=hashlib.sha256(evidence['text'].encode('utf-8')).hexdigest()
    else:
        key='audio_path' if task['modality']=='A' else 'video_path'
        path=Path(evidence[key])
        if not path.is_absolute(): path=Path(dataset_root)/path
        h=hashlib.sha256()
        with path.open('rb') as handle:
            for b in iter(lambda:handle.read(1<<20),b''): h.update(b)
        actual=h.hexdigest()
        evidence={**evidence,key:str(path)}
    if actual!=task['evidence_hash']: raise ValueError('Evidence hash mismatch')
    return evidence


def load_cache(path, tasks, manifest_sha256):
    expected={x['inference_cache_key']:x for x in tasks}
    result={}
    if not Path(path).exists(): return result
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        row=json.loads(line)
        key=row['inference_cache_key']
        if key in result or key not in expected: raise ValueError('Duplicate/unexpected resume cache key')
        protocol.validate_resume_record(row,expected[key],manifest_sha256)
        result[key]=row
    return result
