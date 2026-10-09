"""Within-dataset structural analysis: EmotionTalk (Phase2 pairs, ERI1 AV audio-reliability intervention)."""
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1.common import *

SUB = 'tables'


def shares(df, col='outcome', cats=('SIDE_1', 'SIDE_2', 'OTHER', 'PARSE_FAIL', 'TECH_MISSING', 'SHARED')):
    n = len(df); r = {'n_trials': n, 'n_items': df.item_id.nunique()}
    for c in cats:
        k = int((df[col] == c).sum()); lo, hi = wilson(k, n)
        r[f'{c}_n'] = k; r[f'{c}_share'] = k / n if n else np.nan; r[f'{c}_wilson_lo'] = lo; r[f'{c}_wilson_hi'] = hi
    return r


def item_boot_share(df, cat, reps=B, seed=SEED):
    y = (df.outcome == cat).values.astype(float)
    return cluster_boot(df.cluster_id.values, lambda i: y[i].mean(), reps, seed)


def run():
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    et = L[L.dataset == 'EmotionTalk']
    panel = read_csv('manifests/emotiontalk/source_measurements.csv')
    elig = read_csv('experiments/emotiontalk_reliability_v1/ELIGIBILITY_AND_SAMPLING_V1.csv')
    res = {}

    # ---- E1 source-label topology and readability coverage
    topo = panel.assign(AV='conflict'); topo['AV'] = np.where(panel.y_A == panel.y_V, 'consistent', 'conflict')
    topo['AT'] = np.where(panel.y_A == panel.y_T, 'consistent', 'conflict'); topo['VT'] = np.where(panel.y_V == panel.y_T, 'consistent', 'conflict')
    rows = []
    for pat, g in topo.groupby('trimodal_pattern'):
        r = dict(trimodal_pattern=pat, n_panel=len(g), AV=g.AV.iloc[0], AT=g.AT.iloc[0], VT=g.VT.iloc[0])
        for k in ['Readable_T', 'Readable_A', 'Readable_V', 'DualReadable_AT', 'DualReadable_AV', 'DualReadable_VT', 'TripleReadable']:
            r[k] = int(g[k].sum())
        r['DualReadable_AV_coverage'] = r['DualReadable_AV'] / len(g)
        rows.append(r)
    write(pd.DataFrame(rows), 'ET_E1_topology_readability.csv', SUB)

    # coverage funnel by pair-relation
    fun = []
    for pair, (a, b) in {'AT': ('A', 'T'), 'AV': ('A', 'V'), 'VT': ('V', 'T')}.items():
        for rel in ['conflict', 'consistent']:
            m = (topo[pair] == rel); d = panel['DualReadable_' + pair]
            fun.append(dict(pair=pair, relation=rel, panel_n=int(m.sum()), dual_readable_n=int((m & d).sum()), coverage=float((m & d).sum() / m.sum())))
    # exact AV-consistent DualReadable counts + eligibility flags
    avc = elig[(elig.av_source_relation == 'CONSISTENT') & (elig.DualReadable_AV)]
    res['AV_consistent_DualReadable_n'] = len(avc)
    res['AV_consistent_DualReadable_silent_video_PASS'] = int((avc.silent_video_validation == 'PASS').sum())
    res['AV_consistent_DualReadable_tech_complete'] = int((avc.technical_complete_A & avc.technical_complete_V).sum())
    res['AV_consistent_DualReadable_by_pattern'] = avc.trimodal_pattern.value_counts().to_dict()
    res['AV_consistent_DualReadable_by_shared_label'] = avc.y_A.value_counts().to_dict()
    res['AV_consistent_DualReadable_n_dialogue_clusters'] = int(avc.utterance_id.str[:9].nunique())
    res['AV_consistent_DualReadable_with_historical_phase2_arms'] = int((avc.historical_phase2_AV_arm_count > 0).sum())
    cv = elig[(elig.av_source_relation == 'CONFLICT') & (elig.DualReadable_AV)]
    res['AV_conflict_DualReadable_n'] = len(cv); res['AV_conflict_eligible_ERI1'] = int(elig.eligible.sum())
    res['AV_conflict_DualReadable_by_pattern'] = cv.trimodal_pattern.value_counts().to_dict()
    write(pd.DataFrame(fun), 'ET_E1_dualreadable_coverage_by_pair_relation.csv', SUB)

    # ---- E6 Phase2 pair outcome by third-modality topology (non-input modality label relation)
    p2 = et[et.regime.str.startswith('ET_') & (et.stratum == 'CONFLICT')].copy()
    p2['third_rel'] = np.where(p2.y_third == p2.y1, 'THIRD=MOD1', np.where(p2.y_third == p2.y2, 'THIRD=MOD2', 'THIRD=NEITHER'))
    rows = []
    for (pair, rel), g in p2.groupby(['pair', 'third_rel']):
        r = dict(pair=pair, third_modality=g.third_mod.iloc[0], third_label_relation=rel, **shares(g))
        r['SIDE_1_share_boot'] = item_boot_share(g, 'SIDE_1', 1000, SEED)[1:3]
        rows.append(r)
    t = pd.DataFrame(rows); t[['SIDE_1_boot_lo', 'SIDE_1_boot_hi']] = pd.DataFrame(t.SIDE_1_share_boot.tolist(), index=t.index); t = t.drop(columns='SIDE_1_share_boot')
    write(t, 'ET_E6_phase2_conflict_by_third_modality_topology.csv', SUB)
    # per pair x order
    rows = [dict(pair=pr, order=o, **shares(g)) for (pr, o), g in p2.groupby(['pair', 'order'])]
    write(pd.DataFrame(rows), 'ET_E6_phase2_conflict_outcome_by_pair_order.csv', SUB)

    # ---- OTHER label identity: does OTHER output the label of the NOT-INPUT modality?
    rows = []
    for name, d in [('PHASE2_CONFLICT', p2), ('ERI1_ALL_CONDITIONS', et[et.regime.str.startswith('ERI1_')]), ('ERI1_CLEAN+RECODE', et[et.regime.isin(['ERI1_AV_CLEAN', 'ERI1_AV_RECODE'])]),
                    ('ERI1_SNR00', et[et.regime == 'ERI1_AV_SNR00'])]:
        o = d[(d.outcome == 'OTHER') & d.out_label.notna()]
        inf = o[~((o.y_third == o.y1) | (o.y_third == o.y2))]
        k = int((inf.out_label == inf.y_third).sum()); n = len(inf)
        # exact binomial against chance 1/5 (labels outside the two input labels in a 7-label space)
        rows.append(dict(population=name, n_OTHER=len(o), n_informative_third_label_distinct=n, n_output_equals_noninput_modality_label=k,
                         observed_rate=k / n if n else np.nan, wilson_lo=wilson(k, n)[0], wilson_hi=wilson(k, n)[1], chance_rate_uniform_over_5_remaining=0.2,
                         note='informative = third-modality label differs from both input-side labels; chance is a uniform-guess reference, not a fitted null'))
    write(pd.DataFrame(rows), 'ET_E_OTHER_identity_vs_noninput_label.csv', SUB)

    # ---- ERI1 146-item topology and full trajectory
    er = et[et.regime.str.startswith('ERI1_')].copy()
    er['condition'] = er.regime.str.replace('ERI1_AV_', '')
    er = er.merge(elig[['utterance_id', 'trimodal_pattern']].rename(columns={'utterance_id': 'item_id', 'trimodal_pattern': 'topo'}), on='item_id')
    rows = []
    for (topo_, cond, order), g in er.groupby(['topo', 'condition', 'order']):
        rows.append(dict(topology=topo_, condition=cond, order=order, **shares(g)))
    for (cond, order), g in er.groupby(['condition', 'order']):
        rows.append(dict(topology='ALL_146', condition=cond, order=order, **shares(g)))
    traj = pd.DataFrame(rows)
    write(traj, 'ET_E2_ERI1_topology_by_condition_order.csv', SUB)
    # order-averaged item-level SIDE_A by topology & condition with cluster bootstrap; and SNR00-RECODE per topology (descriptive, ALL topologies shown)
    items = er.assign(sa=(er.outcome == 'SIDE_1').astype(float), sv=(er.outcome == 'SIDE_2').astype(float), ot=(er.outcome == 'OTHER').astype(float)) \
        .groupby(['item_id', 'cluster_id', 'topo', 'condition'], as_index=False)[['sa', 'sv', 'ot']].mean()
    wide = items.pivot_table(index=['item_id', 'cluster_id', 'topo'], columns='condition', values=['sa', 'sv', 'ot']).reset_index()
    wide.columns = ['_'.join(c).strip('_') for c in wide.columns]
    rows = []
    for name, g in [('ALL_146', wide)] + [(t_, wide[wide.topo == t_]) for t_ in sorted(wide.topo.unique())]:
        for out in ['sa', 'sv', 'ot']:
            for a_, b_ in [('SNR00', 'RECODE'), ('SNR10', 'RECODE'), ('SNR20', 'RECODE'), ('RECODE', 'CLEAN')]:
                d = (g[f'{out}_{a_}'] - g[f'{out}_{b_}']).values
                pt, lo, hi, nb = cluster_boot(g.cluster_id.values, lambda i: d[i].mean(), 2000, SEED + 7)
                rows.append(dict(topology=name, n_items=len(g), outcome=out, contrast=f'{a_}-{b_}', mean_diff=pt, ci_lo=lo, ci_hi=hi,
                                 status='POST_HOC_DESCRIPTIVE_ALL_SUBGROUPS_SHOWN_NO_SELECTION'))
    write(pd.DataFrame(rows), 'ET_E2_ERI1_contrasts_by_topology.csv', SUB)

    # full trajectory incl. A_ONLY unimodal readability/entropy per condition
    pr = read_csv('results/eri1_scientific_closure_v1/ERI1_SCIENTIFIC_TRIAL_PROJECTION_V1.csv')
    ao = pr[pr.order_or_arm == 'A_ONLY']
    rows = []
    for c in ['CLEAN', 'RECODE', 'SNR20', 'SNR10', 'SNR00']:
        a = ao[ao.condition == c]; j = pr[(pr.condition == c) & pr.order_or_arm.isin(['A_THEN_V', 'V_THEN_A'])]
        rows.append(dict(condition=c, n_items_A_ONLY=len(a), A_ONLY_correct_source_label_rate=(a.outcome_class == 'CORRECT_SOURCE_LABEL').mean(),
                         A_ONLY_other_label_rate=(a.outcome_class == 'OTHER_LABEL').mean(), A_ONLY_mean_norm_entropy=a.normalized_entropy_unimodal.mean(),
                         joint_SIDE_A=(j.outcome_class == 'SIDE_A').mean(), joint_SIDE_V=(j.outcome_class == 'SIDE_V').mean(), joint_OTHER=(j.outcome_class == 'OTHER').mean(),
                         joint_PARSE_FAIL=(j.outcome_class == 'PARSE_FAIL').mean(), joint_mean_norm_entropy=j.normalized_entropy_joint.mean(), joint_mean_p_audio_label=j.joint_p_audio_label.mean(), n_joint_trials=len(j)))
    write(pd.DataFrame(rows), 'ET_E3_ERI1_full_trajectory.csv', SUB)

    # per-item monotone trajectory (order-averaged SIDE_A across RECODE>SNR20>SNR10>SNR00)
    w = wide[['item_id', 'sa_RECODE', 'sa_SNR20', 'sa_SNR10', 'sa_SNR00']].dropna()
    arr = w[['sa_RECODE', 'sa_SNR20', 'sa_SNR10', 'sa_SNR00']].values
    d = np.diff(arr, axis=1)
    res['ERI1_item_trajectory'] = dict(n=len(w), monotone_nonincreasing=int((d <= 1e-12).all(1).sum()), strictly_any_decrease_overall=int((arr[:, -1] < arr[:, 0]).sum()),
                                       increase_overall=int((arr[:, -1] > arr[:, 0]).sum()), unchanged_overall=int((arr[:, -1] == arr[:, 0]).sum()))

    # ---- E4 unimodal entropy and joint output: item-level within-item associations
    aon = ao.pivot_table(index='item_id', columns='condition', values='normalized_entropy_unimodal')
    sa_ = wide.set_index('item_id')
    rows = []
    cl = wide.set_index('item_id').cluster_id
    for a_, b_ in [('SNR00', 'RECODE'), ('SNR10', 'RECODE'), ('SNR20', 'RECODE')]:
        dH = (aon[a_] - aon[b_]); dS = (sa_['sa_' + a_] - sa_['sa_' + b_]).reindex(dH.index); dPa = None
        ok = dH.notna() & dS.notna(); x = dH[ok].values; y = dS[ok].values; c = cl.reindex(dH.index)[ok].values
        def spearman(i):
            return pd.Series(x[i]).rank().corr(pd.Series(y[i]).rank())
        pt, lo, hi, nb = cluster_boot(c, spearman, 2000, SEED + 11)
        rows.append(dict(contrast=f'{a_}-{b_}', n_items=int(ok.sum()), within_item_spearman_dEntropyA_vs_dSIDE_A=pt, ci_lo=lo, ci_hi=hi,
                         mean_dEntropyA=x.mean(), frac_items_entropy_up=(x > 0).mean(), frac_items_SIDE_A_down=(y < 0).mean(),
                         note='ASSOCIATION of within-item changes; noise acts through multiple paths so mediation is NOT identified'))
    # baseline (cross-sectional): lower-entropy rule on clean/RECODE rows
    base = et[et.regime.isin(['ERI1_AV_RECODE'])]
    base = base[base.outcome.isin(['SIDE_1', 'SIDE_2'])]
    y = (base.outcome == 'SIDE_1').values.astype(float); sc = (base.H2 - base.H1).values
    pt, lo, hi, nb = cluster_boot(base.cluster_id.values, lambda i: auroc(y[i], sc[i]), 2000, SEED + 13)
    rows.append(dict(contrast='CROSS_SECTIONAL_RECODE_unfitted_lower_entropy_rule_AUROC(SIDE_A vs SIDE_V; clean-audio Phase1 entropy)', n_items=base.item_id.nunique(), within_item_spearman_dEntropyA_vs_dSIDE_A=pt, ci_lo=lo, ci_hi=hi,
                     note='unfitted sign-fixed score H_V-H_A; binary-resolved trials only'))
    write(pd.DataFrame(rows), 'ET_E4_entropy_vs_joint_output.csv', SUB)

    # ---- CLEAN (ERI1) vs historical Phase2 AV conflict replication
    h = et[et.regime == 'ET_AV_conflict'].set_index(['item_id', 'order'])['outcome']
    c_ = et[et.regime == 'ERI1_AV_CLEAN'].set_index(['item_id', 'order'])['outcome']
    j = pd.concat([h, c_], axis=1, keys=['phase2', 'eri1_clean']).dropna()
    res['ERI1_CLEAN_vs_Phase2_AV_conflict'] = dict(n_trials=len(j), identical_outcome=int((j.phase2 == j.eri1_clean).sum()))
    # source-label group sizes
    res['ERI1_topology_counts_146'] = elig[elig.eligible].trimodal_pattern.value_counts().to_dict()
    res['ERI1_distinct_dialogue_clusters'] = int(er.cluster_id.nunique())
    import json
    (INTER / 'ET_within_summary.json').write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
    save_registry('a02_et')
    return res


