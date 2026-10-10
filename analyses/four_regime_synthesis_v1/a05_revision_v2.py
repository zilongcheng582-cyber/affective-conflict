"""REVISION V2 (post-hoc): ERI1 readability accounting, target-constant oracle audit, CA-MER subset confounding, CA-MER identity/leakage checks.
All CPU, read-only on frozen inputs. Any target-side fitting here (calibration, constants) is a post-hoc DIAGNOSTIC, never a transfer baseline."""
import hashlib
import json
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1.common import *

SUB = 'tables_v2'
SEVEN = {'angry', 'disgusted', 'fearful', 'happy', 'neutral', 'sad', 'surprised'}


def eri1_readability():
    d = read_csv('results/eri1_scientific_closure_v1/ERI1_SCIENTIFIC_TRIAL_PROJECTION_V1.csv')
    a = d[d.order_or_arm == 'A_ONLY'].copy()
    s = read_csv('manifests/emotiontalk/source_measurements.csv').set_index('utterance_id')
    rows = []
    for c in ['CLEAN', 'RECODE', 'SNR20', 'SNR10', 'SNR00']:
        x = a[a.condition == c]; k = int((x.outcome_class == 'CORRECT_SOURCE_LABEL').sum()); n = len(x)
        r = dict(condition=c, n_items=n, n_correct_source_label=k, rate=k / n, wilson_lo=wilson(k, n)[0], wilson_hi=wilson(k, n)[1],
                 n_OTHER_LABEL=int((x.outcome_class == 'OTHER_LABEL').sum()), n_PARSE_FAIL=int((x.outcome_class == 'PARSE_FAIL').sum()),
                 n_not_correct=n - k, rate_not_correct=(n - k) / n)
        if c == 'CLEAN':
            r['n_equal_to_Phase1_pred_A'] = int((x.set_index('item_id').parsed_emotion_label == s.loc[x.item_id, 'pred_A'].values).sum())
        rows.append(r)
    t = pd.DataFrame(rows)
    cl = a[a.condition == 'CLEAN'].set_index('item_id'); rc = a[a.condition == 'RECODE'].set_index('item_id')
    both = cl.join(rc, lsuffix='_c', rsuffix='_r')
    t.attrs['pair'] = dict(n=len(both), changed_label=int((both.parsed_emotion_label_c != both.parsed_emotion_label_r).sum()))
    write(t, 'V2_A1_ERI1_A_ONLY_readability_accounting.csv', SUB)
    return t


def ll_cv(y, s_logit, order, clusters, seed=SEED + 200, K=5):
    n = len(y); codes, uniq = pd.factorize(clusters); rng = np.random.default_rng(seed); fold_of = rng.integers(0, K, len(uniq))[codes]
    oof = {k: np.zeros(n) for k in ['const', 'order_const', 'shift', 'platt', 'platt_order']}
    for f in range(K):
        tr = fold_of != f; te = ~tr
        oof['const'][te] = y[tr].mean()
        for o in np.unique(order):
            m = tr & (order == o); oof['order_const'][te & (order == o)] = y[m].mean() if m.sum() else y[tr].mean()
        # shift: logit(p)+b
        b = 0.0
        for _ in range(60):
            p = 1 / (1 + np.exp(-(s_logit[tr] + b))); g = (p - y[tr]).sum(); h = (p * (1 - p)).sum() + 1e-9; b -= g / h
        oof['shift'][te] = 1 / (1 + np.exp(-(s_logit[te] + b)))
        w = logit_fit(s_logit[tr][:, None], y[tr], l2=1e-4); oof['platt'][te] = logit_pred(w, s_logit[te][:, None])
        Xo = np.column_stack([s_logit, (order == np.unique(order)[0]).astype(float)])
        w = logit_fit(Xo[tr], y[tr], l2=1e-4); oof['platt_order'][te] = logit_pred(w, Xo[te])
    return {k: np.clip(v, 1e-6, 1 - 1e-6) for k, v in oof.items()}


