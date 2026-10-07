"""Current Phase1 executor, including unconditional scoring after successful generation."""
import argparse,json,traceback
from collections import Counter
from pathlib import Path
from src.common.runtime import REPO,verify_release
from src.emotiontalk.phase1 import execution as ex,plan
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute-gpu',action='store_true');a=p.parse_args();verify_release()
    context={'official_repo_commit':'cb8397e226ce7c1fccee41ea21161a3f98f578e1'}
    samples,panel,patterns,pairs,media=plan.build_samples(ex,context)
    if not a.execute_gpu:print(json.dumps({'status':'CPU_INPUT_PASS','samples':len(samples),'slots':4500,'GPU_executed':False}));return
    if a.output.exists():raise ValueError('Output must be new; failure rows cannot be removed')
    from src.emotiontalk.runtime import load
    from src.common.benchmarks.emotiontalk_controlled_parser_v1 import parse_label
    torch,process_mm_info,processor,model=load();prompt=ex.read_json(ex.PROMPT_PATH);counters=Counter()
    summary=a.output.with_name(a.output.stem+'_summary')
    if summary.exists():raise ValueError('Summary output must be new')
    summary.mkdir(parents=True)
    plan.OUT=summary;plan.REPORT_JSON=summary/'competence.json';plan.REPORT_MD=summary/'competence.md'
    definitions={str(path.relative_to(REPO)):plan.sha_file(path) for path in
                 (ex.PANEL_CSV,ex.MEDIA_MANIFEST,ex.FREEZE_PROVENANCE,ex.PROMPT_PATH)}
    frozen_hashes={'frozen_input_bundle_sha256':plan.stable_digest(definitions)}
    records=[]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f:
        for sample in samples:
            for arm in plan.ARMS:
                before=counters['generation_attempt_count']
                try:
                    rec=ex.perform_arm(sample,arm,prompt,processor,model,torch,process_mm_info,parse_label,counters)
                except Exception as exc:
                    rec={'utterance_id':sample['utterance_id'],'arm':arm,'resource_tier':'MASTER_PANEL',
                         'generation_attempted':counters['generation_attempt_count']>before,
                         'generation_success':False,'parser_execution':False,'candidate_scoring_status':'NOT_RUN',
                         'failure_type':'CUDA_OOM' if 'out of memory' in str(exc).lower() else 'UNKNOWN_TECHNICAL_FAILURE',
                         'failure_message':str(exc),'failure_traceback':traceback.format_exc()}
                rec.update({'phase1_record_index':sample['frozen_panel_row_index'],'phase1_attempt_number':1,
                            'frozen_input_bundle_sha256':frozen_hashes['frozen_input_bundle_sha256'],
                            'frozen_hashes_verified':True,'technical_runner_revision_sha256':plan.sha_file(Path(__file__)),
                            'speaker_id':sample['speaker_id'],'official_split':sample['official_split'],
                            'trimodal_pattern':sample['trimodal_pattern'],'text_emotion':sample['text_emotion'],
                            'audio_emotion':sample['audio_emotion'],'video_emotion':sample['video_emotion'],
                            'multimodal_emotion':sample['multimodal_emotion'],
                            'video_file_size_bytes':sample['video_file_size_bytes'] if arm=='V_ONLY' else None,
                            'frozen_panel_row_index':sample['frozen_panel_row_index']})
                if rec.get('parser_status')=='PARSER_EXCEPTION':rec['failure_type']='PARSER_EXECUTION_FAILURE'
                records.append(rec)
                f.write(json.dumps(rec,ensure_ascii=False,allow_nan=False)+'\n');f.flush()
    report=plan.summarize(ex,samples,panel,records,frozen_hashes)
    print(json.dumps(report,ensure_ascii=False,allow_nan=False))
if __name__=='__main__':main()
