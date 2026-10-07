"""Current six-order trimodal executor with the frozen 402-row primary plan."""
import argparse,json
from pathlib import Path
from src.common.runtime import REPO,relocate,verify_release
from src.emotiontalk.phase3 import execution as ex
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True,type=Path);p.add_argument('--execute-gpu',action='store_true');a=p.parse_args();verify_release()
    rows=ex.read_csv(REPO/'manifests/emotiontalk/trimodal_plan.csv')
    if len(rows)!=402 or len({(r['utterance_id'],r['tri_order']) for r in rows})!=402:raise ValueError('Frozen plan identity mismatch')
    if not a.execute_gpu:print(json.dumps({'status':'CPU_PLAN_PASS','rows':402,'GPU_executed':False}));return
    if a.output_dir.exists():raise ValueError('Output directory must be new')
    a.output_dir.mkdir(parents=True);ex.OUT=a.output_dir
    from src.emotiontalk.runtime import load
    torch,process_mm_info,processor,model=load();parse=ex.load_parser();prompt=json.loads((REPO/'configs/mainline/emotiontalk_controlled_prompt_v1.json').read_text(encoding='utf-8'))
    ex.LOCKS={path:digest for path,digest in ex.LOCKS.items() if path!=ex.PHASE2_JSONL}
    ex.run_records('full',rows,prompt,process_mm_info,processor,model,parse)
if __name__=='__main__':main()
