"""POST_AUDIT_REANALYSIS: observed-response joins and source-fixed comparisons.

Run with python -m analyses.post_audit.replay --output NEW_DIRECTORY.
No inference, target fitting, calibration, selection, or threshold optimization.
"""
import argparse
import contextlib
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.special import expit
from analyses.phase2 import publication_cv_math as source_math
from src.common.runtime import REPO, verify_release
from src.common.benchmarks.emotiontalk_controlled_parser_v1 import parse_label
from src.cross_regime.zero_refit import evaluate, metrics
from src.reconstruction.mcr.content_duplicates import content_groups

ORIGIN = 'POST_AUDIT_REANALYSIS'
SEED = 20261008
BOOTSTRAPS = 2000
METRICS = ('log_loss', 'Brier_score', 'AUROC', 'balanced_accuracy')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def csvrows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def jsonrows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s]

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('x', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

def verify_evidence(root=REPO):
    manifest = read(root/'evidence/EVIDENCE_MANIFEST_V1.json')
    for item in manifest['files']:
        path = root/item['path']
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Unsafe evidence path')
        if not path.is_file() or digest(path) != item['sha256']:
            raise ValueError('Missing or hash-mismatched evidence: '+item['path'])
    return len(manifest['files'])

def unique(rows, fields):
    result = {}
    for row in rows:
        key = tuple(row[f] for f in fields)
        if key in result:
            raise ValueError('Duplicate scientific join key: '+str(key))
        result[key] = row
    return result

def compare_prediction_rows(actual, reference, tolerance=1e-12):
    """Exact scientific IDs and support; tolerate only numeric roundoff, not drift."""
    keys=['analysis_role','target_record_id']
    a,b=unique(actual,keys),unique(reference,keys)
    if a.keys()!=b.keys():
        raise ValueError('B3 corrected prediction identity mismatch')
    numeric={'predicted_p_SIDE_A','delta_source_label_probability_raw',
             'delta_normalized_entropy_raw','delta_top1_top2_margin_raw'}
    for key,row in a.items():
        if row.keys()!=b[key].keys():
            raise ValueError('B3 corrected prediction schema mismatch')
        for field,value in row.items():
            old=b[key][field]
            if field in numeric and value!='' and old!='':
                if not np.isfinite(float(value)) or not np.isfinite(float(old)) or abs(float(value)-float(old))>tolerance:
                    raise ValueError('B3 corrected prediction value mismatch '+field)
            elif value!=old:
                raise ValueError('B3 corrected prediction identity/support mismatch '+field)
    return len(a)

def response_outcome(row):
    parsed = parse_label(row['raw_generation'])
    if (parsed['parsed_label'], parsed['parser_status']) != (row['parsed_label'], row['parser_status']):
        raise ValueError('Response/parser mismatch')
    if not row['generation_success'] or not row['parser_execution']:
        raise ValueError('Historical response execution incomplete')
    label = parsed['parsed_label']
    if parsed['parser_status'] != 'OK':
        return 'PARSE_FAIL'
    if row['y_M1'] == row['y_M2']:
        return 'SHARED_LABEL' if label == row['y_M1'] else 'OTHER'
    return 'SIDE_MODALITY_1' if label == row['y_M1'] else 'SIDE_MODALITY_2' if label == row['y_M2'] else 'OTHER'

def reconstruct_source():
    measurements = unique(csvrows(REPO/'manifests/emotiontalk/source_measurements.csv'), ['utterance_id'])
    responses = jsonrows(REPO/'evidence/emotiontalk/phase2_observed_responses.jsonl')
    observed = unique(responses, ['utterance_id', 'pair', 'arm'])
    expected = set()
    for (uid,), row in measurements.items():
        for pair in ('AT', 'AV', 'VT'):
            if metrics.truth(row['DualReadable_'+pair]):
                for order in (pair, pair[::-1]):
                    expected.add((uid, pair, '_THEN_'.join(order)))
    if set(observed) != expected or len(observed) != 2132:
        raise ValueError('Phase2 frozen population/order identities changed')
    binding = read(REPO/'frozen/source_model/binding.json')
    scales = binding['scalers']
    records = []
    for row in responses:
        uid, pair = row['utterance_id'], row['pair']
        measurement = measurements[(uid,)]
        for key in ('candidate_sequence_id', 'candidate_sequence'):
            if row[key] != measurement[key]:
                raise ValueError('Phase2 candidate identity changed')
        if (row['y_M1'], row['y_M2']) != (measurement['y_'+pair[0]], measurement['y_'+pair[1]]):
            raise ValueError('Phase2 source labels changed')
        if row['actual_evidence_order'] != row['arm'].split('_THEN_'):
            raise ValueError('Phase2 presentation identity changed')
        outcome = response_outcome(row)
        canonical='SIDE_'+pair[0] if outcome=='SIDE_MODALITY_1' else 'SIDE_'+pair[1] if outcome=='SIDE_MODALITY_2' else outcome
        if outcome != row['joint_outcome'] or canonical != row['canonical_modality_outcome']:
            raise ValueError('Phase2 observed outcome changed')
        if row['y_M1'] == row['y_M2'] or outcome not in ('SIDE_MODALITY_1', 'SIDE_MODALITY_2'):
            continue
        record = {'utterance_id':uid, 'pair':pair, '_y':int(outcome=='SIDE_MODALITY_1'),
                  '_order':int(row['actual_evidence_order'][0]==pair[0])}
        for prefix, key, zkey in [('source_prob','source_probability','_srcz'),
                                 ('entropy','normalized_entropy','_entz'),
                                 ('margin','top1_top2_margin','_marz')]:
            delta = float(measurement[prefix+'_'+pair[0]])-float(measurement[prefix+'_'+pair[1]])
            record[zkey] = (delta-scales[key]['mean'])/scales[key]['sd']
        records.append(record)
    reference = read(REPO/'frozen/source_model/publication_cv_records.json')
    if isinstance(reference, dict):
        reference = reference['records']
    if len(records) != 663 or len(reference) != len(records):
        raise ValueError('Source fitting population mismatch')
    for actual, frozen in zip(records, reference):
        for key in actual:
            if isinstance(actual[key], float):
                if abs(actual[key]-frozen[key]) > 1e-12:
                    raise ValueError('Independent source feature reconstruction mismatch '+key)
            elif actual[key] != frozen[key]:
                raise ValueError('Source analysis row identity mismatch '+key)
    return records, observed

def source_baselines(records):
    """Only this source-only function fits the new diagnostic baseline."""
    if len(records)!=663 or any(r.get('target_dataset') for r in records):
        raise ValueError('Frozen source population required')
    if records!=read(REPO/'frozen/source_model/publication_cv_records.json'):
        raise ValueError('Baseline fitting requires the exact verified source records')
    m0 = {r['term']:float(r['coefficient_log_odds']) for r in
          csvrows(REPO/'frozen/source_model/08_M0_M3_model_results.csv') if r['model']=='M0'}
    if set(m0) != {'intercept_AT','pair_AV','pair_VT'}:
        raise ValueError('Frozen M0 coefficient set changed')
    for pair in ('AT','AV','VT'):
        rows = [r for r in records if r['pair']==pair]
        p = float(expit(m0['intercept_AT']+m0.get('pair_'+pair,0)))
        if abs(p-np.mean([r['_y'] for r in rows]))>1e-12:
            raise ValueError('M0 source prevalence binding mismatch')
    X, names = source_math.design(records, ['ord'])
    fitted = source_math.fit(X, np.asarray([r['_y'] for r in records]))
    if not fitted['ok']:
        raise ValueError('Source-only diagnostic baseline did not converge')
    common = {'fit_population':'EMOTIONTALK_SOURCE_RESOLVED_CONFLICT_663',
              'analysis_origin':ORIGIN,
              'source_records_sha256':digest(REPO/'frozen/source_model/publication_cv_records.json'),
              'target_fit':False,'threshold':0.5}
    return {'M0':{**common,'parameters':m0,'role':'EARLIER_DECLARED_SOURCE_FIXED_CONSTANT_PREFERENCE',
                   'fit_identity':'HISTORICAL_FROZEN_COEFFICIENTS_NOT_REFITTED'},
            'M0_PLUS_ORDER':{**common,'parameters':dict(zip(names,map(float,fitted['b']))),
                   'role':'POST_AUDIT_DIAGNOSTIC_SOURCE_ONLY_BASELINE',
                   'algorithm':'Historical unpenalized Newton/IRLS design [AT intercept, AV/VT offsets, FIRST_IS_MODALITY1]',
                   'fit_identity':'POST_AUDIT_SOURCE_ONLY_FIT', 'iterations':fitted['it']}}

def baseline_predict(binding, pair, order):
    """Prediction only; no fitting or calibration path."""
    if binding['target_fit'] or binding['fit_population']!='EMOTIONTALK_SOURCE_RESOLVED_CONFLICT_663' or binding['threshold']!=0.5:
        raise ValueError('Source-fixed baseline required')
    c=binding['parameters']
    return float(expit(c['intercept_AT']+c.get('pair_'+pair,0)+c.get('FIRST_IS_MODALITY1',0)*order))

def verify_phase3(plans, outputs, phase2):
    plan = unique(plans, ['utterance_id','tri_order'])
    actual = unique(outputs, ['utterance_id','tri_order'])
    if set(plan)!=set(actual):
        raise ValueError('Missing/unexpected Phase3 observed-output join')
    result = []
    for key, row in plan.items():
        output = actual[key]
        order = row['tri_order'].split('_THEN_')
        if set(order)!=set('ATV') or len(order)!=3:
            raise ValueError('Invalid trimodal order')
        if sorted(Counter(row['y_'+m] for m in 'ATV').values()) != [1,2]:
            raise ValueError('Phase3 population must be TWO_VS_ONE')
        if output['actual_evidence_order']!=order:
            raise ValueError('Phase3 execution order mismatch')
        for field in ('y_A','y_T','y_V','candidate_sequence_id','candidate_sequence','majority_label','minority_label'):
            if output[field]!=row[field]:
                raise ValueError('Phase3 input identity mismatch '+field)
        majority = {m for m in 'ATV' if row['y_'+m]==row['majority_label']}
        minority = next(m for m in 'ATV' if m not in majority)
        edge_info = []
        selections = []
        failures = []
        for number in (1,2):
            # Derive the informative edge from modality identities; compare the frozen plan.
            pair = row['informative_pair_'+str(number)]
            if pair not in ('AT','AV','VT') or minority not in pair or len(majority.intersection(pair))!=1:
                raise ValueError('Invalid frozen informative edge')
            arm = '_THEN_'.join(sorted(pair, key=order.index))
            edge_key = (row['utterance_id'],pair,arm)
            if edge_key not in phase2:
                raise ValueError('Missing Phase2 composition evidence')
            edge = phase2[edge_key]
            outcome = response_outcome(edge)
            selected = pair[0] if outcome=='SIDE_MODALITY_1' else pair[1] if outcome=='SIDE_MODALITY_2' else None
            if selected is None:
                failures.append('PARSE_FAIL_INVOLVED' if outcome=='PARSE_FAIL' else 'OTHER_INVOLVED')
            selections.append(selected)
            if (arm,outcome,selected or '') != (row['matched_phase2_arm_'+str(number)],row['phase2_pairwise_outcome_'+str(number)],row['phase2_selected_modality_'+str(number)]):
                raise ValueError('Frozen composition edge differs from observed response')
            edge_info.append({'phase2_edge_'+str(number):'|'.join(edge_key),
                              'phase2_outcome_'+str(number):outcome})
        if row['informative_pair_1']==row['informative_pair_2']:
            raise ValueError('Duplicated composition edge')
        if failures:
            cls,label,reason='UNRESOLVED',None,failures[0]
        elif all(m in majority for m in selections):
            cls,label,reason='MAJORITY',row['majority_label'],''
        elif all(m==minority for m in selections):
            cls,label,reason='MINORITY',row['minority_label'],''
        else:
            cls,label,reason='UNRESOLVED',None,'EDGE_DISAGREEMENT'
        if (cls,label or '',reason)!=(row['composition_prediction_class'],row['composition_predicted_label'],row['unresolved_reason']):
            raise ValueError('Independently derived composition prediction differs from freeze')
        parsed=parse_label(output['raw_generation'])
        if (parsed['parsed_label'],parsed['parser_status']) != (output['parsed_label'],output['parser_status']):
            raise ValueError('Phase3 output parser mismatch')
        if not output['generation_success'] or not output['parser_execution']:
            raise ValueError('Phase3 observed execution incomplete')
        resolved=cls!='UNRESOLVED'
        result.append({'utterance_id':key[0],'tri_order':key[1],
                       **edge_info[0],**edge_info[1],'prediction_class':cls,
                       'predicted_label':label,'observed_label':parsed['parsed_label'],
                       'prediction_resolved':resolved,'match_indicator':int(label==parsed['parsed_label']) if resolved else None,
                       'unresolved_reason':reason,'execution_state':'GENERATION_SUCCESS',
                       'parser_status':parsed['parser_status'],
                       'scientific_role':'TWO_VS_ONE_PAIRWISE_TO_TRIMODAL_CONSISTENCY',
                       'analysis_origin':ORIGIN})
    return result

def listen_condition(rows, condition):
    if condition not in ('3A','3B','3C','ALL'):
        raise ValueError('Unknown LISTEN condition')
    return [r for r in rows if condition=='ALL' or r['condition']==condition]

def target_rows():
    measurements = csvrows(REPO/'evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv')
    lookup = unique(measurements,['dataset','stable_dataset_id','modality'])
    datasets={}
    for ds,folder in [('MCR','mcr'),('LISTEN','listen'),('CA-MER','camer')]:
        rows=csvrows(REPO/'manifests'/folder/'frozen_joint_outcomes.csv')
        unique(rows,['target_record_id'])
        for row in rows:
            a=lookup[(ds,row['source_item_id'],'A')]
            b=lookup[(ds,row['source_item_id'],'V' if ds=='CA-MER' else 'T')]
            fa=evaluate.protocol.features(json.loads(a['candidate_labels']),json.loads(a['candidate_probabilities']),a['raw_source_label'])
            fb=evaluate.protocol.features(json.loads(b['candidate_labels']),json.loads(b['candidate_probabilities']),b['raw_source_label'])
            for raw,feat in [('delta_source_label_probability_raw','source_label_probability'),
                             ('delta_normalized_entropy_raw','normalized_entropy'),
                             ('delta_top1_top2_margin_raw','top1_top2_margin')]:
                row[raw]=fa[feat]-fb[feat] if fa[feat] is not None and fb[feat] is not None else None
            for field in ('z_delta_source_label_probability','z_delta_normalized_entropy','z_delta_top1_top2_margin'):
                row[field]=''
        datasets[ds]=rows
    return datasets

def transferred_predict(row, pair, model, binding):
    if any(binding[k] for k in ('target_coefficient_fit','target_scaler_fit','target_threshold_tuning')):
        raise ValueError('Frozen source-only transfer required')
    c=binding['models'][model]['parameter_values']
    strength='source_probability' if model=='M3a' else 'top1_top2_margin'
    raw='delta_source_label_probability_raw' if model=='M3a' else 'delta_top1_top2_margin_raw'
    term='delta_source_label_probability_per_SD' if model=='M3a' else 'delta_top1_top2_margin_per_SD'
    if row[raw] is None:
        return None
    s=binding['scalers']
    z=(row[raw]-s[strength]['mean'])/s[strength]['sd']
    ent=(row['delta_normalized_entropy_raw']-s['normalized_entropy']['mean'])/s['normalized_entropy']['sd']
    return float(expit(c['intercept_AT']+c.get('pair_'+pair,0)+c[term]*z+c['delta_normalized_entropy_per_SD']*ent+
                       c['FIRST_IS_MODALITY1']*metrics.truth(row['FIRST_IS_MODALITY1'])))

def uncertainty(rows, pair, predictions, cluster_ids, bootstraps=BOOTSTRAPS):
    """Paired percentile CIs; sample all conflict clusters including unresolved trials."""
    keep=[i for i,r in enumerate(rows) if r['source_relation']=='CONFLICT']
    conflict=[rows[i] for i in keep]
    if not conflict:
        raise ValueError('Empty prespecified conflict denominator')
    y=np.array([1 if metrics.resolve_side(r,pair)=='SIDE_A' else 0 if metrics.resolve_side(r,pair) else -1 for r in conflict])
    pred={name:np.array([scores[i] for i in keep],float) for name,scores in predictions.items()}
    finite=np.logical_and.reduce([np.isfinite(p) for p in pred.values()])
    mask=(y>=0)&finite
    if not mask.any():
        raise ValueError('No shared evaluated rows')
    groups={}
    for i,index in enumerate(keep):
        groups.setdefault(cluster_ids[index],[]).append(i)
    groups=[np.array(groups[g],int) for g in sorted(groups)]
    estimates={name:source_math.metric(y[mask],p[mask]) for name,p in pred.items()}
    estimates={name:{**m,'coverage':float(mask.mean())} for name,m in estimates.items()}
    names=tuple(pred)
    samples={name:{metric:[] for metric in (*METRICS,'coverage')} for name in names}
    references=[name for name in ('M0','M0_PLUS_ORDER') if name in names]
    deltas={name:{base:{metric:[] for metric in METRICS} for base in references} for name in names}
    rng=np.random.default_rng(SEED)
    for _ in range(bootstraps):
        idx=np.concatenate([groups[j] for j in rng.integers(0,len(groups),len(groups))])
        valid=mask[idx]
        yi=y[idx][valid]
        current={}
        for name,p in pred.items():
            m=source_math.metric(yi,p[idx][valid]) if len(yi) else {key:None for key in METRICS}
            m['coverage']=float(valid.mean())
            current[name]=m
            for key,value in m.items():
                if value is not None:samples[name][key].append(value)
        for name in names:
            for reference in references:
                for key in METRICS:
                    value,base=current[name][key],current[reference][key]
                    if value is not None and base is not None:deltas[name][reference][key].append(value-base)
    result=[]
    identity=hashlib.sha256('\n'.join(r['target_record_id'] for r,m in zip(conflict,mask) if m).encode()).hexdigest()
    for name in names:
        row={'model':name,'N_planned':len(rows),'N_conflict':len(conflict),'N_evaluated':int(mask.sum()),
             'class_SIDE_A':int(sum(y[mask]==1)),'class_other_side':int(sum(y[mask]==0)),
             'N_clusters':len(groups),'evaluated_identity_sha256':identity,**estimates[name],
             'threshold':0.5,'bootstrap_seed':SEED,'bootstrap_replicates':bootstraps,
             'CI_method':'PAIRED_CLUSTER_PERCENTILE_95_ALL_CONFLICT_CLUSTERS',
             'target_fit':False,'analysis_origin':ORIGIN}
        for key,values in samples[name].items():
            row[key+'_CI_low'],row[key+'_CI_high']=map(float,np.quantile(values,[.025,.975])) if values else (None,None)
            row[key+'_defined_bootstraps']=len(values)
        for reference in references:
            for key,values in deltas[name][reference].items():
                value,base=estimates[name][key],estimates[reference][key]
                prefix=key+'_minus_'+reference
                row[prefix]=value-base if value is not None and base is not None else None
                row[prefix+'_CI_low'],row[prefix+'_CI_high']=map(float,np.quantile(values,[.025,.975])) if values else (None,None)
                row[prefix+'_defined_bootstraps']=len(values)
        result.append(row)
    return result

def compare_targets(datasets, baselines, bootstraps=BOOTSTRAPS):
    binding=read(REPO/'frozen/source_model/binding.json')
    specs=[('MCR_AT_PRIMARY','MCR','AT','M3a',datasets['MCR']),
           ('MCR_AT_MARGIN_SENSITIVITY','MCR','AT','M3b',datasets['MCR']),
           ('CAMER_AV_SUPPORT_LIMITED_SOURCEPROB','CA-MER','AV','M3a',
            [r for r in datasets['CA-MER'] if r['support_limited_diagnostic_role']=='SUPPLEMENTARY_SUPPORT_LIMITED_DIAGNOSTIC']),
           ('CAMER_AV_MARGIN_SENSITIVITY','CA-MER','AV','M3b',datasets['CA-MER'])]
    for cond,role in [('3C','LISTEN_3C_JOINT_ARBITRATION'),('3A','LISTEN_3A_TEXT_DIAGNOSTIC'),
                      ('3B','LISTEN_3B_AUDIO_DIAGNOSTIC'),('ALL','LISTEN_ALL_MIXED_HISTORICAL')]:
        specs.append((role,'LISTEN','AT','M3b',listen_condition(datasets['LISTEN'],cond)))
    comparisons=[]
    for role,ds,pair,model,rows in specs:
        predictions={name:[baseline_predict(value,pair,metrics.truth(r['FIRST_IS_MODALITY1'])) for r in rows]
                     for name,value in baselines.items()}
        predictions['FROZEN_POOLED_'+model]=[transferred_predict(r,pair,model,binding) for r in rows]
        cluster=[r['source_item_id'].rsplit('_',1)[0] if ds=='LISTEN' else r['source_item_id'] for r in rows]
        reports=uncertainty(rows,pair,predictions,cluster,bootstraps)
        for report in reports:
            report.update(analysis_role=role,dataset=ds,transfer_model=model,
                          model_role=baselines[report['model']]['role'] if report['model'] in baselines else 'FROZEN_POOLED_TRANSFER',
                          metric_origin='CORRECTED_B3_PROBABILITY_VECTORS',
                          scientific_role='LATER_ADDED_EXPLORATORY_LABEL_ASSERTION_REGIME' if ds=='MCR' else 'EARLIER_DECLARED_TARGET_ROUTE',
                          cluster_definition='UNDERLYING_UID_ACROSS_CONDITIONS' if ds=='LISTEN' else 'SOURCE_ITEM_ID_ACROSS_ORDERS',
                          counterbalanced_order_effect_identifiable=False if role=='LISTEN_3C_JOINT_ARBITRATION' else None)
        comparisons.extend(reports)
    return comparisons

def run(output, bootstraps=BOOTSTRAPS):
    output=Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new output directory; frozen evidence is immutable')
    verify_release()
    evidence_count=verify_evidence()
    output.mkdir(parents=True)
    source,phase2=reconstruct_source()
    baselines=source_baselines(source)
    write_json(output/'SOURCE_BASELINE_BINDING_V1.json',baselines)
    write_csv(output/'PHASE2_RECONSTRUCTED_SOURCE_RECORDS_V1.csv',[{**r,'analysis_origin':ORIGIN} for r in source])
    evaluate.G=REPO/'evidence/b3'
    evaluate.OUT=output/'corrected_replay'
    with contextlib.redirect_stdout(io.StringIO()):
        evaluate.main()
    prediction_count=compare_prediction_rows(csvrows(evaluate.OUT/'B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv'),
                                            csvrows(REPO/'evidence/b3/historical_corrected_zero_refit_predictions.csv'))
    current=read(evaluate.OUT/'B3_ZERO_REFIT_FINAL_EVALUATION_V1.json')
    historical=read(REPO/'results/mainline_summary/cross_regime/B3_ZERO_REFIT_FINAL_EVALUATION_V1.json')
    for role,actual in current['analyses'].items():
        old=historical['analyses'][role]
        for key in ('N_prespecified','N_evaluated','analysis_role'):
            if actual.get(key)!=old.get(key):
                raise ValueError('B3 corrected historical replay mismatch '+role+' '+key)
        if set(actual.get('metrics') or {})!=set(old.get('metrics') or {}):
            raise ValueError('B3 historical metric schema/support mismatch')
        for key,value in (actual.get('metrics') or {}).items():
            prior=old['metrics'][key]
            if (value is None)!=(prior is None) or (value is not None and abs(value-prior)>1e-12):
                raise ValueError('B3 historical metric replay mismatch '+role+' '+key)
        if actual.get('metrics') is None and old.get('metrics') is not None:
            raise ValueError('B3 structural support mismatch')
        if actual.get('coverage')!=old.get('coverage'):
            raise ValueError('B3 frozen coverage mismatch')
    phase3=verify_phase3(csvrows(REPO/'manifests/emotiontalk/trimodal_plan.csv'),
                         jsonrows(REPO/'evidence/emotiontalk/phase3_observed_outputs.jsonl'),phase2)
    resolved=sum(r['prediction_resolved'] for r in phase3)
    correct=sum(r['match_indicator'] or 0 for r in phase3)
    if (len(phase3),resolved,correct,len(phase3)-resolved)!=(402,294,268,108):
        raise ValueError('Recomputed Phase3 historical identities disagree')
    counts=Counter(r['utterance_id'] for r in phase3)
    if len(counts)!=67 or set(counts.values())!={6}:
        raise ValueError('Phase3 67 UID x 6 orders mismatch')
    write_csv(output/'PHASE3_ROW_LEVEL_VERIFICATION_V1.csv',phase3)
    datasets=target_rows()
    comparisons=compare_targets(datasets,baselines,bootstraps)
    write_csv(output/'ZERO_REFIT_BASELINE_COMPARISON_V1.csv',comparisons)
    listen=[r for r in comparisons if r['dataset']=='LISTEN']
    write_csv(output/'LISTEN_CONDITION_DIAGNOSTICS.csv',listen)
    write_csv(output/'LISTEN_JOINT_ONLY_REPORT.csv',[r for r in listen if r['analysis_role']=='LISTEN_3C_JOINT_ARBITRATION'])
    canonical=unique(csvrows(REPO/'manifests/mcr/canonical_arbitration.csv'),['sample_id'])
    identities=csvrows(REPO/'evidence/mcr/recomputed_audio_identities.csv')
    subset=[r for r in identities if (r['sample_id'],) in canonical]
    if len(subset)!=909 or len(identities)!=1000:
        raise ValueError('MCR rehashed/frozen population mismatch')
    for row in subset:
        if row['actual_audio_sha256']!=canonical[(row['sample_id'],)]['audio_sha256']:
            raise ValueError('Stored and actual WAV byte hashes disagree')
    duplicates=content_groups(subset)
    if len(duplicates)!=7 or len({r['actual_audio_sha256'] for r in duplicates})!=3:
        raise ValueError('MCR content duplicate group mismatch')
    write_csv(output/'MCR_CONTENT_DUPLICATE_AUDIT_V1.csv',duplicates)
    affected={r['sample_id'] for r in duplicates}
    sensitivity=[]
    for model in ('M3a','M3b'):
        rows=[r for r in datasets['MCR'] if r['source_item_id'] not in affected]
        binding=read(REPO/'frozen/source_model/binding.json')
        predictions={'M0':[baseline_predict(baselines['M0'],'AT',metrics.truth(r['FIRST_IS_MODALITY1'])) for r in rows],
                     'FROZEN_POOLED_'+model:[transferred_predict(r,'AT',model,binding) for r in rows]}
        reports=uncertainty(rows,'AT',predictions,[r['source_item_id'] for r in rows],bootstraps)
        sensitivity.extend({**r,'scientific_role':'SEPARATE_POST_AUDIT_DUPLICATE_EXCLUSION_SENSITIVITY',
                            'exclusion_rule':'ALL_7_FROZEN_IDS_IN_ANY_RECOMPUTED_CONTENT_DUPLICATE_GROUP',
                            'historical_population_modified':False} for r in reports)
    write_csv(output/'MCR_CONTENT_DUPLICATE_SENSITIVITY_V1.csv',sensitivity)
    summary={'analysis_origin':ORIGIN,'evidence_files_verified':evidence_count,
             'B3_CORRECTED_PREDICTION_ROWS_VERIFIED':prediction_count,'numeric_replay_tolerance':1e-12,
             'B3_CORRECTED_ROW_LEVEL_REPLAY':'PASS','PHASE2_EVIDENCE_RECOVERED':'PASS',
             'PHASE2_SOURCE_RECORDS':len(source),'PHASE3_ROW_LEVEL_REPLAY':'PASS',
             'PHASE3_PLANNED':len(phase3),'PHASE3_RESOLVED':resolved,'PHASE3_CORRECT':correct,
             'PHASE3_UNRESOLVED':len(phase3)-resolved,'PHASE3_FRACTION':correct/resolved,
             'PHASE3_ROLE':'TWO_VS_ONE_PAIRWISE_TO_TRIMODAL_CONSISTENCY',
             'LISTEN_3C_EVALUATION':'PASS','SOURCE_M0_BASELINE':'PASS',
             'MCR_DUPLICATE_VALIDATION':'PASS','MCR_CONTENT_DUPLICATE_GROUPS':3,
             'MCR_CONTENT_DUPLICATE_ROWS':7,'HISTORICAL_ARTIFACTS_MODIFIED':False,
             'GPU_EXECUTION':False,'target_fit':False,'SCIENTIFIC_RULING':'REQUIRES_INTERPRETATION',
             'bootstrap_seed':SEED,'bootstrap_replicates':bootstraps}
    write_json(output/'POST_AUDIT_CPU_REPLAY_V1.json',summary)
    print(json.dumps(summary,indent=2))
    return summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.output)

if __name__=='__main__':
    main()
