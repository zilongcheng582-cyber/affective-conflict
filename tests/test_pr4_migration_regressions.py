"""PR4 Remediation V1 regression tests (independent review findings F01-F06, F09, F10).

Validator behaviour is exercised on disposable clones of the committed HEAD; the working checkout is never modified.
"""
import csv, importlib.util, json, shutil, subprocess, sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PROV = REPO / 'evidence/provenance/recovered_evidence_migration_v1'
VALIDATOR = 'analyses/transfer_failure_integration_v1/validate_migration.py'


def load_validator(root=REPO):
    spec = importlib.util.spec_from_file_location('validate_migration_under_test', root / VALIDATOR)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def table(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


# ---------- F01 payload identity
def test_payload_bytes_recorded_equals_allowlist_equals_actual():
    prov = json.loads((PROV / 'MIGRATION_PROVENANCE.json').read_text(encoding='utf-8'))
    allow = table(PROV / 'MIGRATION_ALLOWLIST.csv')
    actual = sum((REPO / r['target_path']).stat().st_size for r in allow)
    assert prov['payload_bytes'] == sum(int(r['bytes']) for r in allow) == actual == 16358604
    assert len(allow) == prov['payload_file_count'] == 222


def test_validation_report_has_no_stale_payload_value():
    report = (PROV / 'MIGRATION_VALIDATION_REPORT.md').read_text(encoding='utf-8')
    assert '16,358,604' in report
    # the erroneous value may only appear inside the correction note, never as the stated payload
    assert 'with 16,372,203 payload bytes' not in report


# ---------- F05 exclusions
def test_exclusion_status_matches_gap_analysis_row_by_row():
    gap = {r['source_path']: r for r in table(PROV / 'GITHUB_GAP_ANALYSIS.csv')}
    rows = table(PROV / 'MIGRATION_EXCLUSIONS.csv')
    mapping = load_validator().EXCLUSION_STATUS
    assert len(rows) == 58
    for r in rows:
        g = gap[r['source']]
        assert r['status'] == mapping[g['gap_status']] and r['gap_status'] == g['gap_status']
        assert r['upload_decision'] == 'NOT_UPLOADED' and r['status'] != 'CANDIDATE'
        assert r['status_before_remediation_v1']  # history preserved


# ---------- F02 status index
def test_status_index_single_current_next_step_and_full_coverage():
    v = load_validator(); c = v.Checker(); out = {'tests': {}}
    sums = {l.split('  ', 1)[1]: l.split('  ', 1)[0] for l in (PROV / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines()}
    v.check_status_index(c, out, sums)
    assert c.failures == []
    index = json.loads((REPO / v.STATUS_INDEX).read_text(encoding='utf-8'))
    assert index['current_next_step']['value'] == 'CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION'
    assert index['current_next_step']['gpu_authorized'] is False
    statuses = {d['path']: d['status'] for d in index['documents']}
    assert statuses['results/four_regime_structural_synthesis_v1/05_QWEN_GPU_EXPERIMENT_DECISION.md'] == 'SUPERSEDED'
    assert statuses['results/four_regime_structural_synthesis_v1/08_QWEN_GPU_EXPERIMENT_DECISION_V2.md'] == 'SUPERSEDED'
    assert statuses['results/recovered_evidence_scientific_analysis_v1/06_QWEN_NEXT_EXPERIMENT_DECISION.md'] == 'CURRENT'
    assert {w['id'] for w in index['withdrawn_or_limited_premises']} >= {'W1', 'W2', 'W3', 'W4', 'W5', 'W6'}


# ---------- F10 companion metadata
def test_claim_companion_preserves_statuses_and_only_eri1_confirmatory():
    claims = {r['id']: r for r in table(REPO / 'results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX.csv')}
    comp = {r['id']: r for r in table(REPO / 'results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX_EVIDENCE_STATUS_V1.csv')}
    assert set(comp) == set(claims) and len(comp) == 25
    assert all(comp[k]['claim_status_unchanged'] == claims[k]['status'] for k in claims)
    assert [k for k, r in comp.items() if r['may_be_cited_as_confirmatory'] != 'NO'] == ['X2']
    assert comp['X2']['upstream_evidence_status'] == 'PREREGISTERED_CONFIRMATORY_FROZEN'
    assert all(claims[k]['analysis_origin'] == 'POST_HOC_EXPLORATORY' for k in claims)


# ---------- F06 sanitization register
def test_retained_text_register_matches_files_and_main():
    v = load_validator(); c = v.Checker(); out = {'tests': {}}
    v.check_sanitization(c, out)
    assert c.failures == [] and out['tests']['sanitization_retained_values'] == 30


# ---------- F09 metric edge cases
def test_single_class_metrics_are_undefined_not_crash():
    m = load_validator().metrics([1, 1, 1], [.2, .3, .4])
    assert m['AUROC'] is None and m['balanced_accuracy'] is None and m['log_loss'] is not None
    assert load_validator().metrics([], [])['AUROC'] is None


def test_validator_has_no_assert_statements():
    import ast
    tree = ast.parse((REPO / VALIDATOR).read_text(encoding='utf-8'))
    assert not any(isinstance(n, ast.Assert) for n in ast.walk(tree))


# ---------- validator behaviour on disposable clones (F03, F04, F09)
def clone(tmp_path, *config):
    dest = tmp_path / 'repo'
    subprocess.run(['git', *sum((['-c', x] for x in config), []), 'clone', '-q', str(REPO), str(dest)], check=True)
    for x in config:
        k, val = x.split('=', 1); subprocess.run(['git', '-C', str(dest), 'config', k, val], check=True)
    head = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(['git', '-C', str(dest), 'checkout', '-q', head], check=True)
    return dest


def run(repo, tmp_path, *flags):
    rep = tmp_path / 'report.json'
    proc = subprocess.run([sys.executable, *flags, str(repo / VALIDATOR), '--report', str(rep)], capture_output=True, text=True)
    report = json.loads(rep.read_text()) if rep.exists() else None
    return proc, report


@pytest.fixture
def repo(tmp_path):
    return clone(tmp_path)


def failing_checks(report):
    return {f['check'] for f in report['failures']}


def test_clean_clone_passes(repo, tmp_path):
    proc, report = run(repo, tmp_path)
    assert proc.returncode == 0 and report['status'] == 'PASS' and report['failures'] == []
    assert len(report['tests']['frozen_route_baseline_checks']) == 18


@pytest.mark.parametrize('flags', [(), ('-O',)])
def test_tampered_file_fails_even_under_python_O(repo, tmp_path, flags):
    f = repo / 'results/transfer_failure_integration_v1/04_TRANSFER_CLAIM_BOUNDARY_MATRIX.md'
    f.write_bytes(f.read_bytes() + b'x')
    proc, report = run(repo, tmp_path, *flags)
    assert proc.returncode != 0 and report['status'] == 'FAIL' and '"status": "PASS"' not in proc.stdout
    assert any(x['check'] == 'sha256_mismatch' and '04_TRANSFER_CLAIM_BOUNDARY_MATRIX.md' in x['detail'] for x in report['failures'])


def test_missing_file_fails(repo, tmp_path):
    (repo / 'results/transfer_failure_integration_v1/04_TRANSFER_CLAIM_BOUNDARY_MATRIX.md').unlink()
    proc, report = run(repo, tmp_path, '-O')
    assert proc.returncode != 0 and 'sha256_file_missing' in failing_checks(report)


def test_manifest_mismatch_fails(repo, tmp_path):
    sums = repo / 'evidence/provenance/recovered_evidence_migration_v1/SHA256SUMS.txt'
    lines = sums.read_text(encoding='utf-8').splitlines()
    lines[0] = '0' * 64 + lines[0][64:]
    sums.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    proc, report = run(repo, tmp_path)
    assert proc.returncode != 0 and 'sha256_mismatch' in failing_checks(report)


def test_unlisted_committed_file_fails(repo, tmp_path):
    extra = repo / 'results/transfer_failure_integration_v1/UNLISTED_EXTRA.csv'
    extra.write_text('a,b\n1,2\n')
    subprocess.run(['git', '-C', str(repo), 'add', str(extra)], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'extra'], check=True)
    proc, report = run(repo, tmp_path)
    assert proc.returncode != 0 and 'sha256sums_missing_entry_for_added_file' in failing_checks(report)


def test_modified_main_file_fails(repo, tmp_path):
    f = repo / 'README.md'
    f.write_bytes(f.read_bytes() + b'\n')
    subprocess.run(['git', '-C', str(repo), '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qam', 'touch'], check=True)
    proc, report = run(repo, tmp_path)
    assert proc.returncode != 0 and 'base_file_blob_changed' in failing_checks(report)


def test_windows_autocrlf_true_clone_passes(tmp_path):
    repo = clone(tmp_path, 'core.autocrlf=true')
    for rel in ['.gitattributes', 'docs/RECOVERED_EVIDENCE_MIGRATION_V1.md']:
        assert b'\r\n' not in (repo / rel).read_bytes()
    proc, report = run(repo, tmp_path)
    assert proc.returncode == 0 and report['status'] == 'PASS', report['failures'][:5]