def oracle_audit():
    pr = read_csv('results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv')
    cit = read_csv('results/post_audit/closure_v1/ZERO_REFIT_BASELINE_COMPARISON_V1.csv')
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    Lt = L[L.target_record_id.notna()][['target_record_id', 'regime', 'outcome', 'order', 'cluster_id']]
    cfg = [('MCR_AT_PRIMARY', 'MCR_AT_PRIMARY', 'FROZEN_POOLED_M3a'), ('CAMER_AV_SUPPORT_LIMITED_SOURCEPROB', 'CAMER_AV_SUPPORT_LIMITED_SOURCEPROB', 'FROZEN_POOLED_M3a'),
           ('CAMER_AV_MARGIN_SENSITIVITY', 'CAMER_AV_MARGIN_SENSITIVITY', 'FROZEN_POOLED_M3b'), ('LISTEN_AT_MARGIN_SENSITIVITY', 'LISTEN_3C_JOINT_ARBITRATION', 'FROZEN_POOLED_M3b')]
    rows = []
    for role, crole, fm in cfg:
        p = pr[pr.analysis_role == role].merge(Lt, on='target_record_id')
        if role.startswith('LISTEN'): p = p[p.regime == 'LISTEN_3C']
        p = p[p.outcome.isin(['SIDE_1', 'SIDE_2'])].reset_index(drop=True)
        y = (p.outcome == 'SIDE_1').values.astype(float); sc = np.clip(p.predicted_p_SIDE_A.values, 1e-6, 1 - 1e-6); lg = np.log(sc / (1 - sc)); order = p.order.values
        oof = ll_cv(y, lg, order, p.cluster_id.values)
        ll = {k: np.array([-(yy * np.log(pp) + (1 - yy) * np.log(1 - pp)) for yy, pp in zip(y, v)]) for k, v in oof.items()}
        ll['frozen'] = -(y * np.log(sc) + (1 - y) * np.log(1 - sc))
        m0 = cit[(cit.model == 'M0') & (cit.analysis_role == crole)] if 'analysis_role' in cit else None
        r = dict(role=role, n=len(y), prevalence=y.mean(), LL_frozen=ll['frozen'].mean())
        # cited M0 (source-fixed) log loss
        r['LL_M0_cited'] = float(cit[(cit.model == 'M0')].iloc[0].log_loss) if False else np.nan
        for k in ['const', 'order_const', 'shift', 'platt', 'platt_order']: r['LL_oof_' + k] = ll[k].mean()
        def bs(a, b, seed):
            d = a - b; return cluster_boot(p.cluster_id.values, lambda i: d[i].mean(), 1000, seed)
        for nm, a, b in [('frozen_minus_oof_const', 'frozen', 'const'), ('platt_minus_oof_const', 'platt', 'const'), ('shift_minus_oof_const', 'shift', 'const'),
                         ('platt_order_minus_oof_order_const', 'platt_order', 'order_const'), ('frozen_minus_oof_shift', 'frozen', 'shift')]:
            pt, lo, hi, _ = bs(ll[a], ll[b], SEED + 211)
            r[nm], r[nm + '_lo'], r[nm + '_hi'] = pt, lo, hi
        rows.append(r)
    t = pd.DataFrame(rows)
    # cited M0 log losses (unchanged frozen table) for the decomposition
    c = cit[cit.model == 'M0'][['N_evaluated', 'log_loss']].reset_index(drop=True)
    m0map = {'MCR_AT_PRIMARY': 0.678, 'CAMER_AV_SUPPORT_LIMITED_SOURCEPROB': 0.717, 'CAMER_AV_MARGIN_SENSITIVITY': 0.714, 'LISTEN_AT_MARGIN_SENSITIVITY': 0.697}
    t['LL_M0_cited_rounded'] = t.role.map(m0map)
    t['gap_M0_to_oof_const'] = t.LL_M0_cited_rounded - t.LL_oof_const; t['gain_M0_to_frozen'] = t.LL_M0_cited_rounded - t.LL_frozen
    write(t, 'V2_A2_calibration_vs_evidence_decomposition.csv', SUB)
    return t


def strat_auc(d, keys):
    """pooled within-stratum Mann-Whitney concordance, weights = pos*neg pairs in each stratum."""
    num = den = 0.0
    for _, g in d.groupby(keys, sort=False):
        pos = g.s.values[g.y.values == 1]; neg = g.s.values[g.y.values == 0]
        if len(pos) and len(neg):
            diff = pos[:, None] - neg[None, :]; num += (diff > 0).sum() + 0.5 * (diff == 0).sum(); den += diff.size
    return (num / den if den else np.nan), den


