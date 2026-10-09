# EMOTIONTALK_RELIABILITY_INTERVENTION_V1 — Protocol

Status: **DESIGN FROZEN BEFORE ANY GPU EXECUTION.** The freeze is recorded in `DESIGN_FREEZE_RECORD_V1.json` and in the design-freeze git commit.
Experiment branch: `experiment/emotiontalk-reliability-intervention-v1`, created from `main` at `d7b713f2a834e7341a6250e794867df7f3661779`.
This is a new, separately recorded experiment. It does not modify the R1–R3 reports, frozen models, manifests, evidence or historical results.

## 1. Motivation and question

R1 (`results/post_audit/scientific_analysis_v1/`) found an *observational* predictive association in EmotionTalk. Qwen2.5-Omni's bimodal
choice is predicted by the difference in its own unimodal normalized entropy (CV AUROC ≈ 0.80). The model tends to choose the side whose unimodal
output was less uncertain. Within AV conflicts the association is strong, and the AV pair-specific diagnostic entropy coefficient is −6.31 per unit [−8.25, −4.38].

**Causal question.** If the quality of one modality's input is randomly degraded, does the model's (i) unimodal uncertainty and
(ii) bimodal arbitration change reproducibly and in the predicted direction?

Three quantities are kept separate:
1. effect of degradation on audio-only entropy (manipulation check);
2. **causal effect of degradation on the joint arbitration choice (primary)**;
3. association between entropy change and choice change (exploratory, associational).

Because the intervention changes the audio input itself, it can affect the joint choice through paths other than the entropy the model
expresses in an audio-only pass. **This design does not identify entropy as a causal mediator, and no such claim will be made.**

## 2. Design summary

| Element | Locked choice |
|---|---|
| Modality pair | **Audio–Video (AV)** |
| Manipulated modality | Audio only. Video is the frozen derived silent MP4, byte-identical in every condition (SHA256 verified per trial). |
| Population | All **146** items with AV source-label conflict and Phase1 `DualReadable_AV` (= the historical Phase2 AV conflict population; 292 historical arms) |
| Conditions | CLEAN (original file); RECODE (pipeline control, no noise); SNR20; SNR10; SNR00 (white Gaussian noise at 20/10/0 dB) |
| Measurements per condition | A_ONLY (generation + teacher-forced 7-label scoring), A_THEN_V, V_THEN_A (generation + secondary teacher-forced scoring) |
| Video-only | V_ONLY once per item (CLEAN), since video never changes |
| Trials | 16 per item; **2,336 full** (146 items); **96 pilot** (6 items) |
| Assignment | Fully crossed within item: every item receives every condition and both orders. Assignment therefore cannot depend on potential outcomes. Execution order is a seeded random permutation. |
| Candidate sequence | Each item's frozen `candidate_sequence` (CS01–CS14), identical across all of its trials |
| Prompt / parser / decoding | Frozen `configs/mainline/emotiontalk_controlled_prompt_v1.json`, frozen parser, greedy decoding with `max_new_tokens=16`, `use_audio_in_video=False`; same as Phase1/Phase2 |
| Kernels | `phase1.execution.perform_arm`, `phase2.execution.execute_pairwise_record`, `phase1.execution.score_candidate_strings`, unchanged |

AV was chosen over AT because it has more eligible conflict items (146 vs 62 in the frozen Phase2 population) and stronger R1 signal (AV out-of-fold AUROC 0.79 vs AT 0.69).
Audio degradation is executable from the frozen WAVs, with no new assets. Video degradation, text masking and AT are deferred to later, separate protocols.

## 3. Population and sampling (`ELIGIBILITY_AND_SAMPLING_V1.csv`)

Eligibility uses only frozen pre-intervention data:
- AV source labels conflict (`y_A ≠ y_V`);
- Phase1 technical completion for A and V;
- Phase1 `Readable_A` and `Readable_V` (`DualReadable_AV`);
- the silent video is certified (`validation_status = PASS`, 0 audio streams).

This is exactly the frozen Phase2 AV conflict definition. The builder checks that it reproduces `DualReadable_AV` and that each eligible item has both historical Phase2 AV arms.
Phase2 outcomes, entropy values and correctness are **not** used for selection. Items are not restricted to historically "resolved" or "correct" joint responses.

Accounting over the 1,500-item panel: 146 eligible and 1,354 excluded. Exclusion reasons are listed per row. Of the 900 AV conflict items, 754 are excluded for Phase1 readability (322 neither modality, 261 V only, 171 A only).
The 146 eligible items cover 19 speaker codes and three patterns: T=A≠V 58, T=V≠A 51, ALL_DIFFERENT 37.

