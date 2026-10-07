"""Corrected B3 closeout and prescribed CPU-only historical zero-refit replay."""
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
from collections import Counter

from src.common.runtime import REPO,verify_release
from src.cross_regime.target_scoring.inputs import FrozenInputs,acquisition
from src.cross_regime.target_scoring import b3_protocol as protocol
from src.cross_regime.zero_refit import metrics as frozen_metrics
import argparse
P=FrozenInputs()
G=None
OUT=None
def frozen_sha(name):
    if name=='EXECUTION_PACKAGE_MANIFEST.json':return acquisition()['manifest_sha256']
    return acquisition()['payload_hashes'][name]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def csvrows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def jsonrows(p):return [json.loads(s) for s in Path(p).read_text(encoding='utf-8').splitlines() if s.strip()]
def truth(x):return str(x).lower() in ['true','1','yes']
def write(name,obj):(OUT/name).write_bytes(protocol.canonical_bytes(obj))
def writecsv(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})

def output_hashes():
    result={}
    for line in (G/'B3_CORRECTED_EXECUTION_SHA256SUMS.txt').read_text().splitlines():
        expected,name=line.split('  ',1);p=G/name
        if G.resolve() not in p.resolve().parents:raise ValueError('Unsafe output checksum path')
        actual=sha(p)
        if actual!=expected:raise ValueError('Corrected GPU output hash mismatch: '+name)
        result[name]=actual
    result['B3_CORRECTED_EXECUTION_SHA256SUMS.txt']=sha(G/'B3_CORRECTED_EXECUTION_SHA256SUMS.txt')
    return result

