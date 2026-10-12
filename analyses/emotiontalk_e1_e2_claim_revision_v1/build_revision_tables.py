"""Build the claim-revision tables for E1 V2 / E2 from the reviewed public projections (CPU only).

No model, no media, no refit; frozen result files are read, never written.
Usage: python -I analyses/emotiontalk_e1_e2_claim_revision_v1/build_revision_tables.py --repo-root . --output-dir results/emotiontalk_e1_e2_claim_revision_v1
"""
import argparse, collections, csv, json, math, pathlib
from fractions import Fraction
import numpy as np

ORDERS = ('A_THEN_V', 'V_THEN_A')
E1_CONDS = ('CLEAN', 'RECODE', 'BLUR_L1', 'BLUR_L2', 'BLUR_L3')
E2_CONDS = ('A_CLEAN', 'A_RECODE', 'A_SNR20', 'A_SNR10', 'A_SNR00')
LABELS = ('angry', 'disgusted', 'fearful', 'happy', 'neutral', 'sad', 'surprised')


def rows(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write(path, data):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator='\n'); w.writeheader(); w.writerows(data)


def exact_signflip(d):
    """Exact two-sided paired sign-flip p over all 2^n sign vectors (values on a rational grid)."""
    fr = [Fraction(float(x)).limit_denominator(1000) for x in d]
    den = math.lcm(*[f.denominator for f in fr])
    ints = [abs(int(f * den)) for f in fr]
    total = sum(ints); p = np.zeros(2 * total + 1); p[total] = 1.0
    for v in ints:
        if v:
            q = np.zeros_like(p); q[v:] += .5 * p[:-v]; q[:-v] += .5 * p[v:]; p = q
    obs = abs(sum(int(f * den) for f in fr)); k = np.arange(-total, total + 1)
    return float(p[np.abs(k) >= obs].sum())


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); out = [0.0] * len(ps); run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - r) * ps[i])); out[i] = run
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo-root', type=pathlib.Path, required=True); ap.add_argument('--output-dir', type=pathlib.Path, required=True)
    a = ap.parse_args(); root = a.repo_root; out = a.output_dir; out.mkdir(parents=True, exist_ok=True)
    e1 = {(r['utterance_id'], r['condition'], r['arm']): r for r in rows(root / 'results/emotiontalk_e1_video_v2/full_outcomes.csv')}
    e2 = {(r['utterance_id'], r['condition'], r['arm']): r for r in rows(root / 'results/emotiontalk_e2_consistent_audio_v1/full_outcomes.csv')}
    u1 = sorted({k[0] for k in e1}); u2 = sorted({k[0] for k in e2})
    assert len(e1) == 2336 and len(u1) == 146 and len(e2) == 3375 and len(u2) == 225

    # 1. E1 V_ONLY output by source video label and condition (manipulation check content)
    t1 = []
    for c in E1_CONDS:
        for yv in sorted({e1[u, 'RECODE', 'V_ONLY']['y_V'] for u in u1}):
            items = [u for u in u1 if e1[u, c, 'V_ONLY']['y_V'] == yv]
            cnt = collections.Counter(e1[u, c, 'V_ONLY']['parsed_label'] for u in items)
            t1.append({'condition': c, 'y_V': yv, 'items': len(items), 'source_label_match': cnt[yv], **{'output_' + l: cnt[l] for l in LABELS}})
    write(out / 'E1_V_ONLY_OUTPUT_BY_SOURCE_LABEL.csv', t1)

    # 2. E1 paired RECODE -> condition transitions in joint arms (gross vs net)
    t2 = []
    for c in ('BLUR_L1', 'BLUR_L2', 'BLUR_L3'):
        for o in ORDERS + ('BOTH',):
            os_ = ORDERS if o == 'BOTH' else (o,)
            cnt = collections.Counter((e1[u, 'RECODE', x]['outcome'], e1[u, c, x]['outcome']) for u in u1 for x in os_)
            n = 146 * len(os_)
            for (f, t), k in sorted(cnt.items()):
                t2.append({'from_condition': 'RECODE', 'to_condition': c, 'order': o, 'from': f, 'to': t, 'slots': k, 'denominator_slots': n})
    write(out / 'E1_PAIRED_JOINT_TRANSITIONS.csv', t2)
    both = collections.Counter((r['from'], r['to']) for r in t2 for _ in range(int(r['slots'])) if r['to_condition'] == 'BLUR_L3' and r['order'] == 'BOTH')
    v_out = sum(n for (f, t), n in both.items() if f == 'SIDE_V' and t != 'SIDE_V')
    reallocation = {'paired_slots': 292, 'SIDE_V_gross_outflow': v_out, 'SIDE_V_to_SIDE_A': both['SIDE_V', 'SIDE_A'], 'SIDE_V_to_OTHER': both['SIDE_V', 'OTHER'],
                    'SIDE_A_to_SIDE_V': both['SIDE_A', 'SIDE_V'], 'SIDE_A_to_OTHER': both['SIDE_A', 'OTHER'], 'OTHER_to_SIDE_A': both['OTHER', 'SIDE_A'],
                    'share_of_SIDE_V_outflow_going_to_SIDE_A': both['SIDE_V', 'SIDE_A'] / v_out}

    # 3. Pre-declaration sensitivity: original V1 plan vs executed V2 plan (exact sign-flip)
    def rate(c, k):
        return np.array([sum(e1[u, c, o]['outcome'] == k for o in ORDERS) / 2 for u in u1])
    d = {k: rate('BLUR_L3', k) - rate('RECODE', k) for k in ('SIDE_V', 'SIDE_A', 'OTHER')}
    v2p = {k: exact_signflip(v) for k, v in d.items()}; v2h = dict(zip(v2p, holm(list(v2p.values()))))
    sec = {'SIDE_A_HIGH_MINUS_RECODE': d['SIDE_A'], 'OTHER_HIGH_MINUS_RECODE': d['OTHER'], 'PARSE_FAIL_HIGH_MINUS_RECODE': rate('BLUR_L3', 'PARSE_FAIL') - rate('RECODE', 'PARSE_FAIL'),
           'TECHNICAL_FAILURE_HIGH_MINUS_RECODE': np.zeros(146), 'CLEAN_MINUS_RECODE_PIPELINE': rate('CLEAN', 'SIDE_V') - rate('RECODE', 'SIDE_V'),
           'ORDER_INTERACTION': np.array([(int(e1[u, 'BLUR_L3', ORDERS[0]]['outcome'] == 'SIDE_V') - int(e1[u, 'RECODE', ORDERS[0]]['outcome'] == 'SIDE_V')) - (int(e1[u, 'BLUR_L3', ORDERS[1]]['outcome'] == 'SIDE_V') - int(e1[u, 'RECODE', ORDERS[1]]['outcome'] == 'SIDE_V')) for u in u1]),
           'BLUR_L1_MINUS_RECODE': rate('BLUR_L1', 'SIDE_V') - rate('RECODE', 'SIDE_V'), 'BLUR_L2_MINUS_RECODE': rate('BLUR_L2', 'SIDE_V') - rate('RECODE', 'SIDE_V'),
           'ORDINAL_DOSE_RESPONSE': np.column_stack([rate(c, 'SIDE_V') for c in ('RECODE', 'BLUR_L1', 'BLUR_L2', 'BLUR_L3')]) @ np.array([-1.5, -.5, .5, 1.5]) / 5,
           'UNIMODAL_SOURCE_LABEL_MATCH': np.array([int(e1[u, 'BLUR_L3', 'V_ONLY']['parsed_label'] == e1[u, 'BLUR_L3', 'V_ONLY']['y_V']) - int(e1[u, 'RECODE', 'V_ONLY']['parsed_label'] == e1[u, 'RECODE', 'V_ONLY']['y_V']) for u in u1])}
    sp = {k: exact_signflip(v) for k, v in sec.items()}
    # The V1 family also contained the continuous entropy endpoint; its frozen Monte Carlo p is taken from the V2 results.
    ent = next(x for x in json.loads((root / 'results/emotiontalk_e1_video_v2/scientific_results.json').read_text())['secondary'] if x['endpoint'] == 'V_ONLY_NORMALIZED_ENTROPY_L3_MINUS_RECODE')
    sp['UNIMODAL_ENTROPY'] = ent['p_two_sided']; sh = dict(zip(sp, holm(list(sp.values()))))
    t3 = [{'endpoint': f'{k}_L3_MINUS_RECODE', 'effect': float(d[k].mean()), 'exact_p': v2p[k], 'V2_executed_plan_role': 'CO_PRIMARY_HOLM_3', 'V2_holm_p': v2h[k],
           'V1_original_plan_role': 'SOLE_PRIMARY' if k == 'SIDE_V' else 'SECONDARY_HOLM_11', 'V1_holm_p': v2p[k] if k == 'SIDE_V' else sh[k + '_HIGH_MINUS_RECODE'],
           'significant_under_both_plans': (v2h[k] < .05) and ((v2p[k] if k == 'SIDE_V' else sh[k + '_HIGH_MINUS_RECODE']) < .05)} for k in ('SIDE_V', 'SIDE_A', 'OTHER')]
    write(out / 'E1_PREDECLARATION_PLAN_SENSITIVITY.csv', t3)

    # 4. E2 unimodal audio output by condition (RECODE control and label-shift content)
    t4 = []
    for c in E2_CONDS:
        cnt = collections.Counter(e2[u, c, 'A_ONLY']['parsed_label'] for u in u2)
        t4.append({'condition': c, 'items': 225, 'A_ONLY_source_label_match': sum(e2[u, c, 'A_ONLY']['parsed_label'] == e2[u, c, 'A_ONLY']['y_A'] for u in u2),
                   'joint_shared_label_slots': sum(e2[u, c, o]['outcome'] == 'SHARED_LABEL' for u in u2 for o in ORDERS), 'joint_slots': 450, **{'A_ONLY_output_' + l: cnt[l] for l in LABELS}})
    write(out / 'E2_AUDIO_CONTROL_AND_LABEL_SHIFT.csv', t4)
    e1v = collections.Counter(e1[u, c, 'V_ONLY']['parsed_label'] for c in E1_CONDS for u in u1)
    summary = {'E1_directional_choice_reallocation_L3': reallocation,
               'E1_V_ONLY_neutral_outputs': {c: sum(e1[u, c, 'V_ONLY']['parsed_label'] == 'neutral' for u in u1) for c in E1_CONDS},
               'E1_y_V_neutral_items': sum(e1[u, 'RECODE', 'V_ONLY']['y_V'] == 'neutral' for u in u1),
               'E1_L3_V_ONLY_match_on_non_neutral_y_V': [sum(e1[u, 'BLUR_L3', 'V_ONLY']['parsed_label'] == e1[u, 'BLUR_L3', 'V_ONLY']['y_V'] for u in u1 if e1[u, 'BLUR_L3', 'V_ONLY']['y_V'] != 'neutral'),
                                                         sum(e1[u, 'BLUR_L3', 'V_ONLY']['y_V'] != 'neutral' for u in u1)],
               'E1_predeclaration': t3, 'E2_A_ONLY_match': {r['condition']: r['A_ONLY_source_label_match'] for r in t4}, 'all_V_ONLY_labels': dict(e1v)}
    (out / 'REVISION_SUMMARY.json').write_text(json.dumps(summary, indent=2, default=float) + '\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('E1_directional_choice_reallocation_L3', 'E1_V_ONLY_neutral_outputs', 'E1_L3_V_ONLY_match_on_non_neutral_y_V', 'E2_A_ONLY_match')}, indent=1, default=float))


if __name__ == '__main__':
    main()
