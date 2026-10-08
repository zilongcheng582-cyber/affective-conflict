"""R2 - EmotionTalk Phase3 compositionality falsification (POST_AUDIT_SCIENTIFIC_ANALYSIS_V1).

Uses the frozen composition (B1) exactly as published in PHASE3_ROW_LEVEL_VERIFICATION_V1.csv
and compares it to alternative baselines. Phase3 outcomes are never used to fit or select any
baseline except the explicitly labelled within-item oracle-like diagnostic.
Run: python -m analyses.post_audit.sci_r2_compositionality
"""
import json
import warnings
from collections import Counter, defaultdict

import numpy as np
from sklearn.linear_model import LogisticRegression

from analyses.post_audit.sci_common import (REPO, OUT, SEED, BOOTSTRAPS, ORIGIN, csvrows, jsonl, write_csv,
                                            grouped_folds, cluster_bootstrap, ci)

N_SHUFFLES = 2000


def compose(selected_1, selected_2, majority_mods, minority_mod, maj_label, min_label):
    """Frozen composition rule (identical to analyses/post_audit/replay.verify_phase3)."""
    if selected_1 is None or selected_2 is None:
        return 'UNRESOLVED', None
    if selected_1 in majority_mods and selected_2 in majority_mods:
        return 'MAJORITY', maj_label
    if selected_1 == minority_mod and selected_2 == minority_mod:
        return 'MINORITY', min_label
    return 'UNRESOLVED', None


