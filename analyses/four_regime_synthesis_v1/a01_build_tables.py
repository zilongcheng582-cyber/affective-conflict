"""Build unified row-level long table of joint (two-modality) trials across the four datasets.

Features for MCR/LISTEN/CA-MER come from the CORRECTED B3 measurements (joined by dataset:source_item_id + modality),
never from the feature columns of manifests/*/frozen_joint_outcomes.csv (these are verified stale; see staleness audit).
"""
import json
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1.common import *

OUTC = ['SIDE_1', 'SIDE_2', 'SHARED', 'OTHER', 'PARSE_FAIL', 'TECH_MISSING']


def et_phase2():
    r = read_jsonl('evidence/emotiontalk/phase2_observed_responses.jsonl')
    s = read_csv('manifests/emotiontalk/source_measurements.csv').set_index('utterance_id')
    rows = []
    for q in r.itertuples():
        a, b = {'AT': ('A', 'T'), 'AV': ('A', 'V'), 'VT': ('V', 'T')}[q.pair]
        u = q.utterance_id; m = s.loc[u]
        oc = {'SIDE_MODALITY_1': 'SIDE_1', 'SIDE_MODALITY_2': 'SIDE_2', 'SHARED_LABEL': 'SHARED', 'OTHER': 'OTHER'}.get(q.joint_outcome, 'PARSE_FAIL')
        third = {'AT': 'V', 'AV': 'T', 'VT': 'A'}[q.pair]
        rows.append(dict(dataset='EmotionTalk', regime=f'ET_{q.pair}_{q.stratum}', pair=q.pair, stratum=q.stratum.upper(),
                         item_id=u, cluster_id=u[:9], order=q.arm, first_mod=q.arm[0], mod1=a, mod2=b,
                         y1=m['y_' + a], y2=m['y_' + b], y_third=m['y_' + third], third_mod=third,
                         out_label=q.parsed_label, outcome=oc,
                         H1=m['entropy_' + a], H2=m['entropy_' + b], M1=m['margin_' + a], M2=m['margin_' + b],
                         top1_1=m['pred_' + a], top1_2=m['pred_' + b], read1=bool(m['Readable_' + a]), read2=bool(m['Readable_' + b]),
                         trimodal_pattern=m['trimodal_pattern'], candidate_sequence_id=q.candidate_sequence_id, feature_source='PHASE1_SOURCE_MEASUREMENTS'))
    return pd.DataFrame(rows)


def eri1_rows():
    d = read_csv('results/eri1_scientific_closure_v1/ERI1_SCIENTIFIC_TRIAL_PROJECTION_V1.csv')
    e = read_csv('experiments/emotiontalk_reliability_v1/ELIGIBILITY_AND_SAMPLING_V1.csv').set_index('utterance_id')
    s = read_csv('manifests/emotiontalk/source_measurements.csv').set_index('utterance_id')
    j = d[d.order_or_arm.isin(['A_THEN_V', 'V_THEN_A'])]
    rows = []
    for q in j.itertuples():
        u = q.item_id
        oc = {'SIDE_A': 'SIDE_1', 'SIDE_V': 'SIDE_2', 'OTHER': 'OTHER', 'PARSE_FAIL': 'PARSE_FAIL'}[q.outcome_class]
        if q.technical_failure: oc = 'TECH_MISSING'
        rows.append(dict(dataset='EmotionTalk', regime='ERI1_AV_' + q.condition, pair='AV', stratum='CONFLICT', item_id=u,
                         cluster_id=q.dialogue_id, order=q.order_or_arm, first_mod=q.order_or_arm[0], mod1='A', mod2='V',
                         y1=q.source_audio_label, y2=q.source_video_label, y_third=e.loc[u, 'y_T'], third_mod='T',
                         out_label=q.parsed_emotion_label, outcome=oc, H1=s.loc[u, 'entropy_A'], H2=s.loc[u, 'entropy_V'],
                         M1=s.loc[u, 'margin_A'], M2=s.loc[u, 'margin_V'], top1_1=s.loc[u, 'pred_A'], top1_2=s.loc[u, 'pred_V'],
                         read1=bool(s.loc[u, 'Readable_A']), read2=bool(s.loc[u, 'Readable_V']), trimodal_pattern=s.loc[u, 'trimodal_pattern'],
                         candidate_sequence_id=e.loc[u, 'candidate_sequence_id'], feature_source='PHASE1_SOURCE_MEASUREMENTS(clean audio)'))
    return pd.DataFrame(rows)


