"""Run the complete four-regime synthesis (CPU only) and write RUN_PROVENANCE.json + OUTPUT_MANIFEST.json.
Usage (from repo root): python -m analyses.four_regime_synthesis_v1.run_all"""
import json
import platform
import subprocess
import sys
import time
import numpy as np
import pandas as pd
from analyses.four_regime_synthesis_v1 import common
from analyses.four_regime_synthesis_v1.common import OUT, INTER, REPO, sha256
import warnings

warnings.filterwarnings('ignore')
CITED = ['results/post_audit/scientific_analysis_v1/SCIENTIFIC_ANALYSIS_V1_FINAL_REPORT.md', 'results/post_audit/scientific_analysis_v1/R1_SOURCE_STRUCTURE_REPORT.md',
         'results/post_audit/scientific_analysis_v1/R2_COMPOSITIONALITY_REPORT.md', 'results/post_audit/scientific_analysis_v1/R3_LISTEN_BEHAVIOR_REPORT.md',
         'results/eri1_scientific_closure_v1/SCIENTIFIC_CLOSURE_FINAL_REPORT.md', 'results/eri1_scientific_closure_v1/CLAIM_REGISTER_V1.md', 'results/eri1_scientific_closure_v1/ERI1_FROZEN_ANALYSIS_RESULTS_V1.json',
         'docs/SCIENTIFIC_CLAIM_STATUS_V1.md', 'docs/KNOWN_LIMITATIONS.md', 'docs/EVIDENCE_AVAILABILITY_V1.md', 'docs/PROJECT_STATE.md', 'docs/DATASETS.md',
         'protocols/mcr/MCR_CONTROLLED_SCIENTIFIC_RESULTS_V2.md', 'protocols/mcr/MCR_CONTROLLED_ARBITRATION_ANALYSIS_SPEC_V2.md', 'protocols/mcr/MCR_CONTROLLED_FULL_V2_COMPLETENESS.json',
         'protocols/mcr/MCR_CONTROLLED_DUAL_READABLE_DIAGNOSTICS_V2.csv', 'protocols/camer/CAMER_CONTROLLED_PROTOCOL_V1.md', 'configs/mainline/camer_controlled_arbitration_prompt_v1.json',
         'configs/mainline/mcr_controlled_arbitration_prompt_v2.json', 'src/common/benchmarks/listen_adapter.py', 'experiments/emotiontalk_reliability_v1/PROTOCOL_V1.md',
         'manifests/emotiontalk/EMOTIONTALK_MASTER_PANEL_V1.csv', 'manifests/emotiontalk/trimodal_plan.csv']
STEPS = ['a01_build_tables', 'a02_emotiontalk', 'a02_mcr', 'a02_listen', 'a02_camer', 'a03_cross_regime', 'a04_inventory']


def last_commit(rel):
    return subprocess.run(['git', '-C', str(REPO), 'log', '-1', '--format=%H', '--', rel], capture_output=True, text=True).stdout.strip()


def main():
    import importlib
    t0 = time.time()
    for s in STEPS:
        m = importlib.import_module(f'analyses.four_regime_synthesis_v1.{s}')
        if s == 'a01_build_tables':
            t = pd.concat([m.et_phase2(), m.eri1_rows(), m.target_rows()], ignore_index=True)
            t['outcome'] = pd.Categorical(t.outcome, m.OUTC).astype(str)
            common.write(t, 'JOINT_LONG_V1.csv', 'intermediate'); common.write(m.staleness_audit(), 'MANIFEST_FEATURE_STALENESS_AUDIT.csv', 'intermediate'); common.save_registry('a01')
        elif s == 'a02_emotiontalk':
            m.run(); m.extras()
        else:
            m.run()
        print('done', s, round(time.time() - t0, 1), 's')
    used = {}
    for p in sorted(INTER.glob('INPUTS_USED_*.json')):
        used.update(json.loads(p.read_text()))
    # the JOINT_LONG intermediate is an internal product, not an external input
    used = {k: v for k, v in used.items() if 'four_regime_structural_synthesis_v1' not in k}
    cited = {c: dict(sha256=sha256(REPO / c), last_commit=last_commit(c)) for c in CITED}
    used_full = {k: dict(sha256=v, last_commit=last_commit(k)) for k, v in used.items()}
    scripts = {str(p.relative_to(REPO)): sha256(p) for p in sorted((REPO / 'analyses/four_regime_synthesis_v1').glob('*.py'))}
    outs = {str(p.relative_to(REPO)): sha256(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('RUN_PROVENANCE.json', 'OUTPUT_MANIFEST.json') and not p.name.startswith('INPUTS_USED_')}
    prov = dict(task='FOUR_REGIME_STRUCTURAL_SYNTHESIS_V1', origin=common.ORIGIN, script_version=common.SCRIPT_VERSION, base_commit_main=common.git_head(),
                branch=subprocess.run(['git', '-C', str(REPO), 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True).stdout.strip(),
                eri1_scientific_seal_commit='544ca0efae158df369a7b25dd110dc4254f67a7d', seed=common.SEED, bootstrap_replicates_default=common.B,
                python=sys.version.split()[0], numpy=np.__version__, pandas=pd.__version__, platform=platform.platform(),
                gpu_used=False, model_loaded=False, frozen_models_refit=False, frozen_files_modified=False,
                statistical_units='see 02_WITHIN_DATASET_STRUCTURAL_ANALYSIS.md section 0 (cluster = dialogue / audio-dialogue token / LISTEN base item / CA-MER sample)',
                input_files_read_by_code=used_full, cited_files_not_read_by_code=cited, analysis_scripts_sha256=scripts, runtime_seconds=round(time.time() - t0, 1))
    (OUT / 'RUN_PROVENANCE.json').write_text(json.dumps(prov, indent=1))
    (OUT / 'OUTPUT_MANIFEST.json').write_text(json.dumps(dict(n_files=len(outs), files=outs), indent=1))
    print('inputs', len(used), 'outputs', len(outs))


if __name__ == '__main__':
    main()
