"""PR4 independent review boundary tests (V2: defect-proof tests converted to regressions after Remediation V1; F07/F14 still documented as open). Read-only against the reviewed checkout; never writes into it."""
import importlib, math, os, shutil, subprocess, sys, json, csv
from pathlib import Path
import numpy as np
import pytest

CHECKOUT = Path(os.environ.get('PR4_CHECKOUT', Path(__file__).resolve().parents[1] / 'checkout'))
A = CHECKOUT / 'analyses'

def load(folder, name):
    sys.path.insert(0, str(A / folder))
    try:
        if name in sys.modules: del sys.modules[name]
        return importlib.import_module(name)
    finally:
        sys.path.pop(0)

vm = load('transfer_failure_integration_v1', 'validate_migration')
p4 = load('transfer_failure_integration_v1', 'phase4_transfer')
an = load('recovered_evidence_scientific_analysis_v1', 'analysis')
sys.path.insert(0, str(CHECKOUT))
from analyses.four_regime_synthesis_v1 import common as fr

def pairwise_auc(y, p):
    y = np.array(y); p = np.array(p); a = p[y == 1]; b = p[y == 0]
    return ((a[:, None] > b[None]).sum() + .5 * (a[:, None] == b[None]).sum()) / (len(a) * len(b))

RNG = np.random.default_rng(7)
Y = (RNG.random(300) < .2).astype(int); P = np.round(RNG.random(300), 2)  # rounding creates ties

# ---- metric correctness / direction / ties / order invariance
def test_auroc_direction_and_ties_all_implementations():
    ref = pairwise_auc(Y, P)
    assert abs(vm.metrics(list(Y), list(P))['AUROC'] - ref) < 1e-12
    assert abs(p4.metric(list(Y), list(P))['AUROC'] - ref) < 1e-12
    assert abs(fr.auroc(Y, P) - ref) < 1e-12
    # direction: perfect positive scores -> 1
    assert vm.metrics([0, 0, 1, 1], [.1, .2, .8, .9])['AUROC'] == 1.0

def test_metrics_row_order_invariant():
    perm = RNG.permutation(len(Y))
    a = p4.metric(list(Y), list(P)); b = p4.metric(list(Y[perm]), list(P[perm]))
    for k in a: assert abs(a[k] - b[k]) < 1e-12

def test_logloss_brier_label_encoding():
    m = p4.metric([1, 0], [.9, .2])
    assert abs(m['log_loss'] - (-(math.log(.9) + math.log(.8)) / 2)) < 1e-12
    assert abs(m['Brier_score'] - ((.1 ** 2 + .2 ** 2) / 2)) < 1e-12

def test_balanced_accuracy_threshold_is_inclusive_half():
    # p == 0.5 counts as predicting SIDE_A in both implementations (frozen threshold .5)
    assert p4.metric([1, 0], [.5, .49])['balanced_accuracy'] == 1.0
    assert vm.metrics([1, 0], [.5, .49])['balanced_accuracy'] == 1.0

# ---- single-class / empty behaviour
def test_single_class_phase4_returns_undefined():
    m = p4.metric([1, 1, 1], [.2, .3, .4])
    assert m['AUROC'] is None and m['balanced_accuracy'] is None and m['log_loss'] is not None
    assert p4.metric([], [])['AUROC'] is None
    assert math.isnan(fr.auroc([1, 1], [.1, .2]))

def test_single_class_validate_migration_reports_undefined():
    """F09 regression (was: ZeroDivisionError). Single-class AUROC/BA are undefined (None)."""
    m = vm.metrics([1, 1, 1], [.2, .3, .4])
    assert m['AUROC'] is None and m['balanced_accuracy'] is None and m['log_loss'] is not None

# ---- outcome classification edge cases (phase4_transfer.out)
def row(**kw):
    base = dict(technical_missing='FALSE', source_relation='CONFLICT', observed_outcome_available='TRUE', observed_outcome='angry',
                modality1_source_label='angry', modality2_source_label='sad', route='AT')
    base.update(kw); return base

