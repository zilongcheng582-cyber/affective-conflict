"""POST_HOC_EXPLORATORY: stdlib-only, read-only identity/metric replay; no fitting.

Remediation V1 (PR4 review F04/F09): every required check is an explicit condition that records a
named failure; nothing relies on `assert`, so `python -O` cannot skip validation. Any failure gives
status FAIL and a non-zero exit code; PASS is printed only when the failure list is empty.
"""
import argparse,ast,csv,hashlib,json,math,re,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROV=ROOT/'evidence/provenance/recovered_evidence_migration_v1'
STATUS_INDEX='results/four_regime_structural_synthesis_v1/STATUS_AND_SUPERSESSION.json'
VALIDATOR_PATH='analyses/transfer_failure_integration_v1/validate_migration.py'  # defines the decision tokens; not a decision document
# Directories and files owned by this migration; every added file in this scope must be in SHA256SUMS.
SCOPE_DIRS=('analyses/four_regime_synthesis_v1/','results/four_regime_structural_synthesis_v1/','analyses/historical_evidence_reconciliation_v2/',
            'results/historical_evidence_reconciliation_v2/','analyses/recovered_evidence_scientific_analysis_v1/','results/recovered_evidence_scientific_analysis_v1/',
            'analyses/transfer_failure_integration_v1/','results/transfer_failure_integration_v1/','evidence/provenance/recovered_evidence_migration_v1/')
SCOPE_FILES=('.gitattributes','docs/RECOVERED_EVIDENCE_MIGRATION_V1.md','tests/test_pr4_migration_regressions.py')
DECISION_TOKENS=re.compile(r"NEXT_STEP[\s\"'\]\[:=*]+[A-Z][A-Z_]{5,}|ONE_FINAL_QWEN_EXPERIMENT_REQUIRED|CPU_ANALYSIS_INCOMPLETE|QWEN_CAN_FREEZE_AND_MOVE_TO_NEXT_MODEL|SECOND_MODEL")
DECISION_NAMES=re.compile(r'QWEN_.*(DECISION|PRIORITY)|EXECUTIVE_SUMMARY')
EXCLUSION_STATUS={'SUPERSEDED_HISTORICAL':'EXCLUDED_SUPERSEDED_HISTORICAL','LARGE_OR_RESTRICTED':'HELD_ON_AUTODL_LARGE_OR_RESTRICTED','UNSAFE_TO_UPLOAD':'EXCLUDED_UNSAFE_TO_UPLOAD'}


class ValidationError(Exception):
    """A required migration identity, provenance or metric condition does not hold."""


class Checker:
    def __init__(self):self.failures=[]
    def require(self,condition,check,detail):
        if not condition:self.failures.append({'check':check,'detail':str(detail)})
        return bool(condition)


def git(*args,binary=False):
    out=subprocess.run(['git','-C',str(ROOT),*args],capture_output=True)
    if out.returncode!=0:raise ValidationError('git '+' '.join(args)+': '+out.stderr.decode(errors='replace').strip())
    return out.stdout if binary else out.stdout.decode()

