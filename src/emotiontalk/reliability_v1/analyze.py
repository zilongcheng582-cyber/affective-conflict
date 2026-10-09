"""Pre-registered analysis for EMOTIONTALK_RELIABILITY_INTERVENTION_V1 (see ANALYSIS_PLAN_V1.md).

  python -m src.emotiontalk.reliability_v1.analyze --trials FULL_RUN/trials.jsonl --output-dir NEW_DIR
  python -m src.emotiontalk.reliability_v1.analyze --synthetic-dry-run --output-dir NEW_DIR   # CPU pipeline check only

Pilot records must never be passed to this script. Synthetic output is labelled SYNTHETIC and has no scientific meaning.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from src.emotiontalk.reliability_v1 import design

N_BOOT = 10000
N_PERM = 100000
LEVEL_CONDS = ('RECODE', 'SNR20', 'SNR10', 'SNR00')
# Frozen external prediction (R1 post-audit diagnostic AV pair-specific full fit: order + normalized-entropy
# difference, raw units; results/post_audit/scientific_analysis_v1/R1_PAIR_HETEROGENEITY.csv,
# table PAIR_SPECIFIC_FULL_FIT_ORDER_ENTROPY, pair AV). Fitted on binary-resolvable records only; used solely for
# the S7 exploratory conditional reference (amendment 001), never for a decision.
R1_AV = {'intercept': 0.14388778454069137, 'FIRST_IS_AUDIO': -0.5809606963495942, 'delta_entropy_A_minus_V': -6.312168584849124}


def latest(records):
    by = {}
    for r in records:
        if r['trial_id'] not in by or r['attempt'] > by[r['trial_id']]['attempt']:
            by[r['trial_id']] = r
    return by


# Pre-execution amendment 001: residual technical failures are stored as NaN (complete case) and imputed only by
# explicit, condition-directional fill maps. "Conservative" means the fill can only move an estimate AGAINST the
# hypothesis being tested, whichever condition (reference or degraded) failed. CLEAN never enters a confirmatory
# contrast, so it is never imputed (complete case).
FILL_SIDE_A_CONSERVATIVE = {'RECODE': 0.0, 'SNR20': 0.0, 'SNR10': 1.0, 'SNR00': 1.0}   # against H1 (negative effect / slope)
FILL_SIDE_A_FAVORABLE = {'RECODE': 1.0, 'SNR20': 1.0, 'SNR10': 0.0, 'SNR00': 0.0}      # mirror bound, sensitivity only
FILL_SIDE_V_CONSERVATIVE = {'RECODE': 1.0, 'SNR20': 1.0, 'SNR10': 0.0, 'SNR00': 0.0}   # against S3 (expected increase)


def tables(trials, recs):
    """Item x condition x order arrays; residual technical failures are NaN (complete case)."""
    items = sorted({t['utterance_id'] for t in trials})
    idx = {u: i for i, u in enumerate(items)}
    conds = list(design.CONDITIONS)
    n = len(items)
    shape = (n, len(conds), 2)
    side_a, side_v, other, parse_fail = (np.full(shape, np.nan) for _ in range(4))
    tech = np.zeros(shape, bool)
    h_a = np.full((n, len(conds)), np.nan)
    acc_a = np.full((n, len(conds)), np.nan)
    h_v = np.full(n, np.nan)
    p_a_joint = np.full(shape, np.nan)
    accounting = Counter()
    for t in trials:
        i, c = idx[t['utterance_id']], conds.index(t['condition'])
        r = recs.get(t['trial_id'])
        failed = r is None or r['technical_failure']
        if t['arm'] in ('A_THEN_V', 'V_THEN_A'):
            o = 0 if t['arm'] == 'A_THEN_V' else 1
            out = None if failed else r['joint_outcome']
            accounting[(t['condition'], t['arm'], out or 'TECHNICAL_FAILURE')] += 1
            tech[i, c, o] = failed
            if not failed:
                side_a[i, c, o] = float(out == 'SIDE_MODALITY_1')
                side_v[i, c, o] = float(out == 'SIDE_MODALITY_2')
                other[i, c, o] = float(out in ('OTHER', 'PARSE_FAIL'))
                parse_fail[i, c, o] = float(out == 'PARSE_FAIL')
                if r.get('joint_scoring_status') == 'OK':
                    p_a_joint[i, c, o] = r['joint_p_audio_label']
        elif t['arm'] == 'A_ONLY':
            if not failed:
                h_a[i, c] = r['candidate_entropy_primary']['normalized_by_log7']
                acc_a[i, c] = float(r.get('parsed_label') == t['y_A'])
            accounting[(t['condition'], 'A_ONLY', 'TECHNICAL_FAILURE' if failed else 'OK')] += 1
        else:
            if not failed:
                h_v[i] = r['candidate_entropy_primary']['normalized_by_log7']
            accounting[('CLEAN', 'V_ONLY', 'TECHNICAL_FAILURE' if failed else 'OK')] += 1
    return {'items': items, 'conds': conds, 'side_a_cc': side_a, 'side_v_cc': side_v, 'other_cc': other,
            'parse_fail_cc': parse_fail, 'tech': tech, 'h_a': h_a, 'acc_a': acc_a, 'h_v': h_v, 'p_a_joint': p_a_joint,
            'accounting': accounting}


def fill(arr_cc, conds, fill_map):
    """Impute NaN cells condition-wise from fill_map; conditions absent from the map stay complete case (NaN)."""
    out = arr_cc.copy()
    for cond, value in fill_map.items():
        k = conds.index(cond)
        sl = out[:, k, :]
        sl[np.isnan(sl)] = value
    return out


def contrast(arr, c, hi='SNR00', lo='RECODE'):
    """Item-level difference of order-averaged rates; NaN if any needed cell is still missing."""
    return arr[:, c[hi], :].mean(1) - arr[:, c[lo], :].mean(1)


def pooled_share(num, den, c, cond, idx):
    a = np.nansum(num[idx][:, c[cond], :])
    b = a + np.nansum(den[idx][:, c[cond], :])
    return a / b if b > 0 else np.nan


def boot_ci(x, seed, n_boot=N_BOOT):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return float('nan'), float('nan'), float('nan'), 0
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), (n_boot, len(x)))].mean(axis=1)
    return float(x.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)), len(x)


def signflip_p(x, seed, n_perm=N_PERM):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return float('nan')
    rng = np.random.default_rng(seed)
    obs = abs(x.mean())
    hits = 0
    for start in range(0, n_perm, 10000):
        k = min(10000, n_perm - start)
        s = rng.choice((-1.0, 1.0), size=(k, len(x)))
        hits += int(np.sum(np.abs((s * x).mean(axis=1)) >= obs - 1e-15))
    return (hits + 1) / (n_perm + 1)


def summarize(T, seed):
    conds = T['conds']
    c = {name: conds.index(name) for name in conds}
    sa_cc = T['side_a_cc']
    sa_cons = fill(sa_cc, conds, FILL_SIDE_A_CONSERVATIVE)
    sa_fav = fill(sa_cc, conds, FILL_SIDE_A_FAVORABLE)
    res = {}
    # PRIMARY (decision basis): ITT, all 146 items, residual technical failures filled conservatively against H1:
    # a failed SNR00 cell counts as SIDE_A (1) and a failed RECODE cell as not-SIDE_A (0), so either failure can only
    # push D_i upward (toward/above 0). A failed reference can never manufacture a negative effect.
    d = contrast(sa_cons, c)
    est, lo, hi, n = boot_ci(d, seed)
    res['PRIMARY_dSIDE_A_SNR00_minus_RECODE'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                                 'p_two_sided_signflip': signflip_p(d, seed + 1),
                                                 'missing_data_rule': 'CONSERVATIVE_DIRECTIONAL_vs_H1'}
    sens = (('SENS_primary_complete_case', sa_cc, 20),
            ('SENS_primary_FAVORABLE_bound_for_H1', sa_fav, 26),
            ('SENS_primary_PARSE_FAIL_as_SIDE_A', fill(np.fmax(sa_cc, T['parse_fail_cc']), conds, FILL_SIDE_A_CONSERVATIVE), 22))
    for key, arr, s in sens:
        dd = contrast(arr, c)
        est, lo, hi, n = boot_ci(dd, seed + s)
        res[key] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n}
    res['SENS_primary_missing_data_bounds_point'] = [res['PRIMARY_dSIDE_A_SNR00_minus_RECODE']['estimate'],
                                                     res['SENS_primary_FAVORABLE_bound_for_H1']['estimate']]
    # S1 manipulation check: audio-only entropy. Missing either cell -> item delta 0 (toward the null, never toward S1).
    dh_cc = T['h_a'][:, c['SNR00']] - T['h_a'][:, c['RECODE']]
    dh = np.where(np.isfinite(dh_cc), dh_cc, 0.0)
    est, lo, hi, n = boot_ci(dh, seed + 2)
    res['S1_dEntropyA_SNR00_minus_RECODE'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                              'p_two_sided_signflip': signflip_p(dh, seed + 3),
                                              'missing_data_rule': 'ITEM_DELTA_ZERO_IF_EITHER_MISSING'}
    est, lo, hi, n = boot_ci(dh_cc, seed + 24)
    res['SENS_S1_complete_case'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n}
    res['DESC_audio_only_accuracy_by_condition'] = {cond: float(np.nanmean(T['acc_a'][:, c[cond]])) for cond in conds}
    # S2 dose-response GEE over RECODE<SNR20<SNR10<SNR00 with the conservative fill (low levels 0, high levels 1).
    def gee(arr):
        import statsmodels.api as sm
        rows = [(i, lvl, o, arr[i, c[cond], o]) for i in range(len(T['items'])) for lvl, cond in enumerate(LEVEL_CONDS) for o in (0, 1)]
        rows = [r for r in rows if np.isfinite(r[3])]
        g = np.array([r[0] for r in rows]); lvl = np.array([r[1] for r in rows], float)
        a_first = np.array([1.0 - r[2] for r in rows]); y = np.array([r[3] for r in rows])
        X = sm.add_constant(np.column_stack([lvl, a_first, lvl * a_first]))
        m = sm.GEE(y, X, groups=g, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
        return {'level_coef': float(m.params[1]), 'level_CI': [float(v) for v in m.conf_int()[1]], 'level_p': float(m.pvalues[1]),
                'order_coef': float(m.params[2]), 'level_x_order_coef': float(m.params[3]), 'level_x_order_p': float(m.pvalues[3]),
                'N_rows': len(rows)}
    for key, arr in (('S2_dose_response_GEE', sa_cons), ('SENS_S2_complete_case', sa_cc)):
        try:
            res[key] = gee(arr)
        except Exception as exc:
            res[key] = {'status': 'NOT_COMPUTED', 'error': repr(exc)}
    # S3 SIDE_V increase: conservative fill against S3. S4 OTHER (two-sided): complete case + both bounds.
    sv = fill(T['side_v_cc'], conds, FILL_SIDE_V_CONSERVATIVE)
    dd = contrast(sv, c)
    est, lo, hi, n = boot_ci(dd, seed + 4)
    res['S3_dSIDE_V_SNR00_minus_RECODE'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                            'p_two_sided_signflip': signflip_p(dd, seed + 5), 'missing_data_rule': 'CONSERVATIVE_DIRECTIONAL_vs_S3'}
    dd = contrast(T['other_cc'], c)
    est, lo, hi, n = boot_ci(dd, seed + 6)
    res['S4_dOTHER_SNR00_minus_RECODE'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                           'p_two_sided_signflip': signflip_p(dd, seed + 7), 'missing_data_rule': 'COMPLETE_CASE_TWO_SIDED',
                                           'bounds_point': [float(np.nanmean(contrast(fill(T['other_cc'], conds, {'RECODE': 1.0, 'SNR00': 0.0}), c))),
                                                            float(np.nanmean(contrast(fill(T['other_cc'], conds, {'RECODE': 0.0, 'SNR00': 1.0}), c)))]}
    # S5 order interaction (two-sided): complete case.
    d_av = sa_cc[:, c['SNR00'], 0] - sa_cc[:, c['RECODE'], 0]
    d_va = sa_cc[:, c['SNR00'], 1] - sa_cc[:, c['RECODE'], 1]
    est, lo, hi, n = boot_ci(d_av - d_va, seed + 8)
    res['S5_order_interaction_dA_THEN_V_minus_dV_THEN_A'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                                            'p_two_sided_signflip': signflip_p(d_av - d_va, seed + 9),
                                                            'dSIDE_A_A_THEN_V': float(np.nanmean(d_av)), 'dSIDE_A_V_THEN_A': float(np.nanmean(d_va)),
                                                            'missing_data_rule': 'COMPLETE_CASE_TWO_SIDED'}
    fam = {'S1': res['S1_dEntropyA_SNR00_minus_RECODE']['p_two_sided_signflip'],  # NaN p (no data) -> treated as 1.0 below
           'S2': res['S2_dose_response_GEE'].get('level_p', 1.0),
           'S3': res['S3_dSIDE_V_SNR00_minus_RECODE']['p_two_sided_signflip'],
           'S4': res['S4_dOTHER_SNR00_minus_RECODE']['p_two_sided_signflip'],
           'S5': res['S5_order_interaction_dA_THEN_V_minus_dV_THEN_A']['p_two_sided_signflip']}
    fam = {k: (1.0 if not np.isfinite(v) else v) for k, v in fam.items()}
    order = sorted(fam, key=fam.get)
    adj, running = {}, 0.0
    for k, name in enumerate(order):
        running = max(running, min(1.0, (len(order) - k) * fam[name]))
        adj[name] = running
    res['HOLM_ADJUSTED_P_S1_S5'] = adj
    # S6 pipeline control (descriptive, complete case).
    for key, arr in (('S6_pipeline_dSIDE_A_RECODE_minus_CLEAN', sa_cc[:, c['RECODE'], :].mean(1) - sa_cc[:, c['CLEAN'], :].mean(1)),
                     ('S6_pipeline_dEntropyA_RECODE_minus_CLEAN', T['h_a'][:, c['RECODE']] - T['h_a'][:, c['CLEAN']])):
        est, lo, hi, n = boot_ci(arr, seed + 10)
        res[key] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n}
    # S7 EXPLORATORY CONDITIONAL REFERENCE (amendment 001). R1 coefficients were estimated on binary-resolvable
    # records (SIDE outcomes only) and describe P(audio side | a side was chosen). They are compared ONLY with the
    # observed change in the conditional binary share P(SIDE_A | SIDE_A or SIDE_V), complete case. This is not an
    # ITT quantity, its conditioning set is itself affected by the intervention, it is not a test, and it is
    # never evidence of mediation. It does not enter decide().
    def p_pred(h, o):
        eta = R1_AV['intercept'] + R1_AV['FIRST_IS_AUDIO'] * (1 - o) + R1_AV['delta_entropy_A_minus_V'] * (h - T['h_v'])
        return 1 / (1 + np.exp(-eta))
    pred = np.mean([p_pred(T['h_a'][:, c['SNR00']], o) - p_pred(T['h_a'][:, c['RECODE']], o) for o in (0, 1)], axis=0)
    pest, plo, phi, pn = boot_ci(pred, seed + 12)
    sv_cc = T['side_v_cc']
    def cond_shift(idx):
        return pooled_share(sa_cc, sv_cc, c, 'SNR00', idx) - pooled_share(sa_cc, sv_cc, c, 'RECODE', idx)
    rng = np.random.default_rng(seed + 13)
    nitem = len(T['items'])
    boots = np.array([cond_shift(rng.integers(0, nitem, nitem)) for _ in range(N_BOOT)])
    boots = boots[np.isfinite(boots)]
    obs = cond_shift(np.arange(nitem))
    res['S7_EXPLORATORY_CONDITIONAL_R1_REFERENCE'] = {
        'status': 'EXPLORATORY_CONDITIONAL_REFERENCE_NOT_A_TEST_NOT_MEDIATION',
        'R1_predicted_change_P_SIDE_A_given_SIDE': {'estimate': pest, 'CI_low': plo, 'CI_high': phi, 'N_items': pn},
        'observed_change_conditional_binary_share_SIDE_A_among_SIDE': {
            'estimate': float(obs), 'CI_low': float(np.percentile(boots, 2.5)) if len(boots) else float('nan'),
            'CI_high': float(np.percentile(boots, 97.5)) if len(boots) else float('nan')},
        'scale': 'CONDITIONAL_BINARY_P(SIDE_A|SIDE)_NOT_ITT',
        'caveats': ['R1 coefficients come from binary-resolvable source records only',
                    'conditioning on SIDE outcomes is post-intervention selection',
                    'not comparable to the ITT primary endpoint', 'no mediation inference']}
    # S8 exploratory (ASSOCIATIONAL, not mediation): item-level dEntropy vs dSIDE_A, complete case.
    from scipy.stats import spearmanr
    d_cc = contrast(sa_cc, c)
    ok = np.isfinite(dh_cc) & np.isfinite(d_cc)
    rho = spearmanr(dh_cc[ok], d_cc[ok]).statistic if ok.sum() > 2 else np.nan
    res['S8_EXPLORATORY_spearman_dEntropy_vs_dSIDE_A'] = {'rho': float(rho), 'N_items': int(ok.sum()),
                                                         'interpretation': 'ASSOCIATIONAL_ONLY_NOT_MEDIATION'}
    pj = T['p_a_joint']
    dj = np.nanmean(pj[:, c['SNR00'], :], 1) - np.nanmean(pj[:, c['RECODE'], :], 1)
    est, lo, hi, n = boot_ci(dj, seed + 14)
    res['SEC_joint_teacher_forced_p_audio_label_SNR00_minus_RECODE'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n}
    res['SEC_CONDITIONAL_BINARY_share_SIDE_A_among_SIDE'] = {
        cond: float(pooled_share(sa_cc, sv_cc, c, cond, np.arange(nitem))) for cond in conds}
    res['TECHNICAL_FAILURES_joint'] = int(T['tech'].sum())
    res['TECHNICAL_FAILURES_joint_RECODE_SNR00'] = int(T['tech'][:, [c['RECODE'], c['SNR00']], :].sum())
    res['TECHNICAL_RISK_FLAG'] = bool(T['tech'].sum() > 0.05 * T['tech'].size)
    res['decision'] = decide(res)
    return res


def verdict(p):
    if p['CI_high'] < 0:
        return 'NEGATIVE_EXCLUDES_ZERO'
    if p['CI_low'] > 0:
        return 'POSITIVE_EXCLUDES_ZERO'
    return 'INCLUDES_ZERO'


def decide(res):
    p, s1 = res['PRIMARY_dSIDE_A_SNR00_minus_RECODE'], res['S1_dEntropyA_SNR00_minus_RECODE']
    manip = s1['CI_low'] > 0
    # Each claim is judged on the missing-data bound least favourable to THAT claim: support for H1 on the
    # conservative bound (PRIMARY); contradiction / disconfirmation of H1 on the H1-favourable bound.
    fav = res['SENS_primary_FAVORABLE_bound_for_H1']
    if p['CI_high'] < 0 and p['p_two_sided_signflip'] < 0.05:
        behaviour = 'H1_SUPPORTED_AUDIO_DEGRADATION_REDUCES_AUDIO_SIDE_CHOICE'
    elif p['CI_low'] > 0 and fav['CI_low'] > 0:
        behaviour = 'H1_CONTRADICTED_OPPOSITE_DIRECTION'
    elif manip and p['CI_low'] > -0.05 and fav['CI_low'] > -0.05:
        behaviour = 'H1_DISCONFIRMED_ENTROPY_ROSE_CHOICE_EFFECT_EXCLUDED_BEYOND_5PTS'
    else:
        behaviour = 'H1_NOT_SUPPORTED'
    cc = res['SENS_primary_complete_case']
    if not np.isfinite(p['estimate']) or not np.isfinite(p.get('p_two_sided_signflip', np.nan)):
        behaviour = 'H1_NOT_EVALUABLE_NO_DATA'
    return {'manipulation_check': 'PASS' if manip else 'FAIL_ENTROPY_LINK_UNINTERPRETABLE',
            'primary': behaviour,
            'primary_missing_data_rule': 'CONSERVATIVE_DIRECTIONAL_vs_H1',
            'complete_case_agrees_with_primary_direction': verdict(cc) == verdict(p),
            'entropy_up_but_choice_not_in_predicted_direction': bool(manip and not p['CI_high'] < 0),
            'S7_role': 'EXPLORATORY_CONDITIONAL_REFERENCE_EXCLUDED_FROM_DECISION',
            'mediation_claim': 'NOT_IDENTIFIED_BY_DESIGN'}


def synthetic_records(trials, seed):
    """Fake records exercising every code path; SYNTHETIC, no relation to the model."""
    rng = np.random.default_rng(seed)
    out = []
    for t in trials:
        lvl = {'CLEAN': 0, 'RECODE': 0, 'SNR20': 1, 'SNR10': 2, 'SNR00': 3}[t['condition']]
        r = {'trial_id': t['trial_id'], 'attempt': 1, 'technical_failure': bool(rng.random() < 0.01)}
        if t['role'] == 'UNIMODAL_MEASUREMENT':
            h = float(np.clip(0.6 + (0.08 * lvl if t['arm'] == 'A_ONLY' else 0) + rng.normal(0, 0.05), 0, 1))
            r.update({'candidate_entropy_primary': {'normalized_by_log7': h}, 'parsed_label': t['y_A'] if t['arm'] == 'A_ONLY' else t['y_V']})
        else:
            pa = 0.45 - 0.08 * lvl
            u = rng.random()
            r.update({'joint_outcome': 'SIDE_MODALITY_1' if u < pa else 'SIDE_MODALITY_2' if u < 0.95 else 'OTHER',
                      'joint_scoring_status': 'OK', 'joint_p_audio_label': float(np.clip(pa + rng.normal(0, 0.1), 0, 1))})
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--trials', type=Path)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--synthetic-dry-run', action='store_true')
    a = ap.parse_args()
    _, trials = design.build()
    trials = [{k: str(v) if not isinstance(v, str) else v for k, v in t.items()} for t in trials]
    if a.synthetic_dry_run:
        records = synthetic_records(trials, design.DESIGN_SEED)
        label = 'SYNTHETIC_DRY_RUN_NO_SCIENTIFIC_MEANING'
    else:
        records = [json.loads(line) for line in open(a.trials, encoding='utf-8')]
        if any(r.get('phase') != 'full' for r in records):
            raise SystemExit('FAIL_CLOSED: only full-phase records may be analysed (pilot excluded)')
        label = 'FULL_EXPERIMENT'
    if a.output_dir.exists():
        raise SystemExit('Output must be new')
    a.output_dir.mkdir(parents=True)
    T = tables(trials, latest(records))
    res = summarize(T, design.DESIGN_SEED)
    res['data_label'] = label
    (a.output_dir / 'ANALYSIS_RESULTS.json').write_text(json.dumps(res, indent=1, default=float))
    with open(a.output_dir / 'OUTCOME_ACCOUNTING.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['condition', 'arm', 'outcome', 'n'])
        for (cond, arm, out), n in sorted(T['accounting'].items()):
            w.writerow([cond, arm, out, n])
    print(json.dumps({'data_label': label, 'decision': res['decision'],
                      'primary': res['PRIMARY_dSIDE_A_SNR00_minus_RECODE']}, indent=1))


if __name__ == '__main__':
    main()
