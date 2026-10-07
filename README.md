# Affective-Conflict

 ## Research question

 How do multimodal emotion arbitration structure and within-regime composition relate to strict zero-refit transfer across regimes? Competence/readability, pairwise identification, compositionality and parameter transport are distinct claims.

 ## Repository status

 Current authoritative Qwen mainline, version `v1.0.0-mainline`. Only current implementations and required frozen scientific definitions are included. Raw media, model weights, historical executables, failed packages and bulk inference outputs are external. Packaging/CPU checks do not rerun GPU experiments.

 ## Mainline freeze status

 `QWEN_MAINLINE_SCIENCE = CLOSED`; `B3_FINAL_SCIENTIFIC_RULING = SURVIVES_WITH_CORRECTION`. All 6354 corrected measurement rows and 5515 sequence-aware forwards completed, with zero failed or missing. Closure means the frozen experiment completed, independent of agreement with a hypothesis. See [MAINLINE_FREEZE](docs/MAINLINE_FREEZE.md).

 ## Datasets

 EmotionTalk, MCR-Bench, LISTEN and CA-MER/MER2023 must be acquired from their original providers. The four raw-to-canonical data boundaries passed. Acquisition permissions are not conveyed by this code license. See [DATASETS](docs/DATASETS.md) for required layouts, source revisions and hashes.

 ## Environment

 CPU: Python 3.12, `python -m pip install -r requirements.txt`, then `python -m pytest`. These pinned CPU packages describe the release verification environment. GPU acquisition has a separate frozen Python 3.12.3/CUDA/PyTorch environment in `configs/mainline/b3_runtime.json` and `requirements-gpu.txt`. The recorded transformers development build is required; this release does not assert that it is installable from PyPI. Obtain the exact archived build/environment rather than substituting latest. FFmpeg/ffprobe are required for media preparation. Export `AF_WORK_ROOT`, `AF_DATA_ROOT` and `AF_MODEL_DIR`; optional `AF_PATH_MAPPING` is a JSON prefix-to-directory mapping. `configs/paths.example.yaml` documents these fields; YAML is an example, not silently auto-loaded.

 ## Raw-to-canonical reconstruction

 Run modules from the repository root:

 ```bash
 python -m src.reconstruction.emotiontalk.reconstruct --root "$AF_DATA_ROOT" --output ./workspace/canonical/emotiontalk
 python -m src.reconstruction.mcr.reconstruct --root "$AF_DATA_ROOT" --gap G07 --reconstruct --output ./workspace/canonical/mcr.csv
 PYTHONHASHSEED=42 python -m src.reconstruction.listen.reconstruct --root "$AF_DATA_ROOT" --reconstruct --output ./workspace/canonical/listen.csv
 python -m src.reconstruction.camer.reconstruct --root "$AF_DATA_ROOT" --hf-ref /path/to/MER2023-main-ref --output /path/outside/raw-root/camer
 ```

 EmotionTalk emits 19250 canonical identities and a 1500-item controlled panel using the validated raw prefix. MCR G04/G05/G06/G07 expose the native pool, competitor mapping, duplicate classification and canonical arbitration pool; the unresolved old candidate writer is excluded. LISTEN requires process-start PYTHONHASHSEED=42 and the documented Python version. Media-derived manifests remain explicit frozen inputs; see reproducibility instructions.

 ## EmotionTalk Phase1

 `python -m src.emotiontalk.phase1.run --output ./workspace/phase1.jsonl` validates current input construction on CPU with user-acquired media. Add `--execute-gpu` only for an independently authorized rerun in the pinned environment. The permanently merged final executor scores candidates after every successful generation, including parser failures. The preserved source measurement table records historical Readable/TripleReadable status.

 ## Phase2

 `python -m src.emotiontalk.phase2.run --output ./workspace/phase2.jsonl` prepares the frozen 2132 ordered slots (397 AT, 371 AV, 298 VT memberships, two orders each). Add `--execute-gpu` for a new run. The necessary historical dependency has been reduced to shared helpers; its old CLI is absent. The current publication analysis uses shared utterance-level CV folds:

 ```bash
 python -m analyses.phase2.publication_cv --prepared-source-records frozen/source_model/publication_cv_records.json --input-sha256 8fb93aadd79eac9597677bd3409666ec2a31311762e0c6850673fb50f4129a13 --output ./workspace/publication_cv.json
 ```

 Prepared source records must contain the documented frozen source-standardized fields (`utterance_id`, `pair`, `_y`, `_srcz`, `_marz`, `_entz`, `_order`). This CV does not replace the frozen full-source transfer model.

 ## Phase3

 `python -m src.emotiontalk.phase3.run --output-dir ./workspace/phase3` verifies the frozen 402-slot plan on CPU; `--execute-gpu` uses the current trimodal executor. The 67 utterances have six orders each. The primary frozen compositionality result is 268/294 = 0.911564626 on resolved predictions; coverage 294/402. `python -m analyses.phase3.report --verify` verifies and reads the preserved report. The original primary-plan and complete main-analysis writers were not recovered; use the frozen plan and inference summary as authoritative artifacts, rather than claiming their historical producer has been reconstructed.

 ## Corrected Cross-Regime B3

 ```bash
 python -m src.cross_regime.target_scoring.run --verify --package-only
 python -m src.cross_regime.target_scoring.run --execute-authorized-b3 --data-root "$AF_DATA_ROOT" --model-dir "$AF_MODEL_DIR" --output-dir ../large_outputs/b3
 ```

 One frozen source sequence per scientific sample, shared across modalities, with sequence-aware cache identity. Scoring is teacher-forced candidate likelihood, softmax of mean token log probability. Entropy/log7, top1-top2 margin and structurally defined source-label probability are frozen. Weights/processor are bound to immutable commit `ae9e1690543ffd5c0221dc27f79834d0294cba00` and content manifests. Raw runner JSONL is preserved. The measurement projection/finalization step is documented in REPRODUCIBILITY; no regenerated assignment is used.

 ## Zero-refit evaluation

 ```bash
 python -m src.cross_regime.zero_refit.evaluate --gpu-outputs /path/to/B3_CORRECTED_GPU_OUTPUTS_V1 --output ./workspace/zero_refit
 python -m analyses.cross_regime.report
 ```

 CPU only. No target refit, scaler fit, threshold tuning or calibration. Formal corrected outputs must first pass completeness, identity, feature, cache and hash closeout. Source coefficients/scalers/order terms/threshold 0.5 and frozen outcomes are reused unchanged.

 ## Main results

 | Frozen role | AUROC | Balanced accuracy @0.5 | Coverage |
 |---|---:|---:|---:|
 | MCR primary | 0.727558892 | 0.500000000 | 1734/1818 = 0.953795380 |
 | LISTEN margin sensitivity; primary unsupported | 0.522637549 | 0.489190375 | 518/1139 = 0.454784899 |
 | CA-MER supported supplementary; full primary undefined | 0.686393597 | 0.595715631 | 416/672 = 0.619047619 |
 | CA-MER full margin sensitivity | 0.573999074 | 0.539941342 | 1350/2000 = 0.675000000 |

 Historical log loss remains the primary evaluation metric; AUROC/BA/Brier are prespecified secondary metrics. Full metric and comparison tables are in `results/mainline_summary/cross_regime/`. MCR strongest transfer refers to ranking; frozen-threshold BA remains 0.5. LISTEN's margin AUROC now crosses slightly above 0.5, with BA still below 0.5. Corrected numbers and correction disclosure are required in the paper.

 ## Reproducibility boundaries

 Raw → canonical multimodal population → Phase1 inputs is deterministic. Phase1 outputs → Readable/DualReadable → Phase2 → Phase3 requires **MODEL EXECUTION BY DESIGN**, or the exact archived frozen outputs. This is the normal experimental DAG, not a raw-data reproducibility failure. MCR uses its validated frozen derived artifact at the model-input boundary. See [REPRODUCIBILITY](docs/REPRODUCIBILITY.md).

 ## Known limitations

 Heterogeneous transfer is not universal transport. LISTEN primary is structurally unsupported; CA-MER full sourceprob primary is undefined outside the supported ontology role. Current code does not resurrect missing original historical writers or add new subgroup/robustness/second-model experiments. See [KNOWN_LIMITATIONS](docs/KNOWN_LIMITATIONS.md) and [PROVENANCE](docs/PROVENANCE.md).

 ## Citation

 Use `CITATION.cff` for this software version. No unpublished paper identifier or publication claim is invented. MIT applies to project code; datasets, models, dependencies and external upstream materials retain their own terms.

Frozen full-source model evidence can contain historical CV diagnostics. These are provenance only; obsolete CV result tables/reports are excluded from the current result directory. Corrected publication CV uses the shared-fold implementation and the included minimal prepared source records; packaging does not refit or replace any full-source or target model.

CA-MER media preparation reads `--data-root` and writes a new `--output-root` outside acquired inputs. Use `python -m src.reconstruction.camer.prepare_media --mapping /path/to/CAMER_MEDIA_MAPPING_V1.csv --data-root "$AF_DATA_ROOT" --output-root /path/to/new/camer-work`. The joint replay is `python -m src.cross_regime.run_camer_joint --output-dir ../large_outputs/camer` for CPU plan validation; append `--execute-gpu` only for a separately authorized execution with the frozen derived media in `AF_DATA_ROOT`. All portable orchestration changes are recorded in `docs/portable_orchestration.json`.
