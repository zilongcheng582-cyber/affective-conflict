import hashlib,json
from collections import Counter
from src.common.runtime import REPO,registry

def test_prepared_source_population_and_scaler_boundary():
    path=REPO/'frozen/source_model/publication_cv_records.json'
    rows=json.loads(path.read_text(encoding='utf-8'))
    provenance=json.loads((path.parent/'publication_cv_input_provenance.json').read_text(encoding='utf-8'))
    source=json.loads((path.parent/'EMOTIONTALK_PHASE2_SCIENTIFIC_ANALYSIS_V1_SUMMARY.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==provenance['prepared_SHA256']
    assert len(rows)==source['model_population']['records']==663
    assert len({r['utterance_id'] for r in rows})==source['model_population']['utterance_id_clusters']==274
    assert dict(Counter(r['pair'] for r in rows))==provenance['pair_counts']
    assert provenance['source_scaler_refitted'] is False
    assert provenance['publication_CV_recomputed_during_packaging'] is False
    assert all(r['_y'] in (0,1) and r['_order'] in (0,1) for r in rows)
    for feature in ('_srcz','_marz','_entz'):
        values=[r[feature] for r in rows]
        assert abs(sum(values)/len(values))<1e-12
        assert abs(sum(v*v for v in values)/len(values)-1)<1e-12

def test_registry_inputs_exist_and_old_cv_is_not_a_current_result():
    assert all((REPO/v).is_file() for v in registry().values())
    assert not (REPO/'results/mainline_summary/phase2/09_model_comparison.csv').exists()
    assert not (REPO/'results/mainline_summary/phase2/08_M0_M3_model_results.csv').exists()
    assert (REPO/'frozen/source_model/08_M0_M3_model_results.csv').is_file()
