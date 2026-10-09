"""Within-dataset structural analysis: CA-MER (audio-aligned / video-aligned / consistent controls; 16-label source-local ontology)."""
import json
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1.common import *

SUB = 'tables'
SEVEN = {'angry', 'disgusted', 'fearful', 'happy', 'neutral', 'sad', 'surprised'}


def sh(d, cats=('SIDE_1', 'SIDE_2', 'SHARED', 'OTHER', 'TECH_MISSING')):
    n = len(d); r = {'n_planned': n, 'n_items': d.item_id.nunique()}
    for c in cats:
        r[c] = int((d.outcome == c).sum()); r[c + '_share'] = r[c] / n if n else np.nan
        r[c + '_lo'], r[c + '_hi'] = wilson(r[c], n)
    return r


def run():
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    c = L[L.dataset == 'CA-MER'].copy(); res = {}
    meta = pd.DataFrame([json.loads(l) for l in open(used('manifests/camer/controlled.jsonl'))])
    res['construction_item_counts'] = meta.subset.value_counts().to_dict()
    res['multimodal_ground_truth_available'] = 'NO: final_label deliberately excluded from controlled manifest; y_A/y_V are single-modality pseudo labels'
    res['planned_arms_in_manifest'] = meta.planned_arms.astype(str).unique().tolist()
    res['executed_joint_arms'] = sorted(c.order.unique().tolist()); res['unimodal_A_ONLY_V_ONLY_arm_outputs'] = 'NOT_IN_REPOSITORY (controlled A_ONLY/V_ONLY NOT_RUN per manifest dual_readable_status); B3 unimodal 7-label measurements exist'
    # ---- C1 complete outcomes per construction and order
    rows = []
    for (sub, o), d in c.groupby(['camer_subset', 'order']): rows.append(dict(construction=sub, order=o, **sh(d)))
    for sub, d in c.groupby('camer_subset'): rows.append(dict(construction=sub, order='BOTH', **sh(d)))
    t = pd.DataFrame(rows); write(t, 'CAMER_C1_outcomes_by_construction_order.csv', SUB)
    # item-clustered two-sided heterogeneity: audio-aligned vs video-aligned SIDE_A share among binary-resolved (pooled orders), item bootstrap
    rows = []
    for sub in ['audio-aligned', 'video-aligned']:
        d = c[(c.camer_subset == sub) & c.outcome.isin(['SIDE_1', 'SIDE_2'])]; y = (d.outcome == 'SIDE_1').values.astype(float)
        pt, lo, hi, _ = cluster_boot(d.item_id.values, lambda i: y[i].mean(), 2000, SEED + 51)
        rows.append(dict(construction=sub, n_binary_trials=len(d), n_items=d.item_id.nunique(), P_SIDE_AUDIO_given_binary=pt, ci_lo=lo, ci_hi=hi))
        dd = c[c.camer_subset == sub]; yy = dd.outcome.isin(['SIDE_1', 'SIDE_2']).values.astype(float)
        pt2, lo2, hi2, _ = cluster_boot(dd.item_id.values, lambda i: yy[i].mean(), 2000, SEED + 52)
        rows[-1].update(binary_coverage=pt2, coverage_lo=lo2, coverage_hi=hi2)
    write(pd.DataFrame(rows), 'CAMER_C3_binary_choice_by_construction.csv', SUB)
    # ---- C2 paired order transitions (complete cases)
    w = c[c.stratum == 'CONFLICT'].pivot_table(index=['item_id', 'camer_subset'], columns='order', values='outcome', aggfunc='first').reset_index()
    rows = []
    for sub, g in w.groupby('camer_subset'):
        g2 = g.dropna(subset=['A_THEN_V', 'V_THEN_A'])
        tab = pd.crosstab(g2.A_THEN_V, g2.V_THEN_A).stack().reset_index(); tab.columns = ['A_THEN_V_outcome', 'V_THEN_A_outcome', 'n_items']; tab.insert(0, 'construction', sub); tab['n_complete_items'] = len(g2)
        rows.append(tab)
    write(pd.concat(rows), 'CAMER_C2_order_transition_matrix.csv', SUB)
    rows = []
    for sub, g in w.groupby('camer_subset'):
        g2 = g.dropna(subset=['A_THEN_V', 'V_THEN_A']); n = len(g2)
        a = (g2.A_THEN_V == 'SIDE_1').values; b = (g2.V_THEN_A == 'SIDE_1').values
        same = (g2.A_THEN_V == g2.V_THEN_A).mean()
        rows.append(dict(construction=sub, n_complete=n, SIDE_AUDIO_when_audio_first=a.mean(), SIDE_AUDIO_when_video_first=b.mean(),
                         audio_choice_only_when_audio_first_primacy=int((a & ~b).sum()), audio_choice_only_when_video_first_recency=int((~a & b).sum()), identical_outcome_both_orders=same,
                         mcnemar_exact_b_c=f'{int((a & ~b).sum())}/{int((~a & b).sum())}'))
    write(pd.DataFrame(rows), 'CAMER_C2b_order_effect_summary.csv', SUB)
    # ---- C4 consistent controls: common-label retention
    k = c[c.camer_subset == 'consistent']
    avail = k[k.outcome != 'TECH_MISSING']
    retain = (avail.outcome == 'SHARED').mean()
    lab = k[k.outcome != 'TECH_MISSING'].assign(retained=lambda d: (d.outcome == 'SHARED').astype(float)).groupby('y1').retained.agg(['mean', 'size']).reset_index().rename(columns={'y1': 'shared_label', 'mean': 'retention_rate', 'size': 'n_trials'})
    write(lab, 'CAMER_C4_consistent_label_retention_by_label.csv', SUB)
    res['consistent'] = dict(n_planned=len(k), n_available=len(avail), retention=retain, retention_wilson=wilson(int((avail.outcome == 'SHARED').sum()), len(avail)),
                             B3_both_unimodal_top1_equal_shared_label_retention=float(avail[(avail.read1 & avail.read2)].outcome.eq('SHARED').mean()) if (avail.read1 & avail.read2).any() else None,
                             n_B3_both_readable=int((avail.read1 & avail.read2).sum()))
    # ---- C5 OTHER and ontology coverage (16 labels)
    cf = c[c.stratum == 'CONFLICT']; av = cf[cf.outcome != 'TECH_MISSING']
    o = av[av.outcome == 'OTHER']
    rows = []
    for lab, kk in o.out_label.value_counts().items(): rows.append(dict(output_label=lab, n_OTHER=int(kk), share_of_OTHER=kk / len(o), in_B3_7label_space=lab in SEVEN))
    write(pd.DataFrame(rows), 'CAMER_C5_OTHER_label_identity.csv', SUB)
    outs = av.out_label.value_counts(); res['OTHER'] = dict(n=len(o), share_of_available=len(o) / len(av), n_distinct_labels=int(o.out_label.nunique()),
                                                                 other_equals_label_of_other_construction_side_not_applicable=True)
    # label coverage: which of 16 candidate labels are ever output / ever appear as a source side
    cands = json.loads(json.dumps(meta.candidate_labels.iloc[0]))
    srcs = set(cf.y1) | set(cf.y2)
    res['label_space'] = dict(n_candidates=len(cands), n_source_labels_used=len(srcs), candidates_never_a_source_label=sorted(set(cands) - srcs), candidates_output_at_least_once=sorted(set(av.out_label.dropna())),
                              source_labels_outside_B3_7=sorted(srcs - SEVEN))
    # labels outside the 7-label B3 space on the source side (B3 unimodal reading cannot represent them)
    for side in ['y1', 'y2']:
        res[f'{side}_share_outside_B3_7'] = float((~cf[side].isin(SEVEN)).mean())
    # ---- C6 unimodal evidence features vs choice by construction
    rows = []
    for sub, d in cf.groupby('camer_subset'):
        d = d[d.outcome.isin(['SIDE_1', 'SIDE_2'])]
        y = (d.outcome == 'SIDE_1').values.astype(float); s = (d.H2 - d.H1).values
        pt, lo, hi, _ = cluster_boot(d.item_id.values, lambda i: auroc(y[i], s[i]), 2000, SEED + 61)
        # concordance of the unfitted lower-entropy rule
        conc = ((s > 0) == (y == 1))[s != 0].mean()
        rows.append(dict(construction=sub, n_binary=len(d), AUROC_unfitted_lowerentropy_rule=pt, ci_lo=lo, ci_hi=hi, concordance=conc, binary_coverage=len(d) / len(cf[cf.camer_subset == sub])))
        # order-adjusted: within-order AUROC
        for o_ in ['A_THEN_V', 'V_THEN_A']:
            dd = d[d.order == o_]; yy = (dd.outcome == 'SIDE_1').values.astype(float)
            rows.append(dict(construction=sub + f'|{o_}', n_binary=len(dd), AUROC_unfitted_lowerentropy_rule=auroc(yy, (dd.H2 - dd.H1).values)))
    write(pd.DataFrame(rows), 'CAMER_C6_entropy_rule_by_construction.csv', SUB)
    (INTER / 'CAMER_within_summary.json').write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
    save_registry('a02_camer')
    return res


if __name__ == '__main__':
    print(json.dumps(run(), indent=1, default=str)[:3000])