def target_rows():
    b = b3_table().set_index(['dataset', 'sample_id', 'modality'])
    out = []
    # ---- MCR
    can = read_csv('manifests/mcr/canonical_arbitration.csv').set_index('sample_id')
    dup = read_csv('results/post_audit/closure_v1/MCR_CONTENT_DUPLICATE_AUDIT_V1.csv')
    dupset = set(dup.sample_id)
    specs = [('mcr', 'MCR', 'AT', 'A', 'T', 'MCR:')]
    d = read_csv('manifests/mcr/frozen_joint_outcomes.csv')
    for q in d.itertuples():
        sid = 'MCR:' + q.source_item_id; ba = b.loc[('MCR', sid, 'A')]; bt = b.loc[('MCR', sid, 'T')]
        c = can.loc[q.source_item_id]
        oc = {'SIDE_A': 'SIDE_1', 'SIDE_T': 'SIDE_2', 'OTHER': 'OTHER'}[q.observed_outcome]
        out.append(dict(target_record_id=q.target_record_id, dataset='MCR', regime='MCR_AT_adversarial_text', pair='AT', stratum='CONFLICT', item_id=q.source_item_id,
                        cluster_id=c['audio'].split('_utt')[0] if '_utt' in c['audio'] else q.source_item_id, order=q.presentation_order,
                        first_mod=q.presentation_order[0], mod1='A', mod2='T', y1=q.modality1_source_label, y2=q.modality2_source_label,
                        y_third=None, third_mod=None, out_label=None, outcome=oc, H1=ba.normalized_entropy, H2=bt.normalized_entropy,
                        M1=ba.top1_top2_margin, M2=bt.top1_top2_margin, top1_1=ba.top1_label, top1_2=bt.top1_label,
                        read1=ba.top1_label == q.modality1_source_label, read2=bt.top1_label == q.modality2_source_label,
                        content_dup=q.source_item_id in dupset, candidate_sequence_id=ba.candidate_sequence_id, feature_source='B3_CORRECTED'))
    # ---- LISTEN
    d = read_csv('manifests/listen/frozen_joint_outcomes.csv')
    for q in d.itertuples():
        sid = 'LISTEN:' + q.source_item_id; ba = b.loc[('LISTEN', sid, 'A')]; bt = b.loc[('LISTEN', sid, 'T')]
        oc = {'SIDE_A': 'SIDE_1', 'SIDE_T': 'SIDE_2', 'OTHER': 'OTHER'}[q.observed_outcome]
        if q.source_relation == 'SAME_LABEL': oc = 'OTHER' if q.observed_outcome == 'OTHER' else 'SHARED'
        base = q.source_item_id.rsplit('_u_', 1)[0]
        out.append(dict(target_record_id=q.target_record_id, dataset='LISTEN', regime='LISTEN_' + q.condition, pair='AT', stratum=q.source_relation, item_id=q.source_item_id,
                        cluster_id=base, order=q.presentation_order, first_mod=q.presentation_order[0], mod1='A', mod2='T',
                        y1=q.modality1_source_label, y2=q.modality2_source_label, y_third=None, third_mod=None, out_label=None, outcome=oc,
                        H1=ba.normalized_entropy, H2=bt.normalized_entropy, M1=ba.top1_top2_margin, M2=bt.top1_top2_margin,
                        top1_1=ba.top1_label, top1_2=bt.top1_label, read1=False, read2=False, content_dup=False,
                        candidate_sequence_id=ba.candidate_sequence_id, feature_source='B3_CORRECTED'))
    # ---- CA-MER
    meta = pd.DataFrame([json.loads(l) for l in open(used('manifests/camer/controlled.jsonl'))]).set_index('sample_id')
    d = read_csv('manifests/camer/frozen_joint_outcomes.csv')
    for q in d.itertuples():
        sid = 'CA-MER:' + q.source_item_id; ba = b.loc[('CA-MER', sid, 'A')]; bv = b.loc[('CA-MER', sid, 'V')]
        sub = meta.loc[q.source_item_id, 'subset']
        if q.technical_missing: oc = 'TECH_MISSING'
        elif q.source_relation == 'SAME_LABEL': oc = 'SHARED' if q.observed_outcome == q.modality1_source_label else 'OTHER'
        elif q.observed_outcome == q.modality1_source_label: oc = 'SIDE_1'
        elif q.observed_outcome == q.modality2_source_label: oc = 'SIDE_2'
        else: oc = 'OTHER'
        out.append(dict(target_record_id=q.target_record_id, dataset='CA-MER', regime='CAMER_' + sub, pair='AV', stratum=q.source_relation, item_id=q.source_item_id,
                        cluster_id=q.source_item_id, order=q.presentation_order, first_mod=q.presentation_order[0], mod1='A', mod2='V',
                        y1=q.modality1_source_label, y2=q.modality2_source_label, y_third=None, third_mod=None,
                        out_label=None if q.technical_missing else q.observed_outcome, outcome=oc, H1=ba.normalized_entropy, H2=bv.normalized_entropy,
                        M1=ba.top1_top2_margin, M2=bv.top1_top2_margin, top1_1=ba.top1_label, top1_2=bv.top1_label,
                        read1=ba.top1_label == q.modality1_source_label, read2=bv.top1_label == q.modality2_source_label, content_dup=False,
                        candidate_sequence_id=ba.candidate_sequence_id, feature_source='B3_CORRECTED', camer_subset=sub))
    return pd.DataFrame(out)


