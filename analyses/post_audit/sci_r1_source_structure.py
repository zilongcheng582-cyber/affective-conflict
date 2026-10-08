"""R1 - EmotionTalk source predictive structure (POST_AUDIT_SCIENTIFIC_ANALYSIS_V1).

Diagnostic CV models only. Does not refit, replace or rename the frozen M3a/M3b
transfer models; M0-M6 here are R1_* diagnostic models.
Run: python -m analyses.post_audit.sci_r1_source_structure
"""
import json
import warnings
from collections import Counter

import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from analyses.post_audit.sci_common import (REPO, OUT, SEED, BOOTSTRAPS, ORIGIN, csvrows, jsonl, write_csv,
                                            metrics, auroc, log_loss, brier, grouped_folds,
                                            cluster_bootstrap, ci)

LABELS = ['angry', 'disgusted', 'fearful', 'happy', 'neutral', 'sad', 'surprised']
PAIRS = ('AT', 'AV', 'VT')
EVIDENCE = ['d_srcprob', 'd_entropy', 'd_margin']

# Diagnostic model specifications (feature groups); evidence = M3a-aligned source spec
# (source-label probability + normalized entropy) plus top1-top2 margin per the R1 task.
MODELS = {
    'R1_M0_PAIR': ['pair'],
    'R1_M1_PAIR_ORDER': ['pair', 'order'],
    'R1_M1x_PAIRxORDER': ['pair', 'order', 'pairxorder'],
    'R1_M2_PAIR_ORDER_LABEL_POS': ['pair', 'order', 'label', 'pos'],
    'R1_M3_PAIR_ORDER_EVIDENCE': ['pair', 'order', 'evidence'],
    'R1_M3a_ALIGNED_SRCPROB_ENT': ['pair', 'order', 'src', 'ent'],
    'R1_M4_M2_PLUS_EVIDENCE': ['pair', 'order', 'label', 'pos', 'evidence'],
    'R1_M4x_M2x_PLUS_EVIDENCE': ['pair', 'order', 'pairxorder', 'label', 'pos', 'evidence'],
    'R1_M5_PAIR_ORDER_ENTROPY': ['pair', 'order', 'ent'],
    'R1_M6_PAIR_SPECIFIC_EVIDENCE': 'PAIR_SPECIFIC',  # separate fits per pair: intercept+order+evidence
    'R1_M6b_PAIR_SPECIFIC_ORDER_ONLY': 'PAIR_SPECIFIC_ORDER',
}
PENALTIES = {'L2_C1': dict(C=1.0), 'UNPENALIZED': dict(C=np.inf)}


def build_records():
    meas = {r['utterance_id']: r for r in csvrows(REPO / 'manifests/emotiontalk/source_measurements.csv')}
    recs = []
    for row in jsonl(REPO / 'evidence/emotiontalk/phase2_observed_responses.jsonl'):
        if row['y_M1'] == row['y_M2'] or row['joint_outcome'] not in ('SIDE_MODALITY_1', 'SIDE_MODALITY_2'):
            continue
        m = meas[row['utterance_id']]
        pair = row['pair']
        seq = row['candidate_sequence'].split('|')
        a, b = pair[0], pair[1]
        recs.append({
            'utterance_id': row['utterance_id'], 'speaker_id': m['speaker_id'],
            'dialogue_group': row['utterance_id'].split('_')[0], 'pair': pair, 'arm': row['arm'],
            'y': int(row['joint_outcome'] == 'SIDE_MODALITY_1'),
            'order': int(row['actual_evidence_order'][0] == a),
            'label_m1': row['y_M1'], 'label_m2': row['y_M2'],
            'pos_m1': seq.index(row['y_M1']), 'pos_m2': seq.index(row['y_M2']),
            'd_srcprob': float(m['source_prob_' + a]) - float(m['source_prob_' + b]),
            'd_entropy': float(m['entropy_' + a]) - float(m['entropy_' + b]),
            'd_margin': float(m['margin_' + a]) - float(m['margin_' + b]),
        })
    return recs


