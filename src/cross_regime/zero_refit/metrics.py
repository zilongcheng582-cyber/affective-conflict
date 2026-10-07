"""Frozen equation, outcome accounting and metric helpers; no fitting entry point."""
import math
def finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False

def number(value):
    return float(value) if finite(value) else None

def truth(value):
    return str(value).strip().upper() in {'TRUE', '1', 'YES'}

def sigmoid(x):
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)

def resolve_side(row, route):
    if truth(row.get('technical_missing')) or not truth(row.get('observed_outcome_available')):
        return None
    if row.get('source_relation') != 'CONFLICT':
        return None
    observed = row.get('observed_outcome', '')
    if route == 'AT':
        if observed == 'SIDE_A': return 'SIDE_A'
        if observed == 'SIDE_T': return 'SIDE_T'
        return None
    if observed == 'SIDE_A': return 'SIDE_A'
    if observed == 'SIDE_V': return 'SIDE_V'
    a = row.get('modality1_source_label')
    v = row.get('modality2_source_label')
    if a and v and a != v and observed == a: return 'SIDE_A'
    if a and v and a != v and observed == v: return 'SIDE_V'
    return None

def accounting_class(row, route):
    if truth(row.get('technical_missing')):
        return 'TECHNICAL_MISSING'
    if row.get('source_relation') == 'SAME_LABEL':
        return 'SAME_LABEL_EXCLUDED'
    if not truth(row.get('observed_outcome_available')):
        return 'UNAVAILABLE_OUTCOME'
    if row.get('observed_outcome') == 'PARSE_FAIL':
        return 'PARSE_FAIL'
    side = resolve_side(row, route)
    if side:
        return 'RESOLVED_' + side
    return 'OTHER'

def z_features(row, scalers):
    out = {}
    for raw, key, zkey in [
        ('delta_source_label_probability_raw', 'source_probability', 'z_delta_source_label_probability'),
        ('delta_normalized_entropy_raw', 'normalized_entropy', 'z_delta_normalized_entropy'),
        ('delta_top1_top2_margin_raw', 'top1_top2_margin', 'z_delta_top1_top2_margin'),
    ]:
        value = number(row.get(raw))
        out[key] = None if value is None else (value - scalers[key][0]) / scalers[key][1]
        if out[key] is not None and row.get(zkey, '') not in {'', 'None', 'null'}:
            if not finite(row[zkey]) or abs(float(row[zkey]) - out[key]) > 1e-10:
                raise RuntimeError(f'frozen z-feature mismatch for {row.get("target_record_id")} {zkey}')
    return out

def prediction(row, route, kind, coeff, scalers):
    z = z_features(row, scalers)
    order = 1.0 if truth(row.get('FIRST_IS_MODALITY1')) else 0.0
    if kind == 'primary':
        if z['source_probability'] is None or z['normalized_entropy'] is None:
            return None
        c = coeff['primary']
        intercept = c['intercept_AT'] if route == 'AT' else c['intercept_AV']
        beta_order = c['beta_order_AT'] if route == 'AT' else c['beta_order_AV']
        return sigmoid(intercept + c['beta_sourceprob'] * z['source_probability'] + c['beta_entropy'] * z['normalized_entropy'] + beta_order * order)
    if z['top1_top2_margin'] is None or z['normalized_entropy'] is None:
        return None
    c = coeff['margin']
    intercept = c['intercept_AT'] if route == 'AT' else c['intercept_AV']
    beta_order = c['beta_order_AT'] if route == 'AT' else c['beta_order_AV']
    return sigmoid(intercept + c['beta_margin'] * z['top1_top2_margin'] + c['beta_entropy'] * z['normalized_entropy'] + beta_order * order)

def auc(y, p):
    pos = [(score, label) for score, label in zip(p, y) if label == 1]
    neg = [(score, label) for score, label in zip(p, y) if label == 0]
    if not pos or not neg: return None
    wins = 0.0
    for ps, _ in pos:
        for ns, _ in neg:
            wins += 1.0 if ps > ns else 0.5 if ps == ns else 0.0
    return wins / (len(pos) * len(neg))

