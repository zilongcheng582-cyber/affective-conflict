"""Pre-declaration sensitivity and cross-experiment consistency (CPU, exploratory, no new inference).

1. Counterfactual: analyse the E1 V2 data under the ORIGINAL E1 V1 plan written in
   analyses/emotiontalk_e2_consistent_audio_v1/source_archive/e1e2_pipeline.py::freeze and e1e2_analysis.py
   (single primary SIDE_V; secondary Holm family of 11; joint E1+ERI1 Holm rule). Exact sign-flip p only.
   Purpose: show which E1 conclusions depend on the V1 -> V2 endpoint amendment.
2. Item-level reproduction: E1 V2 CLEAN joint/unimodal labels vs ERI1 CLEAN labels on main (same 146 items,
   same original media, same frozen model/code) - an independent reproducibility check of the pipeline.
Usage: python -I predeclaration_sensitivity.py <pr6_checkout> <main_checkout> <out_json>
"""
import csv, json, sys, pathlib, importlib.util, collections
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ir', HERE / 'independent_replay.py'); IR = importlib.util.module_from_spec(spec); spec.loader.exec_module(IR)
PR6, MAIN, OUT = map(pathlib.Path, sys.argv[1:4])
full = IR.load(PR6 / 'results/emotiontalk_e1_video_v2/full_outcomes.csv')
cells, uids = IR.build(full, IR.derive_e1)
O = IR.ORD


def rate(c, k):
    return IR.rate(cells, uids, c, k)


# ---- 1. V1 plan on V2 data (V1 condition names V_RECODE/V_BLUR_LOW/MED/HIGH map to RECODE/BLUR_L1/L2/L3)
prim = rate('BLUR_L3', 'SIDE_V') - rate('RECODE', 'SIDE_V')
sec = {}
for k in ('SIDE_A', 'OTHER', 'PARSE_FAIL', 'TECHNICAL_FAILURE'):
    sec[k + '_HIGH_MINUS_RECODE'] = rate('BLUR_L3', k) - rate('RECODE', k)
sec['CLEAN_MINUS_RECODE_PIPELINE'] = rate('CLEAN', 'SIDE_V') - rate('RECODE', 'SIDE_V')
sec['ORDER_INTERACTION'] = np.array([(int(cells[u, 'BLUR_L3', O[0]]['derived'] == 'SIDE_V') - int(cells[u, 'RECODE', O[0]]['derived'] == 'SIDE_V')) - (int(cells[u, 'BLUR_L3', O[1]]['derived'] == 'SIDE_V') - int(cells[u, 'RECODE', O[1]]['derived'] == 'SIDE_V')) for u in uids])
for c in ('BLUR_L1', 'BLUR_L2'):
    sec[c + '_MINUS_RECODE'] = rate(c, 'SIDE_V') - rate('RECODE', 'SIDE_V')
Y = np.column_stack([rate(c, 'SIDE_V') for c in ('RECODE', 'BLUR_L1', 'BLUR_L2', 'BLUR_L3')])
sec['ORDINAL_DOSE_RESPONSE'] = np.array([np.polyfit(np.arange(4.0), y, 1)[0] for y in Y])
sec['UNIMODAL_SOURCE_LABEL_MATCH'] = np.array([int(cells[u, 'BLUR_L3', 'V_ONLY']['parsed_label'] == cells[u, 'BLUR_L3', 'V_ONLY']['y_V']) - int(cells[u, 'RECODE', 'V_ONLY']['parsed_label'] == cells[u, 'RECODE', 'V_ONLY']['y_V']) for u in uids])
ent = np.array([float(cells[u, 'BLUR_L3', 'V_ONLY']['entropy_normalized']) - float(cells[u, 'RECODE', 'V_ONLY']['entropy_normalized']) for u in uids])
groups = [cells[u, 'RECODE', 'A_THEN_V']['dialogue_id'] for u in uids]
ent_p = IR.contract_signflip(ent, 99)       # continuous; Monte Carlo with an unrelated seed
ps = {k: IR.exact_signflip(v) for k, v in sec.items()}; ps['UNIMODAL_ENTROPY(MC)'] = ent_p
names = list(ps); hol = dict(zip(names, IR.holm([ps[n] for n in names])))
eri1 = {r['endpoint']: r for r in IR.load(MAIN / 'results/eri1_scientific_closure_v1/ERI1_PRIMARY_RESULTS_V1.csv')}
eri1_p = float(eri1['PRIMARY_dSIDE_A_SNR00_minus_RECODE']['p_raw'])
p_prim = IR.exact_signflip(prim)
joint = dict(zip(['E1_SIDE_V_primary', 'ERI1_SIDE_A_primary'], IR.holm([p_prim, eri1_p])))
v1 = {'primary_SIDE_V': {'effect': float(prim.mean()), 'p_exact': p_prim},
      'secondary_family_size': len(names),
      'secondary': {n: {'effect': float((sec[n] if n in sec else ent).mean()), 'p': ps[n], 'p_holm': hol[n]} for n in names},
      'joint_E1_plus_ERI1_holm': joint, 'ERI1_primary_p_raw_from_main': eri1_p}
# V2 plan for contrast
v2 = {k: IR.exact_signflip(rate('BLUR_L3', k) - rate('RECODE', k)) for k in ('SIDE_V', 'SIDE_A', 'OTHER')}
v2h = dict(zip(v2, IR.holm(list(v2.values()))))

# ---- 2. E1 V2 CLEAN vs ERI1 CLEAN, item level
eri = IR.load(MAIN / 'results/eri1_scientific_closure_v1/ERI1_SCIENTIFIC_TRIAL_PROJECTION_V1.csv')
ec = {(r['item_id'], r['order_or_arm']): r['parsed_emotion_label'] for r in eri if r['condition'] == 'CLEAN'}
match = collections.Counter(); mism = []
for u in uids:
    for arm in ('A_ONLY', 'V_ONLY', 'A_THEN_V', 'V_THEN_A'):
        if (u, arm) in ec:
            ok = ec[u, arm] == cells[u, 'CLEAN', arm]['parsed_label']; match[arm, ok] += 1
            if not ok:
                mism.append((u, arm, ec[u, arm], cells[u, 'CLEAN', arm]['parsed_label']))
# same check against ERI1 RECODE (different audio pipeline) for joint arms -> expected to differ sometimes
er = {(r['item_id'], r['order_or_arm']): r['parsed_emotion_label'] for r in eri if r['condition'] == 'RECODE'}
rmatch = collections.Counter((arm, er[u, arm] == cells[u, 'RECODE', arm]['parsed_label']) for u in uids for arm in ('A_THEN_V', 'V_THEN_A') if (u, arm) in er)
res = {'V1_plan_on_V2_data': v1, 'V2_plan_exact': {'p': v2, 'p_holm': v2h},
       'E1V2_CLEAN_vs_ERI1_CLEAN_item_label_agreement': {f'{a}|{ok}': n for (a, ok), n in sorted(match.items())}, 'mismatches': mism,
       'E1V2_RECODE(video recode, original audio)_vs_ERI1_RECODE(audio recode, original video)_joint_agreement': {f'{a}|{ok}': n for (a, ok), n in sorted(rmatch.items())}}
OUT.write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
