# PILOT PLAN V1 — technical pilot (science-blind)

**Not executed in this round.** The pilot validates execution only. It does not test, estimate or tune the scientific hypothesis.

## Scope

- **6 items**: two per trimodal pattern, seeded and outcome-blind (`pilot_selected=True` in `ELIGIBILITY_AND_SAMPLING_V1.csv`).
- **96 trials**: per item, V_ONLY×1 plus 5 conditions × {A_ONLY, A_THEN_V, V_THEN_A}. That is 96 `generate` calls and 96 teacher-forced scoring passes.
- Executed in `execution_rank_pilot` order, to a NEW pilot output directory.
- Pilot items are re-executed in the full run. Pilot records are never analysed scientifically or pooled; `analyze.py` refuses them.

## Pass criteria (`python -m src.emotiontalk.reliability_v1.pilot_check`)

| Gate | Requirement |
|---|---|
| G1 | All 96 trial IDs recorded; no duplicate (trial, attempt) |
| G2 | Zero residual technical failures after at most one identical re-execution |
| G3 | Run lock matches the frozen manifest SHA256, the committed binding SHA256 and phase=pilot |
| G4a | CLEAN A_ONLY and V_ONLY parsed labels equal historical Phase1 `pred_A`/`pred_V` for all 12 |
| G4b | CLEAN audio-/video-only normalized entropy within 0.01 of historical Phase1 values |
| G4c | CLEAN joint parsed labels equal historical Phase2 labels for ≥ 11 of 12 arms |
| G5a | Stored-file SNR within 0.01 dB of target for every pilot noise file |
| G5b | Model-loader SNR (`librosa.load(sr=16000)`, run in the Qwen environment) within 0.05 dB of target, present for every noise file |
| G6 | Every audio-bearing trial used exactly its bound intervention file (recorded evidence path = binding path) |
| G7 | Resume test: run with `--max-trials 10`, then resume. No duplicates, lock accepted, 96 trials total. |

G4 checks that the reused kernels and environment reproduce the frozen historical measurements on unmodified input. It compares only CLEAN
against history, never the degraded conditions.

Also reported (not gates): pooled PARSE_FAIL count; mean and total runtime per trial; peak GPU allocation.
These are used to plan the full run's batches. `pilot_check` does **not** compute any SIDE_A/SIDE_V/OTHER rate by condition.

## Decision

- All gates PASS → `PILOT_TECHNICAL_STATUS = PASS`. The full run may be authorized with the **same** manifest, binding, code and levels.
- Any gate FAIL → stop and diagnose the execution (environment, paths, processor, memory). A fix that changes code changes the lock fingerprint
  and needs a new, documented pilot. **The pilot outcome never changes the noise levels, the population or the endpoints.**
  It cannot fail on the strength or direction of any effect.
- CUDA OOM → record and stop. Resolve with hardware (larger GPU) or documented memory settings that do not change model inputs. Never use lower quality or shorter media.