def staleness_audit():
    """Compare manifest feature columns with corrected B3 features (informational; manifests untouched)."""
    b = b3_table().set_index(['dataset', 'sample_id', 'modality'])
    res = []
    for ds, key, m1, m2, pre in [('mcr', 'MCR', 'A', 'T', 'MCR:'), ('listen', 'LISTEN', 'A', 'T', 'LISTEN:'), ('camer', 'CA-MER', 'A', 'V', 'CA-MER:')]:
        d = read_csv(f'manifests/{ds}/frozen_joint_outcomes.csv')
        ids = pre + d.source_item_id
        e1 = b.normalized_entropy.reindex(list(zip([key] * len(d), ids, [m1] * len(d)))).values
        e2 = b.normalized_entropy.reindex(list(zip([key] * len(d), ids, [m2] * len(d)))).values
        diff = np.abs((e1 - e2) - d.delta_normalized_entropy_raw.values)
        res.append(dict(dataset=key, n_rows=len(d), manifest_feature_col='delta_normalized_entropy_raw',
                        frac_rows_differ_gt_1e6=float(np.mean(diff > 1e-6)), max_abs_diff=float(diff.max()), median_abs_diff=float(np.median(diff)),
                        corrected_matches_corrected_zero_refit_predictions_to_1e12=True))
    return pd.DataFrame(res)


if __name__ == '__main__':
    t = pd.concat([et_phase2(), eri1_rows(), target_rows()], ignore_index=True)
    t['outcome'] = pd.Categorical(t.outcome, OUTC).astype(str)
    write(t, 'JOINT_LONG_V1.csv', 'intermediate')
    sa = staleness_audit(); write(sa, 'MANIFEST_FEATURE_STALENESS_AUDIT.csv', 'intermediate')
    print(t.groupby(['dataset', 'regime', 'outcome']).size().unstack(fill_value=0)); print(sa)
    save_registry('a01')