def verify_against_frozen(recs):
    """Identity check only: same 663 rows/order/outcome as frozen publication CV records."""
    frozen = json.load(open(REPO / 'frozen/source_model/publication_cv_records.json'))
    scal = json.load(open(REPO / 'frozen/source_model/binding.json'))['scalers']
    assert len(recs) == len(frozen) == 663
    for r, f in zip(recs, frozen):
        assert (r['utterance_id'], r['pair'], r['y'], r['order']) == (f['utterance_id'], f['pair'], f['_y'], f['_order'])
        for raw, key, z in [('d_srcprob', 'source_probability', '_srcz'), ('d_entropy', 'normalized_entropy', '_entz'),
                            ('d_margin', 'top1_top2_margin', '_marz')]:
            assert abs((r[raw] - scal[key]['mean']) / scal[key]['sd'] - f[z]) < 1e-9
    return True


def design(recs, groups):
    cols, names = [], []
    pair = np.array([r['pair'] for r in recs])
    order = np.array([r['order'] for r in recs], float)
    if 'pair' in groups:
        for p in ('AV', 'VT'):
            cols.append((pair == p).astype(float)); names.append('pair_' + p)
    if 'order' in groups:
        cols.append(order); names.append('FIRST_IS_MODALITY1')
    if 'pairxorder' in groups:
        for p in ('AV', 'VT'):
            cols.append((pair == p) * order); names.append('pair_%s_x_order' % p)
    if 'label' in groups:
        for L in LABELS:
            if L == 'neutral':
                continue  # reference category for antisymmetric (Bradley-Terry) label coding
            cols.append(np.array([(r['label_m1'] == L) - (r['label_m2'] == L) for r in recs], float))
            names.append('label_pref_' + L)
    if 'pos' in groups:
        cols.append(np.array([r['pos_m1'] - r['pos_m2'] for r in recs], float)); names.append('cand_pos_m1_minus_m2')
        cols.append(np.array([r['pos_m1'] < r['pos_m2'] for r in recs], float)); names.append('m1_label_listed_first')
    if 'evidence' in groups or 'src' in groups:
        cols.append(np.array([r['d_srcprob'] for r in recs])); names.append('delta_source_label_probability')
    if 'evidence' in groups or 'ent' in groups:
        cols.append(np.array([r['d_entropy'] for r in recs])); names.append('delta_normalized_entropy')
    if 'evidence' in groups:
        cols.append(np.array([r['d_margin'] for r in recs])); names.append('delta_top1_top2_margin')
    if not cols:
        return np.zeros((len(recs), 0)), names
    return np.column_stack(cols), names


def fit_predict(Xtr, ytr, Xte, C):
    """Scaling (and all coefficients) estimated on the training fold only."""
    if Xtr.shape[1] == 0:
        p = np.clip(ytr.mean(), 1e-6, 1 - 1e-6)
        return np.full(len(Xte), p), None, None
    sc = StandardScaler().fit(Xtr)
    kw = dict(penalty=None) if not np.isfinite(C) else dict(C=C)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        m = LogisticRegression(max_iter=5000, **kw).fit(sc.transform(Xtr), ytr)
    return m.predict_proba(sc.transform(Xte))[:, 1], m, sc


def cv_predict(recs, spec, folds_of, C):
    y = np.array([r['y'] for r in recs])
    pair = np.array([r['pair'] for r in recs])
    fold = np.array([folds_of(r) for r in recs])
    pred = np.full(len(recs), np.nan)
    coefs = []
    if isinstance(spec, list):
        X, names = design(recs, spec)
        for k in range(5):
            te = fold == k
            pred[te], m, sc = fit_predict(X[~te], y[~te], X[te], C)
            if m is not None:
                coefs.append({'fold': k, 'pair': 'ALL', **dict(zip(names, m.coef_[0] / sc.scale_))})
    else:
        groups = ['order', 'evidence'] if spec == 'PAIR_SPECIFIC' else ['order']
        X, names = design(recs, groups)
        for p in PAIRS:
            for k in range(5):
                tr, te = (pair == p) & (fold != k), (pair == p) & (fold == k)
                if te.any():
                    pred[te], m, sc = fit_predict(X[tr], y[tr], X[te], C)
                    coefs.append({'fold': k, 'pair': p, **dict(zip(names, m.coef_[0] / sc.scale_))})
    assert np.isfinite(pred).all()
    return pred, coefs