There are 146 independent items. The 292 historical records are two orders of the same items, not independent observations.

**Pilot items:** 6, two per trimodal pattern, chosen by a seeded random draw (`derived_seed('PILOT_SELECTION')`) that uses no outcome information.
Pilot items are also part of the full experiment and are re-executed there. Pilot records are never used in the scientific analysis.

## 4. Audio intervention specification (`src/emotiontalk/reliability_v1/audio.py`, `ERI1_AUDIO_SPEC_V1`)

1. Read the frozen source WAV. Integer PCM is converted to float by dividing by 2^(bits−1), and uint8 is centred at 128.
2. Downmix to mono by the channel mean.
3. Resample to 16,000 Hz with `scipy.signal.resample_poly`, an exact rational ratio. Qwen's loader also uses 16 kHz mono. Generating the noise at 16 kHz means the nominal SNR
   equals the SNR at the model's feature extractor, because no later low-pass removes noise energy.
4. Signal power is the full-clip mean square at 16 kHz, with no voice-activity detection. Zero or non-finite power is a technical failure.
5. Noise is white Gaussian. Each item has one base realization from numpy PCG64 with seed `derived_seed(utterance_id, 'AUDIO_WHITE_NOISE_V1')` (stored per trial in the manifest).
   This same realization is rescaled for 20/10/0 dB, giving a nested design. The realized SNR equals the target within 1e−6 dB, which is asserted.
6. y = x + n (RECODE: y = x). There is no normalization and no clipping. Output is 32-bit IEEE-float WAV, 16 kHz, mono. Peak |y| and the count of samples above 1.0 are recorded, and values above 1.0 are kept.
7. The SHA256 of every written file is recorded in the binding table and verified at use time for every trial (fail-closed). The stored-file SNR
   (|error| ≤ 0.01 dB) and the model-loader SNR (`librosa.load(sr=16000)`, |error| ≤ 0.05 dB) are checked before the pilot proceeds.

CLEAN uses the untouched original file, as in Phase1/Phase2. RECODE passes through the same read/downmix/resample/write path as the noise conditions,
so **SNRxx − RECODE isolates the noise**, and **RECODE − CLEAN measures the pipeline itself**.
The levels (20/10/0 dB) are locked now and will not be changed after any arbitration outcome is seen. The pilot can only stop or repair the execution;
it cannot retune the levels.

## 5. Identity and fail-closed rules

- The manifest regenerates byte-identically from the frozen inputs, and its SHA256 must match `DESIGN_FREEZE_RECORD_V1.json`. The runner checks this before every run.
- Before the pilot, the binding table (`AUDIO_INTERVENTION_BINDING_V1.csv`, produced on AutoDL) must be committed, and its SHA256 passed to every run.
  It must contain one row per item × condition, the frozen silent-video SHA256, and the manifest noise seeds.
- Each trial re-verifies the SHA256 of its audio file, silent video and text JSON before execution. Any mismatch aborts the run instead of recording a row.
- The run lock fingerprint covers phase, manifest SHA, binding SHA and the SHA256 of all kernel/runner/prompt/parser/runtime-config files. A resume with a different fingerprint aborts.
- Outputs go only to new directories. Historical results are never overwritten.
- No cross-trial cache. Each trial builds fresh processor inputs, scoring uses `use_cache=False`, and generation is a new call.

## 6. Technical failures

Technical failures are CUDA OOM, media or processor failure, generation failure and scoring failure. They are retained as records.
**One** identical re-execution of a technically failed trial is allowed (`--retry-technical-failures`). Both attempts are kept, and the analysis uses the latest.
There is no quality reduction, alternate preprocessing, or outcome-based skipping. Residual failures are handled by the analysis plan's conservative
imputation. They are never silently dropped. PARSE_FAIL and OTHER are model behaviour, not technical failure.

## 7. Analysis

Fully pre-specified in `ANALYSIS_PLAN_V1.md` and implemented in `src/emotiontalk/reliability_v1/analyze.py`.

## 8. What would count against the hypothesis

If audio-only entropy rises but the joint choice does not shift away from the audio-side label, that is evidence **against** the core hypothesis.
So is a shift in the opposite direction. Details are in `ANALYSIS_PLAN_V1.md` §6.

## 9. Pre-pilot requirements (not design gaps)

1. On AutoDL, `bind_media` must be run to hash the source WAVs, generate the 584 intervention files and write the binding table.
   No frozen source-WAV hash exists in the repository, so this binding creates the audio identity anchor.
2. The binding table must be committed to the experiment branch, with its SHA256 recorded, before the pilot starts.
3. GPU execution needs separate authorization (`configs/mainline/b3_runtime.json`: `requires_separate_GPU_authorization`).