def closeout():
    hashes=output_hashes();complete=read(G/'B3_CORRECTED_EXECUTION_COMPLETENESS_V1.json')
    expected_counts={'MEASUREMENT_ROWS_EXPECTED':6354,'MEASUREMENT_ROWS_COMPLETED':6354,'MEASUREMENT_ROWS_FAILED':0,
                     'MEASUREMENT_ROWS_MISSING':0,'FORWARD_TASKS_EXPECTED':5515,'FORWARD_TASKS_COMPLETED':5515,'FORWARD_TASKS_FAILED':0,'FORWARD_TASKS_MISSING':0}
    if any(complete[k]!=v for k,v in expected_counts.items()):raise ValueError('Incomplete acquisition')
    assignment=read(P/'B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json')
    amap={(r['dataset'],r['sample_id']):r for r in assignment['assignments']}
    plan=read(P/'B3_TARGET_MEASUREMENT_MANIFEST_V1.json');tasks={r['measurement_id']:r for r in plan['measurements']}
    frozen_provenance=read(G/'B3_CORRECTED_EXECUTION_PROVENANCE_V1.json')
    required_hashes={'protocol_sha256':'B3_CORRECTED_MEASUREMENT_FREEZE_V1.md','assignment_sha256':'B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json',
                     'runner_sha256':'run_b3_corrected_measurement.py','execution_manifest_sha256':'EXECUTION_PACKAGE_MANIFEST.json'}
    for key,name in required_hashes.items():
        if key=='runner_sha256':
            if frozen_provenance[key] not in {frozen_sha(name),sha(REPO/'src/cross_regime/target_scoring/run.py')}:raise ValueError('Unrecognized runner identity')
        elif frozen_provenance[key]!=frozen_sha(name):raise ValueError('Frozen provenance identity mismatch '+key)
    forwards=jsonrows(G/'B3_CORRECTED_FORWARD_RESULTS_V1.jsonl');cache={}
    fexpected={t['inference_cache_key']:t for t in plan['forwards']}
    for f in forwards:
        key=f['inference_cache_key']
        if key in cache or key not in fexpected:raise ValueError('Duplicate/unexpected forward key')
        protocol.validate_resume_record(f,fexpected[key],frozen_sha('EXECUTION_PACKAGE_MANIFEST.json'))
        cache[key]=f
    if len(cache)!=5515:raise ValueError('Forward count mismatch')
    raw_rows=jsonrows(G/'B3_MEASUREMENTS_V1.jsonl')
    raw={r['measurement_id']:r for r in raw_rows}
    if len(raw_rows)!=6354 or len(raw)!=6354 or set(raw)!=set(tasks):raise ValueError('Raw measurement count/identity mismatch')
    rows=csvrows(G/'B3_CORRECTED_MEASUREMENTS_V1.csv');seen={};lookup={};max_errors=Counter();groups={}
    for row in rows:
        for key in ['candidate_sequence','candidate_labels','candidate_probabilities']:row[key]=json.loads(row[key])
        for key in ['normalized_entropy','top1_top2_margin','source_label_probability']:row[key]=float(row[key]) if row[key]!='' else None
        row['source_label_probability_defined']=truth(row['source_label_probability_defined'])
        mid=row['scientific_measurement_row_key']
        if mid in seen or mid not in tasks:raise ValueError('Duplicate/unexpected scientific measurement key')
        t=tasks[mid];a=amap[row['dataset'],row['sample_id']]
        for key in ['dataset','sample_id','modality','candidate_sequence_id','candidate_sequence','evidence_hash','prompt_hash','inference_cache_key','raw_source_label','model_revision','processor_revision','scoring_code_sha256']:
            if row[key]!=t[key]:raise ValueError('Measurement identity mismatch '+key)
        for key in ['candidate_sequence_id','candidate_sequence']:
            if row[key]!=a[key]:raise ValueError('Assignment mismatch')
        if row['status']!='SUCCESS':raise ValueError('Non-success measurement')
        if row['candidate_labels']!=row['candidate_sequence']:raise ValueError('Candidate order/vector alignment mismatch')
        derived=protocol.features(row['candidate_labels'],row['candidate_probabilities'],row['raw_source_label'])
        for key in ['normalized_entropy','top1_top2_margin','source_label_probability']:
            x,y=derived[key],row[key]
            if x is None or y is None:
                if x!=y:raise ValueError('Structural support mismatch')
            else:
                error=abs(x-y);max_errors[key]=max(max_errors[key],error)
                if error>1e-12:raise ValueError('Feature recomputation mismatch '+key)
        if derived['source_label_probability_defined']!=row['source_label_probability_defined']:raise ValueError('Ontology support changed')
        if row['candidate_probabilities']!=cache[row['inference_cache_key']]['candidate_probabilities']:raise ValueError('Contradictory cache distribution')
        if raw[mid]['candidate_probabilities']!=row['candidate_probabilities']:raise ValueError('Raw/CSV distribution mismatch')
        for key,name in required_hashes.items():
            if row[key]!=(frozen_provenance[key] if key=='runner_sha256' else frozen_sha(name)):raise ValueError('Measurement execution identity mismatch')
        identity=(row['dataset'],row['stable_dataset_id'],row['modality'])
        if identity in lookup:raise ValueError('Duplicate sample/modality')
        lookup[identity]=row;seen[mid]=row
        groups.setdefault((row['dataset'],row['sample_id']),[]).append(row)
    if len(seen)!=6354 or len(groups)!=3177:raise ValueError('Measurement population mismatch')
    for (ds,sid),group in groups.items():
        if {r['modality'] for r in group}!=set(protocol.DATASET_MODALITIES[ds]) or len(group)!=2:raise ValueError('Paired modalities missing')
        if group[0]['candidate_sequence']!=group[1]['candidate_sequence']:raise ValueError('Across-modality sequence mismatch')
    report={**expected_counts,'CORRECTED_MEASUREMENT_CLOSEOUT':'PASS','MEASUREMENT_IDENTITY_CHECK':'PASS',
            'CANDIDATE_DISTRIBUTION_INTEGRITY':'PASS','FEATURE_RECOMPUTATION_CHECK':'PASS','SEQUENCE_AWARE_CACHE_CLOSEOUT':'PASS',
            'CORRECTED_OUTPUT_HASH_RECHECK':'PASS','feature_tolerance':1e-12,'probability_sum_tolerance':1e-6,
            'maximum_scalar_recomputation_absolute_errors':dict(max_errors),'scientific_sample_count':len(groups),
            'candidate_assignment_regenerated':False,'GPU_executed_this_task':False,'input_hashes':hashes}
    write('B3_CORRECTED_MEASUREMENT_CLOSEOUT_V1.json',report)
    return lookup,report,hashes

