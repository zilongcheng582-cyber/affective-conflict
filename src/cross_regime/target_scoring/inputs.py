import hashlib,json,os
from pathlib import Path
from src.common.runtime import REPO,relocate
NAMES={'B3_TARGET_MEASUREMENT_MANIFEST_V1.json':'manifests/cross_regime/measurement_tasks.json','B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json':'frozen/target_assignment/assignment.json','B3_SOURCE_MODEL_BINDING_V1.json':'frozen/source_model/binding.json','B3_MODEL_IDENTITY_BINDING_V1.json':'frozen/identity/model.json','B3_PROCESSOR_IDENTITY_BINDING_V1.json':'frozen/identity/processor.json','B3_EXECUTION_CONFIG_V1.json':'configs/mainline/b3_runtime.json','B3_EVALUATION_PLAN_V1.json':'protocols/b3/evaluation_plan.json','B3_CORRECTED_MEASUREMENT_FREEZE_V1.md':'protocols/b3/measurement_freeze.md','B3_OUTPUT_SCHEMA_V1.json':'protocols/b3/output_schema.json','emotiontalk_controlled_prompt_v1.json':'configs/mainline/emotiontalk_prompt.json','EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json':'frozen/candidate_sequences/definition.json','EXECUTION_PACKAGE_MANIFEST.json':'frozen/identity/acquisition.json'}
class FrozenInputs:
    def __truediv__(self,name):
        if name in NAMES:return REPO/NAMES[name]
        if name.startswith('bindings/'):return REPO/'frozen/source_model'/Path(name).name
        if name in ['b3_protocol.py','b3_scorer.py','source_teacher_forcing.py']:return REPO/'src/cross_regime/target_scoring'/name
        raise KeyError('No obsolete package entry: '+name)
def acquisition():return json.loads((REPO/'frozen/identity/acquisition.json').read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    p=Path(path);x=json.loads(p.read_text(encoding='utf-8-sig'))
    if p.name=='b3_runtime.json':x={**x,'research_root':os.environ.get('AF_DATA_ROOT','.'),'model_loading':x['model_loading']}
    if p.name=='model.json':x={**x,'local_snapshot_path':os.environ.get('AF_MODEL_DIR','models/Qwen2.5-Omni-7B')}
    return x
def configure(args):
    if args.data_root:os.environ['AF_DATA_ROOT']=str(args.data_root.resolve())
    if args.model_dir:os.environ['AF_MODEL_DIR']=str(args.model_dir.resolve())