def camer_confound():
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    c = L[(L.dataset == 'CA-MER') & (L.stratum == 'CONFLICT')].copy(); c['in7'] = c.y1.isin(SEVEN) & c.y2.isin(SEVEN)
    avail = c[c.outcome != 'TECH_MISSING']
    comp = []
    for nm, m in [('both_in_7label_space', avail.in7), ('not_both_in_7label_space', ~avail.in7)]:
        d = avail[m]; b = d[d.outcome.isin(['SIDE_1', 'SIDE_2'])]
        comp.append(dict(subset=nm, n_trials=len(d), n_samples=d.item_id.nunique(), binary_coverage=len(b) / len(d), n_binary=len(b), P_SIDE_AUDIO_given_binary=(b.outcome == 'SIDE_1').mean(),
                         frac_audio_aligned=(d.camer_subset == 'audio-aligned').mean(), mean_abs_entropy_diff=(d.H1 - d.H2).abs().mean(), mean_H_audio=d.H1.mean(), mean_H_video=d.H2.mean(),
                         B3_top1_matches_audio_label=(d.top1_1 == d.y1).mean(), B3_top1_matches_video_label=(d.top1_2 == d.y2).mean(), n_distinct_label_pairs=d.groupby(['y1', 'y2']).ngroups,
                         top_labels_audio=str(d.y1.value_counts(normalize=True).head(4).round(3).to_dict()), top_labels_video=str(d.y2.value_counts(normalize=True).head(4).round(3).to_dict())))
    write(pd.DataFrame(comp), 'V2_A3a_camer_subset_composition.csv', SUB)
    b = avail[avail.outcome.isin(['SIDE_1', 'SIDE_2'])].copy().reset_index(drop=True); b['y'] = (b.outcome == 'SIDE_1').astype(float); b['s'] = b.H2 - b.H1
    rows = []
    for sub in ['audio-aligned', 'video-aligned', 'ALL']:
        d0 = b if sub == 'ALL' else b[b.camer_subset == sub]
        for nm, m in [('both_in_7', d0.in7), ('not_both_in_7', ~d0.in7), ('both_B3_readable(top1==own label)', (d0.top1_1 == d0.y1) & (d0.top1_2 == d0.y2))]:
            d = d0[m]
            if d.y.nunique() < 2 or len(d) < 30: rows.append(dict(construction=sub, subset=nm, n_binary=len(d))); continue
            r = dict(construction=sub, subset=nm, n_binary=len(d), n_samples=d.item_id.nunique(), P_SIDE_AUDIO=d.y.mean(), AUROC_crude=auroc(d.y, d.s))
            r['AUROC_within_label_pair'], r['pos_neg_pairs_label_pair'] = strat_auc(d, ['y1', 'y2'])
            r['AUROC_within_label_pair_order_construction'], _ = strat_auc(d, ['y1', 'y2', 'order', 'camer_subset'])
            rows.append(r)
    write(pd.DataFrame(rows), 'V2_A3b_camer_subset_AUROC_confound_controls.csv', SUB)
    drows = []
    for sub in ['audio-aligned', 'video-aligned', 'ALL']:
        d = (b if sub == 'ALL' else b[b.camer_subset == sub]).reset_index(drop=True)
        def diff(i, adj):
            a = d.iloc[i]; m = a.in7.values
            x, z = a[m], a[~m]
            if x.y.nunique() < 2 or z.y.nunique() < 2: return np.nan
            return auroc(x.y, x.s) - auroc(z.y, z.s) if not adj else strat_auc(x, ['y1', 'y2'])[0] - strat_auc(z, ['y1', 'y2'])[0]
        for nm, adj in [('crude', False), ('label_pair_stratified', True)]:
            pt, lo, hi, nb = cluster_boot(d.item_id.values, lambda i: diff(i, adj), 200, SEED + 231)
            drows.append(dict(construction=sub, adjustment=nm, AUROC_in7_minus_not_in7=pt, lo=lo, hi=hi, defined_boot=nb))
    write(pd.DataFrame(drows), 'V2_A3c_camer_in7_minus_out_AUROC_difference.csv', SUB)
    labels = sorted(set(avail.y1) | set(avail.y2)); rng = np.random.default_rng(SEED + 241); nulls = []
    y = b.y.values; sc = b.s.values
    def delta(inset):
        m = (b.y1.isin(inset) & b.y2.isin(inset)).values
        if m.sum() < 150 or (~m).sum() < 150: return np.nan
        return auroc(y[m], sc[m]) - auroc(y[~m], sc[~m])
    obs = delta(SEVEN)
    for _ in range(4000):
        v = delta(set(rng.choice(labels, 7, replace=False)))
        if np.isfinite(v): nulls.append(v)
    nulls = np.array(nulls)
    write(pd.DataFrame([dict(observed_in7_minus_out_AUROC_all_constructions=obs, n_random_7subsets_valid=len(nulls), null_mean=nulls.mean(), null_sd=nulls.std(), null_q95=np.percentile(nulls, 95), null_q99=np.percentile(nulls, 99),
                             frac_random_subsets_with_difference_ge_observed=float((nulls >= obs).mean()),
                             note='trial-level reference distribution over arbitrary 7-label sets of the 16 CA-MER labels; asks whether a label-identity partition of this size routinely yields such a gap')]), 'V2_A3d_random_label_subset_null.csv', SUB)
    meta = pd.DataFrame([json.loads(l) for l in open(used('manifests/camer/controlled.jsonl'))]).set_index('sample_id')
    co = meta.candidate_order.to_dict()
    b['audio_label_earlier'] = [co[r.item_id].index(r.y1) < co[r.item_id].index(r.y2) for r in b.itertuples()]
    e = b.audio_label_earlier.values; yy = b.y.values
    pt, lo, hi, _ = cluster_boot(b.item_id.values, lambda i: yy[i][e[i]].mean() - yy[i][~e[i]].mean(), 2000, SEED + 251)
    g = b.groupby(['camer_subset', 'audio_label_earlier']).y.agg(['mean', 'size']).reset_index()
    g['ALL_diff_earlier_minus_later'] = pt; g['ALL_diff_lo'] = lo; g['ALL_diff_hi'] = hi
    write(g, 'V2_B_camer_candidate_position_vs_choice.csv', SUB)


