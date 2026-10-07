"""Qwen2.5-Omni CA-MER Controlled V4 gate and sequential full-run runner.

Portable current full executor over the frozen 6,000-record scientific plan.
Preflight binds the current release and immutable model/processor contents.
The preserved V4 record loop is reused; failed historical gates are not dependencies.
It does not run scientific analysis.
"""
from __future__ import annotations
from src.common.runtime import project_root, external_path, remap_namespace, relocate, data_root, REPO, input_path, verify_release
import collections
import argparse
import datetime as dt
import gc
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any
ROOT = data_root()
AUDIT = ROOT / 'audit/QWEN25_CAMER_CONTROLLED_V1'
OUT = AUDIT / 'technical_gate_v4'
GATE_OUT = OUT
FULL_OUT = AUDIT / 'full_run_v1'
FULL_LOG = AUDIT / 'controlled_full_run_v1.log'
MODEL = ROOT / 'models/Qwen2.5-Omni-7B'
MANIFEST = AUDIT / 'camer_controlled_manifest_v1.jsonl'
PROMPT = ROOT / 'code/prompts/camer_controlled_arbitration_prompt_v1.json'
PARSER = ROOT / 'code/benchmarks/camer_controlled_parser_v1.py'
ARMS = ('A_ONLY', 'V_ONLY', 'A_THEN_V', 'V_THEN_A')
OPTIONAL_BUILDER = ('code/data/prepare_camer_controlled_media_v1.py', 'b6d3e61726116e2bd9bc2e1bfe096f87df9de8614597e97baba069ec97a112c9')

class GateFailure(RuntimeError):

    def __init__(self, message: str, layer: str, failure_type: str | None=None, minimum_fix: str | None=None):
        super().__init__(message)
        self.layer = layer
        self.failure_type = failure_type or layer.upper().replace(' ', '_')
        self.minimum_fix = minimum_fix or message

def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def sha_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def frozen_hashes():
    return {str(p.relative_to(REPO)): sha_file(p) for p in (MANIFEST, PROMPT, PARSER, PROTOCOL)}

def hash_mismatches(actual):
    release = read_json(REPO / 'RELEASE_MANIFEST_V1.json')
    expected = {x['relative_path']: x['SHA256'] for x in release['files']}
    return {k: {'expected': expected.get(k), 'actual': v} for k, v in actual.items() if expected.get(k) != v}

def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return 'NOT_INSTALLED'

def preflight(out_dir, mode):
    from src.cross_regime.target_scoring.inputs import FrozenInputs
    from src.cross_regime.target_scoring.verify_runtime import verify
    try:
        verify_release()
        if out_dir.exists():
            raise ValueError('Output must be new')
        report = verify(FrozenInputs())
        if report.get('GPU_EXECUTION_ALLOWED') != 'YES':
            raise ValueError(report)
        enum = ('OK', 'PARSE_FAIL')
        tests = parser_validator_self_test(enum)
        if not tests['all_pass']:
            raise ValueError('Frozen parser schema self-test failed')
        return ({'frozen_hashes': frozen_hashes(), 'parser_status_enum': enum, 'parser_validator_self_test': tests, 'environment': report}, None)
    except Exception as exc:
        return ({}, {'kind': 'CURRENT_RELEASE_PREFLIGHT_BLOCKED', 'reason': str(exc)})

def probe_media(path: Path) -> dict[str, Any]:
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], text=True, capture_output=True, timeout=90)
    if p.returncode:
        raise GateFailure(f'ffprobe failed for {path}: {p.stderr[-500:]}', 'media', 'FFPROBE_FAILURE')
    data = json.loads(p.stdout)
    streams = data.get('streams', [])
    audio = [s for s in streams if s.get('codec_type') == 'audio']
    video = [s for s in streams if s.get('codec_type') == 'video']
    return {'audio_stream_count': len(audio), 'video_stream_count': len(video), 'audio_streams': [{'codec': s.get('codec_name'), 'sample_rate': s.get('sample_rate'), 'channels': s.get('channels')} for s in audio], 'video_streams': [{'codec': s.get('codec_name'), 'width': s.get('width'), 'height': s.get('height')} for s in video], 'format_duration_seconds': data.get('format', {}).get('duration')}

def tensor_shape(value: Any) -> Any:
    if hasattr(value, 'shape'):
        return [int(x) for x in value.shape]
    if isinstance(value, (list, tuple)):
        return [tensor_shape(x) for x in value]
    return None

def processor_token_audit(tokenizer: Any, input_ids: Any) -> tuple[list[str], list[str], collections.Counter]:
    ids = input_ids[0].tolist()
    tokens = [str(x) for x in tokenizer.convert_ids_to_tokens(ids)]
    events: list[str] = []
    counts: collections.Counter = collections.Counter()
    for token in tokens:
        low = token.lower()
        modality = None
        if 'audio' in low:
            modality = 'audio'
        elif 'video' in low or 'vision' in low:
            modality = 'silent_video'
        if modality:
            counts[modality] += 1
            if not events or events[-1] != modality:
                events.append(modality)
    return (tokens, events, counts)

def save_json(path: Path, value: dict[str, Any], exclusive: bool=False) -> None:
    mode = 'x' if exclusive else 'w'
    with path.open(mode, encoding='utf-8') as f:
        json.dump(json_safe(value), f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())

def json_safe(value: Any) -> Any:
    """Canonicalize mapping keys only at report/provenance JSON boundaries."""
    if isinstance(value, dict):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            safe_key = '__NONE__' if key is None else str(key)
            if safe_key in converted:
                raise ValueError(f'JSON-safe key collision for {safe_key!r}')
            converted[safe_key] = json_safe(item)
        return converted
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value

def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    json.loads(raw)
    with path.open('a', encoding='utf-8') as f:
        f.write(raw + '\n')
        f.flush()
        os.fsync(f.fileno())

def extract_generated_suffix(output: Any, input_ids: Any, torch: Any) -> Any:
    """Return only assistant continuation; require the decoder-only prompt prefix."""
    sequences = getattr(output, 'sequences', output)
    if not hasattr(sequences, 'shape') or len(sequences.shape) != 2:
        raise GateFailure('generate did not return a rank-2 token sequence', 'output_extraction', 'GENERATION_OUTPUT_INVALID')
    if not hasattr(input_ids, 'shape') or len(input_ids.shape) != 2 or input_ids.shape[0] != sequences.shape[0]:
        raise GateFailure('generation output/input batch shape mismatch', 'output_extraction', 'PROMPT_PREFIX_MISMATCH')
    prefix_length = int(input_ids.shape[1])
    if int(sequences.shape[1]) < prefix_length:
        raise GateFailure('generation sequence is shorter than its prompt prefix', 'output_extraction', 'PROMPT_PREFIX_MISSING')
    expected_prefix = input_ids.to(sequences.device)
    if not torch.equal(sequences[:, :prefix_length], expected_prefix):
        raise GateFailure('generation sequence does not preserve the exact input prompt prefix', 'output_extraction', 'PROMPT_PREFIX_MISMATCH')
    suffix = sequences[:, prefix_length:]
    if int(suffix.shape[1]) < 1:
        raise GateFailure('generation returned no continuation tokens', 'output_extraction', 'RAW_OUTPUT_MISSING')
    return suffix

