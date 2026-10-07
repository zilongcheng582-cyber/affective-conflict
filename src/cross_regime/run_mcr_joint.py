from __future__ import annotations
from src.common.runtime import project_root, external_path, remap_namespace, relocate


import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


from src.common.benchmarks.mcr_ser_parser_v1 import parse_mcr_ser_response  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open('r', encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def render_prompt(item: dict[str, Any], prompt_spec: dict[str, Any]) -> str:
    instruction = prompt_spec['classification_instruction']
    candidates = ', '.join(item['candidate_sequence'])
    return f'{instruction}\nCandidates: {candidates}'


def build_conversation(item: dict[str, Any], prompt_spec: dict[str, Any], audio_root: Path) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    if item['arm'] == 'T_THEN_A':
        if item['text_evidence'] is not None:
            content.append({'type': 'text', 'text': item['text_evidence']})
        if item['audio'] is not None:
            content.append({'type': 'audio', 'audio': str(audio_root / item['audio'])})
    else:
        if item['audio'] is not None:
            content.append({'type': 'audio', 'audio': str(audio_root / item['audio'])})
        if item['text_evidence'] is not None:
            content.append({'type': 'text', 'text': item['text_evidence']})
    content.append({'type': 'text', 'text': render_prompt(item, prompt_spec)})
    return [{'role': 'user', 'content': content}]


def resume_contract(manifest, prompt_spec, execution_config, artifact_identity=None):
    payload=json.dumps({'manifest':manifest,'prompt':prompt_spec,'config':execution_config,
                        'artifact_identity': artifact_identity or {},
                        'model_revision': execution_config.get('model_revision'),
                        'processor_revision': execution_config.get('processor_revision')},sort_keys=True,separators=(',',':'),ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf8')).hexdigest()

def existing_keys(output_path: Path, expected_items=None, contract_sha=None) -> set[str]:
    if not output_path.exists(): return set()
    if expected_items is None or contract_sha is None: raise ValueError('manifest/config identity required for resume')
    latest={}
    for row in load_jsonl(output_path):
        if not isinstance(row,dict) or not row.get('record_key'): raise ValueError('damaged output row; reconcile before resume')
        if row['record_key'] in latest: raise ValueError('duplicate output key; reconcile offline before resume')
        latest[row['record_key']]=row
    completed=set()
    for key,row in latest.items():
        item=expected_items.get(key)
        if item is None or row.get('resume_contract_sha256') != contract_sha:
            raise ValueError('unbound/stale output; reconcile offline before resume')
        if row.get('generation_success') is not True or row.get('technical_error') not in (None,''): continue
        required=['sample_id','arm','candidate_sequence','y_audio','y_text','raw_model_output','normalized_response','parse_status','parsed_label']
        if any(field not in row for field in required): continue
        if any(row.get(field)!=item.get(field) for field in ['sample_id','arm','candidate_sequence','y_audio','y_text']):
            raise ValueError('scientific identity mismatch on resume')
        if not isinstance(row['raw_model_output'],str) or not isinstance(row['normalized_response'],str): continue
        parsed=parse_mcr_ser_response(row['raw_model_output'])
        if any(row.get(field)!=parsed.get(field) for field in ['normalized_response','parse_status','parsed_label']): continue
        # A technically successful PARSE_FAIL is a scientific outcome, never retried for a better answer.
        completed.add(key)
    return completed

def run(args: argparse.Namespace) -> None:
    # Heavy imports remain inside execution. Importing or py_compile-ing this runner is CPU-only.
    import torch
    from qwen_omni_utils import process_mm_info
    from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor

    manifest = load_jsonl(args.manifest)
    prompt_spec = json.loads(args.prompt_spec.read_text(encoding='utf-8'))
    execution_config = json.loads(args.execution_config.read_text(encoding='utf-8'))
    def file_hash(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    model_path=Path(execution_config['model_absolute_path'])
    model_metadata={}
    for name in ('config.json','preprocessor_config.json','tokenizer_config.json','chat_template.json'):
        path=model_path/name
        if path.is_file(): model_metadata[name]=file_hash(path)
    artifact_identity={'manifest_sha256':file_hash(args.manifest),
                       'prompt_sha256':file_hash(args.prompt_spec),
                       'configuration_sha256':file_hash(args.execution_config),
                       'runner_sha256':file_hash(__file__),
                       'available_model_processor_metadata_sha256':model_metadata}
    contract_sha=resume_contract(manifest, prompt_spec, execution_config, artifact_identity)
    expected_items={row['record_key']:row for row in manifest}
    if len(expected_items)!=len(manifest): raise ValueError('duplicate manifest key')
    completed = existing_keys(args.output, expected_items, contract_sha)
    if args.output.exists() and any(row['record_key'] not in completed for row in load_jsonl(args.output)):
        raise ValueError('incomplete output requires offline reconciliation before retry; no duplicate append')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pending = [row for row in manifest if row['record_key'] not in completed]
    if not pending:
        return

    model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
        execution_config['model_absolute_path'],
        torch_dtype=execution_config['torch_dtype'],
        device_map=execution_config['device_map'],
    )
    processor = Qwen2_5OmniProcessor.from_pretrained(execution_config['model_absolute_path'])
    with args.output.open('a', encoding='utf-8') as handle:
        for item in pending:
            output: dict[str, Any] = {
                'protocol_version': item['protocol_version'],
                'runner_version': 'QWEN25_MCR_CONTROLLED_PATCH_V1',
                'resume_contract_sha256': contract_sha,
                'resume_artifact_identity': artifact_identity,
                'model_revision': execution_config.get('model_revision'),
                'processor_revision': execution_config.get('processor_revision'),
                'record_key': item['record_key'],
                'sample_id': item['sample_id'],
                'source_index': item['source_index'],
                'arm': item['arm'],
                'candidate_sequence_id': item['candidate_sequence_id'],
                'candidate_sequence': item['candidate_sequence'],
                'y_audio': item['y_audio'],
                'y_text': item['y_text'],
                'raw_model_output': None,
                'normalized_response': None,
                'parse_status': None,
                'parsed_label': None,
                'matched_labels': [],
                'match_counts': {},
                'generation_success': False,
                'technical_error': None,
                'prompt_version': item['prompt_version'],
                'parser_version': item['parser_version'],
                'execution_config_version': item['execution_config_version'],
                'return_audio': False,
            }
            try:
                # Rebuild both the message list and processor inputs for every record.
                conversation = build_conversation(item, prompt_spec, args.audio_root)
                text = processor.apply_chat_template(
                    conversation,
                    add_generation_prompt=True,
                    tokenize=False,
                )
                audios, images, videos = process_mm_info(
                    conversation,
                    use_audio_in_video=execution_config['use_audio_in_video'],
                )
                inputs = processor(
                    text=text,
                    audio=audios,
                    images=images,
                    videos=videos,
                    return_tensors='pt',
                    padding=True,
                )
                inputs = {key: value.to(model.device) if hasattr(value, 'to') else value for key, value in inputs.items()}
                generated = model.generate(
                    **inputs,
                    max_new_tokens=execution_config['max_new_tokens'],
                    do_sample=execution_config['do_sample'],
                    return_audio=False,
                )
                prompt_length = inputs['input_ids'].shape[1]
                decoded = processor.batch_decode(
                    generated[:, prompt_length:],
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )[0]
                parsed = parse_mcr_ser_response(decoded)
                output['raw_model_output'] = decoded
                output['normalized_response'] = parsed['normalized_response']
                output['parse_status'] = parsed['parse_status']
                output['parsed_label'] = parsed['parsed_label']
                output['matched_labels'] = parsed['matched_labels']
                output['match_counts'] = parsed['match_counts']
                output['generation_success'] = True
            except Exception as exc:  # Serialize technical failure; never silently retry or alter data.
                output['technical_error'] = f'{type(exc).__name__}: {exc}'
            handle.write(json.dumps(output, ensure_ascii=False, sort_keys=True) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--prompt-spec', type=Path, required=True)
    parser.add_argument('--execution-config', type=Path, required=True)
    parser.add_argument('--audio-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args)
    return 0


remap_namespace(globals())

if __name__ == '__main__':
    raise SystemExit(main())

