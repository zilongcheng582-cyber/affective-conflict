"""Independent PR4 review replay of 18 frozen Transfer route/baseline groups.
Read-only; numpy only; no fitting, no threshold change. Different algorithm from PR validator:
probabilities recomputed from frozen binding + corrected B3 measurements (not from prediction-file deltas),
AUROC by explicit pairwise comparison, compared against (a) main pre-PR ZERO_REFIT_BASELINE_COMPARISON_V1.csv
and (b) PR 04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv."""
import csv, json, sys, hashlib, collections
import numpy as np
root = sys.argv[1]
def rd(p): return list(csv.DictReader(open(f'{root}/{p}', newline='', encoding='utf-8-sig')))
preds = rd('results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv')
meas = rd('evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv')
binding = json.load(open(f'{root}/frozen/source_model/binding.json'))
base = json.load(open(f'{root}/results/post_audit/closure_v1/SOURCE_BASELINE_BINDING_V1.json'))
mainref = rd('results/post_audit/closure_v1/ZERO_REFIT_BASELINE_COMPARISON_V1.csv')
prref = rd('results/transfer_failure_integration_v1/04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv')
M = collections.defaultdict(list)
for m in meas: M[(m['dataset'], m['stable_dataset_id'], m['modality'])].append(m)
dup_meas = {k: len(v) for k, v in M.items() if len(v) > 1}
def f(x): return float('nan') if x in ('', 'None', 'nan') else float(x)
# --- recompute deltas from corrected measurements
feat_err = []; feat_missing = 0
for r in preds:
    ds = r['dataset']; sid = r['source_item_id']
    if ds == 'LISTEN':
        continue  # LISTEN ids handled below
    other = 'V' if ds == 'CA-MER' else 'T'
    a = M.get((ds, sid, 'A')); o = M.get((ds, sid, other))
    if not a or not o: feat_missing += 1; continue
    a, o = a[0], o[0]
    for col, key in [('delta_source_label_probability_raw', 'source_label_probability'), ('delta_normalized_entropy_raw', 'normalized_entropy'), ('delta_top1_top2_margin_raw', 'top1_top2_margin')]:
        x = f(r[col]); y = f(a[key]) - f(o[key])
        if np.isnan(x) and np.isnan(y): continue
        feat_err.append(abs(x - y) if not (np.isnan(x) or np.isnan(y)) else float('inf'))
def auroc_pairwise(y, p):
    y = np.asarray(y); p = np.asarray(p); pos = p[y == 1]; neg = p[y == 0]
    if len(pos) == 0 or len(neg) == 0: return float('nan')
    gt = (pos[:, None] > neg[None, :]).sum(); eq = (pos[:, None] == neg[None, :]).sum()
    return (gt + 0.5 * eq) / (len(pos) * len(neg))
def mets(y, p):
    y = np.asarray(y, float); p = np.clip(np.asarray(p, float), 1e-12, 1 - 1e-12)
    pred = p >= binding['threshold']
    tpr = pred[y == 1].mean(); tnr = (~pred[y == 0]).mean()
    return dict(AUROC=auroc_pairwise(y, p), balanced_accuracy=0.5 * (tpr + tnr),
                log_loss=float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()), Brier_score=float(((p - y) ** 2).mean()),
                n_pred_SIDE_A=int(pred.sum()), max_p=float(p.max()), min_p=float(p.min()))
def prob(r, model):
    pair = 'AV' if r['dataset'] == 'CA-MER' else 'AT'
    first = 1 if r['presentation_order'] in ('A_THEN_T', 'A_THEN_V', 'A_ONLY') else 0
    if model in base:
        c = base[model]['parameters']
        z = c['intercept_AT'] + (c.get('pair_AV', 0) if pair == 'AV' else 0) + c.get('FIRST_IS_MODALITY1', 0) * first
    else:
        mk = 'M3a' if model.endswith('M3a') else 'M3b'; c = binding['models'][mk]['parameter_values']; sc = binding['scalers']
        if mk == 'M3a': x = (f(r['delta_source_label_probability_raw']) - sc['source_probability']['mean']) / sc['source_probability']['sd']; b = c['delta_source_label_probability_per_SD']
        else: x = (f(r['delta_top1_top2_margin_raw']) - sc['top1_top2_margin']['mean']) / sc['top1_top2_margin']['sd']; b = c['delta_top1_top2_margin_per_SD']
        e = (f(r['delta_normalized_entropy_raw']) - sc['normalized_entropy']['mean']) / sc['normalized_entropy']['sd']
        z = c['intercept_AT'] + (c['pair_AV'] if pair == 'AV' else 0) + b * x + c['delta_normalized_entropy_per_SD'] * e + c['FIRST_IS_MODALITY1'] * first
    return 1 / (1 + np.exp(-z))