@pytest.mark.parametrize('kw,exp', [
    ({}, 'SIDE_A'), ({'observed_outcome': 'sad'}, 'SIDE_T'), ({'observed_outcome': 'sad', 'route': 'AV'}, 'SIDE_V'),
    ({'observed_outcome': 'happy'}, 'OTHER'), ({'observed_outcome': 'PARSE_FAIL'}, 'PARSE_FAIL'),
    ({'technical_missing': 'TRUE'}, 'TECH_MISSING'), ({'observed_outcome_available': 'FALSE'}, 'TECH_MISSING'),
    ({'source_relation': 'SAME_LABEL'}, 'SAME_LABEL'), ({'technical_missing': 'TRUE', 'source_relation': 'SAME_LABEL'}, 'TECH_MISSING'),
])
def test_outcome_mapping(kw, exp):
    assert p4.out(row(**kw)) == exp

def test_outcome_mapping_is_case_sensitive():
    """Documented behaviour: 'Angry' vs 'angry' would become OTHER (no normalisation). Data audit found 0 such cases."""
    assert p4.out(row(observed_outcome='Angry')) == 'OTHER'

def test_parse_fail_and_tech_missing_never_enter_binary_denominator():
    rows = [dict(row(observed_outcome=o), outcome=None) for o in ['angry', 'sad', 'PARSE_FAIL', 'happy']]
    for r in rows: r['outcome'] = p4.out(r)
    ev = [r for r in rows if r['outcome'] in ('SIDE_A', 'SIDE_T', 'SIDE_V')]
    assert len(ev) == 2

def test_truth_helpers_disagree_on_numeric_strings():
    """FINDING (P3): truth('1') differs across new modules."""
    assert p4.truth('1') is True and an.truth('1') is False
    assert p4.truth(True) and an.truth(True) and an.truth('TRUE') and p4.truth('true')

# ---- bootstrap / clustering
def test_cluster_ci_resamples_whole_clusters_and_is_deterministic():
    vals = [1, 1, 1, 0, 0, 0, 1, 0]; cl = ['a', 'a', 'a', 'b', 'b', 'b', 'c', 'd']
    z1 = an.cluster_ci(vals, cl, 'MCRtest'); z2 = an.cluster_ci(vals, cl, 'MCRtest')
    assert z1 == z2 and z1['n_clusters'] == 4 and z1['n_items'] == 8 and abs(z1['estimate'] - .5) < 1e-12
    # equal-cluster weighting estimand differs when cluster sizes differ
    assert abs(an.cluster_ci(vals, cl, 'MCRtest', True)['estimate'] - (1 + 0 + 1 + 0) / 4) < 1e-12

def test_bootstrap_seed_depends_on_tag_same_population_gets_different_ci():
    """FINDING (P3): identical populations under different tags get different CIs (e.g. LISTEN DUAL vs STRICT_DUAL)."""
    vals = list(RNG.random(61)); cl = [str(i) for i in range(61)]
    a = an.cluster_ci(vals, cl, 'MCRx')['ci95']; b = an.cluster_ci(vals, cl, 'MCRy')['ci95']
    assert a != b

def test_phase4_subgroup_ci_drops_single_class_replicates():
    rows = []
    for i in range(10):
        rows.append(dict(source_relation='CONFLICT', outcome='SIDE_A' if i == 0 else 'SIDE_T', source_item_id=f'i{i}',
                         route='AT', FIRST_IS_MODALITY1='TRUE', delta_source_label_probability_raw=.1 * i,
                         delta_normalized_entropy_raw=.05 * i, delta_top1_top2_margin_raw=.02 * i))
    binding = json.loads((CHECKOUT / 'frozen/source_model/binding.json').read_text())
    z = p4.subgroup_ci(rows, 'M3a', binding, 'tag')
    assert z['defined_bootstraps'] < 2000  # conditional CI: replicates without SIDE_A are discarded

def test_holm_matches_manual():
    rows = [{'p_value': p} for p in [.01, .04, .03, .5]]
    an.holm(rows)
    assert [round(r['p_holm'], 10) for r in rows] == [0.04, 0.09, 0.09, 0.5]

