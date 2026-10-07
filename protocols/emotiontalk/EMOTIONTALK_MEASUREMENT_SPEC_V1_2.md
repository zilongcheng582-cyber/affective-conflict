# EmotionTalk Pre-Full-Run Measurement & Inference Freeze V1.2

Frozen before the 4,500-generation Phase 1. This amendment adds uncertainty measurement and fixes the inference analysis rules. It does not change the panel, prompt, parser, candidate sequence assignment, media, generation configuration, or readability. No full Phase 1 was launched.

## Measurement

The V1.1 greedy generation and parser remain the only source of `Readable_T/A/V`. After each unchanged generation and parse, V1.2 scores the exact seven canonical source strings by teacher forcing because the actual assistant-prefix tokenization is multi-token for several labels. For each label retain token IDs/count, summed and mean token log probability. The primary score probability is softmax of mean token log probability; softmax of summed log probability is a length-sensitive sensitivity. Report normalized entropy, top two, margin, source-label probability, and greedy/parser-label versus score-argmax agreement. These values never alter predictions, readability, selection, or scientific outcomes.

## Annotation uncertainty

For the selected panel, retain official A-E categorical votes and `Confidence_degree` from each modality JSON, with vote entropy, source-label agreement, majority share, and confidence summaries. Metadata is descriptive only. Multimodal annotation metadata, if present, is also descriptive and cannot enter primary analysis or transfer.

## Candidate-order audit

The official frozen builder uses a 14-sequence schedule (seven cyclic and seven reversed cyclic sequences), repeats sequence slots 107 times plus one extra for CS01 and CS02, shuffles the schedule with seed 42, and assigns after selecting/sorting the panel IDs. The assignment is global-randomized after selection and does not use labels. The supplied cross-tab CSV reports candidate label by position against source labels, tri-modal pattern, and pairwise relation. Overall candidate-position balance must differ by at most one. Tables are diagnostic; no reselection or sequence change is allowed.

## Balanced panel and natural-distribution sensitivity

Primary estimates target the frozen equal-quota panel (300 per source T/A/V pattern). The script also counts full-population and panel ordered label tuples. A natural-distribution post-stratified sensitivity uses population tuple count divided by panel tuple count only for supported tuples. Unsupported population tuples remain explicitly unsupported; do not impute or claim full-population identification when any are missing.

## Frozen pairwise and compositionality rules

Pairwise primary population is pairwise source-label conflict AND frozen DualReadable, paired by utterance across reciprocal orders. Consistent AND DualReadable records are controls. Report two-side outcome, coverage, OTHER, PARSE_FAIL, and paired order-switch classes. A source-consistent tri-modal edge is SAME_LABEL, not a directed winner edge. For conflict edges, OTHER/PARSE_FAIL is UNRESOLVED. TWO_VS_ONE prediction requires the two cross-group conflict edges to agree on a shared-versus-minority winner; the shared/shared pair is SAME_LABEL. ALL_DIFFERENT prediction requires all three conflict edges to form a stable transitive total order with a unique top label. Order-conditioned rules use only pair outputs matching the relevant relative evidence order. Cycles, order-sensitive conflicts, disagreement, and unresolved edges yield UNRESOLVED. No rule changes after tri-modal output.

Any later secondary learned-composition analysis must use speaker-grouped cross-fitting; an evaluation fold's tri-modal outputs cannot be used for fitting or tuning.

## Zero-refit transfer

Predeclared mappings are EmotionTalk A-T to LISTEN A-T and EmotionTalk A-V to CA-MER A-V. EmotionTalk V-T has no declared target; EmoMM is held out for a later mapping. Portable features are delta entropy, delta top-1/top-2 margin, delta source-label probability, presentation-order indicator, and pair identity; raw emotion identity is excluded. Fit all scaling on source only. Target is held-out zero-refit only. Log loss is primary; balanced accuracy, AUROC, Brier, and calibration are secondary. Compare with a constant source modality-preference baseline. Claims are conditional on DualReadable.

## Evidence language and compute

Use audio-channel (A), silent visual-channel (V), and textual (T) evidence. Do not claim pure prosodic/acoustic or face-only emotion. Phase 1 remains 4,500 fixed generations; later pairwise and tri-modal counts remain conditional on measured readability. OOM is technical missingness; no automatic video downgrade, altered preprocessing retry, or model-result-based skipping.