def table(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def sha_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def logistic(z):return 1/(1+math.exp(-z))

def metrics(y,p):
    """AUROC/BA are None (undefined) when only one class is present; log loss and Brier stay defined."""
    p=[max(1e-12,min(1-1e-12,v)) for v in p];n=len(y);n1=sum(y);n0=n-n1
    out={'AUROC':None,'balanced_accuracy':None,'log_loss':None,'Brier_score':None}
    if not n:return out
    out['log_loss']=-sum(t*math.log(v)+(1-t)*math.log(1-v) for v,t in zip(p,y))/n
    out['Brier_score']=sum((v-t)**2 for v,t in zip(p,y))/n
    if not n1 or not n0:return out
    ranked=sorted(range(n),key=lambda i:p[i]);ranks=[0.0]*n;j=0
    while j<n:
        k=j+1
        while k<n and p[ranked[k]]==p[ranked[j]]:k+=1
        rank=(j+1+k)/2
        for index in ranked[j:k]:ranks[index]=rank
        j=k
    out['AUROC']=(sum(r for r,v in zip(ranks,y) if v)-n1*(n1+1)/2)/(n1*n0)
    out['balanced_accuracy']=.5*(sum(v>=.5 for v,t in zip(p,y) if t)/n1+sum(v<.5 for v,t in zip(p,y) if not t)/n0)
    return out

def in_scope(path):return path.startswith(SCOPE_DIRS) or path in SCOPE_FILES


def check_manifest(c,out,head):
    sums={}
    for n,line in enumerate((PROV/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines(),1):
        parts=line.split('  ',1)
        if not c.require(len(parts)==2 and re.fullmatch('[0-9a-f]{64}',parts[0] or ''),'sha256sums_format',f'line {n}: {line!r}'):continue
        digest,name=parts;sums[name]=digest;p=ROOT/name
        if c.require(p.is_file(),'sha256_file_missing',name):c.require(sha_file(p)==digest,'sha256_mismatch',name)
    out['tests']['sha256_files']=len(sums)
    base=json.loads((PROV/'MIGRATION_PROVENANCE.json').read_text(encoding='utf-8'))['base_main']
    added=[l.split('\t',1)[1] for l in git('diff','--name-status','--diff-filter=A',base,head).splitlines()]
    scoped={p for p in added if in_scope(p)}-{'evidence/provenance/recovered_evidence_migration_v1/SHA256SUMS.txt'}
    for p in sorted(scoped-set(sums)):c.require(False,'sha256sums_missing_entry_for_added_file',p)
    for p in sorted(set(sums)-scoped):c.require(False,'sha256sums_entry_not_an_added_migration_file',p)
    out['tests']['manifest_coverage_files']=len(scoped)
    return base,sums


def check_base_unchanged(c,out,base,head):
    """Identity of pre-existing main files is checked on Git objects (checkout-conversion independent)."""
    before=dict(l.split('\t',1)[::-1] for l in git('ls-tree','-r',base).splitlines())
    after=dict(l.split('\t',1)[::-1] for l in git('ls-tree','-r',head).splitlines())
    for path,meta in before.items():
        if c.require(path in after,'base_file_deleted',path):c.require(after[path].split()[2]==meta.split()[2],'base_file_blob_changed',path)
    dirty=[l for l in git('status','--porcelain','--untracked-files=no').splitlines() if l.strip()]
    for l in dirty:c.require(False,'tracked_worktree_modified',l)
    drift=0
    if head=='HEAD':
        for path,meta in before.items():
            if sha_file(ROOT/path)!=hashlib.sha256(git('cat-file','blob',meta.split()[2],binary=True)).hexdigest():drift+=1
    out['tests']['existing_main_files_blob_unchanged']=len(before)
    out['tests']['existing_main_files_checkout_byte_drift']=drift
    out['tests']['checkout_byte_drift_note']='Informational: non-zero only when Git checkout converts newlines (e.g. core.autocrlf=true); identity is verified on Git objects.'


def check_lineage_and_payload(c,out):
    allow=table('evidence/provenance/recovered_evidence_migration_v1/MIGRATION_ALLOWLIST.csv');total=0;sizes=0
    for row in allow:
        p=ROOT/row['target_path']
        if not c.require(p.is_file(),'lineage_target_missing',row['target_path']):continue
        digest=sha_file(p);size=p.stat().st_size;total+=int(row['bytes']);sizes+=size
        c.require(digest==row['target_sha256'],'lineage_target_hash',row['target_path'])
        c.require(size==int(row['bytes']),'lineage_bytes_column',row['target_path'])
        if row['byte_identical'].lower()=='true':c.require(digest==row['source_sha256'],'lineage_byte_identical_source_hash',row['target_path'])
        else:c.require(bool(row['transformation_rule']) and row['redacted'].lower()=='true','lineage_sanitized_without_rule',row['target_path'])
    prov=json.loads((PROV/'MIGRATION_PROVENANCE.json').read_text(encoding='utf-8'))
    c.require(prov['payload_file_count']==len(allow)==len({r['target_path'] for r in allow}),'payload_file_count',(prov['payload_file_count'],len(allow)))
    c.require(prov['payload_bytes']==total==sizes,'payload_bytes_recorded_allowlist_actual',(prov['payload_bytes'],total,sizes))
    ident=sum(r['byte_identical'].lower()=='true' for r in allow)
    c.require(prov['byte_identical_payload_files']==ident and prov['sanitized_derivative_payload_files']==len(allow)-ident,'payload_identity_split',(ident,len(allow)-ident))
    for twin in ['MIGRATION_FILE_SHA256.csv','MIGRATION_LINEAGE_MAP.csv']:c.require((PROV/twin).read_bytes()==(PROV/'MIGRATION_ALLOWLIST.csv').read_bytes(),'lineage_twin_differs',twin)
    report=(PROV/'MIGRATION_VALIDATION_REPORT.md').read_text(encoding='utf-8')
    remediation=prov.get('remediation_v1',{});history=set(remediation.get('payload_bytes_snapshot_history',{}).values())|{remediation.get('erroneous_report_value_corrected')}
    for number in re.findall(r'(\d{1,3}(?:,\d{3}){2,})',report):
        value=int(number.replace(',',''))
        c.require(value==prov['payload_bytes'] or value in history,'validation_report_unregistered_byte_count',number)
    out['tests']['migration_lineage_files']=len(allow);out['tests']['payload_bytes']=sizes
    return allow


def check_exclusions(c,out,sums):
    gap={r['source_path']:r for r in table('evidence/provenance/recovered_evidence_migration_v1/GITHUB_GAP_ANALYSIS.csv')}
    rows=table('evidence/provenance/recovered_evidence_migration_v1/MIGRATION_EXCLUSIONS.csv')
    c.require(len(rows)==58 and len({r['source'] for r in rows})==58,'exclusion_row_count',len(rows))
    tracked={sha_file(ROOT/p) for p in sums if (ROOT/p).is_file()}
    for r in rows:
        g=gap.get(r['source'])
        if not c.require(g is not None,'exclusion_not_in_gap_analysis',r['source']):continue
        c.require(g['source_sha256']==r['sha256'],'exclusion_hash_differs_from_gap',r['source'])
        c.require(r.get('gap_status')==g['gap_status'] and r['status']==EXCLUSION_STATUS.get(g['gap_status']),'exclusion_status_inconsistent',(r['source'],r['status'],g['gap_status']))
        c.require(r.get('upload_decision')=='NOT_UPLOADED','exclusion_upload_decision',r['source'])
        c.require(r['sha256'] not in tracked,'excluded_asset_present_in_migration',r['source'])
    out['tests']['exclusion_rows_consistent']=len(rows)


def check_status_index(c,out,sums):
    index=json.loads((ROOT/STATUS_INDEX).read_text(encoding='utf-8'));allowed=set(index['allowed_status'])
    docs={d['path']:d for d in index['documents']}
    md=(ROOT/STATUS_INDEX.replace('.json','.md')).read_text(encoding='utf-8')
    for p,d in docs.items():
        c.require((ROOT/p).is_file(),'status_index_path_missing',p)
        c.require(d['status'] in allowed,'status_index_bad_status',(p,d['status']))
        c.require('`'+p+'`' in md,'status_index_md_json_mismatch',p)
        if d['superseded_by']:c.require((ROOT/d['superseded_by']).is_file(),'status_index_superseded_by_missing',d['superseded_by'])
        if d['status']=='SUPERSEDED':c.require(bool(d['superseded_by']),'status_index_superseded_without_target',p)
    for p in sums:
        if p==VALIDATOR_PATH or p.startswith(('evidence/provenance/','tests/')) or p.endswith('SHA256SUMS.txt') or 'SHA256SUMS' in p or p.startswith(STATUS_INDEX.rsplit('.',1)[0]):continue
        text=(ROOT/p).read_text(encoding='utf-8',errors='replace')
        if DECISION_TOKENS.search(text) or DECISION_NAMES.search(Path(p).name):c.require(p in docs,'decision_document_missing_from_status_index',p)
    current=index['current_next_step']['value']
    for p,d in docs.items():
        if d['status']=='CURRENT' and (ROOT/p).is_file():
            for v in re.findall(r"NEXT_STEP[\s\"'\]\[:=*]+([A-Z][A-Z_]{5,})",(ROOT/p).read_text(encoding='utf-8',errors='replace')):
                c.require(v==current,'current_document_conflicting_next_step',(p,v))
    c.require(index['current_next_step']['gpu_authorized'] is False,'status_index_gpu_authorized',index['current_next_step'])
    c.require(len(index['withdrawn_or_limited_premises'])>=6,'status_index_withdrawn_premises',len(index['withdrawn_or_limited_premises']))
    out['tests']['status_index_documents']=len(docs)


def check_claims(c,out):
    claims=table('results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX.csv')
    expected={'R1 Source Prediction','R2 Compositionality','Frozen Transfer','ERI1 Causal Intervention','Recovered Native Experiments','Transfer Failure Explanation'}
    c.require({x['category'] for x in claims}==expected and len(claims)==25,'claim_categories',len(claims))
    c.require(all(x['analysis_origin']=='POST_HOC_EXPLORATORY' for x in claims),'claim_integration_origin','matrix origin changed')
    comp={r['id']:r for r in table('results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX_EVIDENCE_STATUS_V1.csv')}
    c.require(set(comp)=={x['id'] for x in claims},'claim_companion_ids',sorted(set(comp)^{x['id'] for x in claims}))
    for x in claims:
        r=comp.get(x['id'])
        if r is None:continue
        c.require(r['claim_status_unchanged']==x['status'] and r['category']==x['category'],'claim_companion_status_changed',x['id'])
        c.require((r['may_be_cited_as_confirmatory']!='NO')==(r['upstream_evidence_status']=='PREREGISTERED_CONFIRMATORY_FROZEN'),'claim_confirmatory_flag',x['id'])
        for path in re.findall(r'(?:results|docs)/[A-Za-z0-9_./-]+\.(?:md|csv|json)',r['upstream_source']):c.require((ROOT/path).is_file(),'claim_upstream_source_missing',(x['id'],path))
    c.require([k for k,r in comp.items() if r['may_be_cited_as_confirmatory']!='NO']==['X2'],'claim_confirmatory_set','only ERI1 X2 may be cited as confirmatory')
    out['tests']['claim_categories']=sorted(expected)


def check_sanitization(c,out):
    reg=json.loads((PROV/'SANITIZATION_RETAINED_FIELDS_REGISTER_V1.json').read_text(encoding='utf-8'))
    main=git('show',reg['main_reference']['commit']+':'+reg['main_reference']['path'],binary=True)
    c.require(hashlib.sha256(main).hexdigest()==reg['main_reference']['sha256'],'sanitization_main_reference_hash',reg['main_reference']['path'])
    text=main.decode('utf-8')
    def leaves(o,p=''):
        if isinstance(o,dict):
            for k,v in o.items():yield from leaves(v,p+'/'+str(k))
        elif isinstance(o,list):
            for v in o:yield from leaves(v,p+'/[]')
        elif isinstance(o,str):yield p,o
    seen=0
    for f in sorted({e['file'] for e in reg['entries']}):
        want=sorted((e['json_path'],e['value_sha256']) for e in reg['entries'] if e['file']==f)
        got=[];data=json.loads((ROOT/f).read_text(encoding='utf-8'))
        for p,v in leaves(data):
            h=hashlib.sha256(v.encode()).hexdigest()
            if (p,h) in want:got.append((p,h));c.require(v in text,'sanitization_retained_value_not_public_in_main',(f,p))
        c.require(sorted(got)==want,'sanitization_register_mismatch',f);seen+=len(got)
    out['tests']['sanitization_retained_values']=seen
    for name in ['MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.public_projection.csv','CAMER_6000_KEY_RECONCILIATION_V2.public_projection.csv','LISTEN_V3_ANSWER_OPTION_RECOVERY_V2.public_projection.csv','LISTEN_V4_ANSWER_OPTION_RECOVERY_V2.public_projection.csv','MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.public_projection.csv']:
        with (ROOT/'results/historical_evidence_reconciliation_v2'/name).open(encoding='utf-8-sig',newline='') as fh:header=next(csv.reader(fh))
        c.require(not {'source_text','raw_model_output','raw_generated_sequence','native_adversarial_source_text','controlled_text_evidence'}&set(header),'sanitized_projection_has_raw_column',name)


def check_science(c,out):
    roots=['analyses/four_regime_synthesis_v1','analyses/historical_evidence_reconciliation_v2','analyses/recovered_evidence_scientific_analysis_v1','analyses/transfer_failure_integration_v1']
    code=0
    for folder in roots:
        for p in (ROOT/folder).rglob('*.py'):
            try:ast.parse(p.read_text(encoding='utf8'));code+=1
            except SyntaxError as e:c.require(False,'python_static_parse',f'{p}: {e}')
    out['tests']['python_static_parses']=code
    prefix='results/historical_evidence_reconciliation_v2/'
    projections={'MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.public_projection.csv':4000,'CAMER_6000_KEY_RECONCILIATION_V2.public_projection.csv':6000,
                 'LISTEN_V3_ANSWER_OPTION_RECOVERY_V2.public_projection.csv':1149,'LISTEN_V4_ANSWER_OPTION_RECOVERY_V2.public_projection.csv':1149}
    for name,n in projections.items():c.require(len(table(prefix+name))==n,'projection_row_count',(name,n))
    camer=table(prefix+'CAMER_6000_KEY_RECONCILIATION_V2.public_projection.csv')
    c.require(len({(x['sample_id'],x['arm']) for x in camer})==6000,'camer_unique_keys',6000)
    c.require(sum(x['scientific_available'].lower()=='true' for x in camer)==5825,'camer_usable',5825)
    out['tests']['public_projection_rows']=projections
    links=table('results/transfer_failure_integration_v1/phase4_numeric/TRANSFER_RECOVERED_ROW_LINKAGE.csv')
    c.require(len(links)==5199 and all(x['identity_check']=='PASS' for x in links),'strict_linkage',len(links))
    out['tests']['strict_linkage_rows']=len(links)
    preds=table('results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv')
    c.require(len(preds)==9219 and len({(x['analysis_role'],x['target_record_id']) for x in preds})==9219,'frozen_prediction_rows',len(preds))
    baselines=json.loads((ROOT/'results/post_audit/closure_v1/SOURCE_BASELINE_BINDING_V1.json').read_text(encoding='utf-8'))
    binding=json.loads((ROOT/'frozen/source_model/binding.json').read_text(encoding='utf-8'))
    c.require(binding['threshold']==.5 and not any(binding[k] for k in ['target_coefficient_fit','target_scaler_fit','target_threshold_tuning']),'frozen_binding_flags','threshold/fit flags')
    route_table=table('results/transfer_failure_integration_v1/04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv')
    c.require(len(route_table)==18,'route_table_rows',len(route_table))
    comparisons=[];prediction_errors=[0.0]
    for ref in route_table:
        route=ref['route'];predrole='LISTEN_AT_MARGIN_SENSITIVITY' if route.startswith('LISTEN_') else route;name=ref['source_model']
        allrows=[r for r in preds if r['analysis_role']==predrole and (route!='LISTEN_3C_JOINT_ARBITRATION' or r['target_record_id'].startswith('3C_'))]
        rows=[r for r in allrows if r['resolved_side'] in ['SIDE_A','SIDE_T','SIDE_V']]
        c.require(len(rows)==int(ref['N_evaluated']),'route_denominator',(route,name,len(rows)))
        c.require(hashlib.sha256('\n'.join(r['target_record_id'] for r in rows).encode()).hexdigest()==ref['evaluated_identity_sha256'],'route_identity',(route,name))
        y=[int(r['resolved_side']=='SIDE_A') for r in rows];values=[]
        for r in rows:
            pair='AV' if r['dataset']=='CA-MER' else 'AT';first=int(r['presentation_order'].startswith('A_'))
            if name in baselines:
                k=baselines[name]['parameters'];prob=logistic(k['intercept_AT']+k.get('pair_'+pair,0)+k.get('FIRST_IS_MODALITY1',0)*first)
            else:
                model='M3a' if name.endswith('M3a') else 'M3b';k=binding['models'][model]['parameter_values'];sc=binding['scalers']
                raw='delta_source_label_probability_raw' if model=='M3a' else 'delta_top1_top2_margin_raw'
                key='source_probability' if model=='M3a' else 'top1_top2_margin';term='delta_source_label_probability_per_SD' if model=='M3a' else 'delta_top1_top2_margin_per_SD'
                z=(float(r[raw])-sc[key]['mean'])/sc[key]['sd'];ent=(float(r['delta_normalized_entropy_raw'])-sc['normalized_entropy']['mean'])/sc['normalized_entropy']['sd']
                prob=logistic(k['intercept_AT']+k.get('pair_'+pair,0)+k[term]*z+k['delta_normalized_entropy_per_SD']*ent+k['FIRST_IS_MODALITY1']*first)
                err=abs(prob-float(r['predicted_p_SIDE_A']));prediction_errors.append(err);c.require(err<=1e-12,'frozen_prediction_mismatch',(route,r['target_record_id'],err))
            values.append(prob)
        m=metrics(y,values);errors=[]
        for key,v in m.items():
            ok=(v is None and ref[key]=='') or (v is not None and ref[key]!='' and abs(v-float(ref[key]))<=1e-12)
            c.require(ok,'route_metric_mismatch',(route,name,key,v,ref[key]))
            if v is not None and ref[key]!='':errors.append(abs(v-float(ref[key])))
        comparisons.append({'route':route,'model':name,'N':len(rows),'identity':'PASS','metrics':m,'max_abs_error':max(errors,default=0.0)})
    out['tests']['frozen_route_baseline_checks']=comparisons
    out['tests']['prediction_rows_available']=len(preds)
    out['tests']['max_prediction_abs_error']=max(prediction_errors)
    out['tests']['max_metric_abs_error']=max((x['max_abs_error'] for x in comparisons),default=None)


def validate(head='HEAD'):
    out={'classification':'POST_HOC_EXPLORATORY','GPU':False,'refit':False,'validator':'remediation_v1_explicit_checks','head':head,'tests':{}}
    c=Checker();state={'base':None,'sums':{}}
    def manifest():state['base'],state['sums']=check_manifest(c,out,head)
    def base():
        if c.require(state['base'] is not None,'base_unavailable','manifest step failed'):check_base_unchanged(c,out,state['base'],head)
    steps=[('manifest',manifest),('base',base),('lineage',lambda:check_lineage_and_payload(c,out)),('exclusions',lambda:check_exclusions(c,out,state['sums'])),
           ('status_index',lambda:check_status_index(c,out,state['sums'])),('claims',lambda:check_claims(c,out)),('sanitization',lambda:check_sanitization(c,out)),('science',lambda:check_science(c,out))]
    for name,step in steps:
        try:step()
        except Exception as e:  # a crashed step is a recorded failure, never a silent pass
            c.require(False,'step_error:'+name,f'{type(e).__name__}: {e}')
    out['failures']=c.failures
    out['status']='PASS' if not c.failures else 'FAIL'
    out['scope']='GITHUB_CLEAN_CHECKOUT_IDENTITY_AND_FIXED_METRIC_REPLAY; full raw-archive extraction/bootstrap requires AUTODL_LOCAL_REPLAY'
    return out


def main(argv=None):
    p=argparse.ArgumentParser(description='Validate the recovered-evidence migration in this checkout. After merging, check out the PR4 merge commit first: later main commits are outside the migration record.');p.add_argument('--report',required=True,type=Path)
    args=p.parse_args(argv)
    if args.report.resolve().is_relative_to(ROOT.resolve()):
        print(json.dumps({'status':'FAIL','failures':[{'check':'report_path','detail':'Write verification report outside immutable checkout'}]}));return 2
    result=validate();args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    summary={'status':result['status'],'hash_files':result['tests'].get('sha256_files'),'route_baseline_checks':len(result['tests'].get('frozen_route_baseline_checks',[])),
             'max_metric_abs_error':result['tests'].get('max_metric_abs_error'),'failures':len(result['failures']),'scope':result['scope']}
    if result['failures']:summary['first_failures']=result['failures'][:10]
    print(json.dumps(summary))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':sys.exit(main())