def test_signflip_pvalue_bounds():
    v = [1] * 30 + [0] * 10; cl = [str(i) for i in range(40)]
    z = an.paired(v, cl, 'MCRflip', True)
    assert 0 < z['p_value'] <= 1 and z['p_value'] >= 1 / (an.PERM + 1)

def test_four_regime_cluster_boot_deterministic():
    stat = lambda idx: float(np.mean(Y[idx]))
    cl = np.arange(len(Y)) // 3
    assert fr.cluster_boot(cl, stat, reps=200) == fr.cluster_boot(cl, stat, reps=200)

def test_entropy_uses_seven_candidates():
    assert abs(fr.normalized_entropy_from_probs([1 / 7] * 7) - 1) < 1e-12
    # 16 uniform candidates normalised by log(7) exceeds 1: helper is only valid for 7-class B3 vectors
    assert fr.normalized_entropy_from_probs([1 / 16] * 16) > 1

# ---- CSV/JSON dtype drift
def test_csv_string_booleans_and_numeric_strings():
    assert p4.truth('TRUE') and not p4.truth('False') and not p4.truth('')
    m1 = p4.metric([1, 0, 1], [0.7, 0.2, 0.6]); m2 = p4.metric(['1', '0', '1'], ['0.7', '0.2', '0.6'])
    assert m1 == m2  # np.array(..., int/float) coerces numeric strings

# ---- validator robustness (runs on a disposable copy, never on the reviewed checkout)
@pytest.fixture(scope='module')
def scratch_clone(tmp_path_factory):
    d = tmp_path_factory.mktemp('clone') / 'repo'
    subprocess.run(['git', 'clone', '-q', str(CHECKOUT), str(d)], check=True)
    subprocess.run(['git', '-C', str(d), 'checkout', '-q', os.environ.get('PR4_HEAD', 'HEAD')], check=True)
    return d

def run_validator(repo, tmp_path, *flags):
    rep = tmp_path / 'r.json'
    return subprocess.run([sys.executable, *flags, str(repo / 'analyses/transfer_failure_integration_v1/validate_migration.py'), '--report', str(rep)], capture_output=True, text=True)

def test_validator_detects_corruption_normally(scratch_clone, tmp_path):
    f = scratch_clone / 'results/transfer_failure_integration_v1/04_TRANSFER_CLAIM_BOUNDARY_MATRIX.md'
    orig = f.read_bytes(); f.write_bytes(orig + b'x')
    try:
        r = run_validator(scratch_clone, tmp_path)
        assert r.returncode != 0 and '"status": "FAIL"' in r.stdout and 'sha256_mismatch' in r.stdout
    finally:
        f.write_bytes(orig)

def test_validator_fails_on_corruption_under_python_O(scratch_clone, tmp_path):
    """F04 regression (was: PASS under -O). Corrupted checkout must FAIL with non-zero exit even under python -O."""
    f = scratch_clone / 'results/transfer_failure_integration_v1/04_TRANSFER_CLAIM_BOUNDARY_MATRIX.md'
    orig = f.read_bytes(); f.write_bytes(orig + b'x')
    try:
        r = run_validator(scratch_clone, tmp_path, '-O')
        assert r.returncode != 0 and '"status": "FAIL"' in r.stdout and '"status": "PASS"' not in r.stdout
    finally:
        f.write_bytes(orig)

def test_validator_detects_unlisted_new_files(scratch_clone, tmp_path):
    """F09 regression (was: PASS). A committed in-scope file absent from SHA256SUMS must FAIL."""
    extra = scratch_clone / 'results/transfer_failure_integration_v1/UNLISTED_EXTRA.csv'
    extra.write_text('a,b\n1,2\n')
    subprocess.run(['git', '-C', str(scratch_clone), 'add', str(extra)], check=True)
    subprocess.run(['git', '-C', str(scratch_clone), '-c', 'user.email=r@x', '-c', 'user.name=r', 'commit', '-qm', 'extra'], check=True)
    try:
        r = run_validator(scratch_clone, tmp_path)
        assert r.returncode != 0 and 'sha256sums_missing_entry_for_added_file' in r.stdout
    finally:
        subprocess.run(['git', '-C', str(scratch_clone), 'reset', '-q', '--hard', 'HEAD~1'], check=True)