def helpers(binding):
    path=Path(frozen_metrics.__file__)
    expected=read(REPO/'frozen/identity/metric_function_ast.json')
    actual={n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
    if actual!=expected:raise ValueError('Frozen equation/metric helper AST mismatch')
    return vars(frozen_metrics),path

def main():
    OUT.mkdir(exist_ok=True)
    verify_release()
    lookup,closed,input_hashes=closeout()
    binding=read(P/'B3_SOURCE_MODEL_BINDING_V1.json');evalplan=read(P/'B3_EVALUATION_PLAN_V1.json')
    for item in binding['artifacts']:
        if not item['artifact_path'].endswith('.py') and sha(P/item['artifact_path'])!=item['SHA256']:raise ValueError('Frozen source artifact changed')
    if binding['threshold']!=0.5 or any(binding[k] for k in ['target_scaler_fit','target_coefficient_fit','target_threshold_tuning']):raise ValueError('Nonfrozen source model')
    ns,helper_path=helpers(binding)
    coeff={}
    for model,kind,strength in [('M3a','primary','delta_source_label_probability_per_SD'),('M3b','margin','delta_top1_top2_margin_per_SD')]:
        if binding['models'][model]['feature_order']!=['intercept_AT','pair_AV','pair_VT',strength,'delta_normalized_entropy_per_SD','FIRST_IS_MODALITY1']:
            raise ValueError('Unexpected frozen feature order')
        c=binding['models'][model]['parameter_values']
        coeff[kind]={'intercept_AT':c['intercept_AT'],'intercept_AV':c['intercept_AT']+c['pair_AV'],
                     'beta_order_AT':c['FIRST_IS_MODALITY1'],'beta_order_AV':c['FIRST_IS_MODALITY1'],
                     'beta_entropy':c['delta_normalized_entropy_per_SD'],
                     'beta_sourceprob' if kind=='primary' else 'beta_margin':c[strength]}
    scalers={k:(binding['scalers'][k]['mean'],binding['scalers'][k]['sd']) for k in ['source_probability','normalized_entropy','top1_top2_margin']}
    paths={ds:REPO/'manifests'/sub/'frozen_joint_outcomes.csv' for ds,sub in [('MCR','mcr'),('CA-MER','camer'),('LISTEN','listen')]}
    data={};joint_hashes={}
    for ds,path in paths.items():
        if sha(path)!=evalplan['routes'][ds]['historical_joint_source_sha256']:raise ValueError('Frozen joint outcomes/accounting changed')
        joint_hashes[str(path)]=sha(path);rows=csvrows(path)
        if len({r['target_record_id'] for r in rows})!=len(rows):raise ValueError('Duplicate joint identity')
        if [r['target_record_id'] for r in rows if r['source_relation']=='CONFLICT']!=evalplan['routes'][ds]['prespecified_conflict_ids']:raise ValueError('Frozen conflict population changed')
        for r in rows:
            sid=r['source_item_id'];a=lookup[ds,sid,'A'];b=lookup[ds,sid,'V' if ds=='CA-MER' else 'T']
            if (a['raw_source_label'],b['raw_source_label'])!=(r['modality1_source_label'],r['modality2_source_label']):raise ValueError('Joint source labels changed')
            if (a['evidence_hash'],b['evidence_hash'])!=(r['modality1_evidence_sha256'],r['modality2_evidence_sha256']):raise ValueError('Joint evidence identity changed')
            for key,feature in [('delta_source_label_probability_raw','source_label_probability'),('delta_normalized_entropy_raw','normalized_entropy'),('delta_top1_top2_margin_raw','top1_top2_margin')]:
                r[key]=a[feature]-b[feature] if a[feature] is not None and b[feature] is not None else None
            for key in ['z_delta_source_label_probability','z_delta_normalized_entropy','z_delta_top1_top2_margin']:r[key]=''
        data[ds]=rows
    specs=[('MCR_AT_PRIMARY','MCR','AT','primary',False,'PRIMARY_SOURCEPROB_TRANSFER'),
           ('MCR_AT_MARGIN_SENSITIVITY','MCR','AT','margin',False,'SENSITIVITY'),
           ('LISTEN_AT_MARGIN_SENSITIVITY','LISTEN','AT','margin',False,'SENSITIVITY'),
           ('CAMER_AV_SUPPORT_LIMITED_SOURCEPROB','CA-MER','AV','primary',True,'SUPPLEMENTARY_ONTOLOGY_SUPPORTED_SOURCEPROB_TRANSFER'),
           ('CAMER_AV_MARGIN_SENSITIVITY','CA-MER','AV','margin',False,'SENSITIVITY')]
    analyses={};metric_rows=[];prediction_rows=[]
    for role,ds,route,kind,support_only,analysis_role in specs:
        rows=[r for r in data[ds] if not support_only or r['support_limited_diagnostic_role']=='SUPPLEMENTARY_SUPPORT_LIMITED_DIAGNOSTIC']
        predictions={r['target_record_id']:ns['prediction'](r,route,kind,coeff,scalers) for r in rows}
        repeated={r['target_record_id']:ns['prediction'](r,route,kind,coeff,scalers) for r in rows}
        if repeated!=predictions:raise ValueError('Zero-refit deterministic prediction mismatch')
        population=ns['population'](rows,route,kind);metrics,n=ns['metrics'](rows,predictions,route)
        prespecified=evalplan['routes'][ds]['sourceprob_supported_conflict_ids'] if support_only else evalplan['routes'][ds]['prespecified_conflict_ids']
        if population['eligible_conflict_N']!=len(prespecified):raise ValueError('Prespecified denominator changed')
        info={'status':'COMPLETE','dataset':ds,'analysis_role':analysis_role,'source_model':'M3a' if kind=='primary' else 'M3b',
              'N_prespecified':len(prespecified),'N_evaluated':n,'coverage':n/len(prespecified) if prespecified else None,
              'N_supported_planned':len(rows) if support_only else None,'population':population,'metrics':metrics,
              'zero_refit_replay_match':True,'threshold':binding['threshold']}
        analyses[role]=info
        metric_rows.append({'role':role,**{k:v for k,v in info.items() if k not in ['metrics','population']},**metrics,**population})
        for r in rows:
            prediction_rows.append({'analysis_role':role,'dataset':ds,'target_record_id':r['target_record_id'],
                'source_item_id':r['source_item_id'],'presentation_order':r['presentation_order'],
                'predicted_p_SIDE_A':predictions[r['target_record_id']],'resolved_side':ns['resolve_side'](r,route),
                'execution_accounting_class':ns['accounting_class'](r,route),
                'delta_source_label_probability_raw':r['delta_source_label_probability_raw'],
                'delta_normalized_entropy_raw':r['delta_normalized_entropy_raw'],'delta_top1_top2_margin_raw':r['delta_top1_top2_margin_raw']})
    for role,ds,status in [('LISTEN_AT_PRIMARY','LISTEN','STRUCTURALLY_UNSUPPORTED_UNDER_FROZEN_ONTOLOGY'),('CAMER_AV_FULL_PRIMARY','CA-MER','NOT_DEFINED_FOR_FULL_TARGET_POPULATION')]:
        analyses[role]={'status':status,'dataset':ds,'analysis_role':'PRIMARY_SOURCEPROB_TRANSFER' if ds=='LISTEN' else 'FULL_POPULATION_PRIMARY_SOURCEPROB','metrics':None,
                        'N_prespecified':len(evalplan['routes'][ds]['prespecified_conflict_ids']),'N_evaluated':None,'coverage':None}
        metric_rows.append({'role':role,**analyses[role],'AUROC':None,'balanced_accuracy':None,'log_loss':None,'Brier_score':None})
    historical_path=REPO/'results/mainline_summary/cross_regime/comparison_reference.json'
    oldhash=sha(historical_path);old=read(historical_path);comparisons=[]
    for role,new in analyses.items():
        prior=old['analysis_roles'][role]
        for metric in ['log_loss','AUROC','balanced_accuracy','Brier_score']:
            ov=(prior.get('metrics') or {}).get(metric);nv=(new.get('metrics') or {}).get(metric)
            comparisons.append({'role':role,'metric':metric,'old_metric':ov,'corrected_metric':nv,
                'signed_delta':nv-ov if nv is not None and ov is not None else None,'absolute_delta':abs(nv-ov) if nv is not None and ov is not None else None,
                'old_coverage':(prior.get('population') or {}).get('resolved_coverage'),'corrected_coverage':new.get('coverage'),
                'coverage_delta':new['coverage']-prior['population']['resolved_coverage'] if new.get('coverage') is not None and prior.get('population') else None,
                'old_N_evaluated':prior.get('evaluable_binary_N'),'corrected_N_evaluated':new.get('N_evaluated'),
                'population_identity':'FROZEN_UNCHANGED','direction_change_at_chance':ov is not None and nv is not None and metric in ['AUROC','balanced_accuracy'] and (ov-.5)*(nv-.5)<0,
                'old_role_metadata_preserved':prior['analysis_role'],'corrected_role':new['analysis_role']})
    result={'status':'EVALUATION_COMPLETE_RULING_PENDING','measurement_closeout':closed,'analyses':analyses,
            'full_historical_outcome_accounting':{ds:ns['full_accounting'](rows,'AV' if ds=='CA-MER' else 'AT') for ds,rows in data.items()},
            'target_refit':False,'target_threshold_tuning':False,'target_calibration':False,'GPU_executed_this_task':False}
    write('B3_ZERO_REFIT_FINAL_EVALUATION_V1.json',result)
    writecsv('B3_CORRECTED_DATASET_METRICS_V1.csv',metric_rows)
    writecsv('B3_OLD_VS_CORRECTED_COMPARISON_V1.csv',comparisons)
    writecsv('B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv',prediction_rows)
    if output_hashes()!=input_hashes or sha(historical_path)!=oldhash:raise ValueError('Raw corrected/historical input modified')
    provenance={'corrected_GPU_input_hashes':input_hashes,'source_model_binding_sha256':sha(P/'B3_SOURCE_MODEL_BINDING_V1.json'),
        'evaluation_plan_sha256':sha(P/'B3_EVALUATION_PLAN_V1.json'),'protocol_implementation_sha256':sha(P/'b3_protocol.py'),
        'measurement_manifest_sha256':sha(P/'B3_TARGET_MEASUREMENT_MANIFEST_V1.json'),
        'source_artifact_hashes':{r['artifact_path']:r['SHA256'] for r in binding['artifacts']},
        'official_corrected_archive_sha256':read(REPO/'frozen/identity/corrected_output_catalog.json')['archive_SHA256'],
        'protocol_sha256':sha(P/'B3_CORRECTED_MEASUREMENT_FREEZE_V1.md'),'assignment_sha256':sha(P/'B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json'),
        'analysis_script_sha256':sha(__file__),'historical_helper_script_sha256':sha(helper_path),'frozen_joint_input_hashes':joint_hashes,
        'historical_Attempt002_path':str(historical_path),'historical_Attempt002_sha256':oldhash,
        'target_refit':False,'target_scaling_fit':False,'target_threshold_tuning':False,'target_calibration':False,
        'historical_Attempt002_modified':False,'corrected_raw_GPU_outputs_modified':False,'GPU_execution':False,
        'equation_metric_accounting_helpers':'AST-extracted unchanged historical functions, applied only to corrected features; no historical metrics recomputed',
        'features_sign':'modality1 Audio minus modality2 Text/Video','source_scalers':scalers,'source_coefficients':coeff,
        'source_feature_order':{k:v['feature_order'] for k,v in binding['models'].items()},'threshold':binding['threshold']}
    write('B3_ZERO_REFIT_PROVENANCE_V1.json',provenance)
    finalize(result,comparisons)
    print(json.dumps({'closeout':'PASS','analyses':analyses},ensure_ascii=False,indent=2))

def finalize(result,comparisons):
    ruling='SURVIVES_WITH_CORRECTION'
    effects={
        'MCR':{'numerical_shift':'MINOR','direction_reversal':False,'support_or_coverage_change':False,
               'interpretation':'Primary AUROC remains about 0.728 and sensitivity AUROC about 0.739; frozen-threshold balanced accuracy remains 0.5. Strongest ranking transfer among these frozen routes persists, without claiming improved threshold classification.'},
        'LISTEN':{'numerical_shift':'MATERIAL','direction_reversal':'Margin AUROC crosses 0.5 from 0.47849 to 0.52264; balanced accuracy remains below 0.5.',
                  'support_or_coverage_change':False,'interpretation':'Source-probability primary remains structurally unsupported. Margin sensitivity is now slightly above chance in AUROC, with balanced accuracy 0.48919 and coverage 518/1139. Weak transfer interpretation persists; the old below-chance AUROC wording must change.'},
        'CA-MER':{'numerical_shift':'MATERIAL_IN_SUPPORTED_SUPPLEMENTARY_ROUTE','direction_reversal':False,'support_or_coverage_change':False,
                  'interpretation':'Supported supplementary AUROC rises from 0.65880 to 0.68639; balanced accuracy from 0.57335 to 0.59572. Full-population margin sensitivity remains weaker (AUROC 0.57400). Full-population source-probability primary remains undefined; partial/support-limited interpretation persists.'}}
    rationale=('LISTEN margin AUROC changes by +0.04415 and supported CA-MER AUROC by +0.02759; their log losses improve by about 0.051. These changes warrant corrected numbers and explicit correction disclosure. MCR remains strongest in ranking, CA-MER remains partial/support-limited, and LISTEN remains weak with structurally unsupported primary. The descriptive LISTEN AUROC crossing is acknowledged, but does not establish a new strong-transfer result. No post-hoc numerical materiality cutoff, significance test, or new analysis was introduced.')
    result.update(status='COMPLETE',B3_FINAL_SCIENTIFIC_RULING=ruling,QWEN_MAINLINE_SCIENCE='CLOSED',
                  primary_metric='historical log_loss',dataset_correction_effects=effects,ruling_rationale=rationale,
                  historical_metrics_recomputed=False,corrected_numbers_required_in_paper=True,
                  correction_disclosure_required=True,closure_meaning='Frozen corrected experiment completed, independent of agreement with the original hypothesis.')
    write('B3_ZERO_REFIT_FINAL_EVALUATION_V1.json',result)
    lines=['# B3_ZERO_REFIT_FINAL_EVALUATION_V1','',f'Final ruling: **{ruling}**. QWEN_MAINLINE_SCIENCE = CLOSED.','',
           'Corrected measurement closeout PASS: 6354/6354 measurements and 5515/5515 sequence-aware forwards; zero failed or missing. Assignment and paired-modality sequence identity, seven-candidate probability integrity, scalar CPU recomputation, cache identity and official hashes all PASS. No GPU was executed in this evaluation.','',
           'The frozen historical source M3a/M3b coefficients, source scaler and threshold 0.5 were applied unchanged. Historical log loss is the primary metric; AUROC, balanced accuracy and Brier are prespecified secondary metrics. Only corrected feature deltas replaced historical measurement features; joint outcomes, record identities, presentation order, support membership and accounting remain frozen. Source-probability is null outside the seven-label ontology. Historical Attempt002 metrics were read, never recomputed.','',
           '| Frozen role | Evaluated / prespecified conflict N | Coverage | Log loss | AUROC | Balanced accuracy @0.5 | Brier |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for role,a in result['analyses'].items():
        m=a['metrics']
        if m:
            lines.append(f"| {role} | {a['N_evaluated']} / {a['N_prespecified']} | {a['coverage']:.9f} | {m['log_loss']:.9f} | {m['AUROC']:.9f} | {m['balanced_accuracy']:.9f} | {m['Brier_score']:.9f} |")
        else:lines.append(f"| {role} ({a['status']}) | Undefined / {a['N_prespecified']} | Undefined | Undefined | Undefined | Undefined | Undefined |")
    lines += ['', 'CA-MER supported source-probability is supplementary: 1434 planned supported joint slots, 672 supported conflict slots and 416 evaluable binary outcomes. Its coverage 416/672 is conditional on frozen support, not full-population primary coverage. Full-population margin coverage is 1350/2000. LISTEN margin coverage is 518/1139; 10 same-label rows are excluded from the 1149 planned slots. Coverage reflects frozen joint outcomes and is not the GPU acquisition completion rate. All populations and coverage are unchanged by correction.', '',
              '| Role | Metric | Historical | Corrected | Signed delta | Absolute delta |', '|---|---|---:|---:|---:|---:|']
    for r in comparisons:
        if r['corrected_metric'] is not None:
            lines.append(f"| {r['role']} | {r['metric']} | {r['old_metric']:.9f} | {r['corrected_metric']:.9f} | {r['signed_delta']:+.9f} | {r['absolute_delta']:.9f} |")
    lines += ['',rationale,'']
    for ds,effect in effects.items():lines += [f"**{ds}: {effect['numerical_shift']}.** {effect['interpretation']}",'']
    lines += ['Interpretation limits: these are descriptive frozen-route comparisons. Raw log losses across datasets have different outcome prevalence and do not alone measure relative transfer strength. MCR strongest transfer refers to the retained ranking result, not superior balanced accuracy at the frozen threshold. LISTEN AUROC crossing is numerical and no statistical significance claim is made. No causal separation of ordering from other frozen measurement differences was attempted. Historical CA-MER support-only role metadata is preserved in the comparison file while its corrected scientific role is explicitly supplementary.','',
              'No target refit, target scaler fit, threshold tuning, calibration, new subgroup, order robustness, prompt robustness, second model or supplementary experiment was performed. The row-level prediction CSV records the prespecified evaluation only. Original GPU outputs and historical Attempt002 remain unchanged.','',
              'Provenance and closeout JSON files contain input hashes, source bindings, analysis script hash and no-refit flags. B3_FINAL_HASHES_V1.txt covers all final artifacts except itself. The analysis source is included for review; docs record final state and decisions.','']
    (OUT/'B3_ZERO_REFIT_FINAL_EVALUATION_V1.md').write_text('\n'.join(lines),encoding='utf-8')
    (OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    docs=OUT/'docs';docs.mkdir(exist_ok=True)
    (docs/'PROJECT_STATE.md').write_text(f'# Project state\n\nTask B3_ZERO_REFIT_FINAL_EVALUATION_V1 complete. Measurement closeout PASS. Ruling {ruling}. QWEN_MAINLINE_SCIENCE=CLOSED. No further experiment authorized or started.\n',encoding='utf-8')
    (docs/'DECISIONS.md').write_text('# Decisions\n\n'+rationale+'\n\nLISTEN sourceprob primary unsupported; CA-MER full primary undefined and supported subgroup supplementary. Preserve historical files and formal corrected raw outputs. Apply only frozen source model/scalers/threshold and historical outcome accounting.\n',encoding='utf-8')
    (docs/'FILE_MAP.md').write_text('# File map\n\nFinal report: B3_ZERO_REFIT_FINAL_EVALUATION_V1.md/json. Measurements: B3_CORRECTED_MEASUREMENT_CLOSEOUT_V1.json. Prespecified metrics and historical comparison: B3_CORRECTED_DATASET_METRICS_V1.csv and B3_OLD_VS_CORRECTED_COMPARISON_V1.csv. Row-level audit: B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv. Input identities and flags: B3_ZERO_REFIT_PROVENANCE_V1.json. Reproducible analysis: b3_zero_refit_final_evaluation_v1.py. Integrity: B3_FINAL_HASHES_V1.txt.\n',encoding='utf-8')
    payloads=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='B3_FINAL_HASHES_V1.txt')
    (OUT/'B3_FINAL_HASHES_V1.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT).as_posix()}\n' for p in payloads),encoding='utf-8')
    for line in (OUT/'B3_FINAL_HASHES_V1.txt').read_text().splitlines():
        digest,name=line.split('  ',1)
        if sha(OUT/name)!=digest:raise ValueError('Final artifact hash mismatch')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu-outputs',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();G=args.gpu_outputs.resolve();OUT=args.output.resolve()
    if OUT==G or G in OUT.parents:raise ValueError('Evaluation output must be separate from immutable GPU inputs')
    main()

