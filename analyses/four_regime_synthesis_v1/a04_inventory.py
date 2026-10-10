"""Evidence inventory: dataset x condition matrix with counts computed from the actual row-level files."""
import json
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1.common import *


def cnt(d, col='outcome'):
    vc = d[col].value_counts()
    return {k: int(vc.get(k, 0)) for k in ['SIDE_1', 'SIDE_2', 'SHARED', 'OTHER', 'PARSE_FAIL', 'TECH_MISSING']}


def run():
    L = read_csv('results/four_regime_structural_synthesis_v1/intermediate/JOINT_LONG_V1.csv')
    b3 = read_csv('evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv')
    rows = []

    def add(dataset, cond, **kw):
        base = dict(dataset=dataset, condition=cond, modalities_input='', presentation_order='', conflict_type='', n_independent_items=np.nan, n_trials=np.nan, n_trials_with_outcome=np.nan,
                    SIDE_1=np.nan, SIDE_2=np.nan, SHARED=np.nan, OTHER=np.nan, PARSE_FAIL=np.nan, TECH_MISSING=np.nan, source_label_space='', response_label_space='', eligibility='',
                    pairing_key='', row_level_file='', row_level_availability='', feature_provenance='', missing_scientific_fields='')
        base.update(kw); rows.append(base)

    def from_long(dataset, cond, mask, **kw):
        d = L[mask]; c = cnt(d)
        add(dataset, cond, n_independent_items=d.item_id.nunique(), n_trials=len(d), n_trials_with_outcome=len(d) - c['TECH_MISSING'], **c, **kw)

    ET = 'EmotionTalk'; s = read_csv('manifests/emotiontalk/source_measurements.csv')
    for m_, nm in [('T', 'text'), ('A', 'audio'), ('V', 'video (silent)')]:
        add(ET, f'Phase1 {m_}_ONLY', modalities_input=nm, presentation_order='n/a', conflict_type='n/a (unimodal reading)', n_independent_items=len(s), n_trials=len(s), n_trials_with_outcome=len(s),
            source_label_space='EmotionTalk 7 labels (sad,happy,fearful,angry,surprised,disgusted,neutral); per-modality annotator label y_' + m_, response_label_space='7 labels, candidate-sequence CS01-CS14 rotated',
            eligibility=f'Readable_{m_}: {int(s["Readable_" + m_].sum())}/1500 (pred==source label)', pairing_key='utterance_id', row_level_file='manifests/emotiontalk/source_measurements.csv',
            row_level_availability='YES (parsed label, entropy, margin, source-prob; raw generation text NOT in repo)', feature_provenance='Phase1 measurement (frozen source model input)', missing_scientific_fields='raw generations; full 7-label probability vectors for Phase1')
    for pair, mods in [('AT', 'audio+text'), ('AV', 'audio+silent video'), ('VT', 'silent video+text')]:
        for strat in ['conflict', 'consistent']:
            from_long(ET, f'Phase2 {pair} {strat}', (L.dataset == ET) & (L.regime == f'ET_{pair}_{strat}'), modalities_input=mods, presentation_order='both orders (pairwise counterbalanced)',
                      conflict_type='NATURAL multi-annotator-label conflict between per-modality annotations' if strat == 'conflict' else 'consistent control (same label)',
                      source_label_space='EmotionTalk 7 labels', response_label_space='7 labels', eligibility='DualReadable_' + pair + ' (both unimodal readings correct, Phase1)', pairing_key='utterance_id + arm',
                      row_level_file='evidence/emotiontalk/phase2_observed_responses.jsonl', row_level_availability='YES (parsed label + raw_generation short string)', feature_provenance='Phase1 source_measurements (same measurement protocol)',
                      missing_scientific_fields='unimodal rows are not paired with joint rows other than via Phase1')
    p3 = read_jsonl('evidence/emotiontalk/phase3_observed_outputs.jsonl')
    add(ET, 'Phase3 trimodal (A,T,V; 6 orders)', modalities_input='audio+text+silent video', presentation_order='6 permutations', conflict_type='NATURAL; 2-vs-1 label patterns (T=A!=V, A=V!=T, T=V!=A)',
        n_independent_items=p3.utterance_id.nunique(), n_trials=len(p3), n_trials_with_outcome=int(p3.generation_success.sum()), source_label_space='EmotionTalk 7 labels', response_label_space='7 labels',
        eligibility='TWO_VS_ONE with >=1 informative DualReadable pair; ALL_DIFFERENT eligible n=3 outside primary', pairing_key='utterance_id + tri_order', row_level_file='evidence/emotiontalk/phase3_observed_outputs.jsonl',
        row_level_availability='YES', feature_provenance='n/a (response only)', missing_scientific_fields='ALL_DIFFERENT population (3 eligible only)')
    er = pd.read_csv(used('results/eri1_scientific_closure_v1/ERI1_SCIENTIFIC_TRIAL_PROJECTION_V1.csv'))
    for cond in ['CLEAN', 'RECODE', 'SNR20', 'SNR10', 'SNR00']:
        d = L[(L.regime == f'ERI1_AV_{cond}')]; c = cnt(d)
        e = er[er.condition == cond]
        add(ET, f'ERI1 {cond} (A_ONLY + A_THEN_V + V_THEN_A' + (' + V_ONLY)' if cond == 'CLEAN' else ')'), modalities_input='audio (' + ('original' if cond == 'CLEAN' else 're-encoded' if cond == 'RECODE' else 'white noise ' + cond[3:] + ' dB') + ') + silent video', presentation_order='A_THEN_V,V_THEN_A',
            conflict_type='NATURAL AV annotation conflict; audio-reliability intervention', n_independent_items=146, n_trials=len(e), n_trials_with_outcome=len(e) - int(e.technical_failure.sum()),
            SIDE_1=c['SIDE_1'], SIDE_2=c['SIDE_2'], SHARED=0, OTHER=c['OTHER'], PARSE_FAIL=c['PARSE_FAIL'], TECH_MISSING=c['TECH_MISSING'],
            source_label_space='EmotionTalk 7 labels', response_label_space='7 labels', eligibility='AV conflict & Readable_A & Readable_V (DualReadable_AV), pre-intervention', pairing_key='item_id + condition + arm',
            row_level_file='results/eri1_scientific_closure_v1/ERI1_SCIENTIFIC_TRIAL_PROJECTION_V1.csv', row_level_availability='YES (projection: outcome class, parsed label, entropies, joint p(audio label))',
            feature_provenance='A_ONLY entropy under each condition (own trial); video entropy from Phase1', missing_scientific_fields='raw transcripts; per-item full probability vectors')
    # MCR
    m = L[L.dataset == 'MCR']
    for o, nm in [('A_THEN_T', 'audio then text'), ('T_THEN_A', 'text then audio')]:
        from_long('MCR', o + ' (adversarial text assertion)', (L.dataset == 'MCR') & (L.order == o), modalities_input='audio + text description asserting a competitor label', presentation_order=nm,
                  conflict_type='ARTIFICIAL propositional text assertion != benchmark GT; audio label = GT (not independently annotated per modality)', source_label_space='7 labels (GT / competitor)', response_label_space='7 labels',
                  eligibility='909 canonical arbitration records (7 records in 3 byte-identical audio groups audited separately; none removed)', pairing_key='sample_id (audio) + order',
                  row_level_file='manifests/mcr/frozen_joint_outcomes.csv', row_level_availability='YES (outcome class only; OTHER label identity NOT in repo)', feature_provenance='B3 corrected (joined by dataset:sample_id+modality; manifest feature columns are STALE)',
                  missing_scientific_fields='raw generations; OTHER label identity; row-level A_ONLY/T_ONLY outputs')
    for arm, nm in [('A_ONLY', 'audio'), ('T_ONLY', 'text assertion')]:
        add('MCR', arm + ' (controlled V2 run)', modalities_input=nm, presentation_order='n/a', conflict_type='n/a', n_independent_items=909, n_trials=909, source_label_space='7 labels', response_label_space='7 labels',
            eligibility='Readable audio 466/909 and Readable text 909/909 (aggregate)', pairing_key='sample_id', row_level_file='protocols/mcr/MCR_CONTROLLED_DUAL_READABLE_DIAGNOSTICS_V2.csv (aggregate only)',
            row_level_availability='AGGREGATE_ONLY (row-level outputs not in repo); B3 unimodal rows exist (different prompt)', feature_provenance='B3 corrected 909 rows', missing_scientific_fields='row-level unimodal outputs')
    for tc in ['Faithful', 'Neutral', 'Irrelevant']:
        add('MCR', f'{tc} text condition', modalities_input='audio + ' + tc.lower() + ' text', row_level_availability='NOT_EXECUTED', conflict_type='would be non-conflict/neutral control', source_label_space='7 labels',
            missing_scientific_fields='entire condition (text exists in canonical_arbitration.csv but no arm was run)')
    # LISTEN
    for cnd, mods, order in [('3A', 'text', 'T_ONLY'), ('3B', 'audio', 'A_ONLY'), ('3C', 'audio then text', 'A_THEN_T')]:
        from_long('LISTEN', cnd + ' (' + mods + ')', (L.dataset == 'LISTEN') & (L.regime == 'LISTEN_' + cnd), modalities_input=mods, presentation_order=order,
                  conflict_type='NATURAL/dataset-constructed implicit(audio)-vs-explicit(text) emotion mismatch (MUStARD/MELD-style)', source_label_space='audio: ridicule/frustration/disgust/anger/sadness; text: 8 labels (incl. excitement)',
                  response_label_space='native multiple-choice letters (native choices + 8 augmented emotions), per-item/condition randomized order', eligibility='conflict (A!=T label) rows; SAME_LABEL rows reported separately',
                  pairing_key='source_item_id base (3A has _u_3A suffix); matched via identical evidence hashes', row_level_file='manifests/listen/frozen_joint_outcomes.csv',
                  row_level_availability='YES (outcome class only; no chosen label/letter, no randomized choice list)', feature_provenance='B3 corrected; source-label probability undefined for all LISTEN labels (7-label space mismatch)',
                  missing_scientific_fields='OTHER label identity; randomized choices; raw generations; counterbalanced T_THEN_A order')
    # CA-MER
    for sub in ['audio-aligned', 'video-aligned', 'consistent']:
        for o in ['A_THEN_V', 'V_THEN_A']:
            from_long('CA-MER', f'{sub} {o}', (L.dataset == 'CA-MER') & (L.camer_subset == sub) & (L.order == o), modalities_input='audio + silent video', presentation_order=o,
                      conflict_type=('NATURAL pseudo-label conflict (official ' + sub + ' file)') if sub != 'consistent' else 'consistent control', source_label_space='16 source-local pseudo-labels (audio_pseudo_label, video_pseudo_label); NOT ground truth',
                      response_label_space='16-label union, rotated candidate order', eligibility='none beyond official subset membership (B3 readability not gated)', pairing_key='sample_id + order',
                      row_level_file='manifests/camer/frozen_joint_outcomes.csv (+controlled.jsonl)', row_level_availability='YES (chosen label for 2884/3000 trials; 116 CUDA_OOM technical missing)',
                      feature_provenance='B3 corrected 7-label measurements (32%/43% of audio/video source labels outside 7-label space)', missing_scientific_fields='multimodal final_label (deliberately excluded); controlled A_ONLY/V_ONLY outputs (NOT_RUN); 116 OOM trials')
    for m_, nm in [('A', 'audio'), ('V', 'silent video')]:
        add('CA-MER', f'B3 unimodal {m_}', modalities_input=nm, n_independent_items=1500, n_trials=1500, n_trials_with_outcome=1500, source_label_space='16 pseudo-labels', response_label_space='B3 7-label space',
            pairing_key='sample_id', row_level_file='evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv', row_level_availability='YES (full 7-label probability vectors)', feature_provenance='B3 corrected')
    for m_, nm in [('A', 'audio'), ('T', 'text')]:
        add('LISTEN', f'B3 unimodal {m_}', modalities_input=nm, n_independent_items=768, n_trials=768, n_trials_with_outcome=768, source_label_space='LISTEN labels', response_label_space='B3 7-label space',
            pairing_key='source_item_id', row_level_file='evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv', row_level_availability='YES', feature_provenance='B3 corrected; source-label prob undefined for audio (0/768)')
    for m_, nm in [('A', 'audio'), ('T', 'text assertion')]:
        add('MCR', f'B3 unimodal {m_}', modalities_input=nm, n_independent_items=909, n_trials=909, n_trials_with_outcome=909, source_label_space='7 labels', response_label_space='B3 7-label space',
            pairing_key='sample_id', row_level_file='evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv', row_level_availability='YES', feature_provenance='B3 corrected')
    M = pd.DataFrame(rows); write(M, '01_DATASET_CONDITION_MATRIX.csv')
    # other inventory facts
    facts = dict(B3_rows=len(b3), B3_by_dataset_modality=b3.groupby(['dataset', 'modality']).size().rename('n').reset_index().to_dict('records'),
                 PANEL_n=len(s), phase2_trials=int((L.regime.str.startswith('ET_')).sum()), phase3_trials=len(p3), phase3_utterances=int(p3.utterance_id.nunique()),
                 phase3_patterns=p3.drop_duplicates('utterance_id').trimodal_pattern.value_counts().to_dict(), long_table_rows=len(L))
    st = read_csv('results/four_regime_structural_synthesis_v1/intermediate/MANIFEST_FEATURE_STALENESS_AUDIT.csv'); facts['staleness'] = st.to_dict('records')
    (INTER / 'INVENTORY_FACTS.json').write_text(json.dumps(facts, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)))
    save_registry('a04'); return M


if __name__ == '__main__':
    M = run(); pd.set_option('display.width', 250, 'display.max_columns', 30, 'display.max_colwidth', 40); print(M[['dataset', 'condition', 'n_independent_items', 'n_trials', 'SIDE_1', 'SIDE_2', 'SHARED', 'OTHER', 'PARSE_FAIL', 'TECH_MISSING']].to_string())
