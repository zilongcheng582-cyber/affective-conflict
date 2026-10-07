# CA-MER controlled arbitration protocol V1

Status: frozen for a future technical gate. No model has been loaded and no scientific evaluation has been run.

## Source and construct

The source is the pinned MoSEAR commit `780519a554538451c8700117dd49f1f8b52da228`, using only `audio_pseudo_label` and `video_pseudo_label` from the three official CA-MER annotation files. These are source-provided evidence-side pseudo-labels, not ground truth. `final_label`, `emotionllama_pseudo_label`, reasoning, subtitle, modality analyses, and the media-mapping `target` are excluded from label construction and model input.

Normalize labels mechanically by Unicode casefolding and trimming whitespace/obvious punctuation at the edges only. Do not merge synonyms, related emotions, morphology, or internal punctuation. The conflict rule is exactly `norm(y_A) != norm(y_V)`. The official split yields 500/500 conflicts in audio-aligned, 500/500 in video-aligned, and 0/500 in consistent: 1,000 conflicts and 500 consistent controls.

The measured source-local ontology is finite and atomic, with a 16-label union. Therefore use `FULL_SOURCE_LOCAL_ONTOLOGY`, the unmerged union of both official side-label vocabularies. Keep all 16 candidates available in every arm. No transfer, alternate ontology, or label remapping is part of V1.

## Four arms and masking

| Arm | Payload order | Required masking |
|---|---|---|
| A_ONLY | derived audio, instruction | Audio-only mono 16 kHz file; no video, subtitle, transcript, source label, reasoning, or sample metadata. |
| V_ONLY | silent video, instruction | Actual video stream with zero audio streams; no audio payload, subtitle, transcript, source label, reasoning, or sample metadata. |
| A_THEN_V | separate audio, silent video, instruction | Audio payload first; silent video second. |
| V_THEN_A | silent video, separate audio, instruction | Silent video first; audio payload second. |

Joint arms use separate files; never pass the original audio-video container as the video input. The same shared instruction is last in every arm. Do not insert modality-named headings or source-side labels in the prompt. The candidate array and its order are identical across all four arms for a given sample. Output is only a JSON object with exactly one key, `label`, containing one candidate.

Candidate order is deterministic and balanced: sort sample IDs; rotate the sorted candidate list by rank modulo 16; reverse the base list on alternating 16-sample blocks. Save the resulting per-sample order and its hash in the manifest. This is a fixed schedule, not per-arm or per-run randomization.

## Eligibility and outcomes

`DualReadable` is determined only after the future single-modality outputs exist: a conflict record qualifies iff A_ONLY parses to `y_A` and V_ONLY parses to `y_V), after the frozen mechanical normalization. It is an evaluation-time field and remains unset in the static manifest. Primary arbitration population is conflict-pool � DualReadable; the full 1,000-conflict pool is the prespecified sensitivity population.

For each joint arm on conflict records, map a valid prediction to `SIDE_AUDIO` if it equals `y_A), `SIDE_VIDEO` if it equals `y_V), `OTHER` if it is a valid candidate matching neither, and `PARSE_FAIL` if output violates the strict parser contract. Equal-label controls are not side outcomes; report them separately as control-match / control-other / parse-fail.

Report each joint arm's four outcome counts over the eligible population. Define `AudioShare = SIDE_AUDIO / (SIDE_AUDIO + SIDE_VIDEO)` and `VideoShare = SIDE_VIDEO / (SIDE_AUDIO + SIDE_VIDEO)`. Also report OTHER and PARSE_FAIL rates using the entire eligible N, plus an all-eligible-N share sensitivity so parser failures and other labels cannot disappear silently. Never include consistent controls in either share denominator.

Compare order using paired sample-level differences between the two joint arms. For each conflict sample classify the pair as STABLE_AUDIO, STABLE_VIDEO, RECENCY_LIKE_FLIP (A_THEN_V chooses video and V_THEN_A chooses audio), PRIMACY_LIKE_FLIP (A_THEN_V chooses audio and V_THEN_A chooses video), or OTHER_OR_INVALID. These names denote order-associated patterns, not causal conclusions.

## Candidate interface rationale

All normalized source labels are single-token atomic labels; the union is finite (16), and no observed surface variant or compound-label construction requires special ontology handling. A global union avoids silently restricting one evidence side to the other side's subset while keeping a common, auditable candidate interface. This is a protocol choice, not a claim that source pseudo-labels are exhaustive or objectively correct.

## Leakage, dependence, and scope

The request payload allowlist is limited to the arm's media file(s), the candidate list, and the shared instruction. Keep labels and scoring metadata outside the model request. No subtitle, transcript, analysis, reasoning, original container metadata, or mapping fields enter prompts. Check the silent-video stream count before each V_ONLY/joint request.

The mapping has 1,500 unique archive members, but neither it nor the annotation schema supplies a speaker/person/source-video cluster identifier. Repeated-person or source-video dependence is therefore unknown. Treat each clip as the paired analysis unit; do not claim cluster-robust or population-level inference. Report descriptive results and explicitly mark any sample-level interval as not cluster-robust unless a trusted cluster key is obtained before evaluation.

This freeze covers dataset construction and analysis rules only. It authorizes no model loading, inference, API/judge calls, or scientific result computation.
