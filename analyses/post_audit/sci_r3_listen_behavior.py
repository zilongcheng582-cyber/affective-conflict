"""R3 - LISTEN 3A/3B/3C behavioral diagnostics (POST_AUDIT_SCIENTIFIC_ANALYSIS_V1).

Descriptive/associational only: no target-specific transfer fit, frozen population unchanged.
Run: python -m analyses.post_audit.sci_r3_listen_behavior
"""
import json
import warnings
from collections import Counter, defaultdict

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.contingency_tables import SquareTable
from statsmodels.stats.proportion import proportion_confint

from analyses.post_audit.sci_common import (REPO, OUT, SEED, BOOTSTRAPS, ORIGIN, csvrows, write_csv,
                                            cluster_bootstrap, ci)

CLASSES = ('SIDE_A', 'SIDE_T', 'OTHER')
AUGMENTED_8 = {'neutral', 'sadness', 'surprise', 'happiness', 'fear', 'anger', 'excitement', 'frustration'}


def base_item(row):
    return row['source_item_id'].rsplit('_u_', 1)[0]


def fnum(x):
    return float(x) if x not in ('', None) else np.nan


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = csvrows(REPO / 'manifests/listen/frozen_joint_outcomes.csv')
    assert len(rows) == 1149
    for r in rows:
        r['base_item'] = base_item(r)
        r['subset'] = '_'.join(r['source_item_id'].split('_')[:2])
        r['conflict_pair'] = r['modality1_source_label'] + '|' + r['modality2_source_label']
    conflict = [r for r in rows if r['source_relation'] == 'CONFLICT']
    counts = Counter(r['condition'] for r in conflict)
    assert counts == {'3A': 383, '3B': 378, '3C': 378}

    # ---------------- R3.1 outcome accounting ----------------
    acc = []
    for cond in ('3A', '3B', '3C', 'ALL'):
        rs = [r for r in conflict if cond == 'ALL' or r['condition'] == cond]
        n = len(rs)
        c = Counter(r['observed_outcome'] for r in rs)
        row = {'condition': cond, 'prompt_input': {'3A': 'TEXT_ONLY (T_ONLY)', '3B': 'AUDIO_ONLY (A_ONLY)',
                                                    '3C': 'AUDIO_THEN_TEXT (A_THEN_T)', 'ALL': 'MIXED'}[cond],
               'population': 'CONFLICT', 'N': n, 'N_items_clusters': len(set(r['base_item'] for r in rs))}
        cl = [r['base_item'] for r in rs]
        ind = {k: np.array([r['observed_outcome'] == k for r in rs], float) for k in CLASSES}
        bs = cluster_bootstrap(cl, lambda idx: {**{k: ind[k][idx].mean() for k in CLASSES},
                                                'binary': 1 - ind['OTHER'][idx].mean(),
                                                'A_share_binary': ind['SIDE_A'][idx].sum() / max(1, (1 - ind['OTHER'][idx]).sum())})
        for k in CLASSES:
            row['n_' + k] = c[k]; row['rate_' + k] = c[k] / n
            lo, hi, _ = ci(bs[k]); row['rate_%s_CI_low' % k], row['rate_%s_CI_high' % k] = lo, hi
            wl, wh = proportion_confint(c[k], n, method='wilson'); row['rate_%s_wilson_low' % k], row['rate_%s_wilson_high' % k] = wl, wh
        row['n_binary_resolvable'] = c['SIDE_A'] + c['SIDE_T']
        row['binary_resolvable_rate'] = row['n_binary_resolvable'] / n
        lo, hi, _ = ci(bs['binary']); row['binary_resolvable_CI_low'], row['binary_resolvable_CI_high'] = lo, hi
        row['SIDE_A_share_among_binary'] = c['SIDE_A'] / max(1, row['n_binary_resolvable'])
        lo, hi, _ = ci(bs['A_share_binary']); row['SIDE_A_share_CI_low'], row['SIDE_A_share_CI_high'] = lo, hi
        row['technical_missing'] = sum(r['technical_missing'] == 'TRUE' for r in rs)
        row['CI_method'] = 'ITEM_CLUSTER_PERCENTILE_95 (base item across conditions); Wilson also reported'
        acc.append(row)
    for cond in ('3A', '3B', '3C'):
        rs = [r for r in rows if r['condition'] == cond and r['source_relation'] != 'CONFLICT']
        acc.append({'condition': cond, 'population': 'SAME_LABEL_NON_CONFLICT', 'N': len(rs),
                    'n_OTHER': sum(r['observed_outcome'] == 'OTHER' for r in rs),
                    'note': 'non-conflict rows; outside binary arbitration estimand'})
    for a in acc:
        a.update({'analysis_origin': ORIGIN, 'bootstrap_replicates': BOOTSTRAPS, 'bootstrap_seed': SEED})
    write_csv(OUT / 'R3_OUTCOME_ACCOUNTING.csv', acc)

    # ---------------- R3.2 matched-condition transitions ----------------
    by = defaultdict(dict)
    for r in rows:
        by[r['base_item']].setdefault(r['condition'], []).append(r)
    assert all(len(v) == 1 for d in by.values() for v in d.values())
    by = {k: {c: v[0] for c, v in d.items()} for k, d in by.items()}

    def exact_match(x, y):
        """Exact identity: same underlying item, identical measurement IDs and evidence hashes, same source labels."""
        return all(x[f] == y[f] for f in ('modality1_measurement_id', 'modality2_measurement_id', 'modality1_evidence_sha256',
                                          'modality2_evidence_sha256', 'modality1_source_label', 'modality2_source_label'))

    trans, match_log = [], []
    for src_c, dst_c in (('3B', '3C'), ('3A', '3C'), ('3A', '3B')):
        pairs, unmatched_id, absent = [], 0, Counter()
        for b, d in by.items():
            if src_c in d and dst_c in d:
                if exact_match(d[src_c], d[dst_c]):
                    pairs.append((d[src_c], d[dst_c]))
                else:
                    unmatched_id += 1
            elif src_c in d:
                absent[src_c + '_only'] += 1
            elif dst_c in d:
                absent[dst_c + '_only'] += 1
        both_conflict = [(x, y) for x, y in pairs if x['source_relation'] == 'CONFLICT' and y['source_relation'] == 'CONFLICT']
        match_log.append({'comparison': '%s->%s' % (src_c, dst_c), 'items_with_both_conditions': len(pairs) + unmatched_id,
                          'exact_identity_matched': len(pairs), 'identity_mismatch_not_joined': unmatched_id,
                          'matched_both_conflict': len(both_conflict),
                          'matched_not_both_conflict': len(pairs) - len(both_conflict),
                          'unmatched_%s_only' % src_c: absent[src_c + '_only'], 'unmatched_%s_only' % dst_c: absent[dst_c + '_only']})
        n = len(both_conflict)
        mat = np.zeros((3, 3), int)
        for x, y in both_conflict:
            mat[CLASSES.index(x['observed_outcome']), CLASSES.index(y['observed_outcome'])] += 1
        for i, a in enumerate(CLASSES):
            for j, b in enumerate(CLASSES):
                trans.append({'comparison': '%s->%s' % (src_c, dst_c), 'record_type': 'TRANSITION_CELL', 'from': a, 'to': b,
                              'n': int(mat[i, j]), 'matched_N': n, 'share_of_matched': mat[i, j] / n,
                              'row_conditional_rate': mat[i, j] / max(1, mat[i].sum())})
        X = np.array([[CLASSES.index(x['observed_outcome']), CLASSES.index(y['observed_outcome'])] for x, y in both_conflict])
        def stat(idx):
            s, t = X[idx, 0], X[idx, 1]
            return {'d_SIDE_A': np.mean(t == 0) - np.mean(s == 0), 'd_SIDE_T': np.mean(t == 1) - np.mean(s == 1),
                    'd_OTHER': np.mean(t == 2) - np.mean(s == 2),
                    'OTHER_to_SIDE': np.mean((s == 2) & (t != 2)), 'SIDE_to_OTHER': np.mean((s != 2) & (t == 2)),
                    'A_to_T': np.mean((s == 0) & (t == 1)), 'T_to_A': np.mean((s == 1) & (t == 0)),
                    'same_outcome': np.mean(s == t),
                    'A_share_binary_dst_minus_src': (np.sum(t == 0) / max(1, np.sum(t != 2))) - (np.sum(s == 0) / max(1, np.sum(s != 2)))}
        ids = [x['base_item'] for x, _ in both_conflict]
        bs = cluster_bootstrap(ids, stat)
        pt = stat(np.arange(n))
        st = SquareTable(mat, shift_zeros=False)
        try:
            sm_res = st.homogeneity()
            sm_stat, sm_p = float(sm_res.statistic), float(sm_res.pvalue)
        except Exception:
            sm_stat = sm_p = np.nan
        for k, v in pt.items():
            lo, hi, _ = ci(bs[k])
            trans.append({'comparison': '%s->%s' % (src_c, dst_c), 'record_type': 'SUMMARY', 'from': k, 'to': '',
                          'n': None, 'matched_N': n, 'estimate': v, 'CI_low': lo, 'CI_high': hi,
                          'CI_method': 'ITEM_CLUSTER_PERCENTILE_95'})
        trans.append({'comparison': '%s->%s' % (src_c, dst_c), 'record_type': 'STUART_MAXWELL_MARGINAL_HOMOGENEITY',
                      'from': '', 'to': '', 'matched_N': n, 'estimate': sm_stat, 'p_value': sm_p})
    # three-way patterns on items present & matched in all conditions
    tri = Counter()
    for b, d in by.items():
        if all(c in d for c in ('3A', '3B', '3C')) and exact_match(d['3A'], d['3C']) and exact_match(d['3B'], d['3C']) \
                and all(d[c]['source_relation'] == 'CONFLICT' for c in ('3A', '3B', '3C')):
            tri[(d['3A']['observed_outcome'], d['3B']['observed_outcome'], d['3C']['observed_outcome'])] += 1
    ntri = sum(tri.values())
    for (a, b_, c), n in sorted(tri.items(), key=lambda kv: -kv[1]):
        trans.append({'comparison': '3A,3B->3C', 'record_type': 'THREE_WAY_PATTERN', 'from': '%s,%s' % (a, b_), 'to': c,
                      'n': n, 'matched_N': ntri, 'share_of_matched': n / ntri})
    for t in trans:
        t.update({'analysis_origin': ORIGIN, 'bootstrap_replicates': BOOTSTRAPS, 'bootstrap_seed': SEED})
    for m in match_log:
        trans.append({'comparison': m['comparison'], 'record_type': 'MATCH_ACCOUNTING', **{k: v for k, v in m.items() if k != 'comparison'},
                      'analysis_origin': ORIGIN})
    write_csv(OUT / 'R3_MATCHED_CONDITION_TRANSITIONS.csv', trans)

    # ---------------- R3.3 OTHER associations ----------------
    assoc = []
    def rate_rows(factor, getter):
        for cond in ('3A', '3B', '3C'):
            rs = [r for r in conflict if r['condition'] == cond]
            g = defaultdict(list)
            for r in rs:
                g[getter(r)].append(r)
            for lev, items in sorted(g.items()):
                n = len(items)
                c = Counter(r['observed_outcome'] for r in items)
                lo, hi = proportion_confint(c['OTHER'], n, method='wilson')
                assoc.append({'analysis': 'OTHER_RATE_BY_FACTOR', 'factor': factor, 'level': lev, 'condition': cond, 'N': n,
                              'n_OTHER': c['OTHER'], 'n_SIDE_A': c['SIDE_A'], 'n_SIDE_T': c['SIDE_T'],
                              'OTHER_rate': c['OTHER'] / n, 'OTHER_rate_wilson_low': lo, 'OTHER_rate_wilson_high': hi,
                              'SIDE_A_rate': c['SIDE_A'] / n, 'SIDE_T_rate': c['SIDE_T'] / n})
    rate_rows('audio_implicit_label(modality1)', lambda r: r['modality1_source_label'])
    rate_rows('text_explicit_label(modality2)', lambda r: r['modality2_source_label'])
    rate_rows('audio_label_in_augmented8', lambda r: str(r['modality1_source_label'] in AUGMENTED_8))
    rate_rows('MUStARD_subset', lambda r: r['subset'])
    # conflict pairs with >=10 rows in 3C
    top_pairs = [k for k, v in Counter(r['conflict_pair'] for r in conflict if r['condition'] == '3C').items() if v >= 10]
    rate_rows('conflict_pair(A|T),>=10_in_3C', lambda r: r['conflict_pair'] if r['conflict_pair'] in top_pairs else 'OTHER_PAIRS_POOLED')

    # logistic models with item-cluster robust SE
    def glm(name, rs, cols, outcome='OTHER'):
        X, names = [], []
        for nm, fn in cols:
            X.append(np.array([fn(r) for r in rs], float)); names.append(nm)
        X = np.column_stack(X)
        keep = np.isfinite(X).all(1)
        yv = np.array([r['observed_outcome'] == outcome for r in rs], float)[keep]
        Xk = sm.add_constant(X[keep], has_constant='add')
        cl = np.unique(np.array([r['base_item'] for r in rs])[keep], return_inverse=True)[1]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            res = sm.GLM(yv, Xk, family=sm.families.Binomial()).fit(cov_type='cluster', cov_kwds={'groups': cl})
        cis = res.conf_int()
        for i, nm in enumerate(['intercept'] + names):
            assoc.append({'analysis': 'LOGISTIC_' + outcome + '_' + name, 'factor': nm, 'N': int(keep.sum()),
                          'N_clusters': int(cl.max() + 1), 'coef_log_odds': res.params[i], 'cluster_robust_se': res.bse[i],
                          'CI_low': cis[i][0], 'CI_high': cis[i][1], 'p_value': res.pvalues[i]})
    unimodal = [('normalized_entropy_A', lambda r: fnum(r['normalized_entropy_modality1'])),
                ('normalized_entropy_T', lambda r: fnum(r['normalized_entropy_modality2'])),
                ('top1_top2_margin_A', lambda r: fnum(r['top1_top2_margin_modality1'])),
                ('top1_top2_margin_T', lambda r: fnum(r['top1_top2_margin_modality2']))]
    for cond in ('3A', '3B', '3C'):
        rs = [r for r in conflict if r['condition'] == cond]
        glm(cond + '_UNIMODAL_B3_FEATURES', rs, unimodal)
        glm(cond + '_DELTA_FEATURES', rs, [('delta_normalized_entropy_A_minus_T', lambda r: fnum(r['delta_normalized_entropy_raw'])),
                                           ('delta_top1_top2_margin_A_minus_T', lambda r: fnum(r['delta_top1_top2_margin_raw']))])
        glm(cond + '_UNIMODAL_PLUS_RIDICULE', rs, unimodal + [('audio_label_is_ridicule', lambda r: r['modality1_source_label'] == 'ridicule'),
                                                             ('text_label_is_neutral', lambda r: r['modality2_source_label'] == 'neutral')])
    glm('ALL_CONDITIONS_CONDITION_ONLY', conflict, [('cond_3B', lambda r: r['condition'] == '3B'), ('cond_3C', lambda r: r['condition'] == '3C')])
    glm('ALL_CONDITIONS_PLUS_LABELS_UNIMODAL', conflict,
        [('cond_3B', lambda r: r['condition'] == '3B'), ('cond_3C', lambda r: r['condition'] == '3C'),
         ('audio_label_is_ridicule', lambda r: r['modality1_source_label'] == 'ridicule'),
         ('text_label_is_neutral', lambda r: r['modality2_source_label'] == 'neutral')] + unimodal)
    # matched 3C OTHER predicted by unimodal-condition outcomes (associational)
    m3 = []
    for b, d in by.items():
        if all(c in d for c in ('3A', '3B', '3C')) and all(d[c]['source_relation'] == 'CONFLICT' for c in ('3A', '3B', '3C')):
            m3.append(d)
    if m3:
        rs = [d['3C'] for d in m3]
        for d, r in zip(m3, rs):
            r['_3A_OTHER'] = d['3A']['observed_outcome'] == 'OTHER'
            r['_3B_OTHER'] = d['3B']['observed_outcome'] == 'OTHER'
        glm('3C_GIVEN_MATCHED_UNIMODAL_OTHER', rs, [('3A_was_OTHER', lambda r: r['_3A_OTHER']), ('3B_was_OTHER', lambda r: r['_3B_OTHER'])])
    assoc.append({'analysis': 'NOT_EXECUTABLE', 'factor': 'OTHER_predicted_label_identity',
                  'note': 'Raw generations / parsed LISTEN letters and their mapped labels are not published in this repository; '
                          'only the outcome class (SIDE_A/SIDE_T/OTHER) is available. Labels chosen under OTHER are not inferred.'})
    assoc.append({'analysis': 'NOT_EXECUTABLE', 'factor': 'native_choice_list_per_item',
                  'note': 'Per-item randomized MCQ choice lists are not published; option availability of the source labels cannot be verified.'})
    assoc.append({'analysis': 'CONSTRUCT_NOTE', 'factor': 'B3_feature_label_space',
                  'note': 'B3 unimodal entropy/margin for LISTEN are computed over the 7-label EmotionTalk candidate space; '
                          'LISTEN source labels (e.g. ridicule, frustration, excitement) are outside it (source-label probability undefined for all rows).'})
    for a in assoc:
        a['analysis_origin'] = ORIGIN
    write_csv(OUT / 'R3_OTHER_ASSOCIATIONS.csv', assoc)
    meta = {'analysis_origin': ORIGIN, 'seed': SEED, 'bootstraps': BOOTSTRAPS, 'match_accounting': match_log,
            'three_way_matched_conflict_items': ntri,
            'inputs': ['manifests/listen/frozen_joint_outcomes.csv',
                       'results/post_audit/closure_v1/LISTEN_JOINT_ONLY_REPORT.csv (cited, not recomputed)',
                       'results/post_audit/closure_v1/LISTEN_CONDITION_DIAGNOSTICS.csv (cited, not recomputed)']}
    json.dump(meta, open(OUT / 'R3_RUN_METADATA.json', 'w'), indent=2, default=float)
    print(json.dumps(meta, indent=1, default=float))


if __name__ == '__main__':
    main()
