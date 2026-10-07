"""Project raw successful/failure rows to the formal schema without new scoring."""
import argparse,csv,hashlib,json
from pathlib import Path
from src.cross_regime.target_scoring import b3_protocol as protocol,inputs
from src.common.runtime import REPO,verify_release

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();out=args.output_dir.resolve();verify_release()
    def rows(name):return [json.loads(x) for x in (out/name).read_text(encoding='utf-8').splitlines() if x.strip()]
    def put(name,obj):(out/name).write_bytes(protocol.canonical_bytes(obj))
    plan=inputs.read(inputs.FrozenInputs()/'B3_TARGET_MEASUREMENT_MANIFEST_V1.json')
    taskmap={t['measurement_id']:t for t in plan['measurements']}
    forwards=rows('B3_FORWARD_RESULTS_V1.jsonl');measurements=rows('B3_MEASUREMENTS_V1.jsonl')
    if len({r['measurement_id'] for r in measurements})!=len(measurements) or any(r['measurement_id'] not in taskmap for r in measurements):raise ValueError('Duplicate or unexpected scientific key')
    fmap={t['inference_cache_key']:t for t in plan['forwards']}
    if len({r['inference_cache_key'] for r in forwards})!=len(forwards):raise ValueError('Duplicate forward identity')
    for r in forwards:protocol.validate_resume_record(r,fmap[r['inference_cache_key']],inputs.acquisition()['manifest_sha256'])
    identity={'protocol_sha256':inputs.acquisition()['payload_hashes']['B3_CORRECTED_MEASUREMENT_FREEZE_V1.md'],
              'assignment_sha256':inputs.acquisition()['payload_hashes']['B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json'],
              'runner_sha256':inputs.sha(REPO/'src/cross_regime/target_scoring/run.py'),
              'execution_manifest_sha256':inputs.acquisition()['manifest_sha256']}
    annotated=[]
    for raw in measurements:
        t=taskmap[raw['measurement_id']]
        for key in ['dataset','sample_id','modality','candidate_sequence_id','candidate_sequence','raw_source_label']:
            if raw[key]!=t[key]:raise ValueError('Raw measurement identity mismatch: '+key)
        annotated.append({**raw,**identity,'scientific_measurement_row_key':raw['measurement_id']})
    fields=list(dict.fromkeys(k for r in annotated for k in r))
    with (out/'B3_CORRECTED_MEASUREMENTS_V1.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for r in annotated:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
    with (out/'B3_CORRECTED_FORWARD_RESULTS_V1.jsonl').open('xb') as f:
        for r in forwards:f.write(protocol.canonical_bytes({**r,**identity}))
    failure_path=out/'B3_TECHNICAL_FAILURES_V1.jsonl'
    failures=rows(failure_path.name) if failure_path.exists() else []
    current_keys={r['inference_cache_key'] for r in forwards}
    report={'MEASUREMENT_ROWS_EXPECTED':6354,'MEASUREMENT_ROWS_COMPLETED':sum(r['status']=='SUCCESS' for r in measurements),
            'MEASUREMENT_ROWS_FAILED':sum(r['status']!='SUCCESS' for r in measurements),'MEASUREMENT_ROWS_MISSING':6354-len(measurements),
            'FORWARD_TASKS_EXPECTED':5515,'FORWARD_TASKS_COMPLETED':len(forwards),
            'FORWARD_TASKS_FAILED':len({r['inference_cache_key'] for r in failures if r['inference_cache_key'] not in current_keys}),
            'FORWARD_TASKS_MISSING':5515-len(forwards)-len({r['inference_cache_key'] for r in failures if r['inference_cache_key'] not in current_keys})}
    put('B3_CORRECTED_EXECUTION_COMPLETENESS_V1.json',report)
    put('B3_CORRECTED_EXECUTION_PROVENANCE_V1.json',{**identity,'scientific_runner_origin_sha256':inputs.acquisition()['frozen_runner_sha256'],
        'engineering_change':'Portable release entry point; same frozen protocol/scorer/source-function bytes and scientific tasks',
        'raw_measurements_rewritten':False,'candidate_scoring_repeated_by_finalizer':False})
    files=[p for p in out.iterdir() if p.is_file() and p.name!='B3_CORRECTED_EXECUTION_SHA256SUMS.txt']
    (out/'B3_CORRECTED_EXECUTION_SHA256SUMS.txt').write_text(''.join(inputs.sha(p)+'  '+p.name+'\n' for p in sorted(files)),encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__':main()