def camer_identity():
    meta = pd.DataFrame([json.loads(l) for l in open(used('manifests/camer/controlled.jsonl'))])
    j = read_csv('manifests/camer/frozen_joint_outcomes.csv')
    b = b3_table(); b = b[b.dataset == 'CA-MER']
    res = {}
    res['controlled_manifest_rows'] = len(meta); res['unique_sample_ids'] = int(meta.sample_id.nunique())
    res['keys_in_manifest'] = sorted(meta.columns.tolist())
    res['final_label_or_alignment_fields_present'] = [k for k in meta.columns if 'final' in k.lower() or 'emotionllama' in k.lower() or 'target' in k.lower()]
    res['subset_conflict_pool_crosstab'] = pd.crosstab(meta.subset, meta.conflict_pool).to_dict()
    res['y_A_ne_y_V_matches_conflict_pool'] = bool(((meta.y_A != meta.y_V) == meta.conflict_pool).all())
    res['candidate_order_sha_recomputed_matches'] = None
    ok = 0
    for r in meta.itertuples():
        for ser in (json.dumps(r.candidate_order, separators=(',', ':')), json.dumps(r.candidate_order), json.dumps(r.candidate_order, ensure_ascii=False, separators=(',', ':'))):
            if hashlib.sha256(ser.encode()).hexdigest() == r.candidate_order_sha256: ok += 1; break
    res['candidate_order_sha_recomputed_matches'] = ok
    res['candidate_set_identical_all_rows'] = bool(meta.candidate_labels.map(lambda x: tuple(sorted(x))).nunique() == 1)
    res['candidate_order_is_permutation_of_set'] = bool(meta.apply(lambda r: sorted(r.candidate_order) == sorted(r.candidate_labels), axis=1).all())
    res['n_distinct_candidate_orders'] = int(meta.candidate_order_sha256.nunique())
    sid = set(meta.sample_id); res['joint_samples_equal_manifest'] = (set(j.source_item_id) == sid)
    res['joint_rows_per_sample_counts'] = j.groupby('source_item_id').size().value_counts().to_dict()
    mm = meta.set_index('sample_id')
    res['joint_source_labels_match_manifest'] = bool(((j.modality1_source_label.values == mm.loc[j.source_item_id, 'y_A'].values) & (j.modality2_source_label.values == mm.loc[j.source_item_id, 'y_V'].values)).all())
    ba = b[b.modality == 'A'].set_index('stable_dataset_id'); bv = b[b.modality == 'V'].set_index('stable_dataset_id')
    res['B3_audio_evidence_hash_equals_manifest_audio_sha256'] = int((ba.loc[meta.sample_id, 'evidence_hash'].values == meta.audio_sha256.values).sum())
    res['B3_video_evidence_hash_equals_manifest_silent_video_sha256'] = int((bv.loc[meta.sample_id, 'evidence_hash'].values == meta.silent_video_sha256.values).sum())
    res['B3_video_evidence_hash_note'] = 'if <1500, B3 V evidence hash is bound to a different video artefact than the controlled silent video'
    res['joint_modality1_evidence_sha_equals_audio_sha'] = int((j.modality1_evidence_sha256.values == mm.loc[j.source_item_id, 'audio_sha256'].values).sum())
    res['joint_modality2_evidence_sha_equals_video_sha'] = int((j.modality2_evidence_sha256.values == mm.loc[j.source_item_id, 'silent_video_sha256'].values).sum())
    res['technical_missing_by_subset_order'] = j.assign(sub=mm.loc[j.source_item_id, 'subset'].values).query('technical_missing').groupby(['sub', 'presentation_order']).size().to_dict().__repr__()
    tm = j.assign(sub=mm.loc[j.source_item_id, 'subset'].values, dur=np.nan)
    res['technical_missing_both_orders_same_sample'] = int(j[j.technical_missing].groupby('source_item_id').size().eq(2).sum())
    res['technical_missing_samples'] = int(j[j.technical_missing].source_item_id.nunique())
    res['technical_missing_reason_counts'] = j.technical_missing_reason.value_counts().to_dict()
    res['planned_runner_arms'] = 'A_ONLY,V_ONLY,A_THEN_V,V_THEN_A x 1500 = 6000 records (src/cross_regime/run_camer_joint.py: ARMS, full_counts_valid)'
    res['runner_output_fields'] = 'raw_model_output, parse_status, parsed_label (greedy generate, thinker_do_sample=False); NO candidate scores/logits saved'
    (INTER / 'V2_CAMER_identity_checks.json').write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
    return res


