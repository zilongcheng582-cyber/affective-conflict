"""Current frozen pairwise population and final record executor; GPU only with explicit flag."""
import argparse,json
from pathlib import Path
from src.common.runtime import verify_release,REPO
from src.emotiontalk.phase2 import execution as ex,core
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute-gpu',action='store_true');a=p.parse_args()
    verify_release()
    phase1,plan,counts,eligible=ex.population_and_plan();rows=ex.prepare_full_rows(eligible,plan)
    if not a.execute_gpu:print(json.dumps({'status':'CPU_PLAN_PASS','rows':len(rows),'counts':counts,'GPU_executed':False}));return
    if a.output.exists():raise ValueError('Output must be new; failed rows are retained')
    from src.emotiontalk.runtime import load
    torch,process_mm_info,processor,model=load();parse=core.load_parser();prompt=core.read_json(core.PROMPT_PATH)
    summary=a.output.with_name(a.output.stem+'_summary')
    if summary.exists():raise ValueError('Summary output must be new')
    summary.mkdir(parents=True);records=[]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:
        for i,row in enumerate(rows,1):
            rec=ex.execute_pairwise_record(row,i,processor,model,torch,process_mm_info,parse,prompt)
            records.append(rec)
            f.write(json.dumps(core.jsonable(rec),ensure_ascii=False,allow_nan=False)+'\n');f.flush()
    tables=ex.build_analysis(records,rows)
    for name,table in zip(('completeness','sample_analysis','pair_summary','bootstrap','emotion_pairs'),tables):
        ex.write_csv(summary/(name+'.csv'),table)
if __name__=='__main__':main()
