import ast,csv,hashlib,json,math
from collections import Counter
import pytest
from src.common.runtime import REPO,verify_release
from src.cross_regime.target_scoring import b3_protocol as b3,b3_scorer as scorer
from src.cross_regime.target_scoring.inputs import FrozenInputs,read,acquisition
from src.cross_regime.target_scoring.verify_runtime import portable_inventory_check
from src.cross_regime.zero_refit import metrics
def test_portable_inventory_membership_and_duplicate_rejection():
    portable_inventory_check(['a/x','a-1/y'],['a-1/y','a/x'])
    for observed in [['a/x','a/x'],['a/x'],['a/x','changed']]:
        with pytest.raises(ValueError):portable_inventory_check(['a/x','a-1/y'],observed)
def test_actual_frozen_assignment_modality_and_cache_identity():
    p=FrozenInputs();plan=read(p/'B3_TARGET_MEASUREMENT_MANIFEST_V1.json');assigned=read(p/'B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json')
    a={(r['dataset'],r['sample_id']):r for r in assigned['assignments']};groups={}
    assert (len(plan['measurements']),len(plan['forwards']))==(6354,5515)
    for r in plan['measurements']:
        k=(r['dataset'],r['sample_id']);groups.setdefault(k,[]).append(r)
        assert r['candidate_sequence']==a[k]['candidate_sequence']
        assert r['candidate_sequence_id']==a[k]['candidate_sequence_id']
        assert b3.cache_identity(r)['cache_key']==r['inference_cache_key']
        assert r['scoring_code_sha256']==scorer.implementation_sha256()
    assert len(groups)==3177
    assert Counter(k[0] for k in groups)=={'MCR':909,'LISTEN':768,'CA-MER':1500}
    assert all(len(v)==2 and len({tuple(r['candidate_sequence']) for r in v})==1 for v in groups.values())
def test_frozen_source_binding_and_unmodified_metric_equations():
    p=FrozenInputs();binding=read(p/'B3_SOURCE_MODEL_BINDING_V1.json')
    assert binding['threshold']==.5 and not any(binding[k] for k in ['target_scaler_fit','target_coefficient_fit','target_threshold_tuning'])
    for x in binding['artifacts']:
        if not x['artifact_path'].endswith('.py'):assert hashlib.sha256((p/x['artifact_path']).read_bytes()).hexdigest()==x['SHA256']
    expected=json.loads((REPO/'frozen/identity/metric_function_ast.json').read_text(encoding='utf-8'))
    got={n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in ast.parse(__import__('pathlib').Path(metrics.__file__).read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
    assert got==expected
    row={'delta_source_label_probability_raw':binding['scalers']['source_probability']['mean'],'delta_normalized_entropy_raw':binding['scalers']['normalized_entropy']['mean'],'FIRST_IS_MODALITY1':'TRUE'}
    c=binding['models']['M3a']['parameter_values']
    co={'primary':{'intercept_AT':c['intercept_AT'],'intercept_AV':c['intercept_AT']+c['pair_AV'],'beta_order_AT':c['FIRST_IS_MODALITY1'],'beta_order_AV':c['FIRST_IS_MODALITY1'],'beta_sourceprob':c['delta_source_label_probability_per_SD'],'beta_entropy':c['delta_normalized_entropy_per_SD']}}
    scalers={k:(binding['scalers'][k]['mean'],binding['scalers'][k]['sd']) for k in ['source_probability','normalized_entropy','top1_top2_margin']}
    assert metrics.prediction(row,'AT','primary',co,scalers)==pytest.approx(1/(1+math.exp(-(c['intercept_AT']+c['FIRST_IS_MODALITY1']))))
    assert metrics.prediction(row,'AV','primary',co,scalers)==pytest.approx(1/(1+math.exp(-(c['intercept_AT']+c['pair_AV']+c['FIRST_IS_MODALITY1']))))
def test_metric_fixture_and_no_unsupported_primary_relabeling():
    fixture=[{'target_record_id':'a','source_relation':'CONFLICT','observed_outcome_available':'TRUE','observed_outcome':'SIDE_A'},{'target_record_id':'t','source_relation':'CONFLICT','observed_outcome_available':'TRUE','observed_outcome':'SIDE_T'}]
    m,n=metrics.metrics(fixture,{'a':.8,'t':.2},'AT');assert n==2 and m['AUROC']==m['balanced_accuracy']==1 and m['log_loss']==pytest.approx(-math.log(.8))
    r=json.loads((REPO/'results/mainline_summary/cross_regime/B3_ZERO_REFIT_FINAL_EVALUATION_V1.json').read_text(encoding='utf-8'))
    assert r['analyses']['LISTEN_AT_PRIMARY']['metrics'] is None
    assert r['analyses']['CAMER_AV_FULL_PRIMARY']['metrics'] is None
    assert r['analyses']['CAMER_AV_SUPPORT_LIMITED_SOURCEPROB']['analysis_role'].startswith('SUPPLEMENTARY')
def test_population_identity_canonical_panel_and_raw_rules():
    with (REPO/'manifests/emotiontalk/EMOTIONTALK_MASTER_PANEL_V1.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==len({r['utterance_id'] for r in rows})==1500
    assert set(Counter(r['trimodal_pattern'] for r in rows).values())=={300}
    from src.reconstruction.mcr.reconstruct import emotion,description,duplicate_status
    assert emotion('Description: This audio expresses angry emotion.\nClassify the emotion.')=='angry'
    assert duplicate_status([{'gt':'sad'},{'gt':'happy'}],[0,1])=='CONFLICTING_GT_DUPLICATE'
    with pytest.raises(ValueError):emotion('Description: This audio expresses ambiguous emotion.\nClassify the emotion.')
def test_phase1_scoring_is_unconditional_after_generation():
    from src.emotiontalk.phase1 import execution
    import inspect
    tree=ast.parse(inspect.getsource(execution.perform_arm))
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='score_candidate_strings']
    assert len(calls)==1
    for n in ast.walk(tree):
        if isinstance(n,ast.If) and 'parser_status' in ast.unparse(n.test):assert calls[0] not in list(ast.walk(n))
def test_release_hashes():assert verify_release()['RELEASE_HASH_RECHECK']=='PASS'

def test_unchanged_scientific_kernel_asts():
    registry=json.loads((REPO/'frozen/identity/scientific_kernel_ast.json').read_text(encoding='utf-8'))
    for r in registry:
        funcs={n.name:n for n in ast.parse((REPO/r['current_path']).read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
        assert hashlib.sha256(ast.dump(funcs[r['function']],include_attributes=False).encode()).hexdigest()==r['AST_SHA256']

def test_phase2_frozen_population_and_metadata_semantics():
    from src.emotiontalk.phase2 import core
    phase1=core.read_json(core.PHASE1_JSON)
    counts,eligible,memberships,checks,summary=core.population_preflight(phase1)
    assert memberships==1066
    assert counts=={'AT':{'total':397,'conflict':62,'consistent':335},'AV':{'total':371,'conflict':146,'consistent':225},'VT':{'total':298,'conflict':140,'consistent':158}}
