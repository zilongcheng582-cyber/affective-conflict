import csv, json, sys, collections
root = sys.argv[1]
def rd(p): return list(csv.DictReader(open(f'{root}/{p}', newline='', encoding='utf-8-sig')))
H = 'results/historical_evidence_reconciliation_v2/'; S = 'results/recovered_evidence_scientific_analysis_v1/'
P = rd(H + 'MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.public_projection.csv')
I = rd(H + 'MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.public_projection.csv')
ITEM = rd(S + 'intermediate/MCR_ITEM_IDENTITY_OUTCOMES.csv')
J = rd(S + 'intermediate/MCR_NATIVE_CONTROLLED_PER_ITEM_JOIN.csv')
LABS = ['sad', 'happy', 'fearful', 'angry', 'surprised', 'disgusted', 'neutral']
out = {}
keys = collections.Counter((r['source_index'], r['condition']) for r in P)
per = collections.defaultdict(set); aud = collections.defaultdict(set); gt = collections.defaultdict(set)
for r in P: per[r['source_index']].add(r['condition']); aud[r['source_index']].add(r['audio_sha256']); gt[r['source_index']].add(r['gt'])
out['rows'] = len(P); out['unique_keys'] = len(keys); out['dup_keys'] = sum(v > 1 for v in keys.values())
out['items'] = len(per); out['items_with_all_4_conditions'] = sum(v == {'neutral', 'faithful', 'adversarial', 'irrelevant'} for v in per.values())
out['items_audio_consistent'] = sum(len(v) == 1 for v in aud.values()); out['items_gt_consistent'] = sum(len(v) == 1 for v in gt.values())
out['parse_status'] = dict(collections.Counter(r['condition']+'|'+r['parse_status'] for r in P))
out['parse_ok_label_outside_7'] = sum(r['parse_status'] == 'PARSE_OK' and r['parsed_label'] not in LABS for r in P)
out['parse_fail_with_label'] = sum(r['parse_status'] != 'PARSE_OK' and r['parsed_label'] != '' for r in P)
out['controlled_member_rows'] = collections.Counter(r['controlled_population_member'] for r in P)
# hashes
hashes = {r['source_index']: r['audio_sha256'] for r in P}
hg = collections.defaultdict(set); hitems = collections.Counter(hashes.values())
gtmap = {r['source_index']: r['gt'] for r in P}
for i, h in hashes.items(): hg[h].add(gtmap[i])
ctrl = {r['source_index'] for r in I if r['controlled_included'] == 'True'}
out['native_unique_audio'] = len(hg); out['native_duplicate_hash_groups'] = sum(v > 1 for v in hitems.values())
out['conflicting_gt_hash_groups'] = sum(len(v) > 1 for v in hg.values())
out['controlled_items'] = len(ctrl); out['controlled_unique_audio'] = len({hashes[i] for i in ctrl})
ch = collections.Counter(hashes[i] for i in ctrl)
out['controlled_dup_hash_groups'] = {h[:12]: (n, sorted(hg[h])) for h, n in ch.items() if n > 1}
# identity join checks
out['identity_rows'] = len(I); out['identity_controlled_ids_unique'] = len({r['controlled_sample_id'] for r in I if r['controlled_included'] == 'True'})
out['identity_audio_equal'] = sum(r['native_audio_sha256'] == r['controlled_audio_sha256'] for r in I if r['controlled_included'] == 'True')
out['identity_match_flag_false_in_controlled'] = sum(r['source_index_path_hash_label_match'] != 'True' for r in I if r['controlled_included'] == 'True')
# would a pure audio-SHA join be many-to-many?
byhash = collections.defaultdict(list)
for r in I:
    if r['controlled_included'] == 'True': byhash[r['controlled_audio_sha256']].append(r['controlled_sample_id'])
out['audio_sha_join_ambiguous_hashes'] = {h[:12]: v for h, v in byhash.items() if len(v) > 1}
# outcome claims
it = {r['source_index']: r for r in ITEM}
out['item_rows'] = len(ITEM)
out['native_adv_follows_text_1000'] = sum(r['adversarial'] == r['y_text_adversarial'] for r in ITEM)
out['native_faithful_audio_1000'] = sum(r['faithful'] == r['gt'] for r in ITEM)
out['native_adv_audio_1000'] = sum(r['adversarial'] == r['gt'] for r in ITEM)
out['y_text_equals_gt'] = sum(r['y_text_adversarial'] == r['gt'] for r in ITEM)
# cross-check projection vs item table
mism = 0
for r in P:
    v = it[r['source_index']][r['condition']]
    exp = r['parsed_label'] if r['parse_status'] == 'PARSE_OK' else 'PARSE_FAIL'
    mism += v != exp
out['item_table_vs_projection_mismatch'] = mism
out['join_rows'] = len(J)
out['ctrl_T_ONLY_text_909'] = sum(r['controlled_T_ONLY'] == r['y_text_adversarial'] for r in J)
out['native_adv_text_909'] = sum(r['adversarial'] == r['y_text_adversarial'] for r in J)
out['native_adv_audio_909'] = sum(r['adversarial'] == r['gt'] for r in J)
out['ctrl_A_ONLY_audio_909'] = sum(r['controlled_A_ONLY'] == r['gt'] for r in J)
out['dual_match_items_909'] = sum(r['controlled_A_ONLY'] == r['gt'] and r['controlled_T_ONLY'] == r['y_text_adversarial'] for r in J)
for c in ['neutral', 'faithful', 'adversarial', 'irrelevant']:
    out['audio_match_' + c] = sum(r[c] == r['gt'] for r in ITEM); out['parsefail_' + c] = sum(r[c] == 'PARSE_FAIL' for r in ITEM)
print(json.dumps(out, indent=1, default=str)); json.dump(out, open(sys.argv[2], 'w'), indent=1, default=str)
