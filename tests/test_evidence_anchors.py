import copy
import json
import random
import shutil

import pytest
from analyses.post_audit import replay as r
from src.common.benchmarks.emotiontalk_controlled_parser_v1 import parse_label


def copy_paths(tmp_path, paths):
    for relative in paths:
        target = tmp_path/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(r.REPO/relative, target)
    return tmp_path


def b3_root(tmp_path):
    manifest = r.read(r.REPO/'evidence/EVIDENCE_MANIFEST_V1.json')
    paths = {item['path'] for item in manifest['files']}
    paths |= {'evidence/EVIDENCE_MANIFEST_V1.json', 'RELEASE_MANIFEST_V1.json', r.B3_CATALOG}
    paths |= {'evidence/b3/'+p.name for p in (r.REPO/'evidence/b3').iterdir() if p.is_file()}
    return copy_paths(tmp_path, sorted(paths))


def phase3_root(tmp_path):
    return copy_paths(tmp_path, ['RELEASE_MANIFEST_V1.json', r.PHASE3_AUDIT, r.PHASE3_MERGED])


@pytest.fixture(scope='module')
def phase3_inputs():
    _, phase2 = r.reconstruct_source()
    return (r.csvrows(r.REPO/'manifests/emotiontalk/trimodal_plan.csv'),
            r.jsonrows(r.REPO/r.PHASE3_PROJECTION),
            r.csvrows(r.REPO/r.PHASE3_MERGED), phase2)


def test_original_evidence_passes_all_anchors():
    report = r.verify_evidence_anchors()
    assert (report['B3_PREEXISTING_ANCHOR_CHECK'], report['PHASE3_PROJECTION_BINDING'],
            report['PHASE3_PREEXISTING_ANCHOR'], report['phase3_rows_bound']) == ('PASS', 'PASS', 'PASS', 402)
    assert len(report['b3']['recovered_files_verified']) == 9
    assert len(report['b3']['catalogued_not_released']) == 6
    assert report['b3']['catalog_anchor']['baseline_git_blob'] in ('MATCH', 'GIT_HISTORY_UNAVAILABLE')


def test_a_b3_tamper_with_updated_post_audit_manifest_still_fails(tmp_path):
    root = b3_root(tmp_path)
    target = root/'evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv'
    data = target.read_bytes()
    index = data.index(b'0.', data.index(b'\n')+1)
    target.write_bytes(data[:index]+b'1.'+data[index+2:])
    manifest_path = root/'evidence/EVIDENCE_MANIFEST_V1.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for item in manifest['files']:
        if item['path'] == 'evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv':
            item['sha256'] = r.digest(target)
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    assert r.verify_evidence(root) == len(manifest['files'])
    with pytest.raises(ValueError, match='B3_PREEXISTING_ANCHOR_CHECK = FAIL'):
        r.verify_b3_preexisting_anchor(root)


def test_a_rewritten_catalog_and_release_receipt_still_fail(tmp_path):
    root = b3_root(tmp_path)
    target = root/'evidence/b3/B3_CORRECTED_EXECUTION_CHECKPOINT_V1.json'
    target.write_bytes(target.read_bytes()+b'\n')
    catalog = json.loads((root/r.B3_CATALOG).read_text(encoding='utf-8'))
    for row in catalog['outputs']:
        if row['filename'] == target.name:
            row['SHA256'] = r.digest(target)
    (root/r.B3_CATALOG).write_text(json.dumps(catalog), encoding='utf-8')
    release = json.loads((root/'RELEASE_MANIFEST_V1.json').read_text(encoding='utf-8'))
    for row in release['files']:
        if row['relative_path'] == r.B3_CATALOG:
            row['SHA256'] = r.digest(root/r.B3_CATALOG)
    (root/'RELEASE_MANIFEST_V1.json').write_text(json.dumps(release), encoding='utf-8')
    with pytest.raises(ValueError, match='B3_PREEXISTING_ANCHOR_CHECK = FAIL.*changed since v1.0.0'):
        r.verify_b3_preexisting_anchor(root)


def test_b_two_label_tamper_preserving_268_fails_binding(phase3_inputs):
    plans, outputs, original, phase2 = phase3_inputs
    rows = r.verify_phase3(plans, outputs, phase2)
    right = next(x for x in rows if x['match_indicator'] == 1)
    wrong = next(x for x in rows if x['match_indicator'] == 0)
    changed = copy.deepcopy(outputs)
    for output in changed:
        key = (output['utterance_id'], output['tri_order'])
        if key == (right['utterance_id'], right['tri_order']):
            label = next(x for x in ('sad', 'happy', 'angry', 'neutral') if x != right['predicted_label'])
            output['raw_generation'] = output['parsed_label'] = label
        if key == (wrong['utterance_id'], wrong['tri_order']):
            output['raw_generation'] = output['parsed_label'] = wrong['predicted_label']
    tampered = r.verify_phase3(plans, changed, phase2)
    assert sum(x['match_indicator'] or 0 for x in tampered) == 268
    with pytest.raises(ValueError, match='PHASE3_PROJECTION_BINDING = FAIL'):
        r.verify_phase3_original_evidence_binding(changed, original)


