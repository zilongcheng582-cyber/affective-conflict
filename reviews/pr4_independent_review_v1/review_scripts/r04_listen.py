import csv, json, sys, collections
root = sys.argv[1]
def rd(p): return list(csv.DictReader(open(f'{root}/{p}', newline='', encoding='utf-8-sig')))
H = 'results/historical_evidence_reconciliation_v2/'
o = {}
for v in ['V3', 'V4']:
    R = rd(H + f'LISTEN_{v}_ANSWER_OPTION_RECOVERY_V2.public_projection.csv')
    o[v] = dict(rows=len(R), unique_keys=len({r['key'] for r in R}), conditions=dict(collections.Counter(r['condition'] for r in R)),
                outcome=dict(collections.Counter(r['condition'] + '|' + r['outcome_class_against_V4_labels'] for r in R)),
                parsed_not_in_candidates=sum(1 for r in R if r['parsed_label_recovered'] and r['parsed_label_recovered'] not in json.loads(r['candidate_sequence'])),
                letter_map_inconsistent=sum(1 for r in R if r['parsed_letter'] and json.loads(r['candidate_letter_map']).get(r['parsed_letter']) != r['parsed_label_recovered']),
                empty_parse=sum(1 for r in R if not r['parsed_label_recovered']),
                n_candidates=dict(collections.Counter(len(json.loads(r['candidate_sequence'])) for r in R)),
                prompt_hashes=len({r['prompt_hash'] for r in R}),
                correct_flag_inconsistent=sum((r['parsed_label_recovered'] == r['expected_label']) != (r['source_label_correct'] == 'True') for r in R))
V3 = {r['key']: r for r in rd(H + 'LISTEN_V3_ANSWER_OPTION_RECOVERY_V2.public_projection.csv')}
V4 = {r['key']: r for r in rd(H + 'LISTEN_V4_ANSWER_OPTION_RECOVERY_V2.public_projection.csv')}
o['v3v4_same_keys'] = set(V3) == set(V4)
o['v3v4_same_audio_text_sha'] = sum(V3[k]['audio_sha256'] == V4[k]['audio_sha256'] and V3[k]['text_sha256'] == V4[k]['text_sha256'] for k in V3)
o['v3v4_same_candidate_seq'] = sum(V3[k]['candidate_sequence'] == V4[k]['candidate_sequence'] for k in V3)
o['v3v4_same_candidate_set'] = sum(sorted(json.loads(V3[k]['candidate_sequence'])) == sorted(json.loads(V4[k]['candidate_sequence'])) for k in V3)
o['v3v4_same_label'] = sum(V3[k]['parsed_label_recovered'] == V4[k]['parsed_label_recovered'] for k in V3)
J = rd(H + 'LISTEN_V3_V4_STRICT_IDENTITY_JOIN_V2.csv')
o['join'] = dict(rows=len(J), strict=sum(r['strict_source_content_match'] == 'True' for r in J), cand_eq=sum(r['candidate_sequence_equal'] == 'True' for r in J), prompt_eq=sum(r['prompt_hash_equal'] == 'True' for r in J), pooling=dict(collections.Counter(r['scientific_pooling_allowed'] for r in J)))
D = rd('results/recovered_evidence_scientific_analysis_v1/03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.public_projection.csv')
c = [r for r in D if r['conflict'] == 'True']
o['3C'] = dict(rows=len(D), conflict=len(c), outcomes=dict(collections.Counter(r['joint_outcome'] for r in c)),
               groups=dict(collections.Counter(r['eligibility_group'] for r in c)), common_support=sum(r['common_input_support'] == 'True' for r in c),
               dual=len([r for r in c if r['eligibility_group'] == 'DUAL_MATCH']), dual_yA=dict(collections.Counter(r['y_A'] for r in c if r['eligibility_group'] == 'DUAL_MATCH')),
               dual_strict=sum(r['eligibility_group'] == 'DUAL_MATCH' and r['strict_both_content_support'] == 'True' for r in c),
               OTHER_label_is_source=sum(r['joint_outcome'] == 'OTHER' and r['joint_label'] in (r['y_A'], r['y_T']) for r in c),
               OTHER_labels=dict(collections.Counter(r['joint_label'] for r in c if r['joint_outcome'] == 'OTHER').most_common(12)),
               source_in_options=sum(r['source_A_in_options'] == 'True' and r['source_T_in_options'] == 'True' for r in c),
               outcome_recompute_mismatch=sum((('SIDE_A' if r['joint_label'] == r['y_A'] else 'SIDE_T' if r['joint_label'] == r['y_T'] else 'OTHER') != r['joint_outcome']) for r in c),
               match_vs_group_mismatch=sum(((('DUAL_MATCH' if r['match_A'] == 'True' and r['match_T'] == 'True' else 'A_ONLY_MATCH' if r['match_A'] == 'True' else 'T_ONLY_MATCH' if r['match_T'] == 'True' else 'NEITHER_MATCH') if r['common_input_support'] == 'True' else 'UNOBSERVABLE') != r['eligibility_group']) for r in c),
               v4_join=sum(V4[r['joint_key']]['parsed_label_recovered'] == r['joint_label'] for r in D))
U = rd(H + 'LISTEN_UNIMODAL_CORRECTNESS_JOIN_V2.csv')
o['unimodal_join'] = dict(rows=len(U), by_version=dict(collections.Counter(r['version'] for r in U)), eligibility=dict(collections.Counter(r['version'] + '|' + r['actual_joint_eligibility'] for r in U)))
print(json.dumps(o, indent=1)); json.dump(o, open(sys.argv[2], 'w'), indent=1)
