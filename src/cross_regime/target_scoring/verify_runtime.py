import importlib.metadata,json,platform,os,subprocess
from pathlib import Path
from src.common.runtime import verify_release,REPO
from src.cross_regime.target_scoring import b3_protocol as protocol,b3_scorer as scorer,inputs
def portable_inventory_check(expected,observed):
    if len(expected)!=len(set(expected)) or len(observed)!=len(set(observed)) or sorted(expected)!=sorted(observed):raise ValueError('Duplicate or changed inventory membership')
def verify(package,package_only=False):
    try:
        report=verify_release();plan=inputs.read(package/'B3_TARGET_MEASUREMENT_MANIFEST_V1.json')
        if (len(plan['measurements']),len(plan['forwards']))!=(6354,5515):raise ValueError('Frozen population changed')
        for row in plan['forwards']:
            if row['scoring_code_sha256']!=scorer.implementation_sha256():raise ValueError('Frozen scorer changed')
            protocol.cache_identity(row)
        if not package_only:
            cfg=inputs.read(package/'B3_EXECUTION_CONFIG_V1.json')
            if platform.python_version()!=cfg['python_version']:raise ValueError('Pinned GPU Python version required')
            for name,version in cfg['dependency_versions'].items():
                if importlib.metadata.version(name)!=version:raise ValueError('Pinned GPU dependency differs: '+name)
            model=inputs.read(package/'B3_MODEL_IDENTITY_BINDING_V1.json');snapshot=Path(model['local_snapshot_path'])
            import csv,hashlib
            for filename in ['model_files.csv','processor_files.csv']:
                with (REPO/'frozen/identity'/filename).open(encoding='utf-8-sig',newline='') as f:
                    rows=list(csv.DictReader(f))
                for r in rows:
                    name=r.get('relative_path',r.get('filename',r.get('path')));expected=r.get('SHA256',r.get('sha256'))
                    p=snapshot/name
                    h=hashlib.sha256()
                    with p.open('rb') as g:
                        for b in iter(lambda:g.read(1<<20),b''):h.update(b)
                    if h.hexdigest()!=expected:raise ValueError('Pinned model/processor content mismatch: '+name)
            q=subprocess.run(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],capture_output=True,text=True)
            if q.returncode or not q.stdout.strip():raise ValueError('GPU unavailable')
        return {**report,'SCIENTIFIC_FREEZE_PRESERVED':'YES','GPU_EXECUTION_ALLOWED':'NO' if package_only else 'YES','GPU_EXECUTION_PERFORMED':'NO','engineering_change':'Portable release gate replaces path-order-dependent historical packaging verifier; scorer kernels and scientific definitions byte-identical'}
    except Exception as e:return {'GPU_EXECUTION_ALLOWED':'NO','error':str(e)}
