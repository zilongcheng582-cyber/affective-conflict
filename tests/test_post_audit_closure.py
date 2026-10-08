import copy
import hashlib
import json
from pathlib import Path

import pytest
from analyses.post_audit import replay as r
from src.cross_regime.zero_refit.evaluate import scientific_report
from src.reconstruction.mcr.content_duplicates import audit_audio_files

@pytest.fixture(scope='module')
def source():
    return r.reconstruct_source()

@pytest.fixture(scope='module')
def baseline(source):
    return r.source_baselines(source[0])

@pytest.fixture(scope='module')
def phase3():
    return (r.csvrows(r.REPO/'manifests/emotiontalk/trimodal_plan.csv'),
            r.jsonrows(r.REPO/'evidence/emotiontalk/phase3_observed_outputs.jsonl'))

def test_listen_joint_excludes_both_single_modality_conditions():
    rows=r.csvrows(r.REPO/'manifests/listen/frozen_joint_outcomes.csv')
    joint=r.listen_condition(rows,'3C')
    assert {x['condition'] for x in joint}=={'3C'}
    assert not {x['target_record_id'] for x in joint}.intersection(
        x['target_record_id'] for x in rows if x['condition'] in ('3A','3B'))

def test_listen_joint_denominator_and_scientific_identities():
    rows=r.listen_condition(r.csvrows(r.REPO/'manifests/listen/frozen_joint_outcomes.csv'),'3C')
    conflict=[x for x in rows if x['source_relation']=='CONFLICT']
    resolved=[x for x in conflict if r.metrics.resolve_side(x,'AT')]
    assert (len(rows),len(conflict),len(resolved))==(381,378,167)
    assert len({x['target_record_id'] for x in rows})==381
    assert all(x['target_record_id'].startswith('3C_') for x in rows)
    # 3C intentionally reuses the 3B evidence identities; use condition/record IDs.
    full=r.csvrows(r.REPO/'manifests/listen/frozen_joint_outcomes.csv')
    audio={x['target_record_id']:x for x in full if x['condition']=='3B'}
    assert all(x['source_item_id']==audio[x['target_record_id'].replace('3C_','3B_')]['source_item_id'] for x in rows)
    assert {x['presentation_order'] for x in rows}=={'A_THEN_T'}

def test_source_reconstructed_from_observed_responses(source):
    assert len(source[0])==663 and len(source[1])==2132
    assert len({x['utterance_id'] for x in source[0]})==274

def test_m0_binds_frozen_source_parameters_and_rejects_target_fit(baseline):
    assert baseline['M0']['parameters']['intercept_AT']==-.034486176071169515
    assert baseline['M0_PLUS_ORDER']['role']=='POST_AUDIT_DIAGNOSTIC_SOURCE_ONLY_BASELINE'
    bad=copy.deepcopy(baseline['M0']);bad['target_fit']=True
    with pytest.raises(ValueError,match='Source-fixed'):
        r.baseline_predict(bad,'AT',1)

def test_baseline_cannot_fit_changed_or_target_records(source):
    changed=copy.deepcopy(source[0]);changed[0]['_y']=1-changed[0]['_y']
    with pytest.raises(ValueError,match='exact verified source'):
        r.source_baselines(changed)

def test_target_prediction_never_calls_fit_or_calibration(monkeypatch,baseline):
    def forbidden(*args,**kwargs):
        raise AssertionError('Target fitting invoked')
    monkeypatch.setattr(r.source_math,'fit',forbidden)
    rows=r.target_rows()['LISTEN']
    binding=r.read(r.REPO/'frozen/source_model/binding.json')
    assert 0<r.baseline_predict(baseline['M0_PLUS_ORDER'],'AT',1)<1
    assert 0<r.transferred_predict(rows[0],'AT','M3b',binding)<1
    binding['target_coefficient_fit']=True
    with pytest.raises(ValueError,match='Frozen source-only'):
        r.transferred_predict(rows[0],'AT','M3b',binding)

def test_changed_predictions_change_reported_metrics():
    rows=[{'target_record_id':str(i),'source_relation':'CONFLICT',
           'technical_missing':'FALSE','observed_outcome_available':'TRUE',
           'observed_outcome':'SIDE_A' if i else 'SIDE_T'} for i in (0,1)]
    first=r.uncertainty(rows,'AT',{'M0':[.5,.5],'model':[.1,.9]},['a','b'],10)
    second=r.uncertainty(rows,'AT',{'M0':[.5,.5],'model':[.9,.1]},['a','b'],10)
    assert first[1]['AUROC']==1 and second[1]['AUROC']==0
    assert first[1]['log_loss']<second[1]['log_loss']
    assert first[1]['evaluated_identity_sha256']==second[1]['evaluated_identity_sha256']

