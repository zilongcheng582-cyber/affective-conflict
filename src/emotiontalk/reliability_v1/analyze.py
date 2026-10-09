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
# table PAIR_SPECIFIC_FULL_FIT_ORDER_ENTROPY, pair AV). Used only for the S7 magnitude check.
R1_AV = {'intercept': 0.14388778454069137, 'FIRST_IS_AUDIO': -0.5809606963495942, 'delta_entropy_A_minus_V': -6.312168584849124}


def latest(records):
    by = {}
    for r in records:
        if r['trial_id'] not in by or r['attempt'] > by[r['trial_id']]['attempt']:
            by[r['trial_id']] = r
    return by


def tables(trials, recs):
    """Item-level arrays with the pre-registered missingness policy (conservative imputation)."""
    items = sorted({t['utterance_id'] for t in trials})
    idx = {u: i for i, u in enumerate(items)}
    conds = list(design.CONDITIONS)
    n = len(items)
    side_a = np.full((n, len(conds), 2), np.nan)
    side_v = np.full((n, len(conds), 2), np.nan)
    other = np.full((n, len(conds), 2), np.nan)
    side_a_cc = np.full((n, len(conds), 2), np.nan)  # complete-case: NaN for residual technical failure
    side_a_pf = np.full((n, len(conds), 2), np.nan)  # PARSE_FAIL counted as SIDE_A (conservative sensitivity)
    tech = np.zeros((n, len(conds), 2), bool)
    h_a = np.full((n, len(conds)), np.nan)
    acc_a = np.full((n, len(conds)), np.nan)
    h_v = np.full(n, np.nan)
    p_a_joint = np.full((n, len(conds), 2), np.nan)
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
            side_a[i, c, o] = 1.0 if failed else float(out == 'SIDE_MODALITY_1')  # failure imputed AGAINST H1
            side_v[i, c, o] = 0.0 if failed else float(out == 'SIDE_MODALITY_2')
            other[i, c, o] = 0.0 if failed else float(out in ('OTHER', 'PARSE_FAIL'))
            side_a_cc[i, c, o] = np.nan if failed else float(out == 'SIDE_MODALITY_1')
            side_a_pf[i, c, o] = 1.0 if failed else float(out in ('SIDE_MODALITY_1', 'PARSE_FAIL'))
            if not failed and r.get('joint_scoring_status') == 'OK':
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
    # Entropy missingness: missing condition value -> equal to RECODE (delta 0, against the manipulation check).
    rec_c = conds.index('RECODE')
    h_imp = h_a.copy()
    for i in range(n):
        for c in range(len(conds)):
            if np.isnan(h_imp[i, c]):
                h_imp[i, c] = h_a[i, rec_c] if not np.isnan(h_a[i, rec_c]) else np.nanmean(h_a[:, rec_c])
    return {'items': items, 'conds': conds, 'side_a': side_a, 'side_a_cc': side_a_cc, 'side_a_pf': side_a_pf, 'side_v': side_v, 'other': other, 'tech': tech,
            'h_a': h_a, 'h_a_imputed': h_imp, 'acc_a': acc_a, 'h_v': h_v, 'p_a_joint': p_a_joint, 'accounting': accounting}


def boot_ci(x, seed, n_boot=N_BOOT):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), (n_boot, len(x)))].mean(axis=1)
    return float(x.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)), len(x)


def signflip_p(x, seed, n_perm=N_PERM):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    rng = np.random.default_rng(seed)
    obs = abs(x.mean())
    hits = 0
    for start in range(0, n_perm, 10000):
        k = min(10000, n_perm - start)
        s = rng.choice((-1.0, 1.0), size=(k, len(x)))
        hits += int(np.sum(np.abs((s * x).mean(axis=1)) >= obs - 1e-15))
    return (hits + 1) / (n_perm + 1)


