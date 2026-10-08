import hashlib,json,os
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]
def project_root():return Path(os.environ.get('AF_WORK_ROOT',str(REPO/'workspace'))).resolve()
def registry():return json.loads((REPO/'frozen/identity/artifact_registry.json').read_text(encoding='utf-8'))
def data_root():return Path(os.environ.get('AF_DATA_ROOT',str(project_root()))).resolve()
def external_path(path):
    # Prefixes come from frozen acquisition metadata, not a developer workstation.
    old=json.loads((REPO/'frozen/identity/acquisition.json').read_text(encoding='utf-8'))['research_root']
    text=str(path)
    if text==old or text.startswith(old+'/'):return data_root()/text[len(old):].lstrip('/')
    mappings=json.loads(os.environ.get('AF_PATH_MAPPING','{}'))
    for prefix,dest in sorted(mappings.items(),key=lambda kv:-len(kv[0])):
        if text==prefix or text.startswith(prefix+'/'):return Path(dest)/text[len(prefix):].lstrip('/')
    raise ValueError('External path requires explicit AF_PATH_MAPPING: '+text)
def input_path(relative):return REPO/registry()[relative] if relative in registry() else project_root()/relative
def relocate(value):
    if isinstance(value,list):return [relocate(x) for x in value]
    if isinstance(value,dict):return {relocate(k):relocate(v) for k,v in value.items()}
    if isinstance(value,str):
        old=json.loads((REPO/'frozen/identity/acquisition.json').read_text(encoding='utf-8'))['research_root']
        if value==old or value.startswith(old+'/'):return str(external_path(value))
    return value
def remap_namespace(ns):
    root=project_root()
    def mapone(v):
        if isinstance(v,Path) and v.is_relative_to(root):
            rel=v.relative_to(root).as_posix()
            if rel.startswith(('data/','external/','models/')):return data_root()/rel
            return input_path(rel)
        if isinstance(v,dict):return {mapone(k):mapone(x) for k,x in v.items()}
        if isinstance(v,tuple):return tuple(mapone(x) for x in v)
        return v
    for key,v in list(ns.items()):
        if not key.startswith('__'):ns[key]=mapone(v)
    if 'MODEL_DIR' in ns:ns['MODEL_DIR']=Path(os.environ.get('AF_MODEL_DIR',str(data_root()/'models/Qwen2.5-Omni-7B')))
def verify_release():
    path=REPO/'POST_AUDIT_REPAIR_MANIFEST_V1.json'
    if not path.exists():path=REPO/'RELEASE_MANIFEST_V1.json'
    manifest=json.loads(path.read_text(encoding='utf-8'))
    for r in manifest['files']:
        p=REPO/r['relative_path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=r['SHA256']:raise ValueError('Release file changed: '+str(p))
    return {'RELEASE_HASH_RECHECK':'PASS','files':len(manifest['files'])}
