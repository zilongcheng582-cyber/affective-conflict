"""Corrected primary B3 acquisition only; explicit future execution authorization required."""
import argparse
import json
import os
import sys
from pathlib import Path
from src.cross_regime.target_scoring import b3_protocol as protocol
from src.cross_regime.target_scoring import b3_scorer as scorer
from src.cross_regime.target_scoring import inputs as contract
from src.cross_regime.target_scoring import verify_runtime as verifier


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--package-only',action='store_true')
    parser.add_argument('--execute-authorized-b3',action='store_true',help='Use only after separate GPU execution authorization')
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--data-root',type=Path,required=False);parser.add_argument('--model-dir',type=Path,required=False)
    args=parser.parse_args();package=contract.FrozenInputs();contract.configure(args)
    if not args.verify and not args.execute_authorized_b3:
        parser.print_help();return 0
    if args.package_only and args.execute_authorized_b3:parser.error('--package-only cannot execute GPU work')
    report=verifier.verify(package,package_only=args.package_only)
    print(json.dumps(report,sort_keys=True),flush=True)
    if args.package_only:return 0 if report.get('SCIENTIFIC_FREEZE_PRESERVED')=='YES' and report.get('RELEASE_HASH_RECHECK')=='PASS' else 1
    if report.get('GPU_EXECUTION_ALLOWED')!='YES':return 1
    if not args.execute_authorized_b3:return 0
    if args.output_dir is None:parser.error('An isolated --output-dir is required')
    config=contract.read(package/'B3_EXECUTION_CONFIG_V1.json');out=args.output_dir.resolve()
    historical=Path(config['research_root']).resolve()
    if out==historical or historical in out.parents or out==contract.REPO or contract.REPO in out.parents:
        parser.error('Output must be outside the immutable historical research tree and frozen package')
    # All checks complete before any model/GPU library import.
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    plan=contract.read(package/'B3_TARGET_MEASUREMENT_MANIFEST_V1.json')
    manifest_sha=contract.acquisition()['manifest_sha256']
    forwards=[{**x,'manifest_sha256':manifest_sha} for x in plan['forwards']]
    out.mkdir(parents=True,exist_ok=True)
    cache_path=out/'B3_FORWARD_RESULTS_V1.jsonl';failure_path=out/'B3_TECHNICAL_FAILURES_V1.jsonl'
    cache=scorer.load_cache(cache_path,forwards,manifest_sha)
    # Failures remain explicit; previously successful forwards alone may resume.
    import torch
    from transformers import Qwen2_5OmniProcessor,Qwen2_5OmniForConditionalGeneration
    from qwen_omni_utils import process_mm_info
    identity=contract.read(package/'B3_MODEL_IDENTITY_BINDING_V1.json')
    processor=Qwen2_5OmniProcessor.from_pretrained(identity['local_snapshot_path'],local_files_only=True)
    model=Qwen2_5OmniForConditionalGeneration.from_pretrained(identity['local_snapshot_path'],**config['model_loading'])
    model.eval();prompt=contract.read(package/'emotiontalk_controlled_prompt_v1.json')
    for task in forwards:
        key=task['inference_cache_key']
        if key in cache:continue
        try:
            evidence=contract.relocate({**task['evidence'],'dataset_root':config['research_root'],'locator':task['evidence_locator']})
            result=scorer.score_evidence(task,evidence,prompt,processor,model,torch,process_mm_info)
            # A forward is evidence-level; its auxiliary source probability is
            # structurally absent. Label-specific values are joined per sample.
            record={**{k:task[k] for k in protocol.CACHE_FIELDS},**result,
                    'sample_id':task['sample_id'],'served_measurement_ids':[x['measurement_id'] for x in plan['measurements'] if x['inference_cache_key']==key],
                    'evidence_locator':task['evidence_locator'],'source_label_probability':None,
                    'source_label_probability_defined':False,'raw_source_label':None}
            protocol.validate_resume_record(record,task,manifest_sha)
            with cache_path.open('ab') as f:f.write(protocol.canonical_bytes(record));f.flush();os.fsync(f.fileno())
            cache[key]=record
        except Exception as exc:
            failure={'dataset':task['dataset'],'sample_id':task['sample_id'],'modality':task['modality'],
                     'inference_cache_key':key,'candidate_sequence_id':task['candidate_sequence_id'],
                     'candidate_sequence':task['candidate_sequence'],'manifest_sha256':manifest_sha,
                     'status':'TECHNICAL_FAILURE','error_type':type(exc).__name__,'error':str(exc)}
            with failure_path.open('ab') as f:f.write(protocol.canonical_bytes(failure));f.flush();os.fsync(f.fileno())
            if isinstance(exc,torch.cuda.OutOfMemoryError):torch.cuda.empty_cache()
    measurement_path=out/'B3_MEASUREMENTS_V1.jsonl';tmp=out/'B3_MEASUREMENTS_V1.jsonl.tmp'
    with tmp.open('wb') as f:
        for task in plan['measurements']:
            key=task['inference_cache_key']
            if key in cache:
                r=protocol.measurement_record(task,cache[key],task['raw_source_label'],manifest_sha)
                r.update(status='SUCCESS',measurement_id=task['measurement_id'],inference_cache_key=key,
                         stable_dataset_id=task['stable_dataset_id'],evidence_locator=task['evidence_locator'],
                         model_content_sha256=task['model_content_sha256'],processor_content_sha256=task['processor_content_sha256'])
                for k in ['candidate_log_scores','candidate_sum_log_scores','candidate_probabilities_sum_sensitivity']:r[k]=cache[key][k]
            else:
                r={k:v for k,v in task.items() if k!='evidence'}
                r.update(status='TECHNICAL_MISSING',manifest_sha256=manifest_sha,candidate_probabilities=None)
            f.write(protocol.canonical_bytes(r))
    tmp.replace(measurement_path)
    report={'N_prespecified_measurements':len(plan['measurements']),'N_successful_measurements':sum(x['inference_cache_key'] in cache for x in plan['measurements']),
            'N_prespecified_forwards':len(forwards),'N_successful_forwards':len(cache),'manifest_sha256':manifest_sha,
            'transfer_evaluation_performed':False,'outcome_ruling':'NOT_EVALUATED'}
    (out/'B3_ACQUISITION_COMPLETENESS_V1.json').write_bytes(protocol.canonical_bytes(report))
    print(json.dumps(report,sort_keys=True));return 0 if len(cache)==len(forwards) else 2


if __name__=='__main__':sys.exit(main())
