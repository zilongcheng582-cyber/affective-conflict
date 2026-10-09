"""EmotionTalk reliability intervention v1: frozen design constants and deterministic manifest builder.

CPU only. Builds the eligibility table and the frozen trial manifest from repository data alone.
Nothing here reads model outputs of the intervention (which do not exist yet). Historical Phase1
readability defines the population exactly as the original Phase2 AV population was defined.

  python -m src.emotiontalk.reliability_v1.design --write   # (re)generate design assets (design author only)
  python -m src.emotiontalk.reliability_v1.design --verify  # fail-closed: regenerate in memory, compare to frozen files
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
EXP = REPO / 'experiments/emotiontalk_reliability_v1'
ELIGIBILITY_CSV = EXP / 'ELIGIBILITY_AND_SAMPLING_V1.csv'
MANIFEST_CSV = EXP / 'FROZEN_TRIAL_MANIFEST_V1.csv'
FREEZE_RECORD = EXP / 'DESIGN_FREEZE_RECORD_V1.json'

EXPERIMENT_ID = 'EMOTIONTALK_RELIABILITY_INTERVENTION_V1'
DESIGN_SEED = 20261009
PAIR = 'AV'
ONTOLOGY = ('angry', 'disgusted', 'fearful', 'happy', 'neutral', 'sad', 'surprised')
# Condition name -> (audio variant, target SNR in dB or None). Locked before any GPU execution.
CONDITIONS = {
    'CLEAN': ('ORIGINAL_FILE', None),
    'RECODE': ('PIPELINE_16K_NO_NOISE', None),
    'SNR20': ('PIPELINE_16K_WHITE_NOISE', 20.0),
    'SNR10': ('PIPELINE_16K_WHITE_NOISE', 10.0),
    'SNR00': ('PIPELINE_16K_WHITE_NOISE', 0.0),
}
DEGRADATION_LEVEL = {'RECODE': 0, 'SNR20': 1, 'SNR10': 2, 'SNR00': 3}  # ordinal; CLEAN is the pipeline control reference
ARMS_PER_CONDITION = ('A_ONLY', 'A_THEN_V', 'V_THEN_A')
VIDEO_ONLY_CONDITION = 'CLEAN'  # video is never modified; measured once
PILOT_ITEMS_PER_PATTERN = 2
INPUTS = {
    'source_measurements': 'manifests/emotiontalk/source_measurements.csv',
    'master_panel': 'manifests/emotiontalk/EMOTIONTALK_MASTER_PANEL_V1.csv',
    'media_manifest': 'manifests/emotiontalk/EMOTIONTALK_MEDIA_MANIFEST_V1.csv',
    'phase2_responses': 'evidence/emotiontalk/phase2_observed_responses.jsonl',
    'candidate_sequences': 'protocols/emotiontalk/EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json',
}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def derived_seed(*parts):
    """Stable 63-bit seed; independent of Python hash randomization."""
    payload = '|'.join(str(p) for p in (DESIGN_SEED,) + parts).encode('utf-8')
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big') & ((1 << 63) - 1)


def noise_seed(utterance_id):
    """One base white-noise realization per item, rescaled for every SNR level (nested design)."""
    return derived_seed(utterance_id, 'AUDIO_WHITE_NOISE_V1')


def _csv(rel):
    with open(REPO / rel, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def truth(x):
    return str(x).strip().upper() == 'TRUE'


def build():
    meas = {r['utterance_id']: r for r in _csv(INPUTS['source_measurements'])}
    panel = {r['utterance_id']: r for r in _csv(INPUTS['master_panel'])}
    media = {r['utterance_id']: r for r in _csv(INPUTS['media_manifest'])}
    seqs = {s['candidate_sequence_id']: s['pipe'] for s in
            json.loads((REPO / INPUTS['candidate_sequences']).read_text(encoding='utf-8'))['sequences']}
    p2 = Counter()
    for line in open(REPO / INPUTS['phase2_responses'], encoding='utf-8'):
        r = json.loads(line)
        if r['pair'] == PAIR:
            p2[r['utterance_id']] += 1
    if not (len(meas) == len(panel) == len(media) == 1500):
        raise ValueError('Frozen 1,500-item panel identity changed')

    elig = []
    for uid in sorted(panel):
        p, m, md = panel[uid], meas[uid], media[uid]
        if (p['audio_emotion'], p['video_emotion'], p['text_emotion']) != (m['y_A'], m['y_V'], m['y_T']):
            raise ValueError('Panel/measurement label mismatch ' + uid)
        if p['candidate_sequence'] != m['candidate_sequence'] or seqs.get(p['candidate_sequence_id']) != p['candidate_sequence']:
            raise ValueError('Candidate sequence mismatch ' + uid)
        conflict = m['y_A'] != m['y_V']
        reasons = []
        if not conflict:
            reasons.append('AV_SOURCE_LABELS_CONSISTENT')
        if not truth(m['technical_complete_A']) or not truth(m['technical_complete_V']):
            reasons.append('PHASE1_TECHNICAL_INCOMPLETE')
        if not truth(m['Readable_A']):
            reasons.append('PHASE1_A_NOT_READABLE')
        if not truth(m['Readable_V']):
            reasons.append('PHASE1_V_NOT_READABLE')
        if md.get('validation_status') != 'PASS' or str(md.get('silent_audio_stream_count')) != '0':
            reasons.append('SILENT_VIDEO_NOT_CERTIFIED')
        eligible = not reasons
        if eligible != (conflict and truth(m['DualReadable_AV'])):
            raise ValueError('Eligibility disagrees with frozen DualReadable_AV definition ' + uid)
        if eligible and p2[uid] != 2:
            raise ValueError('Eligible item lacks the two historical Phase2 AV arms ' + uid)
        elig.append({'utterance_id': uid, 'speaker_id': p['speaker_id'], 'trimodal_pattern': p['trimodal_pattern'],
                     'y_A': m['y_A'], 'y_V': m['y_V'], 'y_T': m['y_T'], 'av_source_relation': 'CONFLICT' if conflict else 'CONSISTENT',
                     'technical_complete_A': m['technical_complete_A'], 'technical_complete_V': m['technical_complete_V'],
                     'Readable_A': m['Readable_A'], 'Readable_V': m['Readable_V'], 'DualReadable_AV': m['DualReadable_AV'],
                     'silent_video_validation': md.get('validation_status'), 'historical_phase2_AV_arm_count': p2[uid],
                     'candidate_sequence_id': p['candidate_sequence_id'], 'candidate_sequence': p['candidate_sequence'],
                     'eligible': eligible, 'exclusion_reasons': ';'.join(reasons),
                     'audio_path_frozen': p['audio_path'], 'silent_video_path_frozen': md['silent_video_path'],
                     'silent_video_sha256_frozen': md['silent_video_sha256']})

    eligible = [e for e in elig if e['eligible']]
    # Pilot: seeded selection stratified by trimodal pattern; uses no outcome or entropy information.
    rng = np.random.default_rng(derived_seed('PILOT_SELECTION'))
    pilot = set()
    for pattern in sorted({e['trimodal_pattern'] for e in eligible}):
        ids = sorted(e['utterance_id'] for e in eligible if e['trimodal_pattern'] == pattern)
        pilot.update(ids[i] for i in rng.choice(len(ids), PILOT_ITEMS_PER_PATTERN, replace=False))
    for e in elig:
        e['pilot_selected'] = e['utterance_id'] in pilot
        e['full_experiment_selected'] = e['eligible']  # ITT: every eligible item, including pilot items
        e['selection_basis'] = ('ELIGIBLE_ALL_INCLUDED' + (';PILOT_SEEDED_STRATIFIED' if e['utterance_id'] in pilot else '')
                                if e['eligible'] else 'EXCLUDED')

    trials = []
    for e in eligible:
        uid = e['utterance_id']
        base = {'experiment_id': EXPERIMENT_ID, 'utterance_id': uid, 'speaker_id': e['speaker_id'],
                'trimodal_pattern': e['trimodal_pattern'], 'pair': PAIR, 'y_A': e['y_A'], 'y_V': e['y_V'],
                'candidate_sequence_id': e['candidate_sequence_id'], 'candidate_sequence': e['candidate_sequence'],
                'audio_path_frozen': e['audio_path_frozen'], 'silent_video_path_frozen': e['silent_video_path_frozen'],
                'silent_video_sha256_frozen': e['silent_video_sha256_frozen'], 'audio_noise_seed': noise_seed(uid),
                'pilot_member': e['utterance_id'] in pilot}
        cells = [(VIDEO_ONLY_CONDITION, 'V_ONLY')] + [(c, a) for c in CONDITIONS for a in ARMS_PER_CONDITION]
        for cond, arm in cells:
            variant, snr = CONDITIONS[cond]
            uses_audio = arm != 'V_ONLY'
            trials.append({**base, 'trial_id': f'ERI1|{uid}|{cond}|{arm}', 'condition': cond, 'arm': arm,
                           'evidence_order': {'A_ONLY': 'A', 'V_ONLY': 'V', 'A_THEN_V': 'A>V', 'V_THEN_A': 'V>A'}[arm],
                           'role': 'UNIMODAL_MEASUREMENT' if arm in ('A_ONLY', 'V_ONLY') else 'JOINT_ARBITRATION',
                           'audio_variant': variant if uses_audio else 'NOT_USED',
                           'target_snr_db': '' if snr is None or not uses_audio else snr,
                           'degradation_level': DEGRADATION_LEVEL.get(cond, '') if uses_audio else '',
                           'intervention_audio_relpath': (f'audio/{cond}/{uid}.wav' if uses_audio and cond != 'CLEAN' else ''),
                           'video_input': 'FROZEN_SILENT_VIDEO_UNCHANGED' if arm != 'A_ONLY' else 'NOT_USED'})
    for scope, members in (('full', trials), ('pilot', [t for t in trials if t['pilot_member']])):
        order = np.random.default_rng(derived_seed('EXECUTION_ORDER', scope)).permutation(len(members))
        for rank, idx in enumerate(order, 1):
            members[idx]['execution_rank_' + scope] = rank
    for t in trials:
        t.setdefault('execution_rank_pilot', '')
    return elig, trials


def to_csv_bytes(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode('utf-8')


def summary(elig, trials):
    e = [x for x in elig if x['eligible']]
    return {'panel_items': len(elig), 'eligible_items': len(e), 'pilot_items': sum(x['pilot_selected'] for x in elig),
            'eligible_by_pattern': dict(Counter(x['trimodal_pattern'] for x in e)),
            'eligible_speakers': len({x['speaker_id'] for x in e}),
            'exclusion_counts': dict(Counter(x['exclusion_reasons'] for x in elig if not x['eligible'])),
            'trials_full': len(trials), 'trials_pilot': sum(t['pilot_member'] for t in trials),
            'trials_per_item': len(trials) // max(1, len(e)),
            'trials_by_arm': dict(Counter(t['arm'] for t in trials)),
            'trials_by_condition': dict(Counter(t['condition'] for t in trials))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--write', action='store_true')
    g.add_argument('--verify', action='store_true')
    g.add_argument('--freeze', action='store_true', help='write DESIGN_FREEZE_RECORD_V1.json (design author only)')
    a = ap.parse_args()
    elig, trials = build()
    eb, mb = to_csv_bytes(elig), to_csv_bytes(trials)
    if a.write:
        if FREEZE_RECORD.exists():
            raise SystemExit('Design is frozen; refusing to rewrite frozen assets')
        ELIGIBILITY_CSV.write_bytes(eb)
        MANIFEST_CSV.write_bytes(mb)
        print(json.dumps({'written': True, **summary(elig, trials),
                          'eligibility_sha256': sha256_bytes(eb), 'manifest_sha256': sha256_bytes(mb)}, indent=1))
        return
    if a.freeze:
        if FREEZE_RECORD.exists():
            raise SystemExit('Freeze record exists; a new design version requires a new experiment directory')
        if ELIGIBILITY_CSV.read_bytes() != eb or MANIFEST_CSV.read_bytes() != mb:
            raise SystemExit('Run --write first')
        frozen = {str(p.relative_to(REPO)): sha256_file(p) for p in sorted(EXP.glob('*')) if p.is_file() and p != FREEZE_RECORD}
        frozen.update({str(p.relative_to(REPO)): sha256_file(p) for p in sorted((REPO / 'src/emotiontalk/reliability_v1').glob('*.py'))})
        frozen['tests/test_reliability_v1.py'] = sha256_file(REPO / 'tests/test_reliability_v1.py')
        FREEZE_RECORD.write_text(json.dumps({'experiment_id': EXPERIMENT_ID, 'status': 'DESIGN_FROZEN_BEFORE_ANY_GPU_EXECUTION',
                                             'design_seed': DESIGN_SEED, 'inputs': {p: sha256_file(REPO / p) for p in INPUTS.values()},
                                             'files': frozen, 'summary': summary(elig, trials)}, indent=1, sort_keys=True) + '\n')
        print('FREEZE_RECORD_WRITTEN', sha256_file(FREEZE_RECORD))
        return
    rec = json.loads(FREEZE_RECORD.read_text(encoding='utf-8'))
    checks = {'eligibility_regenerates_identically': ELIGIBILITY_CSV.read_bytes() == eb,
              'manifest_regenerates_identically': MANIFEST_CSV.read_bytes() == mb,
              'eligibility_sha256_matches_freeze': sha256_bytes(eb) == rec['files'][str(ELIGIBILITY_CSV.relative_to(REPO))],
              'manifest_sha256_matches_freeze': sha256_bytes(mb) == rec['files'][str(MANIFEST_CSV.relative_to(REPO))],
              'inputs_match_freeze': all(sha256_file(REPO / p) == rec['inputs'][p] for p in INPUTS.values()),
              'all_frozen_files_unchanged': all(sha256_file(REPO / p) == h for p, h in rec['files'].items())}
    print(json.dumps({'checks': checks, **summary(elig, trials)}, indent=1))
    if not all(checks.values()):
        raise SystemExit('DESIGN_VERIFY_FAIL')


if __name__ == '__main__':
    main()