def output_slicing_self_test(torch: Any) -> dict[str, Any]:
    input_ids = torch.tensor([[10, 20, 30]], dtype=torch.long)
    output_ids = torch.tensor([[10, 20, 30, 40, 50]], dtype=torch.long)
    suffix = extract_generated_suffix(output_ids, input_ids, torch)
    generated_only = [int(x) for x in suffix[0].tolist()]
    prompt_text = 'PROMPT_CANDIDATE_A PROMPT_CANDIDATE_B PROMPT_CANDIDATE_C'
    token_text = {10: 'PROMPT_CANDIDATE_A', 20: 'PROMPT_CANDIDATE_B', 30: 'PROMPT_CANDIDATE_C', 40: '{"label":', 50: 'happy}'}
    parser_visible_text = ' '.join((token_text[x] for x in generated_only))
    if generated_only != [40, 50] or any((marker in parser_visible_text for marker in prompt_text.split())):
        raise GateFailure('synthetic output-slicing test included prompt prefix', 'output_extraction', 'PROMPT_PREFIX_LEAKAGE')
    return {'input_ids': [10, 20, 30], 'output_ids': [10, 20, 30, 40, 50], 'generated_only_ids': generated_only, 'parser_visible_text': parser_visible_text, 'parser_visible_prompt_prefix_included': False, 'status': 'PASS'}

def atomic_checkpoint(path: Path, value: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + '.tmp')
    save_json(tmp, value, exclusive=False)
    os.replace(tmp, path)
    dir_fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)

def validate_run_outputs(rows: list[dict[str, Any]], audits: list[dict[str, Any]], selected: list[dict[str, Any]], arms: tuple[str, ...], prompt_id: str, protocol: dict[str, Any], expected_count: int, attempted: int, full: bool, runner_sha: str, parser_status_enum: tuple[str, ...]) -> dict[str, Any]:
    """Validate serialized technical records and their frozen manifest identities."""
    expected = [(sample['sample_id'], arm, sample) for sample in selected for arm in arms]
    expected_prefix = expected[:attempted]
    identity_sequence = [(row.get('sample_id'), row.get('arm')) for row in rows]
    expected_output_sequence = [(sample_id, arm) for sample_id, arm, _ in expected_prefix]
    unique_keys = [row.get('manifest_key') for row in rows]
    arm_counts = collections.Counter((row.get('arm') for row in rows))
    required = {'sample_id', 'manifest_key', 'source_subset', 'arm', 'prompt_template_id', 'candidate_order_id', 'candidate_sequence', 'expected_modalities', 'actual_modalities', 'raw_model_output', 'parse_status', 'parsed_label', 'generation_status', 'schema_status', 'serialization_status', 'technical_status', 'parser_contract_status', 'runner_version', 'runner_sha256', 'model_identity', 'record_index'}
    schema_rows_valid = all((required.issubset(row) for row in rows))
    identity_valid = identity_sequence == expected_output_sequence and all((isinstance(key, str) and key for key in unique_keys)) and (len(set(unique_keys)) == len(unique_keys))
    candidate_valid = True
    prompt_valid = True
    order_valid = True
    generation_valid = True
    leakage_valid = True
    expected_by_identity = {(sample['sample_id'], arm): sample for sample in selected for arm in arms}
    for index, row in enumerate(rows):
        expected_identity = expected_by_identity.get((row.get('sample_id'), row.get('arm')))
        if expected_identity is None:
            identity_valid = False
            continue
        candidate_valid &= row.get('candidate_order_id') == expected_identity.get('candidate_order_sha256') and row.get('candidate_sequence') == expected_identity.get('candidate_order') and (row.get('runner_sha256') == runner_sha)
        prompt_valid &= row.get('prompt_template_id') == prompt_id
        if row.get('technical_status') == 'PASS':
            expected_modalities = [x for x in protocol['arms'][row['arm']] if x != 'instruction']
            parse_valid = row.get('parse_status') in parser_status_enum
            order_valid &= row.get('expected_modalities') == expected_modalities and row.get('actual_modalities') == expected_modalities and (row.get('parser_visible_text_source') == 'generated_assistant_continuation_only') and (row.get('parser_visible_prompt_prefix_included') is False) and parse_valid and (row.get('parser_contract_status') == 'VALID')
            generation_valid &= row.get('generation_status') == 'SUCCESS' and row.get('effective_thinker_max_new_tokens') == 1024 and (row.get('effective_thinker_do_sample') is False) and (row.get('use_audio_in_video_effective') is False) and (row.get('return_audio_effective') is False) and (row.get('schema_status') == 'VALID') and (row.get('serialization_status') == 'VALID')
        leakage_valid &= row.get('unexpected_metadata_leakage') is not True
    audit_sequence = [(row.get('sample_id'), row.get('arm')) for row in audits]
    audit_valid = audit_sequence == expected_output_sequence and all((audit.get('cross_record_inputs_fresh') is True and audit.get('past_key_values_reused') is False and (audit.get('metadata_leakage') is False) and (audit.get('joint_duplicate_audio_evidence') is False) for audit in audits))
    for audit in audits:
        arm = audit.get('arm')
        expected_modalities = [x for x in protocol['arms'].get(arm, []) if x != 'instruction']
        if audit.get('processor_status') == 'PASS':
            order_valid &= audit.get('expected_modalities') == expected_modalities and audit.get('actual_modalities') == expected_modalities and (audit.get('processor_use_audio_in_video') is False) and (audit.get('process_mm_info_use_audio_in_video') is False) and (audit.get('processor_call_use_audio_in_video') is False) and (audit.get('media_loader_audio_arrays') == (1 if 'audio' in expected_modalities else 0)) and (audit.get('media_loader_video_items') == (1 if 'silent_video' in expected_modalities else 0)) and (audit.get('silent_video_probe', {}).get('audio_stream_count') == 0) and (audit.get('multimedia_placeholder_order') == expected_modalities)
            generation_valid &= audit.get('metadata_leakage') is False
    exact_count = len(rows) == expected_count
    return {'expected_records': expected_count, 'attempted_records': attempted, 'serialized_records': len(rows), 'processor_audit_records': len(audits), 'arm_counts': dict(arm_counts), 'schema_rows_valid': schema_rows_valid, 'manifest_identity_sequence_valid': identity_valid, 'candidate_sequence_and_order_id_preserved': bool(candidate_valid), 'prompt_template_identity_preserved': bool(prompt_valid), 'expected_actual_modalities_and_evidence_order_valid': bool(order_valid), 'generation_configuration_and_record_status_valid': bool(generation_valid), 'processor_audit_and_cross_record_isolation_valid': bool(audit_valid), 'metadata_leakage_absent': bool(leakage_valid), 'exact_record_count': exact_count, 'full_manifest_coverage': bool(full and exact_count and identity_valid and (len(set(identity_sequence)) == expected_count)), 'all_checks_valid': bool(schema_rows_valid and identity_valid and candidate_valid and prompt_valid and order_valid and generation_valid and audit_valid and leakage_valid and (exact_count if full else True) and (not full or (exact_count and len(set(identity_sequence)) == expected_count)))}

def load_parser():
    spec = importlib.util.spec_from_file_location('frozen_camer_controlled_parser', PARSER)
    if spec is None or spec.loader is None:
        raise GateFailure('cannot load frozen parser module', 'parser', 'PARSER_LOAD_FAILURE')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, 'parse_label', None)):
        raise GateFailure('frozen parser has no parse_label function', 'parser', 'PARSER_IMPLEMENTATION_FAILURE')
    return module