def test_c_row_order_is_irrelevant_to_scientific_join(phase3_inputs):
    plans, outputs, original, phase2 = phase3_inputs
    shuffled_outputs, shuffled_original = copy.deepcopy(outputs), copy.deepcopy(original)
    random.Random(1).shuffle(shuffled_outputs)
    random.Random(2).shuffle(shuffled_original)
    assert r.verify_phase3_original_evidence_binding(shuffled_outputs, shuffled_original) == 402
    rows = r.verify_phase3(plans, shuffled_outputs, phase2)
    assert sum(x['match_indicator'] or 0 for x in rows) == 268


def test_d_raw_generation_tamper_with_same_parsed_label_fails(phase3_inputs):
    _, outputs, original, _ = phase3_inputs
    changed = copy.deepcopy(outputs)
    row = changed[0]
    altered = row['raw_generation']+' '
    parsed = parse_label(altered)
    assert (parsed['parsed_label'], parsed['parser_status']) == (row['parsed_label'], row['parser_status'])
    row['raw_generation'] = altered
    with pytest.raises(ValueError, match='PHASE3_PROJECTION_BINDING = FAIL'):
        r.verify_phase3_original_evidence_binding(changed, original)


@pytest.mark.parametrize('field', ['observed_outcome_class', 'parser_status', 'generation_success', 'candidate_sequence', 'actual_evidence_order'])
def test_d_any_bound_field_tamper_fails(phase3_inputs, field):
    _, outputs, original, _ = phase3_inputs
    changed = copy.deepcopy(outputs)
    value = changed[5][field]
    changed[5][field] = (not value if isinstance(value, bool) else list(reversed(value))
                         if isinstance(value, list) else value+'_X')
    with pytest.raises(ValueError, match='PHASE3_PROJECTION_BINDING = FAIL'):
        r.verify_phase3_original_evidence_binding(changed, original)


@pytest.mark.parametrize('change', ['missing', 'altered'])
def test_e_original_phase3_missing_or_hash_mismatch_fails(tmp_path, change):
    root = phase3_root(tmp_path)
    assert r.verify_phase3_preexisting_anchor(root)['PHASE3_PREEXISTING_ANCHOR'] == 'PASS'
    target = root/r.PHASE3_MERGED
    if change == 'missing':
        target.unlink()
    else:
        target.write_bytes(target.read_bytes()+b'\n')
    with pytest.raises(ValueError, match='PHASE3_PREEXISTING_ANCHOR = FAIL'):
        r.verify_phase3_preexisting_anchor(root)


def test_e_changed_recorded_phase3_anchor_fails(tmp_path):
    root = phase3_root(tmp_path)
    audit = json.loads((root/r.PHASE3_AUDIT).read_text(encoding='utf-8'))
    audit['authoritative_analysis_input_sha256'] = '0'*64
    (root/r.PHASE3_AUDIT).write_text(json.dumps(audit), encoding='utf-8')
    with pytest.raises(ValueError, match='PHASE3_PREEXISTING_ANCHOR = FAIL'):
        r.verify_phase3_preexisting_anchor(root)


@pytest.mark.parametrize('name', ['B3_CORRECTED_FORWARD_RESULTS_V1.jsonl', 'B3_CORRECTED_EXECUTION_SHA256SUMS.txt'])
def test_e_missing_recovered_b3_file_fails(tmp_path, name):
    root = b3_root(tmp_path)
    (root/'evidence/b3'/name).unlink()
    with pytest.raises(ValueError, match='B3_PREEXISTING_ANCHOR_CHECK = FAIL'):
        r.verify_b3_preexisting_anchor(root)


@pytest.mark.parametrize('name', ['B3_FORWARD_RESULTS_V1.jsonl', 'UNDECLARED_EXTRA.json'])
def test_e_unreleased_or_uncatalogued_b3_file_cannot_pose_as_recovered(tmp_path, name):
    root = b3_root(tmp_path)
    (root/'evidence/b3'/name).write_text('{}\n', encoding='utf-8')
    with pytest.raises(ValueError, match='B3_PREEXISTING_ANCHOR_CHECK = FAIL'):
        r.verify_b3_preexisting_anchor(root)


def test_replay_entry_point_requires_anchors(tmp_path, monkeypatch):
    def failing(*args, **kwargs):
        raise ValueError('B3_PREEXISTING_ANCHOR_CHECK = FAIL: injected')
    monkeypatch.setattr(r, 'verify_b3_preexisting_anchor', failing)
    output = tmp_path/'replay'
    with pytest.raises(ValueError, match='B3_PREEXISTING_ANCHOR_CHECK = FAIL'):
        r.run(output, bootstraps=2)
    assert not output.exists()
