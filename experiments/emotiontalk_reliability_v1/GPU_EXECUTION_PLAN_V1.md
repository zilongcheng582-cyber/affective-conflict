# GPU EXECUTION PLAN V1

**No GPU work has been executed.** GPU execution needs separate authorization (`configs/mainline/b3_runtime.json`:
`requires_separate_GPU_authorization: true`).

## Environment (reused, frozen)

- Python 3.12.3, the pinned stack in `requirements-gpu.txt` (torch 2.8.0+cu128, transformers 4.52.0.dev0 archived build, qwen-omni-utils 0.0.9,
  flash-attn 2.8.3, librosa 1.0.0), and ffmpeg/ffprobe. Use the archived AutoDL environment; do not install the latest versions.
- Model: Qwen2.5-Omni-7B at `AF_MODEL_DIR`, revision `ae9e1690…`. The content of every model and processor file is hash-verified by
  `src.emotiontalk.runtime.load()` → `src.cross_regime.target_scoring.verify_runtime.verify`. That check also verifies the release manifest, the pinned Python and package versions, and GPU presence.
- Loading: `torch_dtype=auto`, `attn_implementation=flash_attention_2`, `device_map=cuda`, `local_files_only=True` (from `b3_runtime.json`).
- Decoding and scoring: the unchanged Phase1/Phase2 kernels (greedy, `max_new_tokens=16`, `use_audio_in_video=False`, `return_audio=False`, teacher-forced scoring with `use_cache=False`).

## Workload

| Run | Items | Trials | `generate` calls | Teacher-forced scoring passes | Unimodal trials | Joint trials |
|---|---:|---:|---:|---:|---:|---:|
| Pilot | 6 | 96 | 96 | 96 | 36 (30 A_ONLY + 6 V_ONLY) | 60 |
| Full | 146 | 2,336 | 2,336 | 2,336 | 876 (730 A_ONLY + 146 V_ONLY) | 1,460 |

- Per item: 16 trials (1 V_ONLY + 5 conditions × 3 arms), i.e. 16 `generate` calls and 16 scoring passes.
- **Planned GPU model passes for the full run: 4,672** (2,336 generation + 2,336 scoring). The pilot adds 192.
- Each scoring pass is one prefix thinker forward plus one extra forward per candidate label that tokenizes into more than one token. So it takes between 1 and 8 thinker forwards per pass;
  the exact count is recorded per trial (`candidate_scoring_forward_calls`).
- Unimodal scoring is required for the primary manipulation check. Joint scoring is a secondary endpoint; if it fails, that is recorded as `joint_scoring_status=FAILED` without invalidating the joint generation.
- For scale: the historical Phase2 run made 2,132 `generate` calls with the same model, prompt and kernels. The historical Phase1 run made 4,500 generations, each followed by scoring.
- Audio preparation (CPU, AutoDL): 584 intervention WAVs (146 × RECODE/SNR20/SNR10/SNR00), each 16 kHz float32 mono.

**Runtime and cost are not estimated here.** No timing was measured for this configuration. The pilot records `runtime_seconds` and peak GPU memory
for every trial (`pilot_check` → `resource`). Full-run time and cost are computed from those measurements before the full run is authorized.

## GPU memory recommendation

Qwen2.5-Omni-7B weights are loaded in bf16, and the joint trials add the frozen silent-video frames plus up to about one clip of audio.
Recommendation: a **≥ 40 GB GPU** (A100/A800 40 or 80 GB class; earlier mainline work in this project used A100/A800-class cards). 24 GB cards are not recommended without pilot evidence.
This is a recommendation, not a measurement. The pilot's `peak_allocated_bytes_max` is the deciding number. An OOM is a technical failure and is never solved by
reducing media quality or length.

## Checkpoint and resume

- Output: a new directory with `RUN_LOCK.json` and append-only `trials.jsonl`. Each finished trial is written, flushed and `fsync`ed immediately.
- The lock fingerprint covers phase, manifest SHA256, binding SHA256, and the SHA256 of the runner, design, Phase1/Phase2 kernels, prompt, parser and runtime config.
  Resuming with any difference aborts (fail-closed).
- Resume: rerun the identical command, and completed `trial_id`s are skipped. `--max-trials N` runs bounded batches, for example on preemptible instances.
- Retry: `--retry-technical-failures` runs at most one identical re-execution of trials whose only attempt was a technical failure. Both attempts are kept.
- Identity: every trial re-hashes its audio, silent video and text JSON (a cache keyed on size and mtime) before execution. A mismatch aborts the run.
- The binding stores absolute AutoDL paths. Pilot and full must run against the same storage layout, or else a new binding (new SHA) is needed and becomes a new, documented lock.
