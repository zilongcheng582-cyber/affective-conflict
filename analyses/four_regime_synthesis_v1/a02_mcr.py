"""Within-dataset structural analysis: MCR (A_THEN_T / T_THEN_A, adversarial text assertion only)."""
import json
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1.common import *

SUB = 'tables'


def sh(d, cats=('SIDE_1', 'SIDE_2', 'OTHER')):
    n = len(d); r = {'n': n}
    for c in cats: r[c] = int((d.outcome == c).sum()); r[c + '_share'] = r[c] / n if n else np.nan
    return r


def run():
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    m = L[L.dataset == 'MCR'].copy()
    can = read_csv('manifests/mcr/canonical_arbitration.csv').set_index('sample_id')
    m['cand_type'] = m.y2
    res = {}
    # ---- M1 paired order transitions (item = unit; dialogue cluster inferred from audio file name)
    w = m.pivot_table(index=['item_id', 'cluster_id'], columns='order', values='outcome', aggfunc='first').reset_index()
    tab = pd.crosstab(w['A_THEN_T'], w['T_THEN_A']).reindex(index=['SIDE_1', 'SIDE_2', 'OTHER'], columns=['SIDE_1', 'SIDE_2', 'OTHER'], fill_value=0)
    t = tab.stack().reset_index(); t.columns = ['A_THEN_T_outcome(SIDE_1=audio)', 'T_THEN_A_outcome', 'n_items']; t['share'] = t.n_items / len(w)
    write(t, 'MCR_M1_order_transition_matrix.csv', SUB)
    res['n_items'] = len(w); res['n_dialogue_clusters_inferred'] = int(w.cluster_id.nunique())
    for cat in ['SIDE_1', 'SIDE_2', 'OTHER']:
        a = (w['A_THEN_T'] == cat).values.astype(float); b = (w['T_THEN_A'] == cat).values.astype(float)
        pt, lo, hi, _ = cluster_boot(w.cluster_id.values, lambda i: (b[i] - a[i]).mean(), 2000, SEED + 1)
        res[f'share_diff_T_THEN_A_minus_A_THEN_T_{cat}'] = [pt, lo, hi]
    nA, nB = int(((w['A_THEN_T'] == 'SIDE_1') & (w['T_THEN_A'] != 'SIDE_1')).sum()), int(((w['A_THEN_T'] != 'SIDE_1') & (w['T_THEN_A'] == 'SIDE_1')).sum())
    res['SIDE_AUDIO_discordant_pairs_(A_first_only, T_first_only)'] = [nA, nB]
    res['order_stability'] = dict(both_SIDE_AUDIO=int(((w['A_THEN_T'] == 'SIDE_1') & (w['T_THEN_A'] == 'SIDE_1')).sum()), both_SIDE_TEXT=int(((w['A_THEN_T'] == 'SIDE_2') & (w['T_THEN_A'] == 'SIDE_2')).sum()),
                                  audio_choice_only_when_text_first_recency=int(((w['A_THEN_T'] == 'SIDE_2') & (w['T_THEN_A'] == 'SIDE_1')).sum()),
                                  text_choice_only_when_audio_first_primacy=int(((w['A_THEN_T'] == 'SIDE_1') & (w['T_THEN_A'] == 'SIDE_2')).sum()),
                                  any_OTHER=int(((w['A_THEN_T'] == 'OTHER') | (w['T_THEN_A'] == 'OTHER')).sum()))
    # ---- M2 full distribution by order, ground-truth (audio) label, competitor (text) label, and combination
    rows = []
    for o, g in m.groupby('order'): rows.append(dict(stratifier='ALL', level='ALL', order=o, **sh(g)))
    for var in ['y1', 'y2']:
        for (lvl, o), g in m.groupby([var, 'order']): rows.append(dict(stratifier='audio_GT_label' if var == 'y1' else 'text_assertion_label', level=lvl, order=o, **sh(g)))
    for (a, b, o), g in m.groupby(['y1', 'y2', 'order']):
        if len(g) >= 10: rows.append(dict(stratifier='GT_x_assertion(n>=10)', level=f'{a}|{b}', order=o, **sh(g)))
    write(pd.DataFrame(rows), 'MCR_M2_outcome_by_label_strata.csv', SUB)
    # OTHER identity: not in repo
    res['OTHER_label_identity'] = 'NOT_AVAILABLE: row-level MCR generations (audit/QWEN25_MCR_CONTROLLED_V3/full_run/*.jsonl) are not in the repository; only outcome class'
    # ---- readability-proxy: B3 unimodal top-1 vs label (corrected B3, 7-label space)
    rows = []
    for var, top, nm in [('y1', 'top1_1', 'audio_vs_GT'), ('y2', 'top1_2', 'text_vs_assertion')]:
        d = m[m.order == 'A_THEN_T']; rows.append(dict(measure=f'B3 top-1 == {nm}', n=len(d), rate=(d[top] == d[var]).mean()))
    d = m[m.order == 'A_THEN_T']
    both = d[(d.top1_1 == d.y1) & (d.top1_2 == d.y2)]
    rows.append(dict(measure='B3 both-readable (audio==GT & text==assertion)', n=len(both), rate=len(both) / len(d)))
    write(pd.DataFrame(rows), 'MCR_M2b_B3_unimodal_readability.csv', SUB)
    # ---- M3 metrics under extreme imbalance using frozen corrected predictions (replay-only; nothing refit)
    pr = read_csv('results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv')
    pr = pr[pr.analysis_role == 'MCR_AT_PRIMARY'].merge(m[['target_record_id', 'y1', 'y2', 'cluster_id', 'outcome', 'order']], on='target_record_id')
    pr = pr[pr.outcome.isin(['SIDE_1', 'SIDE_2'])]
    y = (pr.outcome == 'SIDE_1').values.astype(float); p = pr.predicted_p_SIDE_A.values
    prev = y.mean()
    def mets(i):
        yy, pp = y[i], p[i]
        return [auroc(yy, pp), log_loss(yy, pp), log_loss(yy, np.full(len(yy), yy.mean()))]
    pt = mets(np.arange(len(y)))
    rows = [dict(metric='N_resolved', value=len(y)), dict(metric='SIDE_AUDIO_prevalence', value=prev), dict(metric='AUROC_frozen_M3a', value=pt[0]),
            dict(metric='log_loss_frozen_M3a', value=pt[1]), dict(metric='log_loss_target_prevalence_constant(oracle,in-sample,NOT a valid model)', value=pt[2]),
            dict(metric='log_loss_M3a_minus_oracle_constant', value=pt[1] - pt[2])]
    ths = pr.predicted_p_SIDE_A
    # BA at 0.5, and at prevalence-matched (top-k) threshold; expected BA of a constant is 0.5
    def ba(pred):
        tpr = pred[y == 1].mean(); tnr = (1 - pred[y == 0]).mean(); return (tpr + tnr) / 2
    rows.append(dict(metric='BA_at_source_threshold_0.5', value=ba((p >= 0.5).astype(float))))
    k = int(y.sum()); thr = np.sort(p)[::-1][k - 1]
    rows.append(dict(metric='BA_at_prevalence_matched_threshold(post-hoc)', value=ba((p >= thr).astype(float))))
    rows.append(dict(metric='fraction_predicted_SIDE_AUDIO_at_0.5', value=float((p >= 0.5).mean())))
    # order-only AUROC, GT-label-stratified AUROC
    ordv = (pr.order == 'A_THEN_T').astype(float).values
    rows.append(dict(metric='AUROC_order_indicator_alone(A_THEN_T=audio first)', value=auroc(y, ordv)))
    rows.append(dict(metric='AUROC_M3a_within_order=A_THEN_T', value=auroc(y[ordv == 1], p[ordv == 1])))
    rows.append(dict(metric='AUROC_M3a_within_order=T_THEN_A', value=auroc(y[ordv == 0], p[ordv == 0])))
    neutral = (pr.y1 == 'neutral').values
    rows.append(dict(metric='AUROC_M3a_within_GT=neutral', value=auroc(y[neutral], p[neutral]), n=int(neutral.sum()), n_pos=int(y[neutral].sum())))
    rows.append(dict(metric='AUROC_M3a_within_GT!=neutral', value=auroc(y[~neutral], p[~neutral]), n=int((~neutral).sum()), n_pos=int(y[~neutral].sum())))
    rows.append(dict(metric='SIDE_AUDIO_prevalence_GT=neutral', value=float(y[neutral].mean())))
    rows.append(dict(metric='SIDE_AUDIO_prevalence_GT!=neutral', value=float(y[~neutral].mean())))
    for nm, i in [('AUROC_M3a', 0), ('log_loss_M3a', 1)]:
        a, lo, hi, _ = cluster_boot(pr.cluster_id.values, lambda ii: mets(ii)[i], 1000, SEED + 5); rows.append(dict(metric=nm + '_ci95', value=a, lo=lo, hi=hi))
    a, lo, hi, _ = cluster_boot(pr.cluster_id.values, lambda ii: mets(ii)[1] - mets(ii)[2], 1000, SEED + 6)
    rows.append(dict(metric='log_loss_M3a_minus_oracle_constant_ci95', value=a, lo=lo, hi=hi))
    # score distribution
    rows.append(dict(metric='M3a_score_quantiles_[5,25,50,75,95]', value=str(np.percentile(p, [5, 25, 50, 75, 95]).round(4).tolist())))
    write(pd.DataFrame(rows), 'MCR_M3_imbalance_metric_decomposition.csv', SUB)
    # ---- M4 executed-condition matrix + duplicates
    ex = [dict(text_condition=c, status=s, evidence=e) for c, s, e in [
        ('Adversarial (text asserts a competitor label != GT)', 'EXECUTED', 'modality2_source_label == competitor_emotion for 1818/1818 joint rows; 0 equal GT; arms A_ONLY,T_ONLY,A_THEN_T,T_THEN_A (3636 calls)'),
        ('Faithful (text asserts GT)', 'NOT_EXECUTED_IN_CONTROLLED_V2', 'text present in canonical_arbitration.csv but no arm uses it (arm_counts only 4 arms x 909)'),
        ('Neutral (no description)', 'NOT_EXECUTED_IN_CONTROLLED_V2', 'same'),
        ('Irrelevant (unrelated sound description)', 'NOT_EXECUTED_IN_CONTROLLED_V2', 'same')]]
    write(pd.DataFrame(ex), 'MCR_M4_text_condition_execution_matrix.csv', SUB)
    dup = read_csv('results/post_audit/closure_v1/MCR_CONTENT_DUPLICATE_AUDIT_V1.csv')
    res['content_dup_items'] = dup.sample_id.tolist()
    res['dialogue_cluster_note'] = 'cluster = dia{N} token from MCR audio filename (inferred, not an official ID)'
    (INTER / 'MCR_within_summary.json').write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
    save_registry('a02_mcr')
    return res


if __name__ == '__main__':
    print(run())
