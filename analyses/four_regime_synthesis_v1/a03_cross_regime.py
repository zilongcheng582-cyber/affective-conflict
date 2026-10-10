"""Cross-regime structure analysis restricted to quantities with a shared operational definition.
Unfitted score: S = H_other - H_audio  (positive => audio side has LOWER normalized entropy). No parameter is estimated.
Frozen zero-refit predictions are replayed (read-only) for diagnostics; no transfer model is refitted."""
import json
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1.common import *

SUB = 'tables'
SEVEN = {'angry', 'disgusted', 'fearful', 'happy', 'neutral', 'sad', 'surprised'}
# regime groups for the cross-regime tables (conflict rows only). ET_VT excluded from A-T/A-V headline: no audio-side-as-mod1 pairing (V-T).
GROUPS = {
    'A-T': ['ET_AT_conflict', 'MCR_AT_adversarial_text', 'LISTEN_3C'],
    'A-V': ['ERI1_AV_CLEAN', 'ET_AV_conflict', 'CAMER_audio-aligned', 'CAMER_video-aligned'],
    'V-T(reference,not cross-dataset)': ['ET_VT_conflict'],
}


def conflict_rows(L):
    d = L[(L.stratum == 'CONFLICT')].copy()
    # in ET: mod1 is V for VT; audio-side share is not defined there. For A-pairs mod1 == A.
    d['audio_is_mod1'] = d.mod1 == 'A'
    return d


def dist(d):
    n = len(d); r = {'n_trials': n, 'n_items': d.item_id.nunique(), 'n_clusters': d.cluster_id.nunique()}
    for c in ['SIDE_1', 'SIDE_2', 'OTHER', 'PARSE_FAIL', 'TECH_MISSING']:
        r[c] = int((d.outcome == c).sum())
    avail = n - r['TECH_MISSING']; r['n_available'] = avail
    for c in ['SIDE_1', 'SIDE_2', 'OTHER', 'PARSE_FAIL']:
        r[c + '_share_of_available'] = r[c] / avail if avail else np.nan
    b = r['SIDE_1'] + r['SIDE_2']; r['binary_coverage'] = b / avail if avail else np.nan; r['P_SIDE_1_given_binary'] = r['SIDE_1'] / b if b else np.nan
    return r


