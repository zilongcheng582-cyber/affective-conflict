"""Within-dataset structural analysis: LISTEN 3A (text), 3B (audio), 3C (audio->text). Reuses R3 matching logic only for identity checks; no R3 table is re-derived."""
import json
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1.common import *

SUB = 'tables'
# Post-hoc, author-defined crude mapping of LISTEN labels to the 7-label B3 space (used ONLY for the B3 unimodal alignment check)
A2B3 = {'anger': 'angry', 'disgust': 'disgusted', 'sadness': 'sad'}                      # audio-side labels with a counterpart
T2B3 = {'neutral': 'neutral', 'happiness': 'happy', 'surprise': 'surprised', 'sadness': 'sad', 'anger': 'angry', 'fear': 'fearful'}


def sh(d):
    n = len(d); r = {'n': n}
    for c in ['SIDE_1', 'SIDE_2', 'OTHER', 'SHARED']:
        r[c] = int((d.outcome == c).sum()); r[c + '_share'] = r[c] / n if n else np.nan
    return r


def run():
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    l = L[L.dataset == 'LISTEN'].copy(); l['cond'] = l.regime.str[-2:]; l['base'] = l.item_id.str.rsplit('_u_', n=1).str[0]
    res = {}
    # ---- L1 identity / comparability of the 3 conditions
    ids = {c: set(l[l.cond == c].base) for c in ['3A', '3B', '3C']}
    res['items_per_condition'] = {c: len(v) for c, v in ids.items()}
    res['rows_per_condition'] = l.cond.value_counts().to_dict()
    res['base_overlap'] = dict(A_and_B=len(ids['3A'] & ids['3B']), A_and_C=len(ids['3A'] & ids['3C']), B_and_C=len(ids['3B'] & ids['3C']), all_three=len(ids['3A'] & ids['3B'] & ids['3C']), union=len(ids['3A'] | ids['3B'] | ids['3C']))
    res['same_item_id_B_C'] = len(set(l[l.cond == '3B'].item_id) & set(l[l.cond == '3C'].item_id))
    # label identity within base: audio/text labels equal across conditions?
    g = l.groupby(['base', 'cond'])[['y1', 'y2']].first().unstack('cond')
    for a, b in [('3A', '3B'), ('3B', '3C'), ('3A', '3C')]:
        ok = g.dropna(subset=[('y1', a), ('y1', b)])
        res[f'label_identity_{a}_{b}'] = dict(n=len(ok), same_audio_label=int((ok[('y1', a)] == ok[('y1', b)]).sum()), same_text_label=int((ok[('y2', a)] == ok[('y2', b)]).sum()))
    # distribution comparability: audio label composition of the three populations
    rows = []
    for c in ['3A', '3B', '3C']:
        d = l[(l.cond == c) & (l.stratum == 'CONFLICT')]
        for var, nm in [('y1', 'audio_label'), ('y2', 'text_label')]:
            for lab, k in d[var].value_counts().items(): rows.append(dict(condition=c, variable=nm, label=lab, n=int(k), share=k / len(d)))
    write(pd.DataFrame(rows), 'LISTEN_L1_label_composition_by_condition.csv', SUB)
    # ---- L2 OTHER vs source-label type and ontology
    rows = []
    cf = l[l.stratum == 'CONFLICT']
    for var, nm in [('y1', 'audio_label'), ('y2', 'text_label')]:
        for (lab, c), d in cf.groupby([var, 'cond']):
            r = dict(variable=nm, label=lab, condition=c, **sh(d)); r['OTHER_wilson_lo'], r['OTHER_wilson_hi'] = wilson(r['OTHER'], r['n'])
            cp = (A2B3 if nm == 'audio_label' else T2B3).get(lab); r['B3_7label_counterpart'] = cp if cp else 'NONE'
            rows.append(r)
    write(pd.DataFrame(rows), 'LISTEN_L2_outcome_by_source_label_and_condition.csv', SUB)
    # B3 unimodal alignment vs LISTEN-native condition behaviour
    rows = []
    d3b = cf[cf.cond == '3B']; d3a = cf[cf.cond == '3A']
    for lab, cp in A2B3.items():
        d = cf[(cf.cond == '3B') & (cf.y1 == lab)]; k = (d.top1_1 == cp).sum()
        rows.append(dict(modality='AUDIO', source_label=lab, counterpart_7label=cp, n_3B=len(d), B3_unimodal_top1_equals_counterpart=k / len(d) if len(d) else np.nan, LISTEN_3B_SIDE_A_rate=(d.outcome == 'SIDE_1').mean(), LISTEN_3B_OTHER_rate=(d.outcome == 'OTHER').mean()))
    d = cf[(cf.cond == '3B') & (cf.y1 == 'ridicule')]; rows.append(dict(modality='AUDIO', source_label='ridicule', counterpart_7label='NONE', n_3B=len(d), B3_unimodal_top1_equals_counterpart=np.nan, LISTEN_3B_SIDE_A_rate=(d.outcome == 'SIDE_1').mean(), LISTEN_3B_OTHER_rate=(d.outcome == 'OTHER').mean()))
    d = cf[(cf.cond == '3B') & (cf.y1 == 'frustration')]; rows.append(dict(modality='AUDIO', source_label='frustration', counterpart_7label='NONE', n_3B=len(d), B3_unimodal_top1_equals_counterpart=np.nan, LISTEN_3B_SIDE_A_rate=(d.outcome == 'SIDE_1').mean(), LISTEN_3B_OTHER_rate=(d.outcome == 'OTHER').mean()))
    for lab, cp in T2B3.items():
        d = cf[(cf.cond == '3A') & (cf.y2 == lab)]
        if len(d): rows.append(dict(modality='TEXT', source_label=lab, counterpart_7label=cp, n_3B=len(d), B3_unimodal_top1_equals_counterpart=(d.top1_2 == cp).mean(), LISTEN_3B_SIDE_A_rate=(d.outcome == 'SIDE_2').mean(), LISTEN_3B_OTHER_rate=(d.outcome == 'OTHER').mean()))
    t = pd.DataFrame(rows).rename(columns={'n_3B': 'n_rows_in_native_unimodal_condition', 'LISTEN_3B_SIDE_A_rate': 'LISTEN_native_label_match_rate(3B:audio label / 3A:text label)', 'LISTEN_3B_OTHER_rate': 'LISTEN_native_OTHER_rate'})
    write(t, 'LISTEN_L2b_B3_unimodal_alignment_vs_native_label_match.csv', SUB)
    top = cf[cf.cond == '3B'].groupby('y1').top1_1.value_counts(normalize=True).rename('share').reset_index().rename(columns={'y1': 'LISTEN_audio_label', 'top1_1': 'B3_audio_top1_7label'})
    top['n_label'] = top.LISTEN_audio_label.map(cf[cf.cond == '3B'].y1.value_counts())
    write(top, 'LISTEN_L2c_B3_audio_top1_distribution_by_listen_audio_label.csv', SUB)
    # ---- L3 selection in the conditional binary 3C estimand
    c3 = cf[cf.cond == '3C']; bi = c3[c3.outcome.isin(['SIDE_1', 'SIDE_2'])]
    rows = []
    for var, nm in [('y1', 'audio_label'), ('y2', 'text_label')]:
        full = c3[var].value_counts(normalize=True); sub = bi[var].value_counts(normalize=True)
        for lab in full.index: rows.append(dict(variable=nm, label=lab, share_in_all_3C_conflicts=full[lab], share_in_binary_resolvable=sub.get(lab, 0.0), ratio=sub.get(lab, 0.0) / full[lab], n_all=int((c3[var] == lab).sum()), n_binary=int((bi[var] == lab).sum())))
    write(pd.DataFrame(rows), 'LISTEN_L3_binary_subset_composition_3C.csv', SUB)
    n = len(c3); kA = int((c3.outcome == 'SIDE_1').sum()); kT = int((c3.outcome == 'SIDE_2').sum()); kO = n - kA - kT
    # post-stratified A-share: reweight binary subset to full 3C audio-label composition (assumes label-specific MAR; sensitivity only)
    wl = c3.y1.value_counts(normalize=True)
    byl = bi.groupby('y1').apply(lambda d: (d.outcome == 'SIDE_1').mean(), include_groups=False)
    ps = float(sum(wl[k] * byl[k] for k in wl.index if k in byl.index) / sum(wl[k] for k in wl.index if k in byl.index))
    pt, lo, hi, _ = cluster_boot(bi.cluster_id.values, lambda i: (bi.outcome.values[i] == 'SIDE_1').mean(), 2000, SEED + 41)
    res['L3_3C'] = dict(n_conflict=n, SIDE_A=kA, SIDE_T=kT, OTHER=kO, binary_share_A=kA / (kA + kT), binary_share_A_ci=[lo, hi], poststrat_audio_label_share_A=ps,
                        manski_bounds_A_share_all_conflicts=[kA / n, (kA + kO) / n], manski_bounds_T_share_all_conflicts=[kT / n, (kT + kO) / n],
                        labels_with_zero_binary_rows=[k for k in wl.index if k not in byl.index])
    # selection model: how well do audio label + text label predict being binary-resolvable (item-level; in-sample deviance, descriptive)
    c3 = c3.assign(binary=c3.outcome.isin(['SIDE_1', 'SIDE_2']).astype(float))
    lab_rate = c3.groupby('y1').binary.transform('mean')
    res['L3_binary_resolvable_AUROC_from_audio_label_alone(in-sample,descriptive)'] = auroc(c3.binary, lab_rate)
    # ---- L4: persistence of OTHER across conditions at the item level (identity check on already-reported finding R3: reported only as count)
    w = cf.pivot_table(index='base', columns='cond', values='outcome', aggfunc='first')
    w3 = w.dropna()
    res['L4_triple_matched_items'] = len(w3)
    res['L4_OTHER_all_three'] = int((w3 == 'OTHER').all(axis=1).sum())
    # option-order / choice-list: NOT recoverable
    res['OTHER_label_identity'] = 'NOT_AVAILABLE: raw LISTEN generations and randomized choice lists are not in the repository'
    res['order_identifiability'] = '3C has presentation_order A_THEN_T only (n=%d); A/T order effect NOT_IDENTIFIABLE' % int((l[l.cond == '3C'].order == 'A_THEN_T').sum())
    (INTER / 'LISTEN_within_summary.json').write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
    save_registry('a02_listen')
    return res


if __name__ == '__main__':
    print(json.dumps(run(), indent=1, default=str)[:3500])