def metrics(rows, preds, route):
    y, p = [], []
    for row in rows:
        side = resolve_side(row, route)
        key = row['target_record_id']
        if side is None or key not in preds or preds[key] is None:
            continue
        y.append(1 if side == 'SIDE_A' else 0)
        p.append(preds[key])
    if not y:
        return None, 0
    clipped = [min(max(x, 1e-12), 1.0 - 1e-12) for x in p]
    logloss = sum(-(yy * math.log(pp) + (1 - yy) * math.log(1 - pp)) for yy, pp in zip(y, clipped)) / len(y)
    brier = sum((pp - yy) ** 2 for yy, pp in zip(y, clipped)) / len(y)
    pred = [pp >= 0.5 for pp in clipped]
    pos = [pred[i] for i, yy in enumerate(y) if yy == 1]
    neg = [pred[i] for i, yy in enumerate(y) if yy == 0]
    balanced = (sum(pos) / len(pos) + sum(not x for x in neg) / len(neg)) / 2 if pos and neg else None
    return {'log_loss': logloss, 'balanced_accuracy': balanced, 'AUROC': auc(y, clipped), 'Brier_score': brier, 'threshold': 0.5}, len(y)

def population(rows, route, feature_kind, subset=lambda r: True):
    selected = [r for r in rows if subset(r) and r.get('source_relation') == 'CONFLICT']
    if feature_kind == 'primary':
        ready = [r for r in selected if finite(r.get('delta_source_label_probability_raw')) and finite(r.get('delta_normalized_entropy_raw'))]
    else:
        ready = [r for r in selected if finite(r.get('delta_top1_top2_margin_raw')) and finite(r.get('delta_normalized_entropy_raw'))]
    counts = {}
    for row in ready:
        cls = accounting_class(row, route)
        counts[cls] = counts.get(cls, 0) + 1
    resolved = counts.get('RESOLVED_SIDE_A', 0) + counts.get('RESOLVED_SIDE_T', 0) + counts.get('RESOLVED_SIDE_V', 0)
    other = counts.get('OTHER', 0)
    parse_fail = counts.get('PARSE_FAIL', 0)
    technical = counts.get('TECHNICAL_MISSING', 0)
    return {
        'planned_rows_in_route': len(rows), 'eligible_conflict_N': len(ready),
        'resolved_SIDE_N': resolved, 'resolved_SIDE_A_N': counts.get('RESOLVED_SIDE_A', 0),
        'resolved_SIDE_MODALITY2_N': counts.get('RESOLVED_SIDE_T', 0) + counts.get('RESOLVED_SIDE_V', 0),
        'OTHER_N': other, 'PARSE_FAIL_N': parse_fail, 'technical_missing_N': technical,
        'feature_missing_N': len(selected) - len(ready),
        'resolved_coverage': resolved / len(ready) if ready else None,
        'denominator_definition': 'CONFLICT rows with required frozen analysis features finite; technical missing remains in denominator',
    }

def full_accounting(rows, route):
    counts = {}
    for row in rows:
        cls = accounting_class(row, route)
        counts[cls] = counts.get(cls, 0) + 1
    return {
        'planned_rows': len(rows), 'source_relation_conflict': sum(r.get('source_relation') == 'CONFLICT' for r in rows),
        'same_label': sum(r.get('source_relation') == 'SAME_LABEL' for r in rows),
        'observed_outcome_available': sum(truth(r.get('observed_outcome_available')) for r in rows),
        'technical_missing': counts.get('TECHNICAL_MISSING', 0), 'OTHER': counts.get('OTHER', 0),
        'PARSE_FAIL': counts.get('PARSE_FAIL', 0), 'resolved_SIDE_A': counts.get('RESOLVED_SIDE_A', 0),
        'resolved_SIDE_MODALITY2': counts.get('RESOLVED_SIDE_T', 0) + counts.get('RESOLVED_SIDE_V', 0),
        'same_label_excluded': counts.get('SAME_LABEL_EXCLUDED', 0),
    }