def run():
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    C = conflict_rows(L); res = {}
    # ---- X1 full distribution + cluster CIs for binary coverage and P(audio | binary)
    rows = []
    for grp, regs in GROUPS.items():
        for rg in regs:
            d = C[C.regime == rg]
            d = d[d.outcome != 'TECH_MISSING']
            if len(d) == 0: continue
            r = dict(group=grp, regime=rg, dataset=d.dataset.iloc[0], first_modality_label='mod1=' + d.mod1.iloc[0] + ', mod2=' + d.mod2.iloc[0], **dist(C[C.regime == rg]))
            cov = d.outcome.isin(['SIDE_1', 'SIDE_2']).values.astype(float)
            r['coverage_ci'] = cluster_boot(d.cluster_id.values, lambda i: cov[i].mean(), 2000, SEED + 71)[1:3]
            b = d[d.outcome.isin(['SIDE_1', 'SIDE_2'])]; yb = (b.outcome == 'SIDE_1').values.astype(float)
            r['P_SIDE_1_given_binary_ci'] = cluster_boot(b.cluster_id.values, lambda i: yb[i].mean(), 2000, SEED + 72)[1:3]
            oo = (d.outcome == 'OTHER').values.astype(float)
            r['OTHER_ci'] = cluster_boot(d.cluster_id.values, lambda i: oo[i].mean(), 2000, SEED + 73)[1:3]
            rows.append(r)
    t = pd.DataFrame(rows)
    for c in ['coverage_ci', 'P_SIDE_1_given_binary_ci', 'OTHER_ci']:
        t[[c + '_lo', c + '_hi']] = pd.DataFrame(t[c].tolist(), index=t.index); t = t.drop(columns=c)
    write(t, 'X1_cross_regime_outcome_distribution.csv', SUB)

    # ---- X2 order sensitivity of audio-side choice (audio first vs audio last), item-paired; cluster bootstrap
    rows = []
    for rg in ['ET_AT_conflict', 'ET_AV_conflict', 'MCR_AT_adversarial_text', 'CAMER_audio-aligned', 'CAMER_video-aligned', 'ET_VT_conflict']:
        d = C[(C.regime == rg) & (C.outcome != 'TECH_MISSING')]
        d = d.assign(audio_first=(d.first_mod == 'A') if rg != 'ET_VT_conflict' else (d.first_mod == 'V'))
        sa = d.assign(sa=(d.outcome == 'SIDE_1').astype(float), ot=(d.outcome == 'OTHER').astype(float), bi=d.outcome.isin(['SIDE_1', 'SIDE_2']).astype(float))
        w = sa.pivot_table(index=['item_id', 'cluster_id'], columns='audio_first', values=['sa', 'ot', 'bi']).dropna().reset_index()
        for m_, nm in [('sa', 'P(side=mod1)'), ('ot', 'P(OTHER)'), ('bi', 'binary_coverage')]:
            diff = (w[(m_, True)] - w[(m_, False)]).values
            pt, lo, hi, _ = cluster_boot(w['cluster_id'].values, lambda i: diff[i].mean(), 2000, SEED + 81)
            rows.append(dict(regime=rg, measure=nm, first_listed_modality='VIDEO(mod1)' if rg == 'ET_VT_conflict' else 'AUDIO', mean_first_minus_second=pt, ci_lo=lo, ci_hi=hi, n_paired_items=len(w)))
    write(pd.DataFrame(rows), 'X2_order_sensitivity_paired.csv', SUB)

    # ---- X3 unfitted lower-entropy rule: AUROC (all, within order, dual-readable, both labels in 7-space)
    rows = []
    def add(name, d, filt):
        d = d[d.outcome.isin(['SIDE_1', 'SIDE_2'])]
        if filt is not None: d = d[filt(d)]
        if len(d) < 20 or d.outcome.nunique() < 2:
            rows.append(dict(regime=name[0], restriction=name[1], n_binary=len(d), AUROC=np.nan)); return
        y = (d.outcome == 'SIDE_1').values.astype(float); s = (d.H2 - d.H1).values
        pt, lo, hi, _ = cluster_boot(d.cluster_id.values, lambda i: auroc(y[i], s[i]), 2000, SEED + 91)
        # order-adjusted: mean of within-order AUROCs
        wo = [auroc(y[(d.order == o).values], s[(d.order == o).values]) for o in d.order.unique() if ((d.order == o) & (d.outcome == 'SIDE_1')).sum() > 3 and ((d.order == o) & (d.outcome == 'SIDE_2')).sum() > 3]
        rows.append(dict(regime=name[0], restriction=name[1], n_binary=len(d), n_clusters=d.cluster_id.nunique(), P_SIDE_1=y.mean(), AUROC=pt, ci_lo=lo, ci_hi=hi, mean_within_order_AUROC=np.mean(wo) if wo else np.nan))
    for rg in sum(GROUPS.values(), []):
        d = C[C.regime == rg]
        if rg == 'ET_VT_conflict': pass
        add((rg, 'all binary-resolved'), d, None)
        if d.dataset.iloc[0] != 'LISTEN':
            add((rg, 'both B3 unimodal top-1 == source label (dual-readable, B3 definition)'), d, lambda x: x.read1 & x.read2)
        add((rg, 'both source labels inside 7-label B3 space'), d, lambda x: x.y1.isin(SEVEN) & x.y2.isin(SEVEN))
        add((rg, 'at least one source label OUTSIDE 7-label space'), d, lambda x: ~(x.y1.isin(SEVEN) & x.y2.isin(SEVEN)))
    write(pd.DataFrame(rows), 'X3_unfitted_entropy_rule_by_regime.csv', SUB)

    # ---- X4 frozen zero-refit predictions: replay-only diagnostics
    pr = read_csv('results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv')
    cit = read_csv('results/post_audit/closure_v1/ZERO_REFIT_BASELINE_COMPARISON_V1.csv')
    roles = {'MCR_AT_PRIMARY': 'MCR', 'CAMER_AV_SUPPORT_LIMITED_SOURCEPROB': 'CA-MER', 'CAMER_AV_MARGIN_SENSITIVITY': 'CA-MER', 'LISTEN_AT_MARGIN_SENSITIVITY': 'LISTEN'}
    rows = []
    Lt = L[L.target_record_id.notna()][['target_record_id', 'dataset', 'regime', 'outcome', 'order', 'cluster_id', 'item_id']]
    for role in roles:
        p = pr[pr.analysis_role == role].merge(Lt, on='target_record_id', suffixes=('', '_L'))
        if role == 'LISTEN_AT_MARGIN_SENSITIVITY': p = p[p.regime == 'LISTEN_3C']
        p = p[(p.outcome.isin(['SIDE_1', 'SIDE_2'])) & (p.execution_accounting_class.isin(['RESOLVED_SIDE_A', 'RESOLVED_SIDE_T', 'RESOLVED_SIDE_V']))]
        y = (p.outcome == 'SIDE_1').values.astype(float); s = p.predicted_p_SIDE_A.values
        first = p.order.str[0].eq('A').values
        base = dict(analysis_role=role, dataset=roles[role], n_evaluated=len(y), prevalence_SIDE_AUDIO=y.mean(), AUROC_frozen=auroc(y, s),
                    AUROC_within_audio_first=auroc(y[first], s[first]), AUROC_within_audio_last=auroc(y[~first], s[~first]),
                    AUROC_of_order_indicator_alone=max(auroc(y, first.astype(float)), 1 - auroc(y, first.astype(float))),
                    log_loss_frozen=log_loss(y, s), log_loss_oracle_target_prevalence_constant=log_loss(y, np.full(len(y), y.mean())))
        base['log_loss_frozen_minus_oracle_constant'] = base['log_loss_frozen'] - base['log_loss_oracle_target_prevalence_constant']
        fo = []
        for o_ in [True, False]:
            m_ = first == o_; fo.append(log_loss(y[m_], np.full(m_.sum(), y[m_].mean())) * m_.mean())
        base['log_loss_oracle_order_specific_constant'] = float(sum(fo))
        base['log_loss_frozen_minus_oracle_order_specific_constant'] = base['log_loss_frozen'] - base['log_loss_oracle_order_specific_constant']
        pt, lo, hi, _ = cluster_boot(p.cluster_id.values, lambda i: log_loss(y[i], s[i]) - log_loss(y[i], np.full(len(i), y[i].mean())), 1000, SEED + 101)
        base['ll_minus_oracle_const_ci_lo'], base['ll_minus_oracle_const_ci_hi'] = lo, hi
        rows.append(base)
    write(pd.DataFrame(rows), 'X4_frozen_zero_refit_replay_diagnostics.csv', SUB)
    # citation table of frozen metrics (read-only copy of selected columns)
    write(cit[['model', 'N_evaluated', 'AUROC', 'balanced_accuracy', 'log_loss', 'coverage']].assign(source='results/post_audit/closure_v1/ZERO_REFIT_BASELINE_COMPARISON_V1.csv(cited,unchanged)'), 'X4b_cited_frozen_metrics.csv', SUB)

    # ---- X5 resolved-binary share by third-factor: label-space overlap with coverage
    rows = []
    for rg, d in C.groupby('regime'):
        d = d[d.outcome != 'TECH_MISSING']
        rows.append(dict(regime=rg, n=len(d), frac_audio_label_in_7=d.y1.isin(SEVEN).mean(), frac_other_label_in_7=d.y2.isin(SEVEN).mean(),
                         frac_both_in_7=(d.y1.isin(SEVEN) & d.y2.isin(SEVEN)).mean(), binary_coverage=d.outcome.isin(['SIDE_1', 'SIDE_2']).mean(),
                         coverage_among_both_in_7=d[d.y1.isin(SEVEN) & d.y2.isin(SEVEN)].outcome.isin(['SIDE_1', 'SIDE_2']).mean() if (d.y1.isin(SEVEN) & d.y2.isin(SEVEN)).any() else np.nan,
                         coverage_among_not_both_in_7=d[~(d.y1.isin(SEVEN) & d.y2.isin(SEVEN))].outcome.isin(['SIDE_1', 'SIDE_2']).mean() if (~(d.y1.isin(SEVEN) & d.y2.isin(SEVEN))).any() else np.nan))
    write(pd.DataFrame(rows), 'X5_label_space_overlap_vs_coverage.csv', SUB)
    # ---- X6 item persistence of OTHER across the two presentation orders (and LISTEN 3A/3B/3C persistence recomputed)
    rows = []
    for rg in ['ET_AT_conflict', 'ET_AV_conflict', 'ET_VT_conflict', 'MCR_AT_adversarial_text', 'CAMER_audio-aligned', 'CAMER_video-aligned']:
        d = C[(C.regime == rg) & (C.outcome != 'TECH_MISSING')]
        w = d.pivot_table(index=['item_id', 'cluster_id'], columns='order', values='outcome', aggfunc='first').dropna().reset_index()
        o1, o2 = [c_ for c_ in w.columns if c_ not in ('item_id', 'cluster_id')]
        a = (w[o1] == 'OTHER').values; b = (w[o2] == 'OTHER').values
        kk = a | b
        rows.append(dict(regime=rg, n_items=len(w), items_OTHER_in_at_least_one_order=int(kk.sum()), items_OTHER_in_both_orders=int((a & b).sum()),
                         P_both_given_any=(a & b).sum() / max(kk.sum(), 1), expected_both_if_independent_given_marginals=float(a.mean() * b.mean() * len(w)), OTHER_label_identity_available=rg.startswith(('ET_', 'CAMER')),
                         note='independence expectation uses the two order-specific OTHER rates'))
    lw = C[C.dataset == 'LISTEN'].assign(base=lambda d: d.item_id.str.rsplit('_u_', n=1).str[0]).pivot_table(index='base', columns='regime', values='outcome', aggfunc='first').dropna()
    oth = (lw == 'OTHER'); kk = oth.any(axis=1)
    rows.append(dict(regime='LISTEN_3A/3B/3C_triple_matched', n_items=len(lw), items_OTHER_in_at_least_one_order=int(kk.sum()), items_OTHER_in_both_orders=int(oth.all(axis=1).sum()), P_both_given_any=oth.all(axis=1).sum() / kk.sum(),
                     expected_both_if_independent_given_marginals=float(oth.mean().prod() * len(lw)), OTHER_label_identity_available=False, note='across CONDITIONS (not orders); independence expectation from the three condition-specific OTHER rates'))
    write(pd.DataFrame(rows), 'X6_OTHER_item_persistence.csv', SUB)
    save_registry('a03')
    return res


if __name__ == '__main__':
    run()
