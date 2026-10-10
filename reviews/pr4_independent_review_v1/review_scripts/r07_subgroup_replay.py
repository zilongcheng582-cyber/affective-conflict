"""Independent recomputation of TRANSFER_FAILURE_SUBGROUPS point estimates from public linkage + frozen predictions."""
import csv, json, sys, collections
import numpy as np
root = sys.argv[1]
def rd(p): return list(csv.DictReader(open(f'{root}/{p}', newline='', encoding='utf-8-sig')))
P = rd('results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv')
L = {(r['dataset'], r['record_id']): r for r in rd('results/transfer_failure_integration_v1/phase4_numeric/TRANSFER_RECOVERED_ROW_LINKAGE.csv')}
S = rd('results/transfer_failure_integration_v1/phase4_numeric/TRANSFER_FAILURE_SUBGROUPS.csv')
meas = {(m['dataset'], m['stable_dataset_id'], m['modality']): m for m in rd('evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv')}
def auroc(y, p):
    y = np.array(y); p = np.array(p); a = p[y == 1]; b = p[y == 0]
    if not len(a) or not len(b): return None
    return float(((a[:, None] > b[None]).sum() + .5 * (a[:, None] == b[None]).sum()) / (len(a) * len(b)))
def ll(y, p):
    y = np.array(y, float); p = np.clip(np.array(p, float), 1e-12, 1 - 1e-12); return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()) if len(y) else None
spec = {'MCR_AT_PRIMARY': ('MCR_AT_PRIMARY', None), 'MCR_AT_MARGIN_SENSITIVITY': ('MCR_AT_MARGIN_SENSITIVITY', None),
        'LISTEN_ALL_MIXED_HISTORICAL': ('LISTEN_AT_MARGIN_SENSITIVITY', None), 'LISTEN_3C_JOINT_ARBITRATION': ('LISTEN_AT_MARGIN_SENSITIVITY', '3C_'),
        'CAMER_AV_SUPPORT_LIMITED_SOURCEPROB': ('CAMER_AV_SUPPORT_LIMITED_SOURCEPROB', None), 'CAMER_AV_MARGIN_SENSITIVITY': ('CAMER_AV_MARGIN_SENSITIVITY', None)}
def conflict(r):
    ds = r['dataset']; o = 'V' if ds == 'CA-MER' else 'T'
    if ds == 'LISTEN':
        return meas[(ds, r['source_item_id'], 'A')]['raw_source_label'] != meas[(ds, r['source_item_id'], 'T')]['raw_source_label']
    return meas[(ds, r['source_item_id'], 'A')]['raw_source_label'] != meas[(ds, r['source_item_id'], o)]['raw_source_label']
res = []; mism = []
for row in S:
    route, g = row['route'], row['group']; role, pre = spec[route]
    rows = [r for r in P if r['analysis_role'] == role and (pre is None or r['target_record_id'].startswith(pre))]
    conf = [r for r in rows if conflict(r)]
    def link(r): return L.get((r['dataset'], r['target_record_id']), {})
    if g == 'FULL_CONFLICT': part = conf
    elif g == 'BINARY_EVALUABLE': part = [r for r in conf if r['resolved_side']]
    elif g in ('DUAL_MATCH', 'A_ONLY_MATCH', 'T_ONLY_MATCH', 'V_ONLY_MATCH', 'NEITHER_MATCH', 'UNOBSERVABLE'): part = [r for r in conf if link(r).get('eligibility_group') == g]
    elif g == 'STRICT_DUAL_CONTENT_MATCH': part = [r for r in conf if link(r).get('eligibility_group') == 'DUAL_MATCH' and link(r).get('strict_content_support') == 'True']
    elif g.startswith('B3_ONTOLOGY_'): part = [r for r in conf if link(r).get('ontology_supported', None) == g.split('_')[-1]] if any(link(r) for r in conf) else None
    elif g.startswith('ORDER_'): part = [r for r in conf if r['presentation_order'] == g[6:]]
    elif g.startswith('A_SOURCE_'): part = [r for r in conf if meas[(r['dataset'], r['source_item_id'], 'A')]['raw_source_label'] == g[9:]]
    elif g.startswith('CONSTRUCT_'):
        sub = g[10:]; dual = sub.endswith('_DUAL'); sub = sub[:-5] if dual else sub
        part = [r for r in conf if link(r).get('subset') == sub and (not dual or link(r).get('eligibility_group') == 'DUAL_MATCH')]
    else: part = None
    if part is None: res.append((route, g, 'NOT_RECOMPUTED')); continue
    ev = [r for r in part if r['resolved_side']]
    y = [int(r['resolved_side'] == 'SIDE_A') for r in ev]; p = [float(r['predicted_p_SIDE_A']) for r in ev]
    a = auroc(y, p); l = ll(y, p)
    ok = len(part) == int(row['conflict']) and len(ev) == int(row['evaluated']) and sum(y) == int(row['SIDE_A']) \
        and ((a is None and row['AUROC'] == '') or (a is not None and row['AUROC'] != '' and abs(a - float(row['AUROC'])) < 1e-12)) \
        and ((l is None and row['log_loss'] == '') or (l is not None and abs(l - float(row['log_loss'])) < 1e-12))
    res.append((route, g, 'MATCH' if ok else 'MISMATCH'))
    if not ok: mism.append(dict(route=route, group=g, mine=(len(part), len(ev), sum(y), a, l), pr=(row['conflict'], row['evaluated'], row['SIDE_A'], row['AUROC'], row['log_loss'])))
c = collections.Counter(x[2] for x in res)
json.dump(dict(counts=c, mismatches=mism, rows=res), open(sys.argv[2], 'w'), indent=1)
print(c); [print(m) for m in mism]
print([x for x in res if x[2] == 'NOT_RECOMPUTED'])