out = []; pred_err = []
for ref in prref:
    route, model = ref['route'], ref['source_model']
    role = 'LISTEN_AT_MARGIN_SENSITIVITY' if route.startswith('LISTEN') else route
    allrows = [r for r in preds if r['analysis_role'] == role and (route != 'LISTEN_3C_JOINT_ARBITRATION' or r['target_record_id'].startswith('3C_'))]
    conflict = [r for r in allrows if r['execution_accounting_class'] != 'SAME_LABEL_EXCLUDED']
    ev = [r for r in conflict if r['resolved_side'] in ('SIDE_A', 'SIDE_T', 'SIDE_V')]
    y = [1 if r['resolved_side'] == 'SIDE_A' else 0 for r in ev]
    p = [prob(r, model) for r in ev]
    if model.startswith('FROZEN'):
        pred_err += [abs(a - float(r['predicted_p_SIDE_A'])) for a, r in zip(p, ev)]
    m = mets(y, p)
    ident = hashlib.sha256('\n'.join(r['target_record_id'] for r in ev).encode()).hexdigest()
    mref = [x for x in mainref if x['evaluated_identity_sha256'] == ident and x['model'] == model]
    cnt = collections.Counter(r['execution_accounting_class'] for r in conflict)
    row = dict(route=route, model=model, N_planned=len(allrows), N_conflict=len(conflict), N_evaluated=len(ev), SIDE_A=sum(y), SIDE_other=len(y) - sum(y),
               OTHER=cnt['OTHER'], TECH_MISSING=cnt['TECHNICAL_MISSING'], coverage=len(ev) / len(conflict),
               clusters_conflict=len({r['source_item_id'] for r in conflict}), clusters_evaluated=len({r['source_item_id'] for r in ev}),
               identity_sha_matches_PR=ident == ref['evaluated_identity_sha256'], main_ref_rows=len(mref), **m)
    for k in ('AUROC', 'balanced_accuracy', 'log_loss', 'Brier_score'):
        row['abs_err_vs_PR_' + k] = abs(m[k] - float(ref[k]))
        row['abs_err_vs_MAIN_' + k] = abs(m[k] - float(mref[0][k])) if mref else None
    for k in ('N_planned', 'N_conflict', 'N_evaluated'):
        row['denominator_match_PR_' + k] = int(ref[k]) == row[k]
        if mref: row['denominator_match_MAIN_' + k] = int(mref[0][k]) == row[k]
    row['PR_N_clusters'] = int(ref['N_clusters']); row['MAIN_N_clusters'] = int(mref[0]['N_clusters']) if mref else None
    out.append(row)
summary = dict(groups=len(out), max_abs_err_vs_PR=max(max(r[k] for k in r if k.startswith('abs_err_vs_PR')) for r in out),
               max_abs_err_vs_MAIN=max(max(r[k] for k in r if k.startswith('abs_err_vs_MAIN') and r[k] is not None) for r in out),
               all_have_main_ref=all(r['main_ref_rows'] == 1 for r in out), all_identity_match=all(r['identity_sha_matches_PR'] for r in out),
               all_denominators_match=all(v for r in out for k, v in r.items() if k.startswith('denominator_match')),
               max_frozen_prediction_abs_err=max(pred_err), frozen_predictions_checked=len(pred_err),
               feature_delta_max_err_vs_corrected_B3=max(feat_err) if feat_err else None, feature_rows_checked=len(feat_err) // 3, feature_rows_missing_measurement=feat_missing,
               duplicate_measurement_keys=len(dup_meas), measurement_rows=len(meas), prediction_rows=len(preds),
               unique_prediction_keys=len({(r['analysis_role'], r['target_record_id']) for r in preds}))
json.dump(dict(summary=summary, groups=out), open(sys.argv[2], 'w'), indent=1, default=float)
print(json.dumps(summary, indent=1))
for r in out:
    print(f"{r['route']:38s} {r['model']:18s} N={r['N_evaluated']:5d}/{r['N_conflict']:5d} A={r['SIDE_A']:4d} AUROC={r['AUROC']:.4f} BA={r['balanced_accuracy']:.4f} LL={r['log_loss']:.4f} Brier={r['Brier_score']:.4f} predA={r['n_pred_SIDE_A']:4d} maxp={r['max_p']:.3f} cl_conf={r['clusters_conflict']} cl_eval={r['clusters_evaluated']} PRcl={r['PR_N_clusters']}")
