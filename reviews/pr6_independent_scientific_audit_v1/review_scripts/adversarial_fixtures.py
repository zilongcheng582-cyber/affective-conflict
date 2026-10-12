"""Adversarial fixtures: perturb copies of the PUBLIC E1/E2 tables and record which verifier detects each defect.

Formal files are never edited: every fixture is a temporary copy. Two verifiers are run per fixture:
  PR6_REPLAY      the PR's own analyses/emotiontalk_e1_video_v2/replay.py (subprocess, isolated -I)
  AUDIT_REPLAY    this audit's review_scripts/independent_replay.py functions
Usage: python -I adversarial_fixtures.py <pr6_checkout> <main_checkout> <out_json>
"""
import csv, json, shutil, subprocess, sys, tempfile, pathlib, importlib.util

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('independent_replay', HERE / 'independent_replay.py')
IR = importlib.util.module_from_spec(spec); spec.loader.exec_module(IR)
E1DIR = 'results/emotiontalk_e1_video_v2'; E2DIR = 'results/emotiontalk_e2_consistent_audio_v1'


def read(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        r = list(csv.DictReader(f))
    return r


def write(p, rows):
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def sync_attempts(d, full):
    """Keep attempts.csv consistent with a perturbed full_outcomes so the perturbation is not trivially caught there."""
    at = read(d / 'attempts.csv'); fi = {r['trial_id']: r for r in full}
    at = [dict(a, parsed_label=fi[a['trial_id']]['parsed_label'], outcome=fi[a['trial_id']]['outcome']) for a in at if a['trial_id'] in fi]
    write(d / 'attempts.csv', at)


def pr6_replay(root, exp):
    out = root / 'pr6_replay_out.json'
    q = subprocess.run([sys.executable, '-I', '-B', str(PR6 / 'analyses/emotiontalk_e1_video_v2/replay.py'), '--repo-root', str(root), '--experiment', exp, '--output', str(out)], capture_output=True, text=True)
    return {'detected': q.returncode != 0, 'message': (q.stderr.strip().splitlines() or [''])[-1][:300]}


def audit_replay(root, exp):
    L = IR.Ledger()
    try:
        if exp == 'E1':
            _, cells, _ = IR.replay_e1(root, MAIN, L); IR.scoring_audit(root, L, 'E1', cells); IR.visual_audit(root, L, cells)
        else:
            _, cells, _ = IR.replay_e2(root, MAIN, L); IR.scoring_audit(root, L, 'E2', cells)
    except Exception as e:  # noqa: BLE001  structural breakage counts as detection
        return {'detected': True, 'failed_checks': ['EXCEPTION: ' + repr(e)[:200]]}
    fails = [x['check'] for x in L.items if x['status'] != 'PASS']
    return {'detected': bool(fails), 'failed_checks': fails[:8]}


def fixture(name, exp, mutate, note):
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        for sub in (E1DIR, E2DIR):
            shutil.copytree(PR6 / sub, root / sub)
        d = root / (E1DIR if exp == 'E1' else E2DIR)
        mutate(d)
        return {'fixture': name, 'experiment': exp, 'note': note, 'PR6_REPLAY': pr6_replay(root, exp), 'AUDIT_REPLAY': audit_replay(root, exp)}


# ---------------------------------------------------------------- mutations
def m_swap_candidate_labels_same_tokens(d):
    rows = read(d / 'candidate_probabilities.csv'); tid = rows[0]['trial_id']
    idx = {r['label']: i for i, r in enumerate(rows) if r['trial_id'] == tid}
    a, b = idx['happy'], idx['sad']            # both single-token labels
    rows[a]['label'], rows[b]['label'] = rows[b]['label'], rows[a]['label']
    write(d / 'candidate_probabilities.csv', rows)


def m_swap_candidate_labels_diff_tokens(d):
    rows = read(d / 'candidate_probabilities.csv'); tid = rows[0]['trial_id']
    idx = {r['label']: i for i, r in enumerate(rows) if r['trial_id'] == tid}
    a, b = idx['happy'], idx['fearful']        # 1 token vs 3 tokens
    rows[a]['label'], rows[b]['label'] = rows[b]['label'], rows[a]['label']
    write(d / 'candidate_probabilities.csv', rows)


def m_outcome_only(d):
    full = read(d / 'full_outcomes.csv')
    r = next(x for x in full if x['condition'] == 'BLUR_L3' and x['arm'] == 'A_THEN_V' and x['outcome'] == 'SIDE_A')
    r['outcome'] = 'SIDE_V'                     # label left unchanged -> internally inconsistent row
    write(d / 'full_outcomes.csv', full); sync_attempts(d, full)


def m_outcome_and_label(d):
    full = read(d / 'full_outcomes.csv')
    r = next(x for x in full if x['condition'] == 'BLUR_L3' and x['arm'] == 'A_THEN_V' and x['outcome'] == 'SIDE_A')
    r['outcome'] = 'SIDE_V'; r['parsed_label'] = r['y_V']   # consistent tamper; frozen JSON unchanged
    write(d / 'full_outcomes.csv', full); sync_attempts(d, full)


def m_delete_condition(d):
    full = [x for x in read(d / 'full_outcomes.csv') if not (x['utterance_id'] == 'G00001_02_02_020' and x['condition'] == 'BLUR_L2')]
    write(d / 'full_outcomes.csv', full)


def m_duplicate_trial(d):
    full = read(d / 'full_outcomes.csv'); full.append(dict(full[5])); write(d / 'full_outcomes.csv', full)


def m_other_to_parsefail(d):
    full = read(d / 'full_outcomes.csv')
    r = next(x for x in full if x['condition'] == 'BLUR_L3' and x['arm'] == 'V_THEN_A' and x['outcome'] == 'OTHER')
    r['outcome'] = 'PARSE_FAIL'; r['parsed_label'] = ''
    write(d / 'full_outcomes.csv', full); sync_attempts(d, full)


def m_swap_orders(d):
    full = read(d / 'full_outcomes.csv'); key = {}
    for x in full:
        key[x['utterance_id'], x['condition'], x['arm']] = x
    u = next(u for (u, c, a) in key if c == 'BLUR_L3' and a == 'A_THEN_V' and key[u, c, 'A_THEN_V']['outcome'] != key[u, c, 'V_THEN_A']['outcome'])
    a, b = key[u, 'BLUR_L3', 'A_THEN_V'], key[u, 'BLUR_L3', 'V_THEN_A']
    for f in ('outcome', 'parsed_label', 'entropy_normalized'):
        a[f], b[f] = b[f], a[f]
    write(d / 'full_outcomes.csv', full); sync_attempts(d, full)


def m_cluster(d):
    full = read(d / 'full_outcomes.csv'); uid = full[0]['utterance_id']
    other = next(x['dialogue_id'] for x in full if x['dialogue_id'] != full[0]['dialogue_id'])
    for x in full:
        if x['utterance_id'] == uid:
            x['dialogue_id'] = other
    write(d / 'full_outcomes.csv', full)
    man = read(d / 'manifest.csv')
    for x in man:
        if x['utterance_id'] == uid:
            x['dialogue_id'] = other
    write(d / 'manifest.csv', man)


def m_probability(d):
    rows = read(d / 'candidate_probabilities.csv'); tid = rows[0]['trial_id']; sub = [r for r in rows if r['trial_id'] == tid]
    sub[0]['probability_mean_score_primary'] = str(float(sub[0]['probability_mean_score_primary']) + 0.05)
    sub[1]['probability_mean_score_primary'] = str(float(sub[1]['probability_mean_score_primary']) - 0.05)
    write(d / 'candidate_probabilities.csv', rows)


def m_same_marginal_new_pairing(d):
    """Swap BLUR_L3 rows between two items with different outcomes: marginal L3 rates unchanged, pairing changed."""
    full = read(d / 'full_outcomes.csv'); key = {(x['utterance_id'], x['condition'], x['arm']): x for x in full}
    uids = sorted({x['utterance_id'] for x in full})
    pair = None
    for u in uids:
        for v in uids:
            if u < v and key[u, 'RECODE', 'A_THEN_V']['outcome'] == 'SIDE_V' and key[v, 'RECODE', 'A_THEN_V']['outcome'] == 'SIDE_A' \
                    and key[u, 'BLUR_L3', 'A_THEN_V']['outcome'] == 'SIDE_A' and key[v, 'BLUR_L3', 'A_THEN_V']['outcome'] == 'SIDE_V':
                pair = (u, v); break
        if pair:
            break
    u, v = pair; a, b = key[u, 'BLUR_L3', 'A_THEN_V'], key[v, 'BLUR_L3', 'A_THEN_V']
    a['outcome'], b['outcome'] = b['outcome'], a['outcome']
    a['parsed_label'], b['parsed_label'] = a['y_V'], b['y_A']   # keep each row self-consistent
    write(d / 'full_outcomes.csv', full); sync_attempts(d, full)


def m_swap_yA_yV_columns(d):
    for fn in ('full_outcomes.csv', 'manifest.csv'):
        rows = read(d / fn)
        for x in rows:
            x['y_A'], x['y_V'] = x['y_V'], x['y_A']
        write(d / fn, rows)


def m_swap_yA_yV_and_outcomes(d):
    """Systematic SIDE_A/SIDE_V mapping inversion, applied consistently to labels, outcomes and frozen JSON-free tables."""
    flip = {'SIDE_A': 'SIDE_V', 'SIDE_V': 'SIDE_A'}
    for fn in ('full_outcomes.csv', 'manifest.csv'):
        rows = read(d / fn)
        for x in rows:
            x['y_A'], x['y_V'] = x['y_V'], x['y_A']
            if 'outcome' in x:
                x['outcome'] = flip.get(x['outcome'], x['outcome'])
        write(d / fn, rows)


def m_visual_contract(d):
    rows = read(d / 'visual_input_contract.csv')
    r = next(x for x in rows if x['condition'] == 'BLUR_L3')
    r['sampled_frame_indices'] = r['sampled_frame_indices'].replace('[0,', '[1,')
    write(d / 'visual_input_contract.csv', rows)


def m_e2_video_changes(d):
    full = read(d / 'full_outcomes.csv')
    for x in full:
        if x['condition'] == 'A_SNR00' and x['utterance_id'] == full[0]['utterance_id']:
            x['video_sha256'] = '0' * 64
    write(d / 'full_outcomes.csv', full)
    man = read(d / 'manifest.csv')
    for x in man:
        if x['condition'] == 'A_SNR00' and x['utterance_id'] == full[0]['utterance_id']:
            x['video_sha256'] = '0' * 64
    write(d / 'manifest.csv', man)


def m_e2_other_as_parsefail(d):
    full = read(d / 'full_outcomes.csv')
    r = next(x for x in full if x['condition'] == 'A_SNR00' and x['outcome'] == 'OTHER' and x['arm'] != 'A_ONLY')
    r['outcome'] = 'PARSE_FAIL'; r['parsed_label'] = ''
    write(d / 'full_outcomes.csv', full); sync_attempts(d, full)


FIXTURES = [
    ('candidate_label_swap_same_token_count', 'E1', m_swap_candidate_labels_same_tokens, 'probabilities still sum to 1, entropy unchanged; label->score mapping wrong (happy<->sad)'),
    ('candidate_label_swap_diff_token_count', 'E1', m_swap_candidate_labels_diff_tokens, 'same as above but happy<->fearful (1 vs 3 tokens)'),
    ('outcome_changed_label_not', 'E1', m_outcome_only, 'one L3 SIDE_A outcome relabelled SIDE_V, parsed_label left'),
    ('outcome_and_label_changed', 'E1', m_outcome_and_label, 'self-consistent row tamper; frozen JSON statistics unchanged'),
    ('delete_condition', 'E1', m_delete_condition, 'remove BLUR_L2 rows for one item'),
    ('duplicate_trial', 'E1', m_duplicate_trial, 'one formal trial duplicated'),
    ('other_to_parse_fail', 'E1', m_other_to_parsefail, 'one OTHER recoded as PARSE_FAIL'),
    ('swap_order_results', 'E1', m_swap_orders, 'swap A_THEN_V and V_THEN_A L3 results for one item'),
    ('dialogue_cluster_changed', 'E1', m_cluster, 'one item moved to another dialogue cluster'),
    ('candidate_probability_shifted', 'E1', m_probability, '0.05 moved between two candidates, sum still 1'),
    ('same_marginals_different_pairing', 'E1', m_same_marginal_new_pairing, 'L3 outcomes swapped between two items; L3 marginal rate unchanged'),
    ('swap_yA_yV_columns_only', 'E1', m_swap_yA_yV_columns, 'source labels swapped, outcomes left'),
    ('swap_yA_yV_and_outcomes_consistently', 'E1', m_swap_yA_yV_and_outcomes, 'systematic SIDE mapping inversion, internally consistent'),
    ('visual_contract_frame_index_changed', 'E1', m_visual_contract, 'one BLUR_L3 sampled frame index changed'),
    ('E2_video_sha_changes_with_audio_condition', 'E2', m_e2_video_changes, 'video identity differs in A_SNR00 for one item'),
    ('E2_other_to_parse_fail', 'E2', m_e2_other_as_parsefail, 'one SNR00 OTHER recoded as PARSE_FAIL'),
]

if __name__ == '__main__':
    PR6, MAIN, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
    results = []
    for name, exp, fn, note in FIXTURES:
        r = fixture(name, exp, fn, note); results.append(r)
        print(f"{name:45s} PR6_REPLAY={'DETECT' if r['PR6_REPLAY']['detected'] else 'MISS':6s} AUDIT={'DETECT' if r['AUDIT_REPLAY']['detected'] else 'MISS'}", flush=True)
    # control: unperturbed copy must pass both
    results.insert(0, fixture('CONTROL_unmodified', 'E1', lambda d: None, 'no change'))
    results.insert(1, fixture('CONTROL_unmodified', 'E2', lambda d: None, 'no change'))
    OUT.write_text(json.dumps(results, indent=1))