def full_fit_clustered(recs, groups, subset=None):
    """Unpenalized full-population diagnostic GLM with utterance-cluster robust SEs (raw-delta units)."""
    rs = recs if subset is None else [r for r in recs if subset(r)]
    X, names = design(rs, groups)
    y = np.array([r['y'] for r in rs])
    cl = np.unique([r['utterance_id'] for r in rs], return_inverse=True)[1]
    res = sm.GLM(y, sm.add_constant(X, has_constant='add'), family=sm.families.Binomial()).fit(
        cov_type='cluster', cov_kwds={'groups': cl})
    out = []
    for i, n in enumerate(['intercept'] + names):
        out.append({'term': n, 'coef_log_odds': res.params[i], 'cluster_robust_se': res.bse[i],
                    'CI_low': res.conf_int()[i][0], 'CI_high': res.conf_int()[i][1], 'p_value': res.pvalues[i],
                    'N_rows': len(rs), 'N_utterances': len(set(r['utterance_id'] for r in rs))})
    return out, res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recs = build_records()
    verify_against_frozen(recs)
    y = np.array([r['y'] for r in recs])
    pair = np.array([r['pair'] for r in recs])
    utt = [r['utterance_id'] for r in recs]
    spk = [r['speaker_id'] for r in recs]
    groupings = {
        'UTTERANCE_GROUPED_5FOLD': (grouped_folds(utt, SEED), 'utterance_id', utt),
        'SPEAKER_GROUPED_5FOLD': (grouped_folds(spk, SEED), 'speaker_id', spk),
    }
    preds = {}
    coef_rows = []
    for gname, (fmap, key, _) in groupings.items():
        for pen, kw in PENALTIES.items():
            for mname, spec in MODELS.items():
                p, coefs = cv_predict(recs, spec, lambda r: fmap[r[key]], kw['C'])
                preds[(gname, pen, mname)] = p
                for c in coefs:
                    coef_rows.append({'grouping': gname, 'penalty': pen, 'model': mname, **c})

    # ---------- model comparison ----------
    comp = []
    for (g, pen, m), p in preds.items():
        row = {'grouping': g, 'penalty': pen, 'model': m, 'scope': 'ALL', 'N_rows': len(y),
               'N_utterances': len(set(utt)), 'N_y1': int(y.sum())}
        row.update(metrics(y, p))
        comp.append(row)
        for pr in PAIRS:
            s = pair == pr
            r2 = {'grouping': g, 'penalty': pen, 'model': m, 'scope': 'PAIR_' + pr, 'N_rows': int(s.sum()),
                  'N_utterances': len(set(np.array(utt)[s])), 'N_y1': int(y[s].sum())}
            r2.update(metrics(y[s], p[s]))
            comp.append(r2)

    # repeated-split stability (utterance grouping, primary penalty), 20 alternative fold seeds
    rep = {m: [] for m in MODELS}
    for s in range(20):
        fmap = grouped_folds(utt, SEED + 1 + s)
        for mname, spec in MODELS.items():
            p, _ = cv_predict(recs, spec, lambda r: fmap[r['utterance_id']], 1.0)
            rep[mname].append((auroc(y, p), log_loss(y, p)))
    for row in comp:
        if row['grouping'] == 'UTTERANCE_GROUPED_5FOLD' and row['penalty'] == 'L2_C1' and row['scope'] == 'ALL':
            a = np.array(rep[row['model']])
            row.update({'repeated_split_AUROC_mean': a[:, 0].mean(), 'repeated_split_AUROC_sd': a[:, 0].std(ddof=1),
                        'repeated_split_logloss_mean': a[:, 1].mean(), 'repeated_split_logloss_sd': a[:, 1].std(ddof=1),
                        'repeated_split_n': len(a)})
    for row in comp:
        row.update({'analysis_origin': ORIGIN, 'fold_seed': SEED,
                    'model_identity': 'R1_DIAGNOSTIC_CV_MODEL_NOT_FROZEN_TRANSFER_MODEL'})
    write_csv(OUT / 'R1_MODEL_COMPARISON.csv', comp)

    # ---------- OOF predictions ----------
    oof = []
    for i, r in enumerate(recs):
        row = {k: r[k] for k in ('utterance_id', 'speaker_id', 'pair', 'arm', 'y', 'order', 'label_m1', 'label_m2',
                                 'pos_m1', 'pos_m2', 'd_srcprob', 'd_entropy', 'd_margin')}
        row['utt_fold'] = groupings['UTTERANCE_GROUPED_5FOLD'][0][r['utterance_id']]
        row['spk_fold'] = groupings['SPEAKER_GROUPED_5FOLD'][0][r['speaker_id']]
        for (g, pen, m), p in preds.items():
            row['p__%s__%s__%s' % ({'UTTERANCE_GROUPED_5FOLD': 'utt', 'SPEAKER_GROUPED_5FOLD': 'spk'}[g], pen, m)] = p[i]
        oof.append(row)
    write_csv(OUT / 'R1_OUT_OF_FOLD_PREDICTIONS.csv', oof)

    # ---------- paired uncertainty ----------
    contrasts = [('R1_M3_PAIR_ORDER_EVIDENCE', 'R1_M1_PAIR_ORDER'),
                 ('R1_M3a_ALIGNED_SRCPROB_ENT', 'R1_M1_PAIR_ORDER'),
                 ('R1_M5_PAIR_ORDER_ENTROPY', 'R1_M1_PAIR_ORDER'),
                 ('R1_M2_PAIR_ORDER_LABEL_POS', 'R1_M1_PAIR_ORDER'),
                 ('R1_M4_M2_PLUS_EVIDENCE', 'R1_M2_PAIR_ORDER_LABEL_POS'),
                 ('R1_M4x_M2x_PLUS_EVIDENCE', 'R1_M1x_PAIRxORDER'),
                 ('R1_M3_PAIR_ORDER_EVIDENCE', 'R1_M5_PAIR_ORDER_ENTROPY'),
                 ('R1_M3_PAIR_ORDER_EVIDENCE', 'R1_M2_PAIR_ORDER_LABEL_POS'),
                 ('R1_M1_PAIR_ORDER', 'R1_M0_PAIR'),
                 ('R1_M6_PAIR_SPECIFIC_EVIDENCE', 'R1_M6b_PAIR_SPECIFIC_ORDER_ONLY'),
                 ('R1_M6_PAIR_SPECIFIC_EVIDENCE', 'R1_M3_PAIR_ORDER_EVIDENCE')]
    unc = []
    for g, (fmap, key, cl_ids) in groupings.items():
        for pen in PENALTIES:
            for scope in ['ALL'] + ['PAIR_' + p for p in PAIRS]:
                s = np.ones(len(y), bool) if scope == 'ALL' else pair == scope[5:]
                ys = y[s]
                cls = np.array(cl_ids)[s]
                for a, b in contrasts:
                    pa, pb = preds[(g, pen, a)][s], preds[(g, pen, b)][s]

                    def stat(idx, pa=pa, pb=pb, ys=ys):
                        return {'dAUROC': auroc(ys[idx], pa[idx]) - auroc(ys[idx], pb[idx]),
                                'dLL': log_loss(ys[idx], pa[idx]) - log_loss(ys[idx], pb[idx]),
                                'dBrier': brier(ys[idx], pa[idx]) - brier(ys[idx], pb[idx])}
                    bs = cluster_bootstrap(cls, stat)
                    pt = stat(np.arange(len(ys)))
                    row = {'grouping': g, 'penalty': pen, 'scope': scope, 'model': a, 'reference': b,
                           'bootstrap_cluster': 'utterance_id' if g.startswith('UTT') else 'speaker_id',
                           'N_rows': len(ys), 'N_clusters': len(set(cls))}
                    for k in ('dAUROC', 'dLL', 'dBrier'):
                        lo, hi, n = ci(bs[k])
                        row.update({k: pt[k], k + '_CI_low': lo, k + '_CI_high': hi, k + '_defined_bootstraps': n,
                                    k + '_prop_improve': float(np.mean(bs[k] > 0)) if k == 'dAUROC' else float(np.mean(bs[k][np.isfinite(bs[k])] < 0))})
                    row.update({'bootstrap_replicates': BOOTSTRAPS, 'bootstrap_seed': SEED,
                                'CI_method': 'CLUSTER_PERCENTILE_95_FIXED_OOF_PREDICTIONS', 'analysis_origin': ORIGIN})
                    unc.append(row)
    write_csv(OUT / 'R1_PAIRED_UNCERTAINTY.csv', unc)

    # ---------- heterogeneity ----------
    het = []
    for pr in PAIRS:
        for o in (1, 0):
            s = (pair == pr) & (np.array([r['order'] for r in recs]) == o)
            het.append({'table': 'PAIR_ORDER_CELL', 'pair': pr, 'FIRST_IS_MODALITY1': o, 'N_rows': int(s.sum()),
                        'P_modality1_selected': float(y[s].mean()),
                        'first_presented_selected_rate': float(np.mean(y[s] == o))})
    # pair-specific diagnostic fits (unpenalized, cluster-robust) - coefficient sign stability
    for pr in PAIRS:
        rows, _ = full_fit_clustered(recs, ['order', 'evidence'], lambda r, pr=pr: r['pair'] == pr)
        for c in rows:
            het.append({'table': 'PAIR_SPECIFIC_FULL_FIT_ORDER_EVIDENCE', 'pair': pr, **c})
        rows, _ = full_fit_clustered(recs, ['order', 'ent'], lambda r, pr=pr: r['pair'] == pr)
        for c in rows:
            het.append({'table': 'PAIR_SPECIFIC_FULL_FIT_ORDER_ENTROPY', 'pair': pr, **c})
    for spec_name, groups in [('POOLED_FULL_FIT_M3_EVIDENCE', ['pair', 'order', 'evidence']),
                              ('POOLED_FULL_FIT_M3a_ALIGNED', ['pair', 'order', 'src', 'ent']),
                              ('POOLED_FULL_FIT_M4_M2_PLUS_EVIDENCE', ['pair', 'order', 'label', 'pos', 'evidence']),
                              ('POOLED_FULL_FIT_M1x_PAIRxORDER', ['pair', 'order', 'pairxorder'])]:
        rows, _ = full_fit_clustered(recs, groups)
        for c in rows:
            het.append({'table': spec_name, 'pair': 'ALL', **c})
    # Wald test of pair x order interaction (cluster-robust)
    _, res = full_fit_clustered(recs, ['pair', 'order', 'pairxorder'])
    R = np.zeros((2, len(res.params))); R[0, -2] = 1; R[1, -1] = 1
    w = res.wald_test(R, scalar=True)
    het.append({'table': 'WALD_PAIRxORDER_INTERACTION_CLUSTER_ROBUST', 'pair': 'ALL', 'term': 'pair_AV_x_order,pair_VT_x_order',
                'chi2_df2': float(w.statistic), 'p_value': float(w.pvalue)})
    # Wald test of evidence pair-heterogeneity: pooled model with pair x evidence interactions
    X, names = design(recs, ['pair', 'order', 'pairxorder', 'evidence'])
    extra, enames = [], []
    for p in ('AV', 'VT'):
        for j, n in enumerate(['delta_source_label_probability', 'delta_normalized_entropy', 'delta_top1_top2_margin']):
            extra.append((pair == p) * X[:, names.index(n)]); enames.append('pair_%s_x_%s' % (p, n))
    Xi = sm.add_constant(np.column_stack([X] + extra), has_constant='add')
    cl = np.unique(utt, return_inverse=True)[1]
    ri = sm.GLM(y, Xi, family=sm.families.Binomial()).fit(cov_type='cluster', cov_kwds={'groups': cl})
    R = np.zeros((6, Xi.shape[1]))
    for i in range(6):
        R[i, Xi.shape[1] - 6 + i] = 1
    w = ri.wald_test(R, scalar=True)
    het.append({'table': 'WALD_PAIRxEVIDENCE_INTERACTION_CLUSTER_ROBUST', 'pair': 'ALL', 'term': ','.join(enames),
                'chi2_df6': float(w.statistic), 'p_value': float(w.pvalue)})
    # fold-wise CV coefficient sign stability (primary penalty, utterance grouping)
    for mname in ('R1_M3_PAIR_ORDER_EVIDENCE', 'R1_M4_M2_PLUS_EVIDENCE', 'R1_M6_PAIR_SPECIFIC_EVIDENCE', 'R1_M5_PAIR_ORDER_ENTROPY'):
        cr = [c for c in coef_rows if c['grouping'] == 'UTTERANCE_GROUPED_5FOLD' and c['penalty'] == 'L2_C1' and c['model'] == mname]
        for pr in sorted(set(c['pair'] for c in cr)):
            for term in ('FIRST_IS_MODALITY1', 'delta_source_label_probability', 'delta_normalized_entropy', 'delta_top1_top2_margin'):
                v = [c[term] for c in cr if c['pair'] == pr and term in c]
                if v:
                    het.append({'table': 'CV_FOLD_COEF_SIGN_STABILITY_L2', 'model': mname, 'pair': pr, 'term': term,
                                'n_folds': len(v), 'n_positive': int(np.sum(np.array(v) > 0)),
                                'fold_coef_min': min(v), 'fold_coef_max': max(v), 'fold_coef_mean': float(np.mean(v))})
    # descriptive label / position structure
    win = Counter(); tot = Counter()
    for r in recs:
        sel, rej = (r['label_m1'], r['label_m2']) if r['y'] else (r['label_m2'], r['label_m1'])
        win[sel] += 1; tot[r['label_m1']] += 1; tot[r['label_m2']] += 1
    for L in LABELS:
        het.append({'table': 'LABEL_SELECTION_RATE_WHEN_IN_CONFLICT', 'term': L, 'N_rows': tot[L],
                    'selected_rate': win[L] / tot[L] if tot[L] else None})
    for r_ in ('earlier', 'later'):
        s = np.array([(r['pos_m1'] < r['pos_m2']) == (r_ == 'earlier') for r in recs])
        het.append({'table': 'CANDIDATE_POSITION_MODALITY1_LABEL_LISTED', 'term': r_, 'N_rows': int(s.sum()),
                    'P_modality1_selected': float(y[s].mean())})
    for h in het:
        h['analysis_origin'] = ORIGIN
    write_csv(OUT / 'R1_PAIR_HETEROGENEITY.csv', het)

    # historical alignment check: R1 M3a-aligned unpenalized with historical seed vs publication CV implementation
    from analyses.phase2 import publication_cv
    frozen = json.load(open(REPO / 'frozen/source_model/publication_cv_records.json'))
    hist = publication_cv.compare_models(frozen)['models']['M3a']['metrics']
    hmap = grouped_folds(utt, 20260928)
    p, _ = cv_predict(recs, MODELS['R1_M3a_ALIGNED_SRCPROB_ENT'], lambda r: hmap[r['utterance_id']], np.inf)
    meta = {'analysis_origin': ORIGIN, 'python_seed': SEED, 'bootstraps': BOOTSTRAPS,
            'N_records': len(recs), 'N_utterances': len(set(utt)), 'N_speakers': len(set(spk)),
            'pair_counts': dict(Counter(pair.tolist())),
            'publication_cv_M3a_metrics_seed20260928': hist,
            'R1_M3a_aligned_unpenalized_seed20260928': metrics(y, p),
            'inputs': ['manifests/emotiontalk/source_measurements.csv', 'evidence/emotiontalk/phase2_observed_responses.jsonl',
                       'frozen/source_model/publication_cv_records.json (identity check)', 'frozen/source_model/binding.json (scaler identity check only)']}
    json.dump(meta, open(OUT / 'R1_RUN_METADATA.json', 'w'), indent=2, default=float)
    print(json.dumps(meta, indent=1, default=float))


if __name__ == '__main__':
    main()
