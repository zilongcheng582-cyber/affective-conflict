"""POST_HOC_EXPLORATORY: stdlib-only, read-only identity/metric replay; no fitting."""
import argparse,ast,csv,hashlib,json,math,subprocess,collections
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROV=ROOT/'evidence/provenance/recovered_evidence_migration_v1'

def table(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def logistic(z):return 1/(1+math.exp(-z))

def metrics(y,p):
    p=[max(1e-12,min(1-1e-12,v)) for v in p];n=len(y);n1=sum(y);n0=n-n1
    ranked=sorted(range(n),key=lambda i:p[i]);ranks=[0.0]*n;j=0
    while j<n:
        k=j+1
        while k<n and p[ranked[k]]==p[ranked[j]]:k+=1
        rank=(j+1+k)/2
        for index in ranked[j:k]:ranks[index]=rank
        j=k
    return {'AUROC':(sum(r for r,v in zip(ranks,y) if v)-n1*(n1+1)/2)/(n1*n0),
            'balanced_accuracy':.5*(sum(v>=.5 for v,t in zip(p,y) if t)/n1+sum(v<.5 for v,t in zip(p,y) if not t)/n0),
            'log_loss':-sum(t*math.log(v)+(1-t)*math.log(1-v) for v,t in zip(p,y))/n,
            'Brier_score':sum((v-t)**2 for v,t in zip(p,y))/n}

def validate():
    out={'classification':'POST_HOC_EXPLORATORY','GPU':False,'refit':False,'tests':{}}
    checks=[]
    for line in (PROV/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split('  ',1);p=ROOT/name
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
        checks.append(name)
    out['tests']['sha256_files']=len(checks)
    allow=table('evidence/provenance/recovered_evidence_migration_v1/MIGRATION_ALLOWLIST.csv')
    for row in allow:
        digest=hashlib.sha256((ROOT/row['target_path']).read_bytes()).hexdigest()
        assert digest==row['target_sha256'],('lineage target hash',row['target_path'])
        if row['byte_identical'].lower()=='true':assert digest==row['source_sha256']
        else:assert row['transformation_rule'] and row['redacted'].lower()=='true'
    out['tests']['migration_lineage_files']=len(allow)
    base=json.loads((PROV/'MIGRATION_PROVENANCE.json').read_text())['base_main']
    changed=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-status',base,'HEAD'],text=True).splitlines()
    assert all(line.startswith('A\t') for line in changed),changed
    for path in subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only',base],text=True).splitlines():
        original=subprocess.check_output(['git','-C',str(ROOT),'show',base+':'+path])
        assert (ROOT/path).read_bytes()==original,('frozen/base file changed',path)
    out['tests']['existing_main_files_byte_unchanged']=True
    roots=['analyses/four_regime_synthesis_v1','analyses/historical_evidence_reconciliation_v2','analyses/recovered_evidence_scientific_analysis_v1','analyses/transfer_failure_integration_v1']
    code=[]
    for folder in roots:
        for p in (ROOT/folder).rglob('*.py'):ast.parse(p.read_text(encoding='utf8'));code.append(p.relative_to(ROOT).as_posix())
    out['tests']['python_static_parses']=len(code)
    claims=table('results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX.csv')
    expected={'R1 Source Prediction','R2 Compositionality','Frozen Transfer','ERI1 Causal Intervention','Recovered Native Experiments','Transfer Failure Explanation'}
    assert {x['category'] for x in claims}==expected and len(claims)==25
    assert all(x['analysis_origin']=='POST_HOC_EXPLORATORY' for x in claims)
    out['tests']['claim_categories']=sorted(expected)
    prefix='results/historical_evidence_reconciliation_v2/'
    projections={
        'MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.public_projection.csv':4000,
        'CAMER_6000_KEY_RECONCILIATION_V2.public_projection.csv':6000,
        'LISTEN_V3_ANSWER_OPTION_RECOVERY_V2.public_projection.csv':1149,
        'LISTEN_V4_ANSWER_OPTION_RECOVERY_V2.public_projection.csv':1149}
    for name,n in projections.items():
        data=table(prefix+name);assert len(data)==n
        assert not {'source_text','raw_model_output','raw_generated_sequence'}&set(data[0])
    camer=table(prefix+'CAMER_6000_KEY_RECONCILIATION_V2.public_projection.csv')
    assert len({(x['sample_id'],x['arm']) for x in camer})==6000
    assert sum(x['scientific_available'].lower()=='true' for x in camer)==5825
    out['tests']['public_projection_rows']=projections
    links=table('results/transfer_failure_integration_v1/phase4_numeric/TRANSFER_RECOVERED_ROW_LINKAGE.csv')
    assert len(links)==5199 and all(x['identity_check']=='PASS' for x in links)
    out['tests']['strict_linkage_rows']=len(links)
    preds=table('results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv')
    assert len(preds)==9219 and len({(x['analysis_role'],x['target_record_id']) for x in preds})==9219
    baselines=json.loads((ROOT/'results/post_audit/closure_v1/SOURCE_BASELINE_BINDING_V1.json').read_text())
    binding=json.loads((ROOT/'frozen/source_model/binding.json').read_text())
    assert binding['threshold']==.5 and not any(binding[k] for k in ['target_coefficient_fit','target_scaler_fit','target_threshold_tuning'])
    route_table=table('results/transfer_failure_integration_v1/04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv');assert len(route_table)==18
    comparisons=[];prediction_errors=[]
    for ref in route_table:
        route=ref['route'];predrole=route
        if route.startswith('LISTEN_'):predrole='LISTEN_AT_MARGIN_SENSITIVITY'
        allrows=[r for r in preds if r['analysis_role']==predrole and (route!='LISTEN_3C_JOINT_ARBITRATION' or r['target_record_id'].startswith('3C_'))]
        rows=[r for r in allrows if r['resolved_side'] in ['SIDE_A','SIDE_T','SIDE_V']]
        assert len(rows)==int(ref['N_evaluated'])
        digest=hashlib.sha256('\n'.join(r['target_record_id'] for r in rows).encode()).hexdigest()
        assert digest==ref['evaluated_identity_sha256'],route
        y=[int(r['resolved_side']=='SIDE_A') for r in rows];values=[]
        for r in rows:
            pair='AV' if r['dataset']=='CA-MER' else 'AT';first=int(r['presentation_order'].startswith('A_'))
            name=ref['source_model']
            if name in baselines:
                c=baselines[name]['parameters'];prob=logistic(c['intercept_AT']+c.get('pair_'+pair,0)+c.get('FIRST_IS_MODALITY1',0)*first)
            else:
                model='M3a' if name.endswith('M3a') else 'M3b';c=binding['models'][model]['parameter_values'];sc=binding['scalers']
                raw='delta_source_label_probability_raw' if model=='M3a' else 'delta_top1_top2_margin_raw'
                key='source_probability' if model=='M3a' else 'top1_top2_margin';term='delta_source_label_probability_per_SD' if model=='M3a' else 'delta_top1_top2_margin_per_SD'
                z=(float(r[raw])-sc[key]['mean'])/sc[key]['sd'];ent=(float(r['delta_normalized_entropy_raw'])-sc['normalized_entropy']['mean'])/sc['normalized_entropy']['sd']
                prob=logistic(c['intercept_AT']+c.get('pair_'+pair,0)+c[term]*z+c['delta_normalized_entropy_per_SD']*ent+c['FIRST_IS_MODALITY1']*first)
                err=abs(prob-float(r['predicted_p_SIDE_A']));assert err<=1e-12;prediction_errors.append(err)
            values.append(prob)
        m=metrics(y,values);error=max(abs(m[k]-float(ref[k])) for k in m);assert error<=1e-12,(route,name,error)
        comparisons.append({'route':route,'model':name,'N':len(rows),'identity':'PASS','metrics':m,'max_abs_error':error})
    out['tests']['frozen_route_baseline_checks']=comparisons
    out['tests']['prediction_rows_available']=len(preds)
    out['tests']['max_prediction_abs_error']=max(prediction_errors)
    out['tests']['max_metric_abs_error']=max(x['max_abs_error'] for x in comparisons)
    out['status']='PASS'
    out['scope']='GITHUB_CLEAN_CHECKOUT_IDENTITY_AND_FIXED_METRIC_REPLAY_PASS; full raw-archive extraction/bootstrap requires AUTODL_LOCAL_REPLAY'
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',required=True,type=Path);args=p.parse_args()
    assert not args.report.resolve().is_relative_to(ROOT.resolve()),'Write verification report outside immutable checkout'
    result=validate();args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],'hash_files':result['tests']['sha256_files'],'route_baseline_checks':len(result['tests']['frozen_route_baseline_checks']),'max_metric_abs_error':result['tests']['max_metric_abs_error'],'scope':result['scope']}))
