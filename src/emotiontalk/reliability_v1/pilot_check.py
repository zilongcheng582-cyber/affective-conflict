"""Technical pass/fail gates for the ERI1 GPU pilot (PILOT_PLAN_V1.md). Science-blind by construction:
no SIDE_A / SIDE_V / OTHER rates are computed or printed by condition.

  python -m src.emotiontalk.reliability_v1.pilot_check --pilot-dir PILOT_OUT --binding B.csv --binding-sha256 H
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from src.emotiontalk.reliability_v1 import design, run

ENTROPY_TOL = 0.01
STORED_SNR_TOL_DB = 0.01
LOADER_SNR_TOL_DB = 0.05


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pilot-dir', type=Path, required=True)
    ap.add_argument('--binding', type=Path, required=True)
    ap.add_argument('--binding-sha256', required=True)
    a = ap.parse_args()
    trials, msha = run.load_manifest('pilot')
    binding = run.load_binding(a.binding, a.binding_sha256)
    lock = json.loads((a.pilot_dir / 'RUN_LOCK.json').read_text())
    recs = [json.loads(line) for line in open(a.pilot_dir / 'trials.jsonl', encoding='utf-8')]
    latest = {}
    for r in recs:
        if r['trial_id'] not in latest or r['attempt'] > latest[r['trial_id']]['attempt']:
            latest[r['trial_id']] = r
    meas = {r['utterance_id']: r for r in csv.DictReader(open(design.REPO / design.INPUTS['source_measurements'], encoding='utf-8-sig'))}
    hist = {}
    for line in open(design.REPO / design.INPUTS['phase2_responses'], encoding='utf-8'):
        r = json.loads(line)
        if r['pair'] == 'AV':
            hist[(r['utterance_id'], r['arm'])] = r['parsed_label']
    g = {}
    g['G1_all_trials_recorded'] = set(latest) == {t['trial_id'] for t in trials}
    g['G1_no_duplicate_attempt_numbers'] = len(recs) == len({(r['trial_id'], r['attempt']) for r in recs})
    g['G2_zero_residual_technical_failures'] = sum(r['technical_failure'] for r in latest.values()) == 0
    g['G3_lock_matches_manifest_and_binding'] = (lock['manifest_sha256'] == msha and lock['binding_sha256'] == a.binding_sha256
                                                and lock['phase'] == 'pilot')
    clean_uni, clean_joint, ent_dev = [], [], []
    for t in trials:
        r = latest.get(t['trial_id'])
        if r is None or r['technical_failure'] or t['condition'] != 'CLEAN':
            continue
        m = meas[t['utterance_id']]
        if t['arm'] in ('A_ONLY', 'V_ONLY'):
            mod = t['arm'][0]
            clean_uni.append(r.get('parsed_label') == m['pred_' + mod])
            ent_dev.append(abs(r['candidate_entropy_primary']['normalized_by_log7'] - float(m['entropy_' + mod])))
        else:
            clean_joint.append(r.get('parsed_label') == hist[(t['utterance_id'], t['arm'])])
    g['G4a_clean_unimodal_labels_reproduce_phase1'] = bool(clean_uni) and all(clean_uni)
    g['G4b_clean_unimodal_entropy_within_tol'] = bool(ent_dev) and max(ent_dev) <= ENTROPY_TOL
    g['G4c_clean_joint_labels_reproduce_phase2_ge_11_of_12'] = sum(clean_joint) >= len(clean_joint) - 1 and len(clean_joint) == 12
    snr_ok, loader_ok = [], []
    for (uid, cond), b in binding.items():
        if cond.startswith('SNR') and uid in {t['utterance_id'] for t in trials}:
            target = float(b['target_snr_db'])
            snr_ok.append(abs(float(b['stored_file_snr_db']) - target) <= STORED_SNR_TOL_DB)
            if b.get('model_loader_snr_db'):
                loader_ok.append(abs(float(b['model_loader_snr_db']) - target) <= LOADER_SNR_TOL_DB)
    g['G5a_stored_snr_within_tol'] = bool(snr_ok) and all(snr_ok)
    g['G5b_model_loader_snr_checked_and_within_tol'] = bool(loader_ok) and all(loader_ok) and len(loader_ok) == len(snr_ok)
    used = Counter()
    for t in trials:
        r = latest.get(t['trial_id'])
        if r and t['arm'] != 'V_ONLY':
            path = r.get('evidence_path_used') or (r.get('input_evidence_references') or [None])[0 if t['arm'] != 'V_THEN_A' else 1]
            used[path == binding[(t['utterance_id'], t['condition'])]['intervention_audio_path']] += 1
    g['G6_each_trial_used_its_bound_audio_file'] = used.get(False, 0) == 0 and used.get(True, 0) > 0
    runtimes = [r.get('runtime_seconds') for r in latest.values() if r.get('runtime_seconds') is not None]
    peaks = [((r.get('gpu_after') or {}).get('peak_allocated_bytes')) for r in latest.values()]
    report = {'gates': g, 'PILOT_TECHNICAL_STATUS': 'PASS' if all(g.values()) else 'FAIL',
              'clean_reproduction_counts': {'unimodal_label_match': f'{sum(clean_uni)}/{len(clean_uni)}',
                                            'joint_label_match': f'{sum(clean_joint)}/{len(clean_joint)}',
                                            'max_entropy_abs_dev': max(ent_dev) if ent_dev else None},
              'parse_fail_count_all_conditions_pooled': sum(r.get('parser_status') == 'PARSE_FAIL' for r in latest.values()),
              'resource': {'trials': len(latest), 'runtime_seconds_sum': sum(runtimes),
                           'runtime_seconds_mean': sum(runtimes) / max(1, len(runtimes)),
                           'peak_allocated_bytes_max': max([p for p in peaks if p] or [None], key=lambda x: x or 0)},
              'science_outputs_computed': False}
    print(json.dumps(report, indent=1))
    if not all(g.values()):
        raise SystemExit('PILOT_TECHNICAL_FAIL')


if __name__ == '__main__':
    main()