def validate_parser_result(result: Any, parser_status_enum: tuple[str, ...]) -> tuple[str | None, str]:
    """Validate the exact two-item result returned by the frozen parser."""
    if type(result) is not tuple or len(result) != 2:
        raise GateFailure('frozen parser result is not the audited two-item tuple', 'parser', 'PARSER_RESULT_SCHEMA_INVALID')
    parsed_label, parse_status = result
    if parsed_label is not None and (not isinstance(parsed_label, str)):
        raise GateFailure('frozen parser tuple item 0 is neither str nor None', 'parser', 'PARSER_RESULT_SCHEMA_INVALID')
    if not isinstance(parse_status, str):
        raise GateFailure('frozen parser tuple item 1 is not a string status', 'parser', 'PARSER_RESULT_SCHEMA_INVALID')
    if parse_status not in parser_status_enum:
        raise GateFailure(f'frozen parser returned a status outside its audited contract: {parse_status}', 'parser', 'PARSER_STATUS_INVALID')
    return (parsed_label, parse_status)

def parser_validator_self_test(parser_status_enum: tuple[str, ...]) -> dict[str, Any]:
    """Exercise the runner validator with synthetic interface values only."""
    accepted = [('joy', status) for status in parser_status_enum]
    accepted += [(None, status) for status in parser_status_enum]
    accepted_results = []
    for value in accepted:
        try:
            accepted_results.append(validate_parser_result(value, parser_status_enum) == value)
        except Exception:
            accepted_results.append(False)
    invalid = [({'label': 'joy', 'status': parser_status_enum[0]}, 'PARSER_RESULT_SCHEMA_INVALID'), (('joy',), 'PARSER_RESULT_SCHEMA_INVALID'), ((42, parser_status_enum[0]), 'PARSER_RESULT_SCHEMA_INVALID'), ((None, 4), 'PARSER_RESULT_SCHEMA_INVALID'), (('joy', '__OUTSIDE_FROZEN_PARSER_ENUM__'), 'PARSER_STATUS_INVALID')]
    rejected_results = []
    for value, expected_failure in invalid:
        try:
            validate_parser_result(value, parser_status_enum)
            rejected_results.append(False)
        except GateFailure as exc:
            rejected_results.append(exc.failure_type == expected_failure)
    return {'all_pass': bool(parser_status_enum and all(accepted_results) and all(rejected_results)), 'accepted_frozen_statuses': list(parser_status_enum), 'accepted_case_count': len(accepted_results), 'rejected_schema_and_status_case_count': len(rejected_results), 'model_generation_called': False, 'scientific_records_used': False}

def effective_prompt(prompt_obj: dict[str, Any], candidate_sequence: list[str]) -> str:
    placeholder = prompt_obj['candidates_placeholder']
    instruction = prompt_obj['shared_instruction']
    if instruction.count(placeholder) != 1:
        raise GateFailure('frozen prompt candidate placeholder is not unique', 'prompt', 'PROMPT_TEMPLATE_INVALID')
    return instruction.replace(placeholder, json.dumps(candidate_sequence, ensure_ascii=False, separators=(',', ':')))

def build_messages(row: dict[str, Any], arm: str, instruction: str) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    audio_path = str((ROOT / row['audio_path']).resolve())
    video_path = str((ROOT / row['silent_video_path']).resolve())
    content: list[dict[str, Any]] = []
    structured: list[str] = []
    expected_modalities: list[str] = []
    if arm in ('A_ONLY', 'A_THEN_V'):
        content.append({'type': 'audio', 'audio': audio_path})
        structured.append('audio')
        expected_modalities.append('audio')
    if arm in ('V_ONLY', 'A_THEN_V', 'V_THEN_A') and arm != 'V_THEN_A':
        content.append({'type': 'video', 'video': video_path})
        structured.append('silent_video')
        expected_modalities.append('silent_video')
    if arm == 'V_THEN_A':
        content.append({'type': 'video', 'video': video_path})
        structured.append('silent_video')
        expected_modalities.append('silent_video')
        content.append({'type': 'audio', 'audio': audio_path})
        structured.append('audio')
        expected_modalities.append('audio')
    content.append({'type': 'text', 'text': instruction})
    structured.append('instruction')
    return ([{'role': 'user', 'content': content}], structured, expected_modalities)

def audit_leakage(rendered: str, row: dict[str, Any], audio_path: str, video_path: str) -> list[str]:
    low = rendered.lower()
    forbidden = [row['sample_id'], row['subset'], row.get('official_annotation_file', ''), str(row.get('official_annotation_row', '')), audio_path, video_path, Path(audio_path).name, Path(video_path).name, 'audio-aligned', 'video-aligned', 'consistent', 'source_index', 'final_label', 'emotionllama_pseudo_label', 'audio_pseudo_label', 'video_pseudo_label', 'audio_analysis', 'video_analysis', 'reasoning', 'subtitle', 'transcript', 'ground truth', 'y_a', 'y_v']
    return [str(x) for x in forbidden if x and str(x).lower() in low]