def selected_modality(outcome, pair):
    return pair[0] if outcome == 'SIDE_MODALITY_1' else pair[1] if outcome == 'SIDE_MODALITY_2' else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plan = csvrows(REPO / 'manifests/emotiontalk/trimodal_plan.csv')
    obs = {(r['utterance_id'], r['tri_order']): r for r in jsonl(REPO / 'evidence/emotiontalk/phase3_observed_outputs.jsonl')}
    ver = {(r['utterance_id'], r['tri_order']): r for r in
           csvrows(REPO / 'results/post_audit/closure_v1/PHASE3_ROW_LEVEL_VERIFICATION_V1.csv')}
    p2 = {(r['utterance_id'], r['pair'], r['arm']): r for r in jsonl(REPO / 'evidence/emotiontalk/phase2_observed_responses.jsonl')}
    meas = {r['utterance_id']: r for r in csvrows(REPO / 'manifests/emotiontalk/source_measurements.csv')}
    assert len(plan) == 402 and len(obs) == 402 and len(ver) == 402

    rows = []
    for pr in plan:
        key = (pr['utterance_id'], pr['tri_order'])
        o, v = obs[key], ver[key]
        order = pr['tri_order'].split('_THEN_')
        maj = {pr['majority_modality_1'], pr['majority_modality_2']}
        mino = pr['minority_modality']
        edges = [pr['informative_pair_1'], pr['informative_pair_2']]
        matched_arms = [pr['matched_phase2_arm_1'], pr['matched_phase2_arm_2']]
        rows.append({'utterance_id': key[0], 'tri_order': key[1], 'speaker_id': pr['speaker_id'],
                     'trimodal_pattern': pr['trimodal_pattern'], 'minority_modality': mino,
                     'majority_modalities': ''.join(sorted(maj)), 'majority_label': pr['majority_label'],
                     'minority_label': pr['minority_label'], 'order': order, 'edges': edges, 'matched_arms': matched_arms,
                     'observed_label': o['parsed_label'],
                     'observed_class': 'MAJORITY' if o['parsed_label'] == pr['majority_label'] else
                                       'MINORITY' if o['parsed_label'] == pr['minority_label'] else 'OTHER',
                     'first_modality': order[0], 'last_modality': order[-1],
                     'B1_class': v['prediction_class'], 'B1_label': v['predicted_label'] or None})
    # sanity: frozen B1 reproduces from Phase2 edges with frozen rule
    for r in rows:
        sel = [selected_modality(p2[(r['utterance_id'], e, a)]['joint_outcome'], e) for e, a in zip(r['edges'], r['matched_arms'])]
        if any(p2[(r['utterance_id'], e, a)]['joint_outcome'] not in ('SIDE_MODALITY_1', 'SIDE_MODALITY_2') for e, a in zip(r['edges'], r['matched_arms'])):
            sel = [None, None]
        c, l = compose(sel[0], sel[1], set(r['majority_modalities']), r['minority_modality'], r['majority_label'], r['minority_label'])
        assert (c, l) == (r['B1_class'], r['B1_label']), r
    frozen294 = np.array([r['B1_class'] != 'UNRESOLVED' for r in rows])
    assert frozen294.sum() == 294
    assert sum(r['B1_label'] == r['observed_label'] for r in rows if r['B1_label']) == 268

    def lab(r, cls):
        return r['majority_label'] if cls == 'MAJORITY' else r['minority_label'] if cls == 'MINORITY' else None

    preds = {}  # name -> list of labels (None = abstain)
    roles = {}
    preds['B1_FROZEN_MATCHED_PAIRWISE'] = [r['B1_label'] for r in rows]
    roles['B1_FROZEN_MATCHED_PAIRWISE'] = 'FROZEN_PRIMARY_COMPOSITION'
    preds['B0_ALWAYS_MAJORITY'] = [r['majority_label'] for r in rows]
    roles['B0_ALWAYS_MAJORITY'] = 'TOPOLOGY_ONLY_BASELINE'
    preds['B0m_ALWAYS_MINORITY'] = [r['minority_label'] for r in rows]
    roles['B0m_ALWAYS_MINORITY'] = 'TOPOLOGY_ONLY_REFERENCE'

    # ---- B2 order-only ----
    def modlabel(r, m):
        return r['minority_label'] if m == r['minority_modality'] else r['majority_label']
    preds['B2a_FIRST_PRESENTED_MODALITY_LABEL'] = [modlabel(r, r['first_modality']) for r in rows]
    preds['B2b_LAST_PRESENTED_MODALITY_LABEL'] = [modlabel(r, r['last_modality']) for r in rows]
    roles['B2a_FIRST_PRESENTED_MODALITY_LABEL'] = roles['B2b_LAST_PRESENTED_MODALITY_LABEL'] = 'ORDER_ONLY_HEURISTIC_NO_FIT'
    # B2c: source-fitted pair x order selection rates (Phase2 resolved conflict records, leave-test-utterance-out),
    # each informative edge predicted from (pair, arm) only, composed with the frozen rule.
    src = [r for r in p2.values() if r['y_M1'] != r['y_M2'] and r['joint_outcome'] in ('SIDE_MODALITY_1', 'SIDE_MODALITY_2')]
    assert len(src) == 663
    cell = defaultdict(lambda: [0, 0])
    cell_u = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for s in src:
        k = (s['pair'], s['arm'])
        cell[k][0] += s['joint_outcome'] == 'SIDE_MODALITY_1'; cell[k][1] += 1
        cell_u[s['utterance_id']][k][0] += s['joint_outcome'] == 'SIDE_MODALITY_1'; cell_u[s['utterance_id']][k][1] += 1
    b2c, b2c_rates = [], {}
    for r in rows:
        sel = []
        for e, a in zip(r['edges'], r['matched_arms']):
            n1 = cell[(e, a)][0] - cell_u[r['utterance_id']][(e, a)][0]
            n = cell[(e, a)][1] - cell_u[r['utterance_id']][(e, a)][1]
            rate = n1 / n
            b2c_rates[(e, a)] = rate
            sel.append(e[0] if rate > .5 else e[1] if rate < .5 else None)
        b2c.append(lab(r, compose(sel[0], sel[1], set(r['majority_modalities']), r['minority_modality'], 0, 0)[0]))
    preds['B2c_SOURCE_ORDER_ONLY_PAIRWISE_COMPOSITION'] = b2c
    roles['B2c_SOURCE_ORDER_ONLY_PAIRWISE_COMPOSITION'] = 'ORDER_ONLY_SOURCE_FIT_LEAVE_TEST_UTTERANCE_OUT'

    # ---- B3 item-level label preference (Phase1/Phase2 only, no Phase3 outcome) ----
    b3a, b3a_t, b3b, b3c = [], [], [], []
    for r in rows:
        uid = r['utterance_id']
        votes = Counter()
        for e in r['edges']:
            for a in ('_THEN_'.join(e), '_THEN_'.join(e[::-1])):
                rec = p2[(uid, e, a)]
                if rec['parsed_label'] in (r['majority_label'], r['minority_label']):
                    votes[rec['parsed_label']] += 1
        vm, vn = votes[r['majority_label']], votes[r['minority_label']]
        b3a.append(r['majority_label'] if vm > vn else r['minority_label'] if vn > vm else None)
        b3a_t.append(r['majority_label'] if vm >= vn else r['minority_label'])
        # order-mismatched composition: opposite arms of the same informative edges
        sel = []
        for e, a in zip(r['edges'], r['matched_arms']):
            opp = '_THEN_'.join(a.split('_THEN_')[::-1])
            sel.append(selected_modality(p2[(uid, e, opp)]['joint_outcome'], e))
        b3b.append(lab(r, compose(sel[0], sel[1], set(r['majority_modalities']), r['minority_modality'], 0, 0)[0]))
        # Phase1 unimodal: label predicted by the most confident (lowest normalized entropy) modality
        m = meas[uid]
        best = min('ATV', key=lambda x: float(m['entropy_' + x]))
        b3c.append(modlabel(r, best))
    preds['B3a_ITEM_PREF_PHASE2_ORDER_POOLED_VOTE'] = b3a
    preds['B3a_t_ITEM_PREF_PHASE2_VOTE_TIE_TO_MAJORITY'] = b3a_t
    preds['B3b_ORDER_MISMATCHED_PAIRWISE_COMPOSITION'] = b3b
    preds['B3c_PHASE1_LOWEST_ENTROPY_MODALITY_LABEL'] = b3c
    roles['B3a_ITEM_PREF_PHASE2_ORDER_POOLED_VOTE'] = 'ITEM_LEVEL_PREFERENCE_PHASE2_BOTH_ORDERS_INFORMATIVE_EDGES'
    roles['B3a_t_ITEM_PREF_PHASE2_VOTE_TIE_TO_MAJORITY'] = 'ITEM_LEVEL_PREFERENCE_FULL_COVERAGE_VARIANT'
    roles['B3b_ORDER_MISMATCHED_PAIRWISE_COMPOSITION'] = 'SAME_ITEM_EDGES_OPPOSITE_ORDER'
    roles['B3c_PHASE1_LOWEST_ENTROPY_MODALITY_LABEL'] = 'PHASE1_UNIMODAL_CONFIDENCE_HEURISTIC'

    # global label preference (Phase2 conflict selections of OTHER utterances)
    b3d = []
    for r in rows:
        w = Counter(); t = Counter()
        for s in src:
            if s['utterance_id'] == r['utterance_id']:
                continue
            t[s['y_M1']] += 1; t[s['y_M2']] += 1; w[s['parsed_label']] += 1
        rm, rn = w[r['majority_label']] / t[r['majority_label']], w[r['minority_label']] / t[r['minority_label']]
        b3d.append(r['majority_label'] if rm > rn else r['minority_label'] if rn > rm else None)
    preds['B3d_GLOBAL_LABEL_PREFERENCE_PHASE2_LOUO'] = b3d
    roles['B3d_GLOBAL_LABEL_PREFERENCE_PHASE2_LOUO'] = 'GLOBAL_LABEL_PRIOR_LEAVE_TEST_UTTERANCE_OUT'

    # B5: unseen-item compositional prediction - edges predicted by a source evidence model (M3a spec:
    # pair + order + delta source-prob + delta entropy) fitted on Phase2 records of other utterances (5-fold grouped).
    p3_utts = sorted(set(r['utterance_id'] for r in rows))
    fmap = grouped_folds(p3_utts, SEED)
    def feats(uid, pair, arm):
        m = meas[uid]
        return [pair == 'AV', pair == 'VT', arm.split('_THEN_')[0] == pair[0],
                float(m['source_prob_' + pair[0]]) - float(m['source_prob_' + pair[1]]),
                float(m['entropy_' + pair[0]]) - float(m['entropy_' + pair[1]])]
    models = {}
    for k in range(5):
        test_u = {u for u in p3_utts if fmap[u] == k}
        tr = [s for s in src if s['utterance_id'] not in test_u]
        X = np.array([feats(s['utterance_id'], s['pair'], s['arm']) for s in tr], float)
        yy = np.array([s['joint_outcome'] == 'SIDE_MODALITY_1' for s in tr], int)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            models[k] = LogisticRegression(penalty=None, max_iter=5000).fit(X, yy)
    b5 = []
    for r in rows:
        mdl = models[fmap[r['utterance_id']]]
        sel = []
        for e, a in zip(r['edges'], r['matched_arms']):
            p = mdl.predict_proba(np.array([feats(r['utterance_id'], e, a)], float))[0, 1]
            sel.append(e[0] if p >= .5 else e[1])
        b5.append(lab(r, compose(sel[0], sel[1], set(r['majority_modalities']), r['minority_modality'], 0, 0)[0]))
    preds['B5_CROSSFIT_M3a_SPEC_PREDICTED_EDGE_COMPOSITION'] = b5
    roles['B5_CROSSFIT_M3a_SPEC_PREDICTED_EDGE_COMPOSITION'] = 'UNSEEN_ITEM_EDGE_PREDICTION_UTTERANCE_CROSSFIT'

    # ---- within-item oracle-like diagnostic: other 5 Phase3 orders of the same utterance ----
    by_u = defaultdict(list)
    for i, r in enumerate(rows):
        by_u[r['utterance_id']].append(i)
    orc = []
    for i, r in enumerate(rows):
        c = Counter(rows[j]['observed_label'] for j in by_u[r['utterance_id']] if j != i)
        top = c.most_common()
        orc.append(top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else None)
    preds['DIAG_WITHIN_ITEM_ORACLE_LIKE_LEAVE_ONE_ORDER_OUT'] = orc
    roles['DIAG_WITHIN_ITEM_ORACLE_LIKE_LEAVE_ONE_ORDER_OUT'] = 'WITHIN_ITEM_ORACLE_LIKE_USES_PHASE3_OUTCOMES_NOT_A_BASELINE'

    # ---- B4 topology/order-matched shuffled pairwise ----
    strata = defaultdict(list)
    for u in p3_utts:
        strata[next(r['minority_modality'] for r in rows if r['utterance_id'] == u)].append(u)
    rng = np.random.default_rng(SEED)
    obs_lab = [r['observed_label'] for r in rows]
    shuffle_rows = []
    edge_sel = {}
    for r in rows:
        for e, a in zip(r['edges'], r['matched_arms']):
            edge_sel[(r['utterance_id'], e, a)] = selected_modality(p2[(r['utterance_id'], e, a)]['joint_outcome'], e)
    for b in range(N_SHUFFLES):
        donor = {}
        for s, us in strata.items():
            while True:
                perm = rng.permutation(len(us))
                if len(us) < 2 or not np.any(perm == np.arange(len(us))):
                    break
            donor.update({u: us[perm[i]] for i, u in enumerate(us)})
        res = []
        for r in rows:
            d = donor[r['utterance_id']]
            sel = [edge_sel[(d, e, a)] for e, a in zip(r['edges'], r['matched_arms'])]
            res.append(lab(r, compose(sel[0], sel[1], set(r['majority_modalities']), r['minority_modality'], 0, 0)[0]))
        res = np.array(res, dtype=object)
        resolved = np.array([x is not None for x in res])
        correct = np.array([x is not None and x == o for x, o in zip(res, obs_lab)])
        shuffle_rows.append({'replicate': b, 'n_resolved': int(resolved.sum()), 'n_correct_of_402': int(correct.sum()),
                             'accuracy_on_own_resolved': correct.sum() / resolved.sum(),
                             'n_resolved_within_frozen294': int(resolved[frozen294].sum()),
                             'n_correct_within_frozen294': int(correct[frozen294].sum()),
                             'accuracy_frozen294_abstain_as_error': correct[frozen294].mean(),
                             'n_pred_minority': int(sum(x is not None and x == r['minority_label'] for x, r in zip(res, rows))),
                             'n_correct_minority': int(sum(x is not None and x == r['minority_label'] and c for x, r, c in zip(res, rows, correct)))})
        if b == 0:
            preds['B4_SHUFFLED_PAIRWISE_REPLICATE0'] = list(res)
            roles['B4_SHUFFLED_PAIRWISE_REPLICATE0'] = 'ONE_SHUFFLE_REPLICATE_FOR_ROW_LEVEL_DISPLAY'

    # ---------- evaluation ----------
    obs_arr = np.array(obs_lab, dtype=object)
    utt = np.array([r['utterance_id'] for r in rows])
    is_min_obs = np.array([r['observed_class'] == 'MINORITY' for r in rows])

    def summarize(name, lab_list):
        L = np.array(lab_list, dtype=object)
        res = np.array([x is not None for x in L])
        cor = np.array([x is not None and x == o for x, o in zip(L, obs_arr)])
        pmin = np.array([x is not None and x == r['minority_label'] for x, r in zip(L, rows)])
        pmaj = np.array([x is not None and x == r['majority_label'] for x, r in zip(L, rows)])
        common = frozen294 & res
        return {'baseline': name, 'role': roles[name],
                'coverage_402': res.mean(), 'n_resolved_402': int(res.sum()), 'n_correct_402': int(cor.sum()),
                'accuracy_own_resolved': cor[res].mean() if res.any() else np.nan,
                'correct_rate_402_abstain_as_error': cor.mean(),
                'n_resolved_on_frozen294': int(res[frozen294].sum()),
                'n_correct_on_frozen294': int(cor[frozen294].sum()),
                'accuracy_frozen294_abstain_as_error': cor[frozen294].mean(),
                'n_common_support_with_B1': int(common.sum()),
                'accuracy_common_support': cor[common].mean() if common.any() else np.nan,
                'B1_accuracy_common_support': np.mean([rows[i]['B1_label'] == obs_lab[i] for i in np.flatnonzero(common)]) if common.any() else np.nan,
                'n_pred_majority': int(pmaj.sum()), 'n_pred_majority_correct': int((pmaj & cor).sum()),
                'n_pred_minority': int(pmin.sum()), 'n_pred_minority_correct': int((pmin & cor).sum()),
                'minority_recall_on_frozen294': (pmin & cor & frozen294).sum() / max(1, (is_min_obs & frozen294).sum()),
                'analysis_origin': ORIGIN}

    comp = [summarize(n, l) for n, l in preds.items()]
    sh = np.array([[s['accuracy_frozen294_abstain_as_error'], s['n_correct_of_402'], s['accuracy_on_own_resolved']] for s in shuffle_rows])
    b1 = comp[0]
    comp.append({'baseline': 'B4_SHUFFLED_PAIRWISE_DISTRIBUTION', 'role': 'TOPOLOGY_ORDER_MATCHED_DONOR_DERANGEMENT_WITHIN_MINORITY_MODALITY_STRATUM',
                 'accuracy_frozen294_abstain_as_error': sh[:, 0].mean(), 'n_correct_402': sh[:, 1].mean(),
                 'accuracy_own_resolved': sh[:, 2].mean(), 'shuffle_replicates': N_SHUFFLES,
                 'shuffle_p_ge_observed_frozen294': (1 + np.sum(sh[:, 0] >= b1['accuracy_frozen294_abstain_as_error'])) / (1 + N_SHUFFLES),
                 'shuffle_p_ge_observed_correct402': (1 + np.sum(sh[:, 1] >= b1['n_correct_402'])) / (1 + N_SHUFFLES),
                 'shuffle_p_ge_observed_own_resolved_acc': (1 + np.sum(sh[:, 2] >= b1['accuracy_own_resolved'])) / (1 + N_SHUFFLES),
                 'analysis_origin': ORIGIN})
    write_csv(OUT / 'R2_BASELINE_COMPARISON.csv', comp)
    for s in shuffle_rows:
        s.update({'seed': SEED, 'analysis_origin': ORIGIN})
    write_csv(OUT / 'R2_SHUFFLE_DISTRIBUTION.csv', shuffle_rows)

    # row-level
    rl = []
    for i, r in enumerate(rows):
        row = {k: r[k] for k in ('utterance_id', 'tri_order', 'speaker_id', 'trimodal_pattern', 'minority_modality',
                                 'majority_label', 'minority_label', 'observed_label', 'observed_class', 'B1_class')}
        row['frozen294_member'] = bool(frozen294[i])
        for n, l in preds.items():
            row['pred__' + n] = l[i]
            row['correct__' + n] = '' if l[i] is None else int(l[i] == obs_lab[i])
        rl.append(row)
    write_csv(OUT / 'R2_PAIRWISE_VS_BASELINES.csv', rl)

    # per-utterance
    pu = []
    for u in p3_utts:
        idx = by_u[u]
        r0 = rows[idx[0]]
        d = {'utterance_id': u, 'trimodal_pattern': r0['trimodal_pattern'], 'minority_modality': r0['minority_modality'],
             'n_orders': len(idx), 'n_obs_majority': sum(rows[i]['observed_class'] == 'MAJORITY' for i in idx),
             'n_obs_minority': sum(rows[i]['observed_class'] == 'MINORITY' for i in idx),
             'n_obs_other': sum(rows[i]['observed_class'] == 'OTHER' for i in idx),
             'B1_n_resolved': sum(frozen294[i] for i in idx),
             'B1_n_correct': sum(rows[i]['B1_label'] == rows[i]['observed_label'] for i in idx if rows[i]['B1_label']),
             'B1_n_pred_minority': sum(rows[i]['B1_class'] == 'MINORITY' for i in idx),
             'B0_n_correct_on_B1_resolved': sum(rows[i]['majority_label'] == rows[i]['observed_label'] for i in idx if frozen294[i]),
             'B3a_n_correct_on_B1_resolved': sum(b3a[i] == rows[i]['observed_label'] for i in idx if frozen294[i] and b3a[i]),
             'observed_labels_constant_across_orders': len(set(rows[i]['observed_label'] for i in idx)) == 1}
        pu.append(d)
    write_csv(OUT / 'R2_PER_UTTERANCE.csv', pu)

    # ---------- clustered uncertainty (67 utterance clusters) ----------
    unc = []
    cor = {n: np.array([x is not None and x == o for x, o in zip(l, obs_lab)]) for n, l in preds.items()}
    resd = {n: np.array([x is not None for x in l]) for n, l in preds.items()}
    for n in preds:
        if n == 'B1_FROZEN_MATCHED_PAIRWISE':
            continue
        for support in ('FROZEN294_ABSTAIN_AS_ERROR', 'COMMON_SUPPORT', 'ALL402_ABSTAIN_AS_ERROR'):
            if support == 'FROZEN294_ABSTAIN_AS_ERROR':
                s = frozen294
            elif support == 'COMMON_SUPPORT':
                s = frozen294 & resd[n]
            else:
                s = np.ones(402, bool)
            a, b_, cl = cor['B1_FROZEN_MATCHED_PAIRWISE'][s].astype(float), cor[n][s].astype(float), utt[s]
            if not len(a):
                continue
            def stat(idx, a=a, b_=b_):
                return {'diff': a[idx].mean() - b_[idx].mean(), 'B1': a[idx].mean(), 'other': b_[idx].mean()}
            bs = cluster_bootstrap(cl, stat)
            row = {'comparison': 'B1_FROZEN_MATCHED_PAIRWISE minus ' + n, 'support': support, 'N_rows': int(s.sum()),
                   'N_utterances': len(set(cl)), 'B1_accuracy': a.mean(), 'baseline_accuracy': b_.mean(),
                   'accuracy_difference': a.mean() - b_.mean()}
            for k in ('diff', 'B1', 'other'):
                lo, hi, nn = ci(bs[k])
                row[k + '_CI_low'], row[k + '_CI_high'] = lo, hi
            row['prop_bootstrap_diff_le_0'] = float(np.mean(bs['diff'] <= 0))
            row.update({'bootstrap_replicates': BOOTSTRAPS, 'bootstrap_seed': SEED,
                        'CI_method': 'UTTERANCE_CLUSTER_PERCENTILE_95', 'analysis_origin': ORIGIN})
            unc.append(row)
    # Rows where the order-pooled item vote ties: only order-matched edge information can separate labels.
    s = frozen294 & ~resd['B3a_ITEM_PREF_PHASE2_ORDER_POOLED_VOTE']
    a, b_, cl = cor['B1_FROZEN_MATCHED_PAIRWISE'][s].astype(float), cor['B3a_t_ITEM_PREF_PHASE2_VOTE_TIE_TO_MAJORITY'][s].astype(float), utt[s]
    bs = cluster_bootstrap(cl, lambda idx, a=a, b_=b_: {'diff': a[idx].mean() - b_[idx].mean()})
    lo, hi, _ = ci(bs['diff'])
    unc.append({'comparison': 'B1_FROZEN_MATCHED_PAIRWISE minus B3a_t_ITEM_PREF_PHASE2_VOTE_TIE_TO_MAJORITY',
                'support': 'FROZEN294_ROWS_WHERE_ORDER_POOLED_ITEM_VOTE_TIES', 'N_rows': int(s.sum()),
                'N_utterances': len(set(cl)), 'B1_accuracy': a.mean(), 'baseline_accuracy': b_.mean(),
                'accuracy_difference': a.mean() - b_.mean(), 'diff_CI_low': lo, 'diff_CI_high': hi,
                'prop_bootstrap_diff_le_0': float(np.mean(bs['diff'] <= 0)),
                'bootstrap_replicates': BOOTSTRAPS, 'bootstrap_seed': SEED, 'CI_method': 'UTTERANCE_CLUSTER_PERCENTILE_95',
                'analysis_origin': ORIGIN})
    # B1 within-class accuracy uncertainty
    for cls in ('MAJORITY', 'MINORITY'):
        s = np.array([r['B1_class'] == cls for r in rows])
        a, cl = cor['B1_FROZEN_MATCHED_PAIRWISE'][s].astype(float), utt[s]
        bs = cluster_bootstrap(cl, lambda idx, a=a: {'acc': a[idx].mean()})
        lo, hi, _ = ci(bs['acc'])
        unc.append({'comparison': 'B1 accuracy among predicted ' + cls, 'support': 'B1_PRED_' + cls, 'N_rows': int(s.sum()),
                    'N_utterances': len(set(cl)), 'B1_accuracy': a.mean(), 'B1_CI_low': lo, 'B1_CI_high': hi,
                    'bootstrap_replicates': BOOTSTRAPS, 'bootstrap_seed': SEED, 'CI_method': 'UTTERANCE_CLUSTER_PERCENTILE_95',
                    'analysis_origin': ORIGIN})
    write_csv(OUT / 'R2_CLUSTERED_UNCERTAINTY.csv', unc)

    meta = {'analysis_origin': ORIGIN, 'seed': SEED, 'bootstraps': BOOTSTRAPS, 'shuffles': N_SHUFFLES,
            'planned': 402, 'frozen_resolved': 294, 'frozen_correct': 268, 'utterances': len(p3_utts),
            'observed_class_counts_402': dict(Counter(r['observed_class'] for r in rows)),
            'observed_class_counts_294': dict(Counter(r['observed_class'] for r, f in zip(rows, frozen294) if f)),
            'strata_utterances': {k: len(v) for k, v in strata.items()},
            'B2c_leave_out_edge_rates_example': {('%s|%s' % k): v for k, v in list(b2c_rates.items())[:12]},
            'inputs': ['manifests/emotiontalk/trimodal_plan.csv', 'evidence/emotiontalk/phase3_observed_outputs.jsonl',
                       'evidence/emotiontalk/phase2_observed_responses.jsonl', 'manifests/emotiontalk/source_measurements.csv',
                       'results/post_audit/closure_v1/PHASE3_ROW_LEVEL_VERIFICATION_V1.csv']}
    json.dump(meta, open(OUT / 'R2_RUN_METADATA.json', 'w'), indent=2, default=float)
    for c in comp:
        print({k: c.get(k) for k in ('baseline', 'coverage_402', 'n_correct_402', 'accuracy_own_resolved',
                                     'n_correct_on_frozen294', 'accuracy_frozen294_abstain_as_error', 'n_common_support_with_B1',
                                     'accuracy_common_support', 'B1_accuracy_common_support', 'n_pred_minority', 'n_pred_minority_correct',
                                     'shuffle_p_ge_observed_frozen294')})
    print(json.dumps(meta, indent=1, default=float))


if __name__ == '__main__':
    main()