def extras():
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    et = L[L.dataset == 'EmotionTalk']
    rng = np.random.default_rng(SEED + 21)
    # permutation null for OTHER-identity: shuffle the non-input-modality label across informative OTHER trials
    rows = []
    p2 = et[et.regime.str.startswith('ET_') & (et.stratum == 'CONFLICT')]
    for name, d in [('PHASE2_CONFLICT', p2), ('ERI1_ALL_CONDITIONS', et[et.regime.str.startswith('ERI1_')])]:
        o = d[(d.outcome == 'OTHER') & d.out_label.notna()]
        inf = o[~((o.y_third == o.y1) | (o.y_third == o.y2))].reset_index(drop=True)
        obs = int((inf.out_label == inf.y_third).sum()); n = len(inf)
        pool = inf.y_third.astype(object).to_numpy(); perm = []
        for _ in range(10000):
            sh = pool.copy(); rng.shuffle(sh)
            ok = (sh != inf.y1.astype(object).to_numpy()) & (sh != inf.y2.astype(object).to_numpy())
            perm.append(((inf.out_label.astype(object).to_numpy() == sh) & ok).sum() / max(ok.sum(), 1) * n)
        perm = np.array(perm)
        rows.append(dict(population=name, n_informative=n, observed_matches=obs, perm_null_mean_matches=perm.mean(), perm_p_one_sided=float((np.sum(perm >= obs) + 1) / (len(perm) + 1)),
                         n_item_clusters=int(inf.cluster_id.nunique()), note='EXPLORATORY; trial-level permutation; repeated trials of one item are not independent so p is anti-conservative'))
    write(pd.DataFrame(rows), 'ET_E_OTHER_identity_permutation.csv', SUB)
    rows = []
    for name, d in [('ALL_THREE_PAIRS', p2)] + [(pr, p2[p2.pair == pr]) for pr in ['AT', 'AV', 'VT']]:
        d = d[d.outcome.isin(['SIDE_1', 'SIDE_2'])]
        dd = d[(d.y_third == d.y1) | (d.y_third == d.y2)].copy()
        dd['chose_supported'] = np.where(dd.y_third == dd.y1, dd.outcome == 'SIDE_1', dd.outcome == 'SIDE_2').astype(float)
        v = dd.chose_supported.values
        pt, lo, hi, nb = cluster_boot(dd.cluster_id.values, lambda i: v[i].mean(), 2000, SEED + 31)
        rows.append(dict(pair=name, n_trials=len(dd), n_items=dd.item_id.nunique(), P_choose_side_supported_by_noninput_modality_label=pt, ci_lo=lo, ci_hi=hi,
                         note='binary-resolved conflict trials where non-input modality label equals exactly one side; reference 0.5; ASSOCIATION (item content confounds)'))
    write(pd.DataFrame(rows), 'ET_E7_noninput_label_support_effect.csv', SUB)
    save_registry('a02_et_extras')


if __name__ == '__main__':
    r = run(); print(r); extras()
