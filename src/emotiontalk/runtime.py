import json,os
from pathlib import Path
from src.common.runtime import REPO,verify_release
def load():
    from src.cross_regime.target_scoring.inputs import FrozenInputs
    from src.cross_regime.target_scoring.verify_runtime import verify
    report=verify(FrozenInputs())
    if report.get('GPU_EXECUTION_ALLOWED')!='YES':raise ValueError(report)
    from src.common.audio_compat import patch_audioread_compat
    patch_audioread_compat()
    import torch
    from transformers import Qwen2_5OmniProcessor,Qwen2_5OmniForConditionalGeneration
    from qwen_omni_utils import process_mm_info
    path=os.environ['AF_MODEL_DIR'];cfg=json.loads((REPO/'configs/mainline/b3_runtime.json').read_text(encoding='utf-8'))
    processor=Qwen2_5OmniProcessor.from_pretrained(path,local_files_only=True)
    model=Qwen2_5OmniForConditionalGeneration.from_pretrained(path,**cfg['model_loading']);model.eval()
    return torch,process_mm_info,processor,model