def test_prediction_replay_tolerates_roundoff_but_rejects_drift():
    reference=[{'analysis_role':'role','target_record_id':'a','predicted_p_SIDE_A':'0.4'}]
    harmless=copy.deepcopy(reference);harmless[0]['predicted_p_SIDE_A']='0.4000000000000001'
    assert r.compare_prediction_rows(harmless,reference)==1
    harmful=copy.deepcopy(reference);harmful[0]['predicted_p_SIDE_A']='0.401'
    with pytest.raises(ValueError,match='value mismatch'):
        r.compare_prediction_rows(harmful,reference)
    harmful[0]['target_record_id']='changed'
    with pytest.raises(ValueError,match='identity mismatch'):
        r.compare_prediction_rows(harmful,reference)

def test_scientific_ruling_is_not_unconditional_success():
    good=scientific_report({'analyses':{'log_loss':.1}},[], 'SURVIVES_WITH_CORRECTION')
    bad=scientific_report({'analyses':{'log_loss':10.0}},[], 'SURVIVES_WITH_CORRECTION')
    assert good['analyses']!=bad['analyses']
    for report in (good,bad):
        assert report['SCIENTIFIC_RULING']=='REQUIRES_INTERPRETATION'
        assert report['B3_FINAL_SCIENTIFIC_RULING']!='SURVIVES_WITH_CORRECTION'
        assert report['HISTORICAL_AUTHOR_INTERPRETATION']=='SURVIVES_WITH_CORRECTION'

def test_different_paths_same_bytes_flag_conflicting_gt(tmp_path):
    for name in ('one.wav','two.wav'):
        (tmp_path/name).write_bytes(b'identical-waveform-bytes')
    found=audit_audio_files([{'audio':'one.wav','gt':'happy'},{'audio':'two.wav','gt':'angry'}],tmp_path)
    assert len(found)==2
    assert all(x['different_paths_same_content'] and x['conflicting_GT'] for x in found)
    assert all(not x['historical_sample_removed'] for x in found)
    assert found[0]['actual_audio_sha256']==hashlib.sha256(b'identical-waveform-bytes').hexdigest()

def test_different_paths_same_bytes_same_gt_are_still_duplicates(tmp_path):
    for name in ('a.wav','b.wav'):(tmp_path/name).write_bytes(b'same')
    found=audit_audio_files([{'audio':'a.wav','gt':'happy'},{'audio':'b.wav','gt':'happy'}],tmp_path)
    assert len(found)==2 and all(not x['conflicting_GT'] for x in found)

def test_phase3_independent_observed_join_counts(source,phase3):
    rows=r.verify_phase3(*phase3,source[1])
    assert (len(rows),sum(x['prediction_resolved'] for x in rows),sum(x['match_indicator'] or 0 for x in rows))==(402,294,268)
    assert sum(x['unresolved_reason']=='EDGE_DISAGREEMENT' for x in rows)==93
    assert sum(x['unresolved_reason']=='OTHER_INVOLVED' for x in rows)==15

@pytest.mark.parametrize('change',['duplicate','missing'])
def test_phase3_duplicate_or_missing_join_fails(source,phase3,change):
    plans,outputs=phase3
    outputs=outputs+[outputs[0]] if change=='duplicate' else outputs[1:]
    with pytest.raises(ValueError,match='Duplicate|Missing'):
        r.verify_phase3(plans,outputs,source[1])

def test_phase3_changed_observed_label_changes_correct_identity(source,phase3):
    plans,outputs=phase3
    original=r.verify_phase3(plans,outputs,source[1])
    index=next(i for i,x in enumerate(original) if x['match_indicator']==1)
    changed=copy.deepcopy(outputs)
    label='sad' if changed[index]['parsed_label']!='sad' else 'happy'
    changed[index]['raw_generation']=changed[index]['parsed_label']=label
    revised=r.verify_phase3(plans,changed,source[1])
    assert sum(x['match_indicator'] or 0 for x in revised)==267

@pytest.mark.parametrize('change',['missing','hash'])
def test_missing_or_changed_evidence_fails_closed(tmp_path,change):
    (tmp_path/'evidence').mkdir()
    p=tmp_path/'evidence/rows.jsonl';p.write_bytes(b'original')
    manifest={'files':[{'path':'evidence/rows.jsonl','sha256':r.digest(p)}]}
    (tmp_path/'evidence/EVIDENCE_MANIFEST_V1.json').write_text(json.dumps(manifest),encoding='utf-8')
    assert r.verify_evidence(tmp_path)==1
    if change=='missing':p.unlink()
    else:p.write_bytes(b'changed')
    with pytest.raises(ValueError,match='Missing or hash-mismatched'):
        r.verify_evidence(tmp_path)
