"""Third-party independent CPU replay for PR #6 (E1 video V2 and E2 consistent audio).

Written for the PR #6 scientific audit. It does NOT import or execute any PR #6 code
(replay.py, e1v2_analysis.py, e1v2_verify.py, e1e2_analysis.py, e1e2_verify.py).

Layers reported separately:
  POINT_ESTIMATE_REPLAY   outcomes re-derived from parsed_label vs frozen y_A/y_V, paired vectors, effects
  BOOTSTRAP_REPLAY        (a) RNG-contract replay from protocol text, (b) alternative-seed stability
  EXACT_INFERENCE         exact paired sign-flip p by full enumeration (dynamic programming), no RNG
  SOURCE_RESULT_LINKAGE   population, labels, candidate order, clusters vs unchanged main files
  INPUT_CONTRACT_AUDIT    visual_input_contract.csv internal consistency (E1)
  SCORING_AUDIT           candidate_probabilities.csv recomputation and label/mapping invariants
Usage: python -I independent_replay.py <pr6_checkout> <main_checkout> <out_json>
"""
import csv, json, math, sys, collections, itertools, hashlib
from fractions import Fraction
from pathlib import Path
import numpy as np

ORD = ('A_THEN_V', 'V_THEN_A')


def load(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- statistics (fresh code)
def contract_bootstrap(d, groups, seed, reps=10000):
    """Replay of the frozen text contract: item bootstrap with seed, cluster ratio bootstrap with seed+1."""
    d = np.asarray(d, float); n = d.size
    g = np.random.default_rng(seed)
    item = np.empty(reps)
    draws = g.integers(n, size=(reps, n))          # one block, as the frozen code draws
    item[:] = d[draws].mean(axis=1)
    keys = sorted(set(groups)); pos = {k: i for i, k in enumerate(keys)}
    tot = np.zeros(len(keys)); cnt = np.zeros(len(keys))
    np.add.at(tot, [pos[x] for x in groups], d); np.add.at(cnt, [pos[x] for x in groups], 1)
    cd = np.random.default_rng(seed + 1).integers(len(keys), size=(reps, len(keys)))
    ratio = tot[cd].sum(1) / cnt[cd].sum(1)
    q = lambda a: [float(np.quantile(a, .025)), float(np.quantile(a, .975))]
    return q(item), q(ratio)


def contract_signflip(d, seed, reps=100000, chunk=25000):
    """Same RNG contract, different chunking (25,000 x 4 instead of 1,000 x 100) to test stream invariance."""
    d = np.asarray(d, float); n = d.size; g = np.random.default_rng(seed + 2); hit = 0; obs = abs(d.mean())
    for _ in range(reps // chunk):
        s = g.integers(2, size=(chunk, n)) * 2 - 1
        hit += int(np.count_nonzero(np.abs(s @ d / n) >= obs - 1e-14))
    return (hit + 1) / (reps + 1)


def exact_signflip(d):
    """Exact two-sided paired sign-flip p over all 2^n sign vectors (values must be rational on a grid)."""
    fr = [Fraction(float(x)).limit_denominator(1000) for x in d]
    if any(abs(float(f) - float(x)) > 1e-12 for f, x in zip(fr, d)):
        return None
    den = math.lcm(*[f.denominator for f in fr]) if fr else 1
    ints = [int(f * den) for f in fr]
    S = sum(abs(v) for v in ints); off = S
    p = np.zeros(2 * S + 1); p[off] = 1.0
    for v in ints:
        v = abs(v)
        if v == 0:
            continue
        q = np.zeros_like(p); q[v:] += .5 * p[:-v] if v else 0; q[:-v] += .5 * p[v:]; p = q
    obs = abs(sum(ints)); k = np.arange(-S, S + 1)
    return float(p[np.abs(k) >= obs].sum())


def alt_bootstrap(d, groups, seed=777, reps=20000):
    d = np.asarray(d, float); g = np.random.default_rng(seed); n = d.size
    item = np.array([d[g.integers(n, size=n)].mean() for _ in range(reps)])
    keys = sorted(set(groups)); members = [np.array([i for i, x in enumerate(groups) if x == k]) for k in keys]
    rat = []
    for _ in range(reps // 4):
        pick = g.integers(len(keys), size=len(keys)); idx = np.concatenate([members[j] for j in pick]); rat.append(d[idx].mean())
    return [float(np.quantile(item, .025)), float(np.quantile(item, .975))], [float(np.quantile(rat, .025)), float(np.quantile(rat, .975))]


def holm(ps):
    m = len(ps); order = sorted(range(m), key=lambda i: ps[i]); out = [0.0] * m; run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * ps[i])); out[i] = run
    return out


# ---------------------------------------------------------------- outcome derivation
def derive_e1(r):
    if r['generation_technical_failure'] == 'True':
        return 'TECHNICAL_FAILURE'
    lab = r['parsed_label']
    if lab == '':
        return 'PARSE_FAIL'
    if lab not in r['candidate_sequence'].split('|'):
        return 'INVALID_LABEL'
    if lab == r['y_V']:
        return 'SIDE_V'
    if lab == r['y_A']:
        return 'SIDE_A'
    return 'OTHER'


def derive_e2(r):
    if r['technical_failure'] == 'True':
        return 'TECH_FAILURE'
    lab = r['parsed_label']
    if lab == '':
        return 'PARSE_FAIL'
    if lab not in r['candidate_sequence'].split('|'):
        return 'INVALID_LABEL'
    return 'SHARED_LABEL' if lab == r['y_A'] else 'OTHER'


class Ledger:
    def __init__(self):
        self.items = []

    def check(self, layer, name, ok, detail=None):
        self.items.append({'layer': layer, 'check': name, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})
        return ok

    def close(self, layer, name, got, ref, tol=1e-12):
        err = float(np.max(np.abs(np.asarray(got, float) - np.asarray(ref, float))))
        return self.check(layer, name, err <= tol, {'max_abs_error': err, 'got': got, 'reference': ref})


def build(full, derive):
    cells = {}
    for r in full:
        cells[r['utterance_id'], r['condition'], r['arm']] = dict(r, derived=derive(r))
    uids = sorted({r['utterance_id'] for r in full})
    return cells, uids


def rate(cells, uids, cond, cat):
    return np.array([sum(cells[u, cond, o]['derived'] == cat for o in ORD) / 2 for u in uids])


def endpoint_stats(L, tag, d, groups, ref, seed, effect_key, item_key, p_key):
    out = {'effect': float(np.mean(d))}
    L.close('POINT_ESTIMATE_REPLAY', tag + ':effect', out['effect'], ref[effect_key])
    ic, cc = contract_bootstrap(d, groups, seed)
    L.close('BOOTSTRAP_REPLAY', tag + ':item_ci_contract', ic, ref[item_key])
    L.close('BOOTSTRAP_REPLAY', tag + ':dialogue_ci_contract', cc, ref['dialogue_cluster_ci95'])
    p = contract_signflip(d, seed)
    L.close('BOOTSTRAP_REPLAY', tag + ':signflip_p_contract', p, ref[p_key])
    out.update(item_ci=ic, cluster_ci=cc, p_mc=p, p_exact=exact_signflip(d))
    ai, ac = alt_bootstrap(d, groups)
    out.update(alt_seed_item_ci=ai, alt_seed_cluster_ci=ac)
    return out


# ---------------------------------------------------------------- E1
def replay_e1(base, main, L):
    R = base / 'results/emotiontalk_e1_video_v2'
    full = load(R / 'full_outcomes.csv'); man = load(R / 'manifest.csv'); att = load(R / 'attempts.csv')
    ref = json.loads((R / 'scientific_results.json').read_text())
    cells, uids = build(full, derive_e1)
    res = {'items': len(uids)}
    # integrity / linkage
    L.check('SOURCE_RESULT_LINKAGE', 'E1:2336_unique_slots', len(full) == 2336 == len({r['trial_id'] for r in full}))
    L.check('SOURCE_RESULT_LINKAGE', 'E1:full_cells_unique', len(cells) == 2336)
    mcols = list(man[0]); mi = {r['trial_id']: r for r in man}
    L.check('SOURCE_RESULT_LINKAGE', 'E1:manifest_fields_equal_full', all(all(mi[r['trial_id']][c] == r[c] for c in mcols) for r in full))
    L.check('POINT_ESTIMATE_REPLAY', 'E1:outcome_rederived_from_labels', all(c['derived'] == c['outcome'] for c in cells.values()),
            collections.Counter((c['derived'], c['outcome']) for c in cells.values() if c['derived'] != c['outcome']))
    L.check('SOURCE_RESULT_LINKAGE', 'E1:conflict_yA_ne_yV', all(c['y_A'] != c['y_V'] for c in cells.values()))
    L.check('SOURCE_RESULT_LINKAGE', 'E1:yA_yV_in_candidates', all(c['y_A'] in c['candidate_sequence'].split('|') and c['y_V'] in c['candidate_sequence'].split('|') for c in cells.values()))
    ai = {r['trial_id']: r for r in att}
    L.check('SOURCE_RESULT_LINKAGE', 'E1:attempts_one_per_slot_full_phase', len(att) == 2336 and all(r['phase'] == 'full' and r['attempt'] == '1' for r in att))
    L.check('SOURCE_RESULT_LINKAGE', 'E1:attempt_label_outcome_equal', all(ai[c['trial_id']]['parsed_label'] == c['parsed_label'] and ai[c['trial_id']]['outcome'] == c['outcome'] for c in cells.values()))
    plan = json.loads((main / 'manifests/emotiontalk/EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json').read_text())['pairs']['AV']
    L.check('SOURCE_RESULT_LINKAGE', 'E1:uids_equal_main_conflict_plan', set(uids) == set(plan['conflict_utterance_ids']))
    sm = {r['utterance_id']: r for r in load(main / 'manifests/emotiontalk/source_measurements.csv')}
    bad = [u for u in uids if any(sm[u][k] != cells[u, 'RECODE', 'V_ONLY'][k] for k in ('y_A', 'y_V', 'y_T', 'candidate_sequence_id', 'candidate_sequence')) or sm[u]['DualReadable_AV'] != 'TRUE']
    L.check('SOURCE_RESULT_LINKAGE', 'E1:labels_order_dualreadable_equal_main_source_measurements', not bad, bad[:5])
    cmap = {r['item_id']: r['dialogue_id'] for r in load(main / 'results/eri1_scientific_closure_v1/DIALOGUE_CLUSTER_MAP_V1.csv')}
    groups = [cells[u, 'RECODE', 'A_THEN_V']['dialogue_id'] for u in uids]
    L.check('SOURCE_RESULT_LINKAGE', 'E1:clusters_equal_ERI1_official_map', all(cmap[u] == g for u, g in zip(uids, groups)) and len(set(groups)) == 134)
    per = collections.defaultdict(set)
    for c in cells.values():
        per[c['utterance_id'], 'audio'].add(c['audio_sha256']); per[c['utterance_id'], 'text'].add(c['text_sha256'])
        per[c['utterance_id'], c['condition'], 'video'].add(c['video_sha256'])
    L.check('INPUT_CONTRACT_AUDIT', 'E1:audio_sha_constant_across_conditions', all(len(v) == 1 for k, v in per.items() if k[1] == 'audio'))
    L.check('INPUT_CONTRACT_AUDIT', 'E1:video_sha_constant_within_condition_across_arms', all(len(v) == 1 for k, v in per.items() if len(k) == 3))
    L.check('INPUT_CONTRACT_AUDIT', 'E1:five_distinct_video_files_per_item', all(len({cells[u, c, 'V_ONLY']['video_sha256'] for c in ('CLEAN', 'RECODE', 'BLUR_L1', 'BLUR_L2', 'BLUR_L3')}) == 5 for u in uids))
    L.check('INPUT_CONTRACT_AUDIT', 'E1:A_ONLY_bound_to_CLEAN_video_file', all(cells[u, 'CLEAN', 'A_ONLY']['video_sha256'] == cells[u, 'CLEAN', 'V_ONLY']['video_sha256'] for u in uids))

    # endpoints
    P = {x['endpoint']: x for x in ref['primary']}; S = {x['endpoint']: x for x in ref['secondary']}
    conds = ['RECODE', 'BLUR_L1', 'BLUR_L2', 'BLUR_L3']
    vec = {}
    for k in ('SIDE_V', 'SIDE_A', 'OTHER'):
        vec[k + '_L3_MINUS_RECODE'] = rate(cells, uids, 'BLUR_L3', k) - rate(cells, uids, 'RECODE', k)
        vec[k + '_CLEAN_MINUS_RECODE'] = rate(cells, uids, 'CLEAN', k) - rate(cells, uids, 'RECODE', k)
        Y = np.column_stack([rate(cells, uids, c, k) for c in conds]); x = np.arange(4.0)
        vec[k + '_ORDINAL_DOSE_SLOPE'] = np.array([np.polyfit(x, y, 1)[0] for y in Y])   # OLS slope via polyfit
        vec[k + '_ORDER_INTERACTION'] = np.array([
            (int(cells[u, 'BLUR_L3', ORD[0]]['derived'] == k) - int(cells[u, 'RECODE', ORD[0]]['derived'] == k)) -
            (int(cells[u, 'BLUR_L3', ORD[1]]['derived'] == k) - int(cells[u, 'RECODE', ORD[1]]['derived'] == k)) for u in uids])
    vec['V_ONLY_CORRECTNESS_L3_MINUS_RECODE'] = np.array([int(cells[u, 'BLUR_L3', 'V_ONLY']['parsed_label'] == cells[u, 'BLUR_L3', 'V_ONLY']['y_V']) - int(cells[u, 'RECODE', 'V_ONLY']['parsed_label'] == cells[u, 'RECODE', 'V_ONLY']['y_V']) for u in uids])
    vec['V_ONLY_NORMALIZED_ENTROPY_L3_MINUS_RECODE'] = np.array([float(cells[u, 'BLUR_L3', 'V_ONLY']['entropy_normalized']) - float(cells[u, 'RECODE', 'V_ONLY']['entropy_normalized']) for u in uids])
    stats = {}
    for fam, refs in (('primary', P), ('secondary', S)):
        ps = []
        for name, r in refs.items():
            st = endpoint_stats(L, 'E1:' + name, vec[name], groups, r, int(r['seed']), 'effect', 'utterance_ci95', 'p_two_sided')
            stats[name] = st; ps.append(st['p_mc'])
        for (name, r), h in zip(refs.items(), holm(ps)):
            L.close('BOOTSTRAP_REPLAY', 'E1:' + name + ':holm', h, r['p_holm']); stats[name]['p_holm_mc'] = h
        ex = [stats[n]['p_exact'] for n in refs]
        if all(e is not None for e in ex):
            for n, h in zip(refs, holm(ex)):
                stats[n]['p_holm_exact'] = h
    # seeds follow frozen rule base+100+10*index across primary then secondary
    seeds = [int(x['seed']) for x in ref['primary'] + ref['secondary']]
    L.check('BOOTSTRAP_REPLAY', 'E1:seed_rule_base+100+10i', seeds == [2026101103 + 100 + 10 * i for i in range(len(seeds))], seeds)
    # order effects (descriptive)
    oe = json.loads((R / 'order_effects.json').read_text()); order = []
    for r in oe:
        d = np.array([int(cells[u, 'BLUR_L3', r['arm']]['derived'] == r['category']) - int(cells[u, 'RECODE', r['arm']]['derived'] == r['category']) for u in uids])
        L.close('POINT_ESTIMATE_REPLAY', f"E1:order:{r['arm']}:{r['category']}:effect", float(d.mean()), r['effect'])
        order.append({'arm': r['arm'], 'category': r['category'], 'effect': float(d.mean()), 'p_exact': exact_signflip(d)})
    # sum identity
    tot = sum(vec[k + '_L3_MINUS_RECODE'] for k in ('SIDE_V', 'SIDE_A', 'OTHER'))
    L.check('POINT_ESTIMATE_REPLAY', 'E1:three_categories_sum_to_zero_per_item(no PF/TF)', bool(np.all(np.abs(tot) < 1e-15)))
    # missing bounds: no technical failure
    L.check('POINT_ESTIMATE_REPLAY', 'E1:no_technical_missing_so_bounds_degenerate', all(c['derived'] != 'TECHNICAL_FAILURE' for c in cells.values()))
    # counts & dose
    counts = {c: {a: dict(collections.Counter(cells[u, c, a]['derived'] for u in uids)) for a in ('V_ONLY',) + ORD} for c in ('CLEAN',) + tuple(conds)}
    traj = {c: {k: float(rate(cells, uids, c, k).mean()) for k in ('SIDE_V', 'SIDE_A', 'OTHER')} for c in ('CLEAN',) + tuple(conds)}
    vonly = {c: sum(cells[u, c, 'V_ONLY']['parsed_label'] == cells[u, c, 'V_ONLY']['y_V'] for u in uids) / 146 for c in ('CLEAN',) + tuple(conds)}
    for row in load(R / 'dose_trajectory.csv'):
        if row['category'] in ('SIDE_V', 'SIDE_A', 'OTHER'):
            L.close('POINT_ESTIMATE_REPLAY', f"E1:dose:{row['condition']}:{row['category']}", traj[row['condition']][row['category']], float(row['rate_equal_item_mean_two_orders']))
        L.close('POINT_ESTIMATE_REPLAY', f"E1:dose:{row['condition']}:{row['category']}:VONLY", vonly[row['condition']], float(row['V_ONLY_correctness']))
    # transitions RECODE -> L3, by order and pooled
    trans = {}
    for o in ORD:
        trans[o] = dict(collections.Counter(f"{cells[u, 'RECODE', o]['derived']}->{cells[u, 'BLUR_L3', o]['derived']}" for u in uids))
    for row in load(R / 'category_transitions.csv'):
        n = sum(cells[u, row['from_condition'], row['arm']]['derived'] == row['from'] and cells[u, row['to_condition'], row['arm']]['derived'] == row['to'] for u in uids)
        if int(row['n']) != n:
            L.check('POINT_ESTIMATE_REPLAY', 'E1:category_transition_row', False, row)
    L.check('POINT_ESTIMATE_REPLAY', 'E1:category_transitions_csv_all_rows', True, 'any mismatch would be logged as FAIL above')
    lt_bad = 0
    lab = lambda c: c['derived'] if c['derived'] in ('PARSE_FAIL', 'TECHNICAL_FAILURE') else c['parsed_label']
    for row in load(R / 'label_transitions.csv'):
        n = sum(lab(cells[u, row['from_condition'], row['arm']]) == row['from_label'] and lab(cells[u, row['to_condition'], row['arm']]) == row['to_label'] for u in uids)
        lt_bad += int(row['n']) != n
    L.check('POINT_ESTIMATE_REPLAY', 'E1:label_transitions_csv_all_rows', lt_bad == 0, lt_bad)
    # item-level paired joint-state decomposition (both orders pooled at slot level, 292 paired slots)
    slot = collections.Counter((cells[u, 'RECODE', o]['derived'], cells[u, 'BLUR_L3', o]['derived']) for u in uids for o in ORD)
    gross = {f'{a}->{b}': n for (a, b), n in sorted(slot.items())}
    # sensitivity: top-level recording group (G000xx) cluster bootstrap, POST HOC, not frozen
    grp = [u.split('_')[0] for u in uids]
    post_hoc_group = {k: alt_bootstrap(vec[k + '_L3_MINUS_RECODE'], grp, seed=4242)[1] for k in ('SIDE_V', 'SIDE_A', 'OTHER')}
    # baseline ceiling: items whose RECODE joint already SIDE_V in both orders, etc.
    base_state = collections.Counter(rate(cells, uids, 'RECODE', 'SIDE_V'))
    res.update(stats=stats, order_effects=order, counts=counts, trajectory=traj, v_only_source_label_match=vonly,
               transitions_recode_to_L3_by_order=trans, paired_slot_transitions_292=gross,
               post_hoc_recording_group_cluster_ci_15_groups=post_hoc_group, groups_top_level=len(set(grp)),
               recode_side_v_item_rate_distribution={str(k): v for k, v in sorted(base_state.items())})
    return res, cells, uids


# ---------------------------------------------------------------- E2
def replay_e2(base, main, L):
    R = base / 'results/emotiontalk_e2_consistent_audio_v1'
    full = load(R / 'full_outcomes.csv'); man = load(R / 'manifest.csv'); att = load(R / 'attempts.csv')
    ref = json.loads((R / 'scientific_results.json').read_text())
    cells, uids = build(full, derive_e2)
    L.check('SOURCE_RESULT_LINKAGE', 'E2:3375_unique_slots', len(full) == 3375 == len({r['trial_id'] for r in full}) == len(cells))
    mi = {r['trial_id']: r for r in man}
    L.check('SOURCE_RESULT_LINKAGE', 'E2:manifest_fields_equal_full', all(all(mi[r['trial_id']][c] == r[c] for c in man[0]) for r in full))
    L.check('POINT_ESTIMATE_REPLAY', 'E2:outcome_rederived_from_labels', all(c['derived'] == c['outcome'] for c in cells.values()),
            collections.Counter((c['derived'], c['outcome']) for c in cells.values() if c['derived'] != c['outcome']))
    L.check('SOURCE_RESULT_LINKAGE', 'E2:consistent_yA_eq_yV', all(c['y_A'] == c['y_V'] for c in cells.values()))
    plan = json.loads((main / 'manifests/emotiontalk/EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json').read_text())['pairs']['AV']
    L.check('SOURCE_RESULT_LINKAGE', 'E2:uids_equal_main_consistent_plan', set(uids) == set(plan['consistent_utterance_ids']))
    sm = {r['utterance_id']: r for r in load(main / 'manifests/emotiontalk/source_measurements.csv')}
    bad = [u for u in uids if any(sm[u][k] != cells[u, 'A_RECODE', 'A_ONLY'][k] for k in ('y_A', 'y_V', 'y_T', 'candidate_sequence_id', 'candidate_sequence')) or sm[u]['DualReadable_AV'] != 'TRUE']
    L.check('SOURCE_RESULT_LINKAGE', 'E2:labels_order_dualreadable_equal_main', not bad, bad[:5])
    strata = collections.Counter(cells[u, 'A_RECODE', 'A_ONLY']['stratum'] for u in uids)
    L.check('SOURCE_RESULT_LINKAGE', 'E2:strata_127_98', strata == {'ALL_SAME': 127, 'A_EQ_V_NE_T': 98}, dict(strata))
    L.check('SOURCE_RESULT_LINKAGE', 'E2:ALL_SAME_iff_yA_eq_yT', all((cells[u, 'A_RECODE', 'A_ONLY']['stratum'] == 'ALL_SAME') == (cells[u, 'A_RECODE', 'A_ONLY']['y_A'] == cells[u, 'A_RECODE', 'A_ONLY']['y_T']) for u in uids))
    groups = [cells[u, 'A_RECODE', 'A_THEN_V']['dialogue_id'] for u in uids]
    L.check('SOURCE_RESULT_LINKAGE', 'E2:177_clusters_eq_uid_prefix', len(set(groups)) == 177 and all(g == '_'.join(u.split('_')[:2]) for u, g in zip(uids, groups)))
    per = collections.defaultdict(set)
    for c in cells.values():
        per[c['utterance_id'], 'video'].add(c['video_sha256']); per[c['utterance_id'], c['condition'], 'audio'].add(c['audio_sha256'])
    L.check('INPUT_CONTRACT_AUDIT', 'E2:video_sha_constant_across_all_conditions', all(len(v) == 1 for k, v in per.items() if k[1] == 'video'))
    L.check('INPUT_CONTRACT_AUDIT', 'E2:audio_sha_constant_within_condition', all(len(v) == 1 for k, v in per.items() if len(k) == 3))
    L.check('INPUT_CONTRACT_AUDIT', 'E2:five_distinct_audio_files_per_item', all(len({cells[u, c, 'A_ONLY']['audio_sha256'] for c in ('A_CLEAN', 'A_RECODE', 'A_SNR20', 'A_SNR10', 'A_SNR00')}) == 5 for u in uids))
    snr = {c: {cells[u, c, 'A_ONLY']['target_snr_db'] for u in uids} for c in ('A_CLEAN', 'A_RECODE', 'A_SNR20', 'A_SNR10', 'A_SNR00')}
    L.check('INPUT_CONTRACT_AUDIT', 'E2:target_snr_labels', snr == {'A_CLEAN': {''}, 'A_RECODE': {''}, 'A_SNR20': {'20'}, 'A_SNR10': {'10'}, 'A_SNR00': {'0'}}, {k: sorted(v) for k, v in snr.items()})
    seeds = {u: {cells[u, c, a]['noise_seed'] for c in ('A_CLEAN', 'A_RECODE', 'A_SNR20', 'A_SNR10', 'A_SNR00') for a in ('A_ONLY',) + ORD} for u in uids}
    L.check('INPUT_CONTRACT_AUDIT', 'E2:one_noise_seed_per_item_nested_design', all(len(v) == 1 for v in seeds.values()) and len({next(iter(v)) for v in seeds.values()}) == 225)
    try:
        sys.path.insert(0, str(main))
        from src.emotiontalk.reliability_v1 import design  # pure-python seed function on main (frozen commit identical)
        okseed = all(next(iter(seeds[u])) == str(design.derived_seed('E2_AV_CONSISTENT_AUDIO_DEGRADATION_CONTROL_V1', u, 'AUDIO_WHITE_NOISE_V1')) for u in uids)
        L.check('INPUT_CONTRACT_AUDIT', 'E2:noise_seed_equals_frozen_derivation', okseed)
        eri1 = {design.noise_seed(u) for u in plan['conflict_utterance_ids']}
        L.check('INPUT_CONTRACT_AUDIT', 'E2:noise_seeds_disjoint_from_ERI1', not ({int(next(iter(seeds[u]))) for u in uids} & eri1))
    except Exception as e:  # noqa: BLE001
        L.check('INPUT_CONTRACT_AUDIT', 'E2:noise_seed_equals_frozen_derivation', False, 'UNVERIFIED: ' + repr(e))

    t = 'SHARED_LABEL'; P = ref['primary']; S = {x['endpoint']: x for x in ref['secondary']}
    vec = {'PRIMARY': rate(cells, uids, 'A_SNR00', t) - rate(cells, uids, 'A_RECODE', t)}
    for k in ('OTHER', 'PARSE_FAIL', 'TECH_FAILURE'):
        vec[k + '_HIGH_MINUS_RECODE'] = rate(cells, uids, 'A_SNR00', k) - rate(cells, uids, 'A_RECODE', k)
    vec['CLEAN_MINUS_RECODE_PIPELINE'] = rate(cells, uids, 'A_CLEAN', t) - rate(cells, uids, 'A_RECODE', t)
    vec['ORDER_INTERACTION'] = np.array([(int(cells[u, 'A_SNR00', ORD[0]]['derived'] == t) - int(cells[u, 'A_RECODE', ORD[0]]['derived'] == t)) - (int(cells[u, 'A_SNR00', ORD[1]]['derived'] == t) - int(cells[u, 'A_RECODE', ORD[1]]['derived'] == t)) for u in uids])
    for c in ('A_SNR10', 'A_SNR20'):
        vec[c + '_MINUS_RECODE'] = rate(cells, uids, c, t) - rate(cells, uids, 'A_RECODE', t)
    Y = np.column_stack([rate(cells, uids, c, t) for c in ('A_RECODE', 'A_SNR20', 'A_SNR10', 'A_SNR00')])
    vec['ORDINAL_DOSE_RESPONSE'] = np.array([np.polyfit(np.arange(4.0), y, 1)[0] for y in Y])
    vec['UNIMODAL_SOURCE_LABEL_MATCH'] = np.array([float(cells[u, 'A_SNR00', 'A_ONLY']['parsed_label'] == cells[u, 'A_SNR00', 'A_ONLY']['y_A']) - float(cells[u, 'A_RECODE', 'A_ONLY']['parsed_label'] == cells[u, 'A_RECODE', 'A_ONLY']['y_A']) for u in uids])
    vec['UNIMODAL_ENTROPY'] = np.array([float(cells[u, 'A_SNR00', 'A_ONLY']['entropy_normalized']) - float(cells[u, 'A_RECODE', 'A_ONLY']['entropy_normalized']) for u in uids])
    stats = {'PRIMARY': endpoint_stats(L, 'E2:PRIMARY', vec['PRIMARY'], groups, P, int(P['seed']), 'estimate', 'item_ci95', 'two_sided_signflip_p')}
    ps = []
    for name, r in S.items():
        stats[name] = endpoint_stats(L, 'E2:' + name, vec[name], groups, r, int(r['seed']), 'estimate', 'item_ci95', 'two_sided_signflip_p'); ps.append(stats[name]['p_mc'])
    for (name, r), h in zip(S.items(), holm(ps)):
        L.close('BOOTSTRAP_REPLAY', 'E2:' + name + ':holm', h, r['holm_p'])
    L.check('POINT_ESTIMATE_REPLAY', 'E2:SHARED_plus_OTHER_complementary(no PF/TF)', bool(np.all(np.abs(vec['PRIMARY'] + vec['OTHER_HIGH_MINUS_RECODE']) < 1e-15)))
    counts = {c: {a: dict(collections.Counter(cells[u, c, a]['derived'] for u in uids)) for a in ('A_ONLY',) + ORD} for c in ('A_CLEAN', 'A_RECODE', 'A_SNR20', 'A_SNR10', 'A_SNR00')}
    traj = {c: float(rate(cells, uids, c, t).mean()) for c in ('A_CLEAN', 'A_RECODE', 'A_SNR20', 'A_SNR10', 'A_SNR00')}
    aonly = {c: sum(cells[u, c, 'A_ONLY']['parsed_label'] == cells[u, c, 'A_ONLY']['y_A'] for u in uids) / 225 for c in traj}
    strat = {}
    for s in ('ALL_SAME', 'A_EQ_V_NE_T'):
        idx = [i for i, u in enumerate(uids) if cells[u, 'A_RECODE', 'A_ONLY']['stratum'] == s]
        strat[s] = {'items': len(idx), 'effect': float(vec['PRIMARY'][idx].mean()), 'p_exact': exact_signflip(vec['PRIMARY'][idx])}
    # what do OTHER responses become? (label of OTHER under SNR00 relative to y_T)
    other = collections.Counter()
    for u in uids:
        for o in ORD:
            c = cells[u, 'A_SNR00', o]
            if c['derived'] == 'OTHER':
                other['equals_y_T' if c['parsed_label'] == c['y_T'] else 'not_y_T:' + c['parsed_label']] += 1
    trans = {o: dict(collections.Counter(f"{cells[u, 'A_RECODE', o]['derived']}->{cells[u, 'A_SNR00', o]['derived']}" for u in uids)) for o in ORD}
    bad_tr = 0
    for row in load(R / 'category_transitions.csv'):
        n = sum(cells[u, 'A_RECODE', row['arm']]['derived'] == row['from'] and cells[u, row['condition'], row['arm']]['derived'] == row['to'] and cells[u, 'A_RECODE', row['arm']]['parsed_label'] == row['from_label'] and cells[u, row['condition'], row['arm']]['parsed_label'] == row['to_label'] for u in uids)
        bad_tr += n != int(row['n'])
    L.check('POINT_ESTIMATE_REPLAY', 'E2:category_transitions_csv_rows', bad_tr == 0, bad_tr)
    grp = [u.split('_')[0] for u in uids]
    return {'items': len(uids), 'stats': stats, 'counts': counts, 'shared_retention_trajectory': traj, 'a_only_source_label_match': aonly,
            'strata': strat, 'snr00_other_labels': dict(other), 'transitions_recode_to_snr00': trans,
            'post_hoc_recording_group_cluster_ci_15_groups': alt_bootstrap(vec['PRIMARY'], grp, seed=4242)[1]}, cells, uids


# ---------------------------------------------------------------- candidate scoring audit
def scoring_audit(base, L, exp, cells):
    R = base / ('results/emotiontalk_e1_video_v2' if exp == 'E1' else 'results/emotiontalk_e2_consistent_audio_v1')
    rows = load(R / 'candidate_probabilities.csv'); by = collections.defaultdict(list)
    for r in rows:
        by[r['trial_id']].append(r)
    full = {c['trial_id']: c for c in cells.values()}
    expected = {t for t, c in full.items() if exp == 'E1' or c['arm'] == 'A_ONLY'}
    L.check('SCORING_AUDIT', exp + ':coverage', set(by) == expected, {'scored': len(by), 'expected': len(expected)})
    tokcount = collections.defaultdict(set); worst = 0.0; agree = collections.Counter(); srcp = collections.defaultdict(list)
    for tid, rs in by.items():
        c = full[tid]; labs = [r['label'] for r in rs]
        if set(labs) != set(c['candidate_sequence'].split('|')) or len(labs) != 7:
            L.check('SCORING_AUDIT', exp + ':label_set', False, tid)
        for r in rs:
            tokcount[r['label']].add(int(r['token_count']))
            worst = max(worst, abs(float(r['sum_log_probability']) / int(r['token_count']) - float(r['mean_token_log_probability'])))
        m = np.array([float(r['mean_token_log_probability']) for r in rs]); s = np.array([float(r['sum_log_probability']) for r in rs])
        pm = np.exp(m - m.max()); pm /= pm.sum(); psum = np.exp(s - s.max()); psum /= psum.sum()
        worst = max(worst, float(np.max(np.abs(pm - [float(r['probability_mean_score_primary']) for r in rs]))), float(np.max(np.abs(psum - [float(r['probability_sum_score_sensitivity']) for r in rs]))))
        h = float(-(pm[pm > 0] * np.log(pm[pm > 0])).sum() / math.log(7))
        worst = max(worst, abs(h - float(c['entropy_normalized'])))
        top = labs[int(np.argmax(pm))]
        agree[(c['condition'], c['arm'], top == c['parsed_label'])] += 1
        ref_label = c['y_V'] if (exp == 'E1' and c['arm'] != 'A_ONLY') else c['y_A']
        srcp[(c['condition'], c['arm'])].append(float(pm[labs.index(ref_label)]))
    L.check('SCORING_AUDIT', exp + ':softmax_mean_sum_entropy_recomputed', worst <= 1e-9, worst)
    L.check('SCORING_AUDIT', exp + ':label_token_count_invariant_across_trials', all(len(v) == 1 for v in tokcount.values()), {k: sorted(v) for k, v in tokcount.items()})
    rate = {}
    for (cond, arm, ok), n in agree.items():
        rate.setdefault(f'{cond}|{arm}', [0, 0]); rate[f'{cond}|{arm}'][0 if ok else 1] += n
    return {'token_counts': {k: sorted(v) for k, v in tokcount.items()},
            'greedy_vs_score_argmax_agree_disagree': rate,
            'mean_prob_reference_label': {f'{k[0]}|{k[1]}': float(np.mean(v)) for k, v in srcp.items()},
            'max_recompute_error': worst}


# ---------------------------------------------------------------- E1 visual input contract audit
def visual_audit(base, L, cells):
    rows = load(base / 'results/emotiontalk_e1_video_v2/visual_input_contract.csv')
    L.check('INPUT_CONTRACT_AUDIT', 'E1:visual_contract_730_rows', len(rows) == 730 and len({(r['utterance_id'], r['condition']) for r in rows}) == 730)
    by = collections.defaultdict(dict)
    for r in rows:
        by[r['utterance_id']][r['condition']] = r
    issues = collections.Counter(); out = {'sigma_model_px': collections.defaultdict(list), 'frames': collections.Counter(), 'nonmonotone': collections.Counter(), 'clean_eq_recode_frames': 0, 'clean_eq_recode_visual_tensor': 0}
    for u, cs in by.items():
        ref = cs['RECODE']; rp = json.loads(ref['processor_contract'])
        for cond, r in cs.items():
            pc = json.loads(r['processor_contract'])
            if r['video_sha256'] != cells[u, cond, 'V_ONLY']['video_sha256']:
                issues['video_sha_not_equal_manifest'] += 1
            for k in ('sampled_frame_indices', 'model_sampled_timestamps', 'model_frame_shape', 'sample_fps', 'duration', 'source_width', 'source_height', 'source_time_base'):
                if r[k] != ref[k]:
                    issues['sampling_field_differs:' + k] += 1
            for arm in ('V_ONLY', 'A_THEN_V', 'V_THEN_A'):
                for k in ('tokens', 'video_grid_thw', 'visual_tensor_shape'):
                    if pc[arm][k] != rp[arm][k]:
                        issues[f'processor_{k}_differs_from_RECODE'] += 1
                if pc[arm]['audio_input_count'] != (0 if arm == 'V_ONLY' else 1):
                    issues['audio_input_count'] += 1
            if len({pc[a]['visual_tensor_sha256'] for a in pc}) != 1:
                issues['visual_tensor_differs_between_arms_same_condition'] += 1
            frac = float(r['sigma_native_short_side_fraction']); w, h = int(r['source_width']), int(r['source_height'])
            if abs(float(r['sigma_native']) - frac * min(w, h)) > 1e-9:
                issues['sigma_not_fraction_times_short_side'] += 1
            if frac:
                shape = json.loads(r['model_frame_shape']); scale = min(shape[2], shape[3]) / min(w, h)
                out['sigma_model_px'][cond].append(float(r['sigma_native']) * scale)
                if r['model_frames_sha256'] == ref['model_frames_sha256']:
                    issues['blur_frames_identical_to_recode'] += 1
                if r['sharpness_proxy_nonmonotone'] == 'True':
                    out['nonmonotone'][cond] += 1
            out['frames'][len(json.loads(r['sampled_frame_indices']))] += 1
        out['clean_eq_recode_frames'] += cs['CLEAN']['model_frames_sha256'] == ref['model_frames_sha256']
        out['clean_eq_recode_visual_tensor'] += json.loads(cs['CLEAN']['processor_contract'])['V_ONLY']['visual_tensor_sha256'] == rp['V_ONLY']['visual_tensor_sha256']
        ts = json.loads(ref['model_sampled_timestamps']); dur = float(ref['duration'])
        if ts and (ts[-1] > dur + 1e-6 or ts[0] < 0):
            issues['timestamps_outside_duration'] += 1
    for k in ('video_sha_not_equal_manifest', 'processor_tokens_differs_from_RECODE', 'processor_video_grid_thw_differs_from_RECODE', 'processor_visual_tensor_shape_differs_from_RECODE', 'audio_input_count', 'visual_tensor_differs_between_arms_same_condition', 'sigma_not_fraction_times_short_side', 'blur_frames_identical_to_recode', 'timestamps_outside_duration'):
        L.check('INPUT_CONTRACT_AUDIT', 'E1:' + k + '==0', issues[k] == 0, issues[k])
    L.check('INPUT_CONTRACT_AUDIT', 'E1:sampling_fields_identical_across_5_conditions', not any(k.startswith('sampling_field') for k in issues), {k: v for k, v in issues.items() if k.startswith('sampling')})
    summ = {c: {'min': min(v), 'median': float(np.median(v)), 'max': max(v)} for c, v in out['sigma_model_px'].items()}
    geo = collections.Counter((r['source_width'], r['source_height'], r['model_frame_shape']) for r in rows if r['condition'] == 'RECODE')
    return {'issues': dict(issues), 'sigma_in_model_input_pixels': summ, 'frames_per_clip_distribution': dict(out['frames']),
            'sharpness_proxy_nonmonotone_by_condition': dict(out['nonmonotone']), 'clean_equals_recode_model_frames_items': out['clean_eq_recode_frames'],
            'clean_equals_recode_visual_tensor_items': out['clean_eq_recode_visual_tensor'], 'geometry_counts': {f'{k[0]}x{k[1]}->{k[2]}': v for k, v in geo.items()}}


def main():
    base, main_, outp = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    L = Ledger()
    e1, c1, _ = replay_e1(base, main_, L)
    e1['scoring'] = scoring_audit(base, L, 'E1', c1)
    e1['visual_contract'] = visual_audit(base, L, c1)
    e2, c2, _ = replay_e2(base, main_, L)
    e2['scoring'] = scoring_audit(base, L, 'E2', c2)
    layers = collections.defaultdict(lambda: collections.Counter())
    for x in L.items:
        layers[x['layer']][x['status']] += 1
    result = {'numpy': np.__version__, 'layers': {k: dict(v) for k, v in layers.items()}, 'failures': [x for x in L.items if x['status'] != 'PASS'],
              'E1': e1, 'E2': e2, 'checks': L.items}
    outp.write_text(json.dumps(result, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o)))
    print(json.dumps({'layers': result['layers'], 'n_fail': len(result['failures'])}, indent=1))
    for f in result['failures']:
        print('FAIL', f['check'], str(f['detail'])[:300])


if __name__ == '__main__':
    main()