def eri1_posttreatment_strata():
    """POST-TREATMENT stratification (descriptive only): split items by whether A_ONLY at SNR00 still reads the source label."""
    d = read_csv('results/eri1_scientific_closure_v1/ERI1_SCIENTIFIC_TRIAL_PROJECTION_V1.csv')
    a = d[d.order_or_arm == 'A_ONLY'].pivot(index='item_id', columns='condition', values='outcome_class')
    j = d[d.order_or_arm.isin(['A_THEN_V', 'V_THEN_A'])].assign(sa=lambda x: (x.outcome_class == 'SIDE_A') * 1., sv=lambda x: (x.outcome_class == 'SIDE_V') * 1., ot=lambda x: (x.outcome_class == 'OTHER') * 1.)
    w = j.groupby(['item_id', 'condition'])[['sa', 'sv', 'ot']].mean().unstack()
    cl = j.drop_duplicates('item_id').set_index('item_id').dialogue_id
    st = a['SNR00'] == 'CORRECT_SOURCE_LABEL'; rc = a['RECODE'] == 'CORRECT_SOURCE_LABEL'
    rows = []
    for nm, m in [('A_ONLY still correct at SNR00 (and RECODE)', st & rc), ('A_ONLY lost at SNR00 (correct at RECODE)', (~st) & rc), ('A_ONLY already not correct at RECODE', ~rc)]:
        ids = m[m].index; r = dict(stratum=nm, n_items=len(ids), SIDE_A_RECODE=w[('sa', 'RECODE')].loc[ids].mean())
        for k in ['sa', 'sv', 'ot']:
            dd = (w[(k, 'SNR00')] - w[(k, 'RECODE')]).loc[ids].values
            pt, lo, hi, _ = cluster_boot(cl.loc[ids].values, lambda i: dd[i].mean(), 2000, SEED + 301)
            r[f'delta_{k}'], r[f'delta_{k}_lo'], r[f'delta_{k}_hi'] = pt, lo, hi
        r['status'] = 'POST_TREATMENT_STRATIFICATION_DESCRIPTIVE_ONLY'; rows.append(r)
    write(pd.DataFrame(rows), 'V2_A1b_ERI1_effect_by_posttreatment_A_ONLY_readability.csv', SUB)


if __name__ == '__main__':
    import warnings; warnings.filterwarnings('ignore')
    eri1_readability(); eri1_posttreatment_strata(); oracle_audit(); camer_confound(); r = camer_identity(); print(json.dumps(r, indent=1, default=str)); save_registry('a05')
