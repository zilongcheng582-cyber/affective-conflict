"""Recompute specific numbers cited in 04_TRANSFER_FAILURE_DECOMPOSITION.md from public frozen predictions + linkage."""
import csv, json, sys, math
import numpy as np
root = sys.argv[1]
def rd(p): return list(csv.DictReader(open(f'{root}/{p}', newline='', encoding='utf-8-sig')))
P = rd('results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv')
L = {r['record_id']: r for r in rd('results/transfer_failure_integration_v1/phase4_numeric/TRANSFER_RECOVERED_ROW_LINKAGE.csv')}
b = json.load(open(f'{root}/frozen/source_model/binding.json')); sc = b['scalers']; c = b['models']['M3a']['parameter_values']
def auc(y, p):
    y = np.array(y); p = np.array(p, float); a = p[y == 1]; z = p[y == 0]
    return float(((a[:, None] > z[None]).sum() + .5 * (a[:, None] == z[None]).sum()) / (len(a) * len(z)))
def ev(role, pred=lambda r: True): return [r for r in P if r['analysis_role'] == role and r['resolved_side'] and pred(r)]
out = {}
m = ev('MCR_AT_PRIMARY'); y = [r['resolved_side'] == 'SIDE_A' for r in m]; p = [float(r['predicted_p_SIDE_A']) for r in m]
out['MCR_prevalence'] = sum(y) / len(y); out['MCR_M3a_max_median_mean_p'] = (max(p), float(np.median(p)), float(np.mean(p)))
prev = sum(y) / len(y); out['MCR_oracle_LL'] = -(prev * math.log(prev) + (1 - prev) * math.log(1 - prev))
for o in ['A_THEN_T', 'T_THEN_A']:
    s = [(yy, pp) for yy, pp, r in zip(y, p, m) if r['presentation_order'] == o]
    out[f'MCR_{o}'] = (len(s), sum(a for a, _ in s), auc([a for a, _ in s], [q for _, q in s]))
dh = [float(r['delta_normalized_entropy_raw']) for r in m]
out['MCR_neg_deltaH7_AUROC'] = auc(y, [-v for v in dh]); out['MCR_mean_deltaH7'] = float(np.mean(dh))
terms = dict(intercept=c['intercept_AT'],
             sourceprob=float(np.mean([c['delta_source_label_probability_per_SD'] * (float(r['delta_source_label_probability_raw']) - sc['source_probability']['mean']) / sc['source_probability']['sd'] for r in m])),
             H7=float(np.mean([c['delta_normalized_entropy_per_SD'] * (v - sc['normalized_entropy']['mean']) / sc['normalized_entropy']['sd'] for v in dh])),
             order=float(np.mean([c['FIRST_IS_MODALITY1'] * (r['presentation_order'] == 'A_THEN_T') for r in m])))
out['MCR_M3a_mean_logit_terms'] = terms
l = ev('LISTEN_AT_MARGIN_SENSITIVITY', lambda r: r['target_record_id'].startswith('3C_')); y = [r['resolved_side'] == 'SIDE_A' for r in l]; p = [float(r['predicted_p_SIDE_A']) for r in l]
prev = sum(y) / len(y); out['LISTEN3C_oracle_LL'] = -(prev * math.log(prev) + (1 - prev) * math.log(1 - prev)); out['LISTEN3C_mean_p'] = float(np.mean(p))
pr = [q >= .5 for q in p]; out['LISTEN3C_TP_FP_FN_TN'] = (sum(a and b_ for a, b_ in zip(y, pr)), sum((not a) and b_ for a, b_ in zip(y, pr)), sum(a and not b_ for a, b_ in zip(y, pr)), sum((not a) and not b_ for a, b_ in zip(y, pr)))
sup = {r['source_item_id'] for r in P if r['analysis_role'] == 'CAMER_AV_SUPPORT_LIMITED_SOURCEPROB'}
cm = ev('CAMER_AV_MARGIN_SENSITIVITY')
for name, sel in [('supported', lambda r: r['source_item_id'] in sup), ('outside', lambda r: r['source_item_id'] not in sup),
                  ('audio-aligned', lambda r: L[r['target_record_id']]['subset'] == 'audio-aligned'), ('video-aligned', lambda r: L[r['target_record_id']]['subset'] == 'video-aligned'),
                  ('audio-aligned_dual', lambda r: L[r['target_record_id']]['subset'] == 'audio-aligned' and L[r['target_record_id']]['eligibility_group'] == 'DUAL_MATCH'),
                  ('video-aligned_dual', lambda r: L[r['target_record_id']]['subset'] == 'video-aligned' and L[r['target_record_id']]['eligibility_group'] == 'DUAL_MATCH')]:
    s = [r for r in cm if sel(r)]; yy = [r['resolved_side'] == 'SIDE_A' for r in s]
    out['CAMER_margin_' + name] = (len(s), auc(yy, [float(r['predicted_p_SIDE_A']) for r in s]), sum(yy) / len(yy))
print(json.dumps(out, indent=1)); json.dump(out, open(sys.argv[2], 'w'), indent=1)