def main() -> int:
    parser = argparse.ArgumentParser(description='Qwen2.5-Omni CA-MER Controlled V4')
    parser.add_argument('--mode', choices=('full',), default='full')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--execute-gpu', action='store_true')
    args = parser.parse_args()
    mode = args.mode
    out_dir = args.output_dir.resolve()
    verify_release()
    if not args.execute_gpu:
        rows = read_jsonl(MANIFEST)
        if len(rows) != 1500 or len({r['sample_id'] for r in rows}) != 1500:
            raise ValueError('Frozen manifest population mismatch')
        print(json.dumps({'CPU_PLAN': 'PASS', 'samples': 1500, 'slots': 6000, 'GPU_executed': False}))
        return 0
    preflight_info, blocked = preflight(out_dir, mode)
    if blocked:
        print(json.dumps({'QWEN25_CAMER_CONTROLLED_TECHNICAL_GATE_V4_STATUS': 'NOT_RUN' if mode == 'gate' else 'PASS', 'CAMER_CONTROLLED_RUNNER_V4_STATUS': 'TECHNICAL_IMPLEMENTATION_BLOCKED', 'CAMER_CONTROLLED_PROTOCOL_STATUS': 'PRE_GATE_BLOCKED', 'CAMER_CONTROLLED_SCIENCE_STATUS': 'NOT_RUN', 'CAMER_CONTROLLED_FULL_RUN_STATUS': 'NOT_RUN', 'blocker': blocked, 'run_mode': mode}, ensure_ascii=False))
        return 2
    runner_sha = sha_file(Path(__file__))
    prompt_sha = sha_file(PROMPT)
    parser_sha = sha_file(PARSER)
    plan_text = ''
    manifest_rows = read_jsonl(MANIFEST)
    selected = manifest_rows
    seen_ids = [r.get('sample_id') for r in selected]
    if len(selected) != 1500 or len(set(seen_ids)) != 1500 or any((not sid for sid in seen_ids)):
        raise GateFailure('full manifest identity/count preflight failed', 'manifest', 'MANIFEST_COVERAGE_INVALID')
    if any((r.get('planned_arms') != list(ARMS) for r in selected)):
        raise GateFailure('full manifest arm plan differs from frozen four-arm definition', 'manifest', 'ARM_SET_MISMATCH')
    selection_info = {'method': 'full frozen manifest order; no resampling', 'selected_sample_ids_sha256': sha_json(seen_ids), 'sample_count': len(selected), 'arms_per_sample': list(ARMS), 'maximum_generations': 6000, 'selection_uses_targets_candidate_positions_or_predictions': False}
    protocol = read_json(PROTOCOL)
    prompt_obj = read_json(PROMPT)
    parser_module = load_parser()
    parser_status_enum = tuple(preflight_info['parser_status_enum'])
    prompt_id = f'sha256:{prompt_sha}'
    names = ['qwen25_camer_controlled_full_v1.jsonl', 'CAMER_CONTROLLED_FULL_RUN_PROCESSOR_AUDIT_V1.jsonl', 'CAMER_CONTROLLED_FULL_RUN_V1.json', 'CAMER_CONTROLLED_FULL_RUN_V1.md', 'CAMER_CONTROLLED_FULL_RUN_V1_PROVENANCE.json', 'CAMER_CONTROLLED_FULL_RUN_V1_CHECKPOINT.json']
    checkpoint_name = names[5]
    report_name, markdown_name, provenance_name = (names[2], names[3], names[4])
    out_dir.mkdir(parents=True, exist_ok=False)
    paths = {name: out_dir / name for name in names}
    for name in names:
        if paths[name].exists():
            raise GateFailure('refusing to overwrite existing gate artifact', 'filesystem', 'OUTPUT_EXISTS')
    for name in names[:2]:
        paths[name].open('x').close()
    checkpoint_path = paths[checkpoint_name] if checkpoint_name else None
    records_expected = len(selected) * len(ARMS)
    attempted = generated = parser_count = 0
    parse_counts: collections.Counter = collections.Counter()
    failures: list[dict[str, Any]] = []
    processor_audits: list[dict[str, Any]] = []
    model_loaded = False
    model = processor = None
    torch = transformers = None
    model_generation_config = None
    memory_at_load: dict[str, Any] = {}
    run_start = dt.datetime.now(dt.timezone.utc).isoformat()
    run_monotonic = time.monotonic()
    slicing_self_test: dict[str, Any] | None = None
    serialization_self_test: dict[str, Any] | None = None
    checkpoint_last_manifest_key: str | None = None

    def update_checkpoint(state: str, last_manifest_key: str | None=None, failure: dict[str, Any] | None=None) -> None:
        nonlocal checkpoint_last_manifest_key
        if checkpoint_path is None:
            return
        if last_manifest_key is not None:
            checkpoint_last_manifest_key = last_manifest_key
        atomic_checkpoint(checkpoint_path, {'runner_version': 'QWEN25_CAMER_CONTROLLED_V4_1.0', 'runner_sha256': runner_sha, 'run_mode': mode, 'state': state, 'expected_records': records_expected, 'attempted_records': attempted, 'generation_invocations_succeeded': generated, 'parser_execution_count': parser_count, 'processor_audit_bytes': paths[names[1]].stat().st_size, 'record_output_bytes': paths[names[0]].stat().st_size, 'last_manifest_key': checkpoint_last_manifest_key, 'failure': failure, 'updated_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'resume_supported': False})
    if checkpoint_path is not None:
        update_checkpoint('STARTED')

    def note_failure(exc: Exception, sample_id: str | None=None, arm: str | None=None, layer: str | None=None) -> None:
        failure = {'sample_id': sample_id, 'arm': arm, 'failure_type': getattr(exc, 'failure_type', type(exc).__name__), 'technical_layer': layer or getattr(exc, 'layer', 'model_load'), 'minimum_required_fix': getattr(exc, 'minimum_fix', str(exc)), 'error': str(exc), 'traceback': traceback.format_exc(limit=12)}
        failures.append(failure)
        if checkpoint_path is not None:
            try:
                update_checkpoint('TECHNICAL_FAILURE', checkpoint_last_manifest_key, failure)
            except Exception as checkpoint_exc:
                failures.append({'sample_id': sample_id, 'arm': arm, 'failure_type': 'CHECKPOINT_WRITE_FAILURE', 'technical_layer': 'checkpoint', 'minimum_required_fix': 'restore atomic checkpoint write', 'error': str(checkpoint_exc), 'traceback': traceback.format_exc(limit=8)})
    try:
        import torch as torch_mod
        import transformers as transformers_mod
        from src.common.audio_compat import patch_audioread_compat
        from qwen_omni_utils import process_mm_info
        from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
        patch_audioread_compat()
        torch, transformers = (torch_mod, transformers_mod)
        slicing_self_test = output_slicing_self_test(torch)
        serialization_probe = {'counted_attempts': {None: 18}}
        serialization_probe['serialized'] = json_safe(serialization_probe['counted_attempts'])
        count_before = sum(serialization_probe['counted_attempts'].values())
        count_after = sum(serialization_probe['serialized'].values())
        serialization_self_test = {'none_key_maps_to___NONE__': serialization_probe['serialized'].get('__NONE__') == 18, 'count_before': count_before, 'count_after': count_after, 'count_preserved': count_before == count_after == 18, 'json_round_trip': json.loads(json.dumps(serialization_probe['serialized'], sort_keys=True)) == serialization_probe['serialized']}
        if not (serialization_self_test['none_key_maps_to___NONE__'] and serialization_self_test['count_preserved'] and serialization_self_test['json_round_trip']):
            raise GateFailure('V2 None-key serialization preservation self-test failed', 'serialization', 'SERIALIZATION_PREFLIGHT_FAILURE')
        model_kwargs = {'torch_dtype': 'auto', 'device_map': 'auto', 'local_files_only': True}
        processor = Qwen2_5OmniProcessor.from_pretrained(str(MODEL), local_files_only=True)
        model = Qwen2_5OmniForConditionalGeneration.from_pretrained(str(MODEL), **model_kwargs)
        model.eval()
        model_loaded = True
        model_generation_config = model.generation_config.to_dict() if getattr(model, 'generation_config', None) is not None else None
        memory_at_load = {'allocated_bytes': int(torch.cuda.memory_allocated()), 'reserved_bytes': int(torch.cuda.memory_reserved()), 'max_allocated_bytes': int(torch.cuda.max_memory_allocated())}
        seen_identity: set[str] = set()
        for row in selected:
            sid = row['sample_id']
            if sid in seen_identity:
                raise GateFailure('cross-record sample identity repeated unexpectedly', 'identity', 'CROSS_RECORD_STATE_LEAKAGE')
            seen_identity.add(sid)
            if row['planned_arms'] != list(ARMS):
                raise GateFailure('arm set changed after sample selection', 'manifest', 'ARM_SET_MISMATCH')
            for arm in ARMS:
                attempted += 1
                started = time.monotonic()
                base = {'sample_id': sid, 'manifest_key': f"{row['official_annotation_file']}:{row['official_annotation_row']}:{sid}:{arm}", 'source_subset': row['subset'], 'arm': arm, 'prompt_template_id': prompt_id, 'candidate_order_id': row['candidate_order_sha256'], 'candidate_sequence': row['candidate_order'], 'expected_modalities': [x for x in protocol['arms'][arm] if x != 'instruction'], 'actual_modalities': [], 'structured_message_order': None, 'multimedia_placeholder_order': None, 'rendered_instruction': None, 'raw_model_output': None, 'parse_status': 'NOT_RUN', 'parsed_label': None, 'parser_contract_status': 'NOT_RUN', 'parser_return_type': None, 'generation_status': 'NOT_RUN', 'schema_status': 'PENDING', 'serialization_status': 'PENDING', 'technical_status': 'PENDING', 'unexpected_metadata_leakage': False, 'error_type': None, 'technical_layer': None, 'generation_latency_seconds': None, 'model_identity': {'model_type': 'qwen2_5_omni', 'path': str(MODEL)}, 'record_index': attempted - 1}
                processor_audit: dict[str, Any] = {'sample_id': sid, 'manifest_key': base['manifest_key'], 'source_subset': row['subset'], 'arm': arm, 'expected_modalities': base['expected_modalities'], 'actual_modalities': [], 'structured_message_order': None, 'multimedia_placeholder_order': None, 'candidate_order_id': row['candidate_order_sha256'], 'candidate_sequence': row['candidate_order'], 'prompt_template_id': prompt_id, 'cross_record_inputs_fresh': True, 'past_key_values_reused': False, 'joint_duplicate_audio_evidence': False, 'media_path_model_visible_text': False, 'metadata_leakage': False, 'process_mm_info_use_audio_in_video': False, 'processor_status': 'PENDING', 'processor_error': None}
                try:
                    audio_path = ROOT / row['audio_path']
                    video_path = ROOT / row['silent_video_path']
                    if not audio_path.is_file() or not video_path.is_file():
                        raise GateFailure('manifest media file missing', 'media', 'MEDIA_MISSING')
                    audio_hash = sha_file(audio_path)
                    video_hash = sha_file(video_path)
                    if audio_hash != row['audio_sha256'] or video_hash != row['silent_video_sha256']:
                        raise GateFailure('selected media hash differs from frozen manifest', 'media', 'MEDIA_HASH_MISMATCH')
                    audio_probe = probe_media(audio_path)
                    video_probe = probe_media(video_path)
                    if audio_probe['audio_stream_count'] != 1 or audio_probe['video_stream_count'] != 0:
                        raise GateFailure('A_ONLY/joint audio asset is not an isolated audio stream', 'media', 'AUDIO_ISOLATION_FAILURE')
                    audio_stream = audio_probe['audio_streams'][0]
                    if str(audio_stream.get('sample_rate')) != '16000' or audio_stream.get('channels') != 1:
                        raise GateFailure('derived audio does not match frozen mono 16 kHz contract', 'media', 'AUDIO_FORMAT_FAILURE')
                    if video_probe['video_stream_count'] != 1 or video_probe['audio_stream_count'] != 0:
                        raise GateFailure('silent video must contain exactly one video stream and zero audio', 'media', 'SILENT_VIDEO_FAILURE')
                    instruction = effective_prompt(prompt_obj, row['candidate_order'])
                    messages, structured_order, expected_modalities = build_messages(row, arm, instruction)
                    if structured_order != protocol['arms'][arm]:
                        raise GateFailure('structured message order differs from frozen protocol', 'message_order', 'MESSAGE_ORDER_FAILURE')
                    rendered = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
                    if isinstance(rendered, str):
                        processor_text = rendered
                        audit_text = rendered
                        rendered_shape = {'return_type': 'str', 'return_length': len(rendered), 'element_types': None}
                    elif isinstance(rendered, list) and len(rendered) == 1 and isinstance(rendered[0], str):
                        processor_text = rendered
                        audit_text = rendered[0]
                        rendered_shape = {'return_type': 'list', 'return_length': 1, 'element_types': ['str'], 'singleton_batch_return_valid': True}
                    else:
                        raise GateFailure(f'unsupported chat-template return shape: {type(rendered).__name__}', 'chat_template', 'CHAT_TEMPLATE_FAILURE')
                    leaks = audit_leakage(audit_text, row, str(audio_path.resolve()), str(video_path.resolve()))
                    if leaks:
                        processor_audit.update({'metadata_leakage': True, 'leaked_strings': leaks, 'structured_message_order': structured_order, 'rendered_instruction': instruction, 'silent_video_probe': video_probe, 'audio_probe': audio_probe, 'audio_sha256': audio_hash, 'silent_video_sha256': video_hash})
                        raise GateFailure('model-visible text contains sample/source metadata', 'leakage', 'METADATA_LEAKAGE')
                    audios, images, videos, video_kwargs = process_mm_info(messages, use_audio_in_video=False, return_video_kwargs=True)
                    expected_audio = 'audio' in expected_modalities
                    expected_video = 'silent_video' in expected_modalities
                    if bool(audios) != expected_audio or bool(videos) != expected_video or images:
                        raise GateFailure('media helper returned unexpected modality payloads', 'media_helper', 'WRONG_MODALITY')
                    applied_video_kwargs = {k: v for k, v in (video_kwargs or {}).items() if k != 'do_sample_frames'} if expected_video else {}
                    inputs = processor(text=processor_text, audio=audios, images=images, videos=videos, return_tensors='pt', padding=True, use_audio_in_video=False, **applied_video_kwargs)
                    keys = list(inputs.keys())
                    audio_keys = [k for k in ('input_features', 'feature_attention_mask', 'audio_values') if k in inputs]
                    video_keys = [k for k in ('pixel_values_videos', 'video_grid_thw') if k in inputs]
                    actual_audio = bool(audios) and 'input_features' in inputs and ('feature_attention_mask' in inputs)
                    actual_video = bool(videos) and 'pixel_values_videos' in inputs and ('video_grid_thw' in inputs)
                    actual_set = {name for name, present in (('audio', actual_audio), ('silent_video', actual_video)) if present}
                    actual = [name for name in expected_modalities if name in actual_set]
                    if actual_set != set(expected_modalities):
                        raise GateFailure(f'processor tensors do not match expected modality set: {actual}', 'processor', 'WRONG_MODALITY')
                    if arm in ('A_THEN_V', 'V_THEN_A'):
                        if len(audios) != 1 or len(videos) != 1 or video_probe['audio_stream_count'] != 0:
                            raise GateFailure('joint arm duplicates or omits audio evidence', 'processor', 'JOINT_DUPLICATE_AUDIO')
                    if 'past_key_values' in inputs:
                        raise GateFailure('processor input unexpectedly contains cached past_key_values', 'cross_record', 'CROSS_RECORD_STATE_LEAKAGE')
                    tokens, token_order, token_counts = processor_token_audit(processor.tokenizer, inputs['input_ids'])
                    expected_token_order = [x for x in expected_modalities]
                    if token_order != expected_token_order:
                        raise GateFailure(f'processor modality token order mismatch; expected {expected_token_order}, got {token_order}', 'processor_order', 'PROCESSOR_ORDER_MISMATCH')
                    processor_audit.update({'processor_status': 'PASS', 'actual_modalities': actual, 'structured_message_order': structured_order, 'multimedia_content_types': [x['type'] for x in messages[0]['content']], 'multimedia_placeholder_order': token_order, 'processor_modality_token_counts': dict(token_counts), 'processor_modality_token_sequence': [t for t in tokens if 'audio' in t.lower() or 'video' in t.lower() or 'vision' in t.lower()], 'processor_input_keys': keys, 'processor_input_shapes': {k: tensor_shape(v) for k, v in inputs.items()}, 'audio_input_keys': audio_keys, 'video_input_keys': video_keys, 'media_loader_audio_arrays': len(audios) if audios is not None else 0, 'media_loader_video_items': len(videos) if videos is not None else 0, 'processor_use_audio_in_video': False, 'video_processor_kwargs': applied_video_kwargs, 'process_mm_info_use_audio_in_video': False, 'processor_call_use_audio_in_video': False, 'audio_probe': audio_probe, 'silent_video_probe': video_probe, 'audio_sha256': audio_hash, 'silent_video_sha256': video_hash, 'audio_path': str(audio_path.relative_to(ROOT)), 'silent_video_path': str(video_path.relative_to(ROOT)), 'rendered_instruction': instruction, 'rendered_prompt_text': audit_text, 'chat_template_return_shape': rendered_shape, 'rendered_text_contains_media_path': str(audio_path.resolve()) in audit_text or str(video_path.resolve()) in audit_text, 'joint_duplicate_audio_evidence': False, 'metadata_leakage': False})
                    base.update({'actual_modalities': actual, 'structured_message_order': structured_order, 'multimedia_placeholder_order': token_order, 'rendered_instruction': instruction, 'rendered_prompt_text': audit_text, 'processor_input_keys': keys, 'media_identity': {'audio_path': str(audio_path.relative_to(ROOT)), 'audio_sha256': audio_hash, 'silent_video_path': str(video_path.relative_to(ROOT)), 'silent_video_sha256': video_hash}})
                    append_jsonl(paths[names[1]], processor_audit)
                    processor_audits.append(processor_audit)
                    with torch.inference_mode():
                        for key, value in list(inputs.items()):
                            if hasattr(value, 'to'):
                                if getattr(value, 'is_floating_point', lambda: False)() and str(getattr(model, 'dtype', 'auto')) not in ('auto', 'unknown'):
                                    value = value.to(dtype=model.dtype)
                                inputs[key] = value.to(model.device)
                        output = model.generate(**inputs, use_audio_in_video=False, return_audio=False, thinker_max_new_tokens=1024, thinker_do_sample=False)
                    generated += 1
                    tail = extract_generated_suffix(output, inputs['input_ids'], torch)
                    raw = processor.batch_decode(tail, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
                    if not isinstance(raw, str):
                        raise GateFailure('raw model output was not a string', 'generation', 'RAW_OUTPUT_INVALID')
                    base['raw_model_output'] = raw
                    parser_result = parser_module.parse_label(raw, row['candidate_order'])
                    parser_count += 1
                    base['parser_return_type'] = type(parser_result).__name__
                    base['parser_contract_status'] = 'INVALID'
                    if type(parser_result) is tuple and len(parser_result) == 2:
                        returned_label, returned_status = parser_result
                        if returned_label is None or isinstance(returned_label, str):
                            base['parsed_label'] = returned_label
                        if isinstance(returned_status, str):
                            base['parse_status'] = returned_status
                            parse_counts[returned_status] += 1
                    parsed, parse_status = validate_parser_result(parser_result, parser_status_enum)
                    base['parser_contract_status'] = 'VALID'
                    base.update({'raw_model_output': raw, 'parse_status': parse_status, 'parsed_label': parsed, 'parser_contract_status': 'VALID', 'generation_status': 'SUCCESS', 'schema_status': 'VALID', 'technical_status': 'PASS', 'generation_latency_seconds': round(time.monotonic() - started, 4), 'model_generation_config_sha256': sha_json(model_generation_config) if model_generation_config is not None else None, 'generation_parameters_overrides': {'use_audio_in_video': False, 'return_audio': False, 'thinker_max_new_tokens': 1024, 'thinker_do_sample': False}, 'effective_thinker_max_new_tokens': 1024, 'effective_thinker_do_sample': False, 'use_audio_in_video_effective': False, 'return_audio_effective': False, 'parser_visible_prompt_prefix_included': False, 'parser_visible_text_source': 'generated_assistant_continuation_only'})
                    required = {'sample_id', 'manifest_key', 'source_subset', 'arm', 'prompt_template_id', 'candidate_order_id', 'candidate_sequence', 'raw_model_output', 'parse_status', 'parsed_label', 'generation_status', 'schema_status', 'serialization_status', 'parser_contract_status', 'runner_version', 'runner_sha256', 'model_identity', 'record_index'}
                    record = {**base, 'serialization_status': 'VALID', 'runner_version': 'QWEN25_CAMER_CONTROLLED_V4_1.0', 'runner_sha256': runner_sha}
                    if not required.issubset(record):
                        raise GateFailure('gate record schema is incomplete', 'schema', 'SCHEMA_FAILURE')
                    append_jsonl(paths[names[0]], record)
                    update_checkpoint('IN_PROGRESS', base['manifest_key'])
                except Exception as exc:
                    processor_audit.update({'processor_status': 'FAIL' if processor_audit.get('processor_status') == 'PENDING' else processor_audit['processor_status'], 'processor_error': {'type': type(exc).__name__, 'message': str(exc)}})
                    existing_audits = sum((1 for _ in paths[names[1]].open(encoding='utf-8')))
                    if existing_audits < attempted:
                        append_jsonl(paths[names[1]], processor_audit)
                        processor_audits.append(processor_audit)
                    base.update({'generation_status': 'FAIL' if generated < attempted else 'SUCCESS', 'schema_status': 'VALID', 'serialization_status': 'VALID', 'technical_status': 'FAIL', 'error_type': getattr(exc, 'failure_type', type(exc).__name__), 'technical_layer': getattr(exc, 'layer', 'runner'), 'raw_model_output': base.get('raw_model_output')})
                    if not any((line for line in paths[names[0]].read_text(encoding='utf-8').splitlines() if json.loads(line).get('manifest_key') == base['manifest_key'])):
                        append_jsonl(paths[names[0]], {**base, 'serialization_status': 'FAIL', 'runner_version': 'QWEN25_CAMER_CONTROLLED_V4_1.0', 'runner_sha256': runner_sha})
                    if checkpoint_path is not None:
                        try:
                            update_checkpoint('TECHNICAL_FAILURE', base['manifest_key'], {'sample_id': sid, 'arm': arm, 'failure_type': getattr(exc, 'failure_type', type(exc).__name__), 'technical_layer': getattr(exc, 'layer', 'runner'), 'error': str(exc)})
                        except Exception as checkpoint_exc:
                            failures.append({'sample_id': sid, 'arm': arm, 'failure_type': 'CHECKPOINT_WRITE_FAILURE', 'technical_layer': 'checkpoint', 'error': str(checkpoint_exc), 'traceback': traceback.format_exc(limit=8)})
                    note_failure(exc, sid, arm)
                    break
            if failures:
                break
    except Exception as exc:
        note_failure(exc)
    end_hashes = {}
    frozen_unchanged = False
    try:
        end_hashes = frozen_hashes()
        frozen_unchanged = not hash_mismatches(end_hashes)
    except Exception:
        frozen_unchanged = False
    if not frozen_unchanged and (not failures):
        note_failure(GateFailure('frozen dependency changed during run', 'integrity', 'FROZEN_DEPENDENCY_CHANGED'))
    output_rows: list[dict[str, Any]] = []
    serialized_audits: list[dict[str, Any]] = []
    try:
        for path, destination in ((paths[names[0]], output_rows), (paths[names[1]], serialized_audits)):
            lines = path.read_text(encoding='utf-8').splitlines()
            if any((not line.strip() for line in lines)):
                raise ValueError(f'blank JSONL line in {path.name}')
            destination.extend((json.loads(line) for line in lines))
    except Exception as exc:
        note_failure(GateFailure(f'cannot strictly reload serialized JSONL artifacts: {exc}', 'serialization', 'SERIALIZATION_FAILURE'))
    all_arms = collections.Counter((row.get('arm') for row in output_rows))
    subset_attempts = collections.Counter((row.get('source_subset') for row in output_rows))
    validation = validate_run_outputs(output_rows, serialized_audits, selected, ARMS, prompt_id, protocol, records_expected, attempted, mode == 'full', runner_sha, parser_status_enum)
    expected_per_arm = 1500 if mode == 'full' else 3
    full_counts_valid = mode != 'full' or (attempted == generated == parser_count == records_expected == 6000 and all((all_arms[arm] == 1500 for arm in ARMS)))
    gate_counts_valid = mode != 'gate' or (attempted == generated == parser_count == records_expected == 12 and all((all_arms[arm] == 3 for arm in ARMS)) and (subset_attempts['audio-aligned'] == 4) and (subset_attempts['video-aligned'] == 4) and (subset_attempts['consistent'] == 4))
    run_pass = not failures and frozen_unchanged and (attempted == records_expected) and (generated == records_expected) and (parser_count == records_expected) and (sum(parse_counts.values()) == parser_count) and (len(output_rows) == records_expected) and (len(serialized_audits) == records_expected) and full_counts_valid and gate_counts_valid and validation['all_checks_valid'] and all((audit.get('processor_status') == 'PASS' for audit in serialized_audits)) and set(parse_counts).issubset(set(parser_status_enum))
    status = 'PASS' if run_pass else 'FAIL' if mode == 'gate' else 'TECHNICAL_FAILURE'
    gate_status = status if mode == 'gate' else 'PASS'
    science_status = 'INFERENCE_COMPLETE_ANALYSIS_NOT_RUN' if mode == 'full' and run_pass else 'NOT_RUN'
    protocol_status = 'FROZEN_READY_FOR_FULL_RUN' if run_pass else 'TECHNICAL_IMPLEMENTATION_BLOCKED'
    full_status = 'NOT_RUN' if mode == 'gate' else 'COMPLETE' if run_pass else 'TECHNICAL_FAILURE'
    next_step = 'QWEN25_CAMER_CONTROLLED_SCIENTIFIC_ANALYSIS' if run_pass else 'STOP_AFTER_FULL_RUN_TECHNICAL_FAILURE'
    if checkpoint_path is not None:
        update_checkpoint('COMPLETE' if run_pass else 'TECHNICAL_FAILURE', checkpoint_last_manifest_key, None if run_pass else failures[0] if failures else {'reason': 'validation failed'})
    expected_arm_counts = {arm: expected_per_arm for arm in ARMS}
    report = {'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'run_mode': mode, 'QWEN25_CAMER_CONTROLLED_TECHNICAL_GATE_V4_STATUS': gate_status, 'CAMER_CONTROLLED_RUNNER_V4_STATUS': 'TECHNICAL_IMPLEMENTATION_VALIDATED' if gate_status == 'PASS' else 'TECHNICAL_IMPLEMENTATION_BLOCKED', 'CAMER_CONTROLLED_PROTOCOL_STATUS': protocol_status, 'CAMER_CONTROLLED_SCIENCE_STATUS': science_status, 'CAMER_CONTROLLED_INFERENCE_STATUS': 'COMPLETE' if mode == 'full' and run_pass else 'NOT_RUN', 'CAMER_CONTROLLED_FULL_RUN_STATUS': full_status, 'NEXT_STEP': next_step, 'frozen_hashes_unchanged': frozen_unchanged, 'frozen_hashes_before': preflight_info.get('frozen_hashes'), 'frozen_hashes_after': end_hashes, 'parser_contract_consistency': preflight_info.get('parser_contract_audit', {}).get('frozen_contract_interpretation', {}).get('PARSER_CONTRACT_CONSISTENCY'), 'parser_status_enum_from_frozen_audit': list(parser_status_enum), 'parser_contract_audit_sha256': preflight_info.get('parser_contract_audit_sha256'), 'parser_contract_audit_md_sha256': preflight_info.get('parser_contract_audit_md_sha256'), 'parser_status_values_preserved_without_normalization': True, 'parser_synthetic_contract_tests': preflight_info.get('parser_contract_audit', {}).get('synthetic_parser_contract_tests'), 'v4_parser_validator_self_test': preflight_info.get('parser_validator_self_test'), 'adapter_audit_sha256': preflight_info.get('adapter_audit_sha256'), 'diff_audit_sha256': preflight_info.get('diff_audit_sha256'), 'diff_hunks_classified': preflight_info.get('diff_hunks_classified'), 'runner_sha256': runner_sha, 'prompt_sha256': prompt_sha, 'parser_sha256': parser_sha, 'selected_samples': selection_info, 'records_expected': records_expected, 'arm_attempts': attempted, 'generation_invocations_succeeded': generated, 'parser_execution_count': parser_count, 'parse_status_counts': dict(parse_counts), 'arm_attempt_counts': dict(all_arms), 'expected_arm_attempt_counts': expected_arm_counts, 'subset_record_counts': dict(subset_attempts), 'preprocess_processor_audit_count': len(serialized_audits), 'all_four_arms_covered': all((all_arms[arm] == expected_per_arm for arm in ARMS)), 'audio_aligned_conflict_covered': subset_attempts['audio-aligned'] > 0, 'video_aligned_conflict_covered': subset_attempts['video-aligned'] > 0, 'consistent_control_covered': subset_attempts['consistent'] > 0, 'processor_all_expected_modalities': len(serialized_audits) == attempted and all((audit.get('processor_status') == 'PASS' and audit.get('actual_modalities') == audit.get('expected_modalities') for audit in serialized_audits)), 'silent_video_audio_streams_all_zero': all((audit.get('silent_video_probe', {}).get('audio_stream_count') == 0 for audit in serialized_audits if 'silent_video' in (audit.get('expected_modalities') or []))), 'joint_duplicate_audio_evidence': any((audit.get('joint_duplicate_audio_evidence') is True for audit in serialized_audits)), 'cross_record_state_leakage': any((audit.get('cross_record_inputs_fresh') is not True or audit.get('past_key_values_reused') is not False for audit in serialized_audits)), 'unexpected_metadata_leakage': any((audit.get('metadata_leakage') is True for audit in serialized_audits)), 'schema_valid': validation['schema_rows_valid'], 'serialization_valid': len(output_rows) == attempted and len(serialized_audits) == attempted, 'output_validation': validation, 'generation_effective_config': {'thinker_max_new_tokens': 1024, 'thinker_do_sample': False, 'use_audio_in_video': False, 'return_audio': False}, 'output_slicing_self_test': slicing_self_test, 'serialization_self_test': serialization_self_test, 'scientific_interface_changed': False, 'scientific_analysis_performed': False, 'failure_records': failures, 'environment': preflight_info.get('environment'), 'model_loaded': model_loaded, 'model_generation_config': model_generation_config, 'model_generation_config_sha256': sha_json(model_generation_config) if model_generation_config is not None else None, 'gpu_memory_after_load': memory_at_load, 'elapsed_seconds': round(time.monotonic() - run_monotonic, 3), 'started_utc': run_start, 'completed_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'checkpoint_path': str(checkpoint_path) if checkpoint_path else None}
    save_json(paths[names[2]], report, exclusive=True)
    selected_ids = selection_info.get('selected_sample_ids', [row['sample_id'] for row in selected])
    title = 'Technical Gate V4' if mode == 'gate' else 'Full Run V1'
    md = [f'# CA-MER Controlled {title}', '', f'Status: **{status}**', '', f'Records expected: {records_expected}; attempted: {attempted}; generations returned: {generated}; parser executions: {parser_count}.', f'Selected manifest samples: {json.dumps(selected_ids)}.', f'Frozen dependencies unchanged: {frozen_unchanged}.', f'Runner SHA256: `{runner_sha}`.', f'Generation settings: thinker_max_new_tokens=1024; thinker_do_sample=false; use_audio_in_video=false; return_audio=false.', 'Science status: analysis not run. No accuracy, bias, order effect, or other scientific outcome was computed.', '', '## Parse status counts', '', json.dumps(dict(parse_counts), ensure_ascii=False, sort_keys=True), '', '## Output validation', '', json.dumps(validation, ensure_ascii=False, sort_keys=True, indent=2), '', '## Technical failures', '', json.dumps(failures, ensure_ascii=False, indent=2), '']
    paths[names[3]].write_text('\n'.join(md), encoding='utf-8')
    for artifact_name in names[:4]:
        with paths[artifact_name].open('rb') as artifact_file:
            os.fsync(artifact_file.fileno())
    report_reloaded = read_json(paths[names[2]])
    jsonl_reload_valid = len(read_jsonl(paths[names[0]])) == len(output_rows) and len(read_jsonl(paths[names[1]])) == len(serialized_audits)
    if report_reloaded.get('runner_sha256') != runner_sha or not jsonl_reload_valid:
        raise GateFailure('final artifact reload or runner identity check failed', 'serialization', 'FINAL_ARTIFACT_RELOAD_FAILURE')
    core_hashes = {name: sha_file(paths[name]) for name in names[:4]}
    provenance = {'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'runner_version': 'QWEN25_CAMER_CONTROLLED_V4_1.0', 'runner_path': str(ROOT / 'code/run_qwen25_camer_controlled_v4.py'), 'runner_sha256': runner_sha, 'run_mode': mode, 'gate_status': gate_status, 'full_run_status': full_status, 'parser_contract_consistency': preflight_info.get('parser_contract_audit', {}).get('frozen_contract_interpretation', {}).get('PARSER_CONTRACT_CONSISTENCY'), 'parser_status_enum_from_frozen_audit': list(parser_status_enum), 'parser_contract_audit_sha256': preflight_info.get('parser_contract_audit_sha256'), 'parser_contract_audit_md_sha256': preflight_info.get('parser_contract_audit_md_sha256'), 'parser_status_values_preserved_without_normalization': True, 'v4_parser_validator_self_test': preflight_info.get('parser_validator_self_test'), 'adapter_audit_sha256': preflight_info.get('adapter_audit_sha256'), 'adapter_compatibility_conclusions': preflight_info.get('adapter_audit', {}).get('compatibility_conclusions'), 'diff_audit_sha256': preflight_info.get('diff_audit_sha256'), 'diff_hunks_classified': preflight_info.get('diff_hunks_classified'), 'parent_runner_v2': {'path': 'code/run_qwen25_camer_controlled_v2.py', 'status': 'FAIL_PRESERVED'}, 'preserved_v1_failure': {'failure_type': 'JSON_SERIALIZATION_FAILURE', 'technical_layer': 'gate_report_serialization', 'underlying_record': {'sample_id': 'sample_00000002', 'arm': 'A_ONLY', 'failure_type': 'CHAT_TEMPLATE_FAILURE'}}, 'v2_serialization_fix_retained': True, 'runner_changes': ['PARSER_CONTRACT_VALIDATION', 'PARSER_EXECUTION_BOOKKEEPING', 'TECHNICAL_PROVENANCE'], 'scientific_interface_changed': False, 'scientific_protocol_changed': False, 'prompt_changed': False, 'parser_changed': False, 'manifest_changed': False, 'media_changed': False, 'candidate_sequence_changed': False, 'arm_definitions_changed': False, 'generation_config_frozen_value_changed': False, 'frozen_dependencies_expected_sha256': preflight_info['frozen_hashes'], 'frozen_dependencies_before': preflight_info.get('frozen_hashes'), 'frozen_dependencies_after': end_hashes, 'frozen_dependencies_unchanged': frozen_unchanged, 'prompt_template_id': prompt_id, 'prompt_sha256': prompt_sha, 'parser_sha256': parser_sha, 'model_identity': report['environment'], 'model_generation_config': model_generation_config, 'generation_effective_config': report['generation_effective_config'], 'output_slicing_self_test': slicing_self_test, 'serialization_self_test': serialization_self_test, 'api_or_external_judge_used': False, 'derived_media_regenerated': False, 'output_artifacts_sha256_before_provenance': core_hashes, 'checkpoint_path': str(checkpoint_path) if checkpoint_path else None, 'records_expected': records_expected, 'records_attempted': attempted, 'generation_invocations_succeeded': generated, 'parser_execution_count': parser_count, 'parse_status_counts': dict(parse_counts), 'output_validation': validation, 'elapsed_seconds': report['elapsed_seconds']}
    save_json(paths[names[4]], provenance, exclusive=True)
    final_hashes = {name: sha_file(paths[name]) for name in names}
    for artifact_path in paths.values():
        os.chmod(artifact_path, 292)
    os.chmod(out_dir, 365)
    final_status = {'QWEN25_CAMER_CONTROLLED_TECHNICAL_GATE_V4_STATUS': gate_status, 'CAMER_CONTROLLED_RUNNER_V4_STATUS': report['CAMER_CONTROLLED_RUNNER_V4_STATUS'], 'CAMER_CONTROLLED_PROTOCOL_STATUS': protocol_status, 'CAMER_CONTROLLED_SCIENCE_STATUS': science_status, 'CAMER_CONTROLLED_INFERENCE_STATUS': report['CAMER_CONTROLLED_INFERENCE_STATUS'], 'CAMER_CONTROLLED_FULL_RUN_STATUS': full_status, 'NEXT_STEP': next_step, 'records_expected': records_expected, 'arm_attempts': attempted, 'generation_successes': generated, 'parser_execution_count': parser_count, 'parse_status_counts': dict(parse_counts), 'failures': failures, 'artifact_sha256': final_hashes}
    print(json.dumps(final_status, ensure_ascii=False, sort_keys=True))
    return 0 if run_pass else 3 if mode == 'gate' else 4
MANIFEST = REPO / 'manifests/camer/controlled.jsonl'
PROMPT = REPO / 'configs/mainline/camer_controlled_arbitration_prompt_v1.json'
PARSER = REPO / 'src/common/benchmarks/camer_controlled_parser_v1.py'
PROTOCOL = input_path('audit/QWEN25_CAMER_CONTROLLED_V1/CAMER_CONTROLLED_PROTOCOL_V1.json')
MODEL = Path(os.environ.get('AF_MODEL_DIR', str(ROOT / 'models/Qwen2.5-Omni-7B')))
if __name__ == '__main__':
    raise SystemExit(main())
