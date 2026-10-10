import csv, json, sys, collections
root = sys.argv[1]
def rd(p): return list(csv.DictReader(open(f'{root}/{p}', newline='', encoding='utf-8-sig')))
K = rd('results/historical_evidence_reconciliation_v2/CAMER_6000_KEY_RECONCILIATION_V2.public_projection.csv')
E = rd('results/recovered_evidence_scientific_analysis_v1/intermediate/CAMER_ITEM_ELIGIBILITY_IDENTITY.csv')
o = {}
o['rows'] = len(K); o['unique_keys'] = len({(r['sample_id'], r['arm']) for r in K}); o['items'] = len({r['sample_id'] for r in K})
o['arms'] = dict(collections.Counter(r['arm'] for r in K))
o['accounting'] = dict(collections.Counter(r['arm'] + '|' + r['accounting_class'] + '|' + r['scientific_available'] + '|' + r['parse_status'] for r in K))
o['scientific_available_true'] = sum(r['scientific_available'].lower() == 'true' for r in K)
o['available_but_parse_not_ok'] = sum(r['scientific_available'].lower() == 'true' and r['parse_status'] != 'OK' for r in K)
o['available_without_label'] = sum(r['scientific_available'].lower() == 'true' and not r['parsed_label'] for r in K)
o['raw_run_type'] = dict(collections.Counter(r['raw_run_type'] + '|' + r['raw_scientific_result'] + '|' + r['scientific_available'] for r in K))
# eligibility recompute
km = {(r['sample_id'], r['arm']): r for r in K}
mism = []; groups = collections.Counter()
for e in E:
    s = e['sample_id']; a = km[(s, 'A_ONLY')]; v = km[(s, 'V_ONLY')]
    obsA = a['scientific_available'].lower() == 'true'; obsV = v['scientific_available'].lower() == 'true'
    mA = obsA and a['parsed_label'] == e['y_A']; mV = obsV and v['parsed_label'] == e['y_V']
    g = 'UNOBSERVABLE' if not (obsA and obsV) else 'DUAL_MATCH' if mA and mV else 'A_ONLY_MATCH' if mA else 'V_ONLY_MATCH' if mV else 'NEITHER_MATCH'
    if g != e['eligibility_group']:
        mism.append((s, g, e['eligibility_group'], obsA, obsV, mA, mV))
    groups[(e['conflict'], e['eligibility_group'])] += 1
    for arm in ['A_THEN_V', 'V_THEN_A']:
        j = km[(s, arm)]
        if j['scientific_available'].lower() != 'true': exp = 'TECH_MISSING' if j['parse_status'] in ('', 'NOT_RUN', 'OOM') or j['generation_status'] != 'SUCCESS' else 'PARSE_FAIL'
        elif e['y_A'] == e['y_V']: exp = 'SAME_LABEL_MATCH' if j['parsed_label'] == e['y_A'] else 'OTHER'
        else: exp = 'SIDE_A' if j['parsed_label'] == e['y_A'] else 'SIDE_V' if j['parsed_label'] == e['y_V'] else 'OTHER'
        if exp != e[arm] and not (exp in ('TECH_MISSING', 'PARSE_FAIL') and e[arm] in ('TECH_MISSING', 'PARSE_FAIL')):
            mism.append((s, arm, exp, e[arm], j['accounting_class'], j['parse_status']))
o['eligibility_mismatches'] = len(mism); o['eligibility_mismatch_examples'] = mism[:10]
o['groups_by_conflict'] = {f'{k[0]}|{k[1]}': v for k, v in sorted(groups.items())}
o['subset_by_conflict'] = dict(collections.Counter(e['subset'] + '|' + e['conflict'] for e in E))
o['joint_outcome_classes'] = dict(collections.Counter(e[a] for e in E for a in ['A_THEN_V', 'V_THEN_A']))
o['label_spaces'] = {'y_A': len({e['y_A'] for e in E}), 'y_V': len({e['y_V'] for e in E}), 'candidate_len': dict(collections.Counter(len(json.loads(e['candidate_sequence'])) for e in E))}
# conflict flag consistency
o['conflict_flag_inconsistent'] = sum((e['y_A'] != e['y_V']) != (e['conflict'] == 'True') for e in E)
o['label_case_variants'] = sorted({e['y_A'] for e in E} | {e['y_V'] for e in E})
print(json.dumps(o, indent=1, default=str)); json.dump(o, open(sys.argv[2], 'w'), indent=1, default=str)