def summarize(T, seed):
    c = {name: T['conds'].index(name) for name in T['conds']}
    sa = T['side_a']
    res = {}
    # PRIMARY: item-level SIDE_A rate (mean over both orders), SNR00 minus RECODE; ITT over all eligible items.
    d = sa[:, c['SNR00'], :].mean(1) - sa[:, c['RECODE'], :].mean(1)
    est, lo, hi, n = boot_ci(d, seed)
    res['PRIMARY_dSIDE_A_SNR00_minus_RECODE'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                                 'p_two_sided_signflip': signflip_p(d, seed + 1)}
    for key, arr, s in (('SENS_primary_complete_case', T['side_a_cc'], 20), ('SENS_primary_PARSE_FAIL_as_SIDE_A', T['side_a_pf'], 22)):
        dd = arr[:, c['SNR00'], :].mean(1) - arr[:, c['RECODE'], :].mean(1)  # items with any failed cell drop out (NaN)
        est, lo, hi, n = boot_ci(dd, seed + s)
        res[key] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n}
    dh_cc = T['h_a'][:, c['SNR00']] - T['h_a'][:, c['RECODE']]
    est, lo, hi, n = boot_ci(dh_cc, seed + 24)
    res['SENS_S1_complete_case'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n}
    acc = T['acc_a']
    res['DESC_audio_only_accuracy_by_condition'] = {cond: float(np.nanmean(acc[:, c[cond]])) for cond in T['conds']}
    # S1 manipulation check: audio-only normalized entropy increase.
    dh = T['h_a_imputed'][:, c['SNR00']] - T['h_a_imputed'][:, c['RECODE']]
    est, lo, hi, n = boot_ci(dh, seed + 2)
    res['S1_dEntropyA_SNR00_minus_RECODE'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                              'p_two_sided_signflip': signflip_p(dh, seed + 3)}
    # S2 dose-response (GEE logistic, exchangeable, item clusters) over RECODE<SNR20<SNR10<SNR00.
    try:
        import statsmodels.api as sm
        rows = [(i, lvl, o, sa[i, c[cond], o]) for i in range(len(T['items'])) for lvl, cond in enumerate(LEVEL_CONDS) for o in (0, 1)]
        g = np.array([r[0] for r in rows]); lvl = np.array([r[1] for r in rows], float)
        order_a_first = np.array([1.0 - r[2] for r in rows]); y = np.array([r[3] for r in rows])
        X = sm.add_constant(np.column_stack([lvl, order_a_first, lvl * order_a_first]))
        m = sm.GEE(y, X, groups=g, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
        res['S2_dose_response_GEE'] = {'level_coef': float(m.params[1]), 'level_CI': [float(v) for v in m.conf_int()[1]],
                                       'level_p': float(m.pvalues[1]), 'order_coef': float(m.params[2]),
                                       'level_x_order_coef': float(m.params[3]), 'level_x_order_p': float(m.pvalues[3])}
    except Exception as exc:
        res['S2_dose_response_GEE'] = {'status': 'NOT_COMPUTED', 'error': repr(exc)}
    # S3 SIDE_V increase; S4 OTHER/PARSE_FAIL change.
    for key, arr, s in (('S3_dSIDE_V_SNR00_minus_RECODE', T['side_v'], 4), ('S4_dOTHER_SNR00_minus_RECODE', T['other'], 6)):
        dd = arr[:, c['SNR00'], :].mean(1) - arr[:, c['RECODE'], :].mean(1)
        est, lo, hi, n = boot_ci(dd, seed + s)
        res[key] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n, 'p_two_sided_signflip': signflip_p(dd, seed + s + 1)}
    # S5 order interaction: primary contrast in A_THEN_V minus V_THEN_A.
    d_av = sa[:, c['SNR00'], 0] - sa[:, c['RECODE'], 0]
    d_va = sa[:, c['SNR00'], 1] - sa[:, c['RECODE'], 1]
    est, lo, hi, n = boot_ci(d_av - d_va, seed + 8)
    res['S5_order_interaction_dA_THEN_V_minus_dV_THEN_A'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                                            'p_two_sided_signflip': signflip_p(d_av - d_va, seed + 9),
                                                            'dSIDE_A_A_THEN_V': float(np.mean(d_av)), 'dSIDE_A_V_THEN_A': float(np.mean(d_va))}
    # Holm over the confirmatory secondary family S1-S5.
    fam = {'S1': res['S1_dEntropyA_SNR00_minus_RECODE']['p_two_sided_signflip'],
           'S2': res['S2_dose_response_GEE'].get('level_p', 1.0),
           'S3': res['S3_dSIDE_V_SNR00_minus_RECODE']['p_two_sided_signflip'],
           'S4': res['S4_dOTHER_SNR00_minus_RECODE']['p_two_sided_signflip'],
           'S5': res['S5_order_interaction_dA_THEN_V_minus_dV_THEN_A']['p_two_sided_signflip']}
    order = sorted(fam, key=fam.get)
    adj, running = {}, 0.0
    for k, name in enumerate(order):
        running = max(running, min(1.0, (len(order) - k) * fam[name]))
        adj[name] = running
    res['HOLM_ADJUSTED_P_S1_S5'] = adj
    # S6 pipeline control (descriptive): CLEAN vs RECODE.
    for key, arr in (('S6_pipeline_dSIDE_A_RECODE_minus_CLEAN', sa[:, c['RECODE'], :].mean(1) - sa[:, c['CLEAN'], :].mean(1)),
                     ('S6_pipeline_dEntropyA_RECODE_minus_CLEAN', T['h_a'][:, c['RECODE']] - T['h_a'][:, c['CLEAN']])):
        est, lo, hi, n = boot_ci(arr, seed + 10)
        res[key] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n}
    # S7 magnitude check against the frozen R1 AV coefficients.
    def p_pred(h_a, o):
        eta = R1_AV['intercept'] + R1_AV['FIRST_IS_AUDIO'] * (1 - o) + R1_AV['delta_entropy_A_minus_V'] * (h_a - T['h_v'])
        return 1 / (1 + np.exp(-eta))
    pred = np.mean([p_pred(T['h_a'][:, c['SNR00']], o) - p_pred(T['h_a'][:, c['RECODE']], o) for o in (0, 1)], axis=0)
    est, lo, hi, n = boot_ci(pred, seed + 12)
    prim = res['PRIMARY_dSIDE_A_SNR00_minus_RECODE']
    res['S7_R1_predicted_dSIDE_A'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n,
                                      'predicted_inside_observed_primary_CI': bool(prim['CI_low'] <= est <= prim['CI_high'])}
    # S8 exploratory (ASSOCIATIONAL, not mediation): item-level dEntropy vs dSIDE_A.
    from scipy.stats import spearmanr
    ok = np.isfinite(dh) & np.isfinite(d)
    rho = spearmanr(dh[ok], d[ok]).statistic if ok.sum() > 2 else np.nan
    res['S8_EXPLORATORY_spearman_dEntropy_vs_dSIDE_A'] = {'rho': float(rho), 'N_items': int(ok.sum()),
                                                         'interpretation': 'ASSOCIATIONAL_ONLY_NOT_MEDIATION'}
    # Secondary continuous joint endpoint and conditional binary analysis.
    pj = T['p_a_joint']
    dj = np.nanmean(pj[:, c['SNR00'], :], 1) - np.nanmean(pj[:, c['RECODE'], :], 1)
    est, lo, hi, n = boot_ci(dj, seed + 14)
    res['SEC_joint_teacher_forced_p_audio_label_SNR00_minus_RECODE'] = {'estimate': est, 'CI_low': lo, 'CI_high': hi, 'N_items': n}
    res['SEC_CONDITIONAL_BINARY_share_SIDE_A_among_SIDE'] = {
        cond: float(np.nansum(T['side_a_cc'][:, c[cond], :]) /
                    max(1.0, np.nansum(T['side_a_cc'][:, c[cond], :]) + np.nansum(T['side_v'][:, c[cond], :])))
        for cond in T['conds']}
    res['TECHNICAL_FAILURES_joint'] = int(T['tech'].sum())
    res['TECHNICAL_RISK_FLAG'] = bool(T['tech'].sum() > 0.05 * T['tech'].size)
    res['decision'] = decide(res)
    return res


def decide(res):
    p, s1 = res['PRIMARY_dSIDE_A_SNR00_minus_RECODE'], res['S1_dEntropyA_SNR00_minus_RECODE']
    manip = s1['CI_low'] > 0
    if p['CI_high'] < 0 and p['p_two_sided_signflip'] < 0.05:
        behaviour = 'H1_SUPPORTED_AUDIO_DEGRADATION_REDUCES_AUDIO_SIDE_CHOICE'
    elif p['CI_low'] > 0:
        behaviour = 'H1_CONTRADICTED_OPPOSITE_DIRECTION'
    elif manip and p['CI_low'] > -0.05:
        behaviour = 'H1_DISCONFIRMED_ENTROPY_ROSE_CHOICE_EFFECT_EXCLUDED_BEYOND_5PTS'
    else:
        behaviour = 'H1_NOT_SUPPORTED'
    return {'manipulation_check': 'PASS' if manip else 'FAIL_ENTROPY_LINK_UNINTERPRETABLE',
            'primary': behaviour,
            'entropy_up_but_choice_not_in_predicted_direction': bool(manip and not p['CI_high'] < 0),
            'magnitude_consistent_with_R1': res['S7_R1_predicted_dSIDE_A']['predicted_inside_observed_primary_CI'],
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
