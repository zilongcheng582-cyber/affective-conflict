"""EmotionTalk reliability intervention v1 — fail-closed, resumable trial executor.

Reuses the frozen kernels unchanged:
  * unimodal A_ONLY / V_ONLY: src.emotiontalk.phase1.execution.perform_arm
    (greedy generation, frozen parser, teacher-forced 7-label scoring -> normalized entropy);
  * joint A_THEN_V / V_THEN_A: src.emotiontalk.phase2.execution.execute_pairwise_record
    (greedy generation, frozen parser, canonical SIDE_A / SIDE_V / OTHER / PARSE_FAIL);
  * secondary joint scoring: phase1 score_candidate_strings applied to the same rendered joint prompt.
Model loading: src.emotiontalk.runtime.load (frozen runtime verification, b3_runtime.json model loading).

CPU dry-run (default; no model import):
  python -m src.emotiontalk.reliability_v1.run --phase pilot --output-dir /new/dir [--binding B.csv --binding-sha256 H]
GPU (separately authorized only):
  python -m src.emotiontalk.reliability_v1.run --phase pilot --binding B.csv --binding-sha256 H --output-dir /new/dir --execute-gpu
Resume: rerun the identical command; completed trial_ids are skipped after lock verification.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

from src.emotiontalk.reliability_v1 import design

KERNEL_FILES = ('src/emotiontalk/phase1/execution.py', 'src/emotiontalk/phase2/execution.py', 'src/emotiontalk/phase2/core.py',
                'src/emotiontalk/runtime.py', 'src/common/benchmarks/emotiontalk_controlled_parser_v1.py',
                'configs/mainline/emotiontalk_controlled_prompt_v1.json', 'configs/mainline/b3_runtime.json')
TECHNICAL_OK_JOINT = {'SIDE_MODALITY_1', 'SIDE_MODALITY_2', 'OTHER', 'PARSE_FAIL'}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load_manifest(phase):
    """Regenerate the manifest in memory and require byte equality with the frozen file and freeze record."""
    elig, trials = design.build()
    frozen = design.MANIFEST_CSV.read_bytes()
    if design.to_csv_bytes(trials) != frozen:
        raise SystemExit('FAIL_CLOSED: frozen manifest does not regenerate identically')
    rec = json.loads(design.FREEZE_RECORD.read_text(encoding='utf-8'))
    rel = str(design.MANIFEST_CSV.relative_to(design.REPO))
    if design.sha256_bytes(frozen) != rec['files'][rel]:
        raise SystemExit('FAIL_CLOSED: manifest SHA256 differs from DESIGN_FREEZE_RECORD_V1.json')
    for p, h in rec['inputs'].items():
        if sha_file(design.REPO / p) != h:
            raise SystemExit('FAIL_CLOSED: design input changed: ' + p)
    rows = list(csv.DictReader(frozen.decode('utf-8').splitlines()))
    key = 'execution_rank_' + phase
    rows = [r for r in rows if r[key] != '']
    rows.sort(key=lambda r: int(r[key]))
    return rows, design.sha256_bytes(frozen)


def load_binding(path, expected_sha):
    if sha_file(path) != expected_sha:
        raise SystemExit('FAIL_CLOSED: binding SHA256 differs from --binding-sha256')
    with open(path, encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    b = {}
    for r in rows:
        k = (r['utterance_id'], r['condition'])
        if k in b:
            raise SystemExit('FAIL_CLOSED: duplicate binding row ' + str(k))
        b[k] = r
    return b


def check_binding_covers(trials, binding):
    missing = sorted({(t['utterance_id'], t['condition']) for t in trials if t['arm'] != 'V_ONLY'} - set(binding))
    missing += sorted({(t['utterance_id'], 'CLEAN') for t in trials} - set(binding))
    if missing:
        raise SystemExit('FAIL_CLOSED: binding lacks rows, e.g. ' + str(missing[:3]))
    for t in trials:
        b = binding[(t['utterance_id'], 'CLEAN')]
        if b['silent_video_sha256'] != t['silent_video_sha256_frozen']:
            raise SystemExit('FAIL_CLOSED: binding silent-video hash differs from frozen media manifest ' + t['utterance_id'])
        if str(b['noise_seed']) != str(t['audio_noise_seed']):
            raise SystemExit('FAIL_CLOSED: binding noise seed differs from manifest ' + t['utterance_id'])


class HashCache:
    """Hash each file once per process, then re-verify size+mtime on every use (fail-closed on change)."""
    def __init__(self):
        self.seen = {}

    def verify(self, path, expected):
        st = os.stat(path)
        key = (str(path), st.st_size, st.st_mtime_ns)
        if key not in self.seen:
            self.seen[key] = sha_file(path)
        if self.seen[key] != expected:
            raise SystemExit(f'FAIL_CLOSED: identity mismatch for {path}')


def build_inputs(t, binding, hashes):
    """Map one manifest trial to the exact dict contracts of the frozen kernels; verify media identities."""
    clean = binding[(t['utterance_id'], 'CLEAN')]
    labels = t['candidate_sequence'].split('|')
    if sorted(labels) != sorted(design.ONTOLOGY):
        raise SystemExit('FAIL_CLOSED: candidate sequence is not the frozen ontology')
    video = clean['silent_video_path']
    hashes.verify(video, t['silent_video_sha256_frozen'])
    audio_path = None
    if t['arm'] != 'V_ONLY':
        b = binding[(t['utterance_id'], t['condition'])]
        audio_path = b['intervention_audio_path']
        hashes.verify(audio_path, b['intervention_audio_sha256'])
        if t['condition'] == 'CLEAN' and b['intervention_audio_sha256'] != clean['source_audio_sha256']:
            raise SystemExit('FAIL_CLOSED: CLEAN must use the bound original file')
    text_path = clean['text_json_path']
    hashes.verify(text_path, clean['text_json_sha256'])
    sample = {'utterance_id': t['utterance_id'], 'resource_tier': design.EXPERIMENT_ID,
              'candidate_sequence_id': t['candidate_sequence_id'], 'candidate_sequence': t['candidate_sequence'],
              'candidate_labels': labels, 'text': None, 'text_json_path': text_path, 'text_path': text_path,
              'audio_path': audio_path or clean['source_audio_path'], 'silent_video_path': video,
              'audio_emotion': t['y_A'], 'video_emotion': t['y_V'], 'text_emotion': None,
              'y_M1': t['y_A'], 'y_M2': t['y_V'], 'labels_by_modality': {'A': t['y_A'], 'V': t['y_V']},
              'video_preflight_error': None, 'video_duration': None, 'resource_rank_within_pair': None}
    if t['arm'] in ('A_ONLY', 'V_ONLY'):
        return 'UNIMODAL', sample
    first, second = t['arm'].split('_THEN_')
    refs = {'A': audio_path, 'V': video}
    rec = {'utterance_id': t['utterance_id'], 'pair': 'AV', 'stratum': 'conflict', 'arm': t['arm'],
           'evidence_1_modality': first, 'evidence_1_reference': refs[first],
           'evidence_2_modality': second, 'evidence_2_reference': refs[second],
           'instruction_position': 'AFTER_EVIDENCE_2', 'candidate_sequence_id': t['candidate_sequence_id'],
           'candidate_sequence': t['candidate_sequence'], 'candidate_labels': labels,
           'y_M1': t['y_A'], 'y_M2': t['y_V'], 'source_relation': 'CONFLICT',
           'audio_path': audio_path, 'text_path': text_path, 'silent_video_path': video, 'video_duration': None,
           'resource_proxy': None, 'resource_rank_within_pair': None, 'sample': sample}
    return 'JOINT', rec


def score_joint(rec, sample, prompt, processor, model, torch, process_mm_info):
    """Secondary endpoint: teacher-forced 7-label probabilities for the identical joint prompt."""
    from src.emotiontalk.phase1 import execution as e1
    from src.emotiontalk.phase2 import core as p2core
    from src.emotiontalk.phase2.execution import normalize_template_result
    messages = p2core.build_messages(rec, prompt)
    rendered, _ = normalize_template_result(processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
    audios, images, videos = process_mm_info(messages, use_audio_in_video=False)
    inputs = processor(text=rendered, audio=audios, images=images, videos=videos, return_tensors='pt', padding=True,
                       use_audio_in_video=False).to(model.device).to(model.dtype)
    s = e1.score_candidate_strings(rendered, inputs, sample, 'A_ONLY', processor, model, torch)
    probs = {k: v['probability_mean_score_primary'] for k, v in s['candidate_scores'].items()}
    return {'joint_scoring_status': 'OK', 'joint_p_audio_label': probs[sample['audio_emotion']],
            'joint_p_video_label': probs[sample['video_emotion']], 'joint_candidate_probabilities_primary': probs,
            'joint_entropy_normalized_primary': s['candidate_entropy_primary']['normalized_by_log7'],
            'joint_scoring_forward_calls': s['candidate_scoring_forward_calls']}


def lock_fingerprint(phase, manifest_sha, binding_sha):
    files = {p: sha_file(design.REPO / p) for p in KERNEL_FILES + ('src/emotiontalk/reliability_v1/run.py',
                                                                  'src/emotiontalk/reliability_v1/design.py')}
    body = {'experiment_id': design.EXPERIMENT_ID, 'phase': phase, 'manifest_sha256': manifest_sha,
            'binding_sha256': binding_sha, 'code_sha256': files}
    return design.sha256_bytes(json.dumps(body, sort_keys=True).encode()), body


def technical_failure(rec):
    if rec['role'] == 'UNIMODAL_MEASUREMENT':
        return not (rec.get('generation_success') and rec.get('candidate_scoring_status') == 'OK')
    return rec.get('joint_outcome') not in TECHNICAL_OK_JOINT


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--phase', choices=('pilot', 'full'), required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--binding', type=Path)
    ap.add_argument('--binding-sha256')
    ap.add_argument('--execute-gpu', action='store_true')
    ap.add_argument('--retry-technical-failures', action='store_true',
                    help='one identical re-execution of trials whose latest attempt is a technical failure')
    ap.add_argument('--max-trials', type=int, default=None, help='stop after N new trials (checkpointed); for resumable batches')
    a = ap.parse_args()
    trials, manifest_sha = load_manifest(a.phase)
    plan = {'phase': a.phase, 'trials': len(trials), 'items': len({t['utterance_id'] for t in trials}),
            'by_arm': dict(Counter(t['arm'] for t in trials)), 'by_condition': dict(Counter(t['condition'] for t in trials)),
            'generate_calls': len(trials), 'teacher_forced_scoring_passes': len(trials), 'manifest_sha256': manifest_sha}
    binding = None
    if a.binding:
        binding = load_binding(a.binding, a.binding_sha256)
        check_binding_covers(trials, binding)
        hashes = HashCache()
        for t in trials:
            build_inputs(t, binding, hashes)
        plan['binding_identity_check'] = 'PASS_ALL_TRIAL_MEDIA_HASHES'
    if not a.execute_gpu:
        print(json.dumps({'status': 'CPU_DRY_RUN_PASS', 'GPU_executed': False, **plan}, indent=1))
        return
    if binding is None:
        raise SystemExit('FAIL_CLOSED: GPU execution requires --binding and --binding-sha256')
    fp, body = lock_fingerprint(a.phase, manifest_sha, a.binding_sha256)
    out = a.output_dir
    lock = out / 'RUN_LOCK.json'
    log = out / 'trials.jsonl'
    if out.exists():
        if json.loads(lock.read_text())['fingerprint'] != fp:
            raise SystemExit('FAIL_CLOSED: resume lock fingerprint differs (code, manifest, binding or phase changed)')
    else:
        out.mkdir(parents=True)
        lock.write_text(json.dumps({'fingerprint': fp, **body, 'created_unix': time.time()}, indent=1))
    done = {}
    if log.exists():
        for line in open(log, encoding='utf-8'):
            r = json.loads(line)
            if r['run_fingerprint'] != fp:
                raise SystemExit('FAIL_CLOSED: checkpoint record from a different run')
            done.setdefault(r['trial_id'], []).append(r)
    todo = []
    for t in trials:
        prev = done.get(t['trial_id'])
        if not prev:
            todo.append((t, 1))
        elif a.retry_technical_failures and len(prev) == 1 and prev[-1]['technical_failure']:
            todo.append((t, 2))
    from src.emotiontalk.runtime import load
    from src.emotiontalk.phase1 import execution as e1
    from src.emotiontalk.phase2 import execution as e2, core as p2core
    torch, process_mm_info, processor, model = load()
    parse = p2core.load_parser()
    prompt = p2core.read_json(p2core.PROMPT_PATH)
    hashes = HashCache()
    counters = Counter()
    n_new = 0
    with open(log, 'a', encoding='utf-8') as f:
        for t, attempt in todo:
            if a.max_trials is not None and n_new >= a.max_trials:
                break
            kind, obj = build_inputs(t, binding, hashes)  # re-verifies media identity at use time
            started = time.time()
            if kind == 'UNIMODAL':
                r = e1.perform_arm(obj, t['arm'], prompt, processor, model, torch, process_mm_info, parse, counters)
            else:
                r = e2.execute_pairwise_record(obj, int(t['execution_rank_' + a.phase]), processor, model, torch,
                                               process_mm_info, parse, prompt)
                try:
                    r.update(score_joint(obj, obj['sample'], prompt, processor, model, torch, process_mm_info))
                except Exception as exc:
                    r.update({'joint_scoring_status': 'FAILED', 'joint_scoring_error': repr(exc),
                              'joint_scoring_traceback': traceback.format_exc()})
            r = p2core.jsonable(r)
            r.update({k: t[k] for k in ('trial_id', 'utterance_id', 'condition', 'arm', 'role', 'y_A', 'y_V',
                                        'target_snr_db', 'degradation_level', 'audio_variant')})
            r.update({'attempt': attempt, 'run_fingerprint': fp, 'wall_started_unix': started,
                      'experiment_id': design.EXPERIMENT_ID, 'phase': a.phase})
            r['technical_failure'] = technical_failure(r)
            f.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n')
            f.flush()
            os.fsync(f.fileno())
            n_new += 1
    print(json.dumps({'status': 'BATCH_DONE', 'new_records': n_new, 'remaining': len(todo) - n_new}, indent=1))


if __name__ == '__main__':
    main()
