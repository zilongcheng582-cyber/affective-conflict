# EmotionTalk Phase 1 Measurement Gate V1.2

**Status: PASS**

This is a pre-full-run measurement and methods gate. It does not report scientific accuracy, readability rate, modality trends, or EmotionTalk scientific outcomes. No 4,500-generation Phase 1 run was started.

## Static freeze

- Candidate order assignment: randomized over the already selected panel with seed 42; label-independent by construction. Position balance check: True.
- Ordered T/A/V tuple support: 1.000000 of the 19,250-row population; unsupported tuple count: 0.
- Selected-panel annotation metadata: 6000 modality rows with official A–E votes and Confidence_degree recorded descriptively.
- Readability stays exactly the frozen V1 rule: parsed greedy unimodal label equals the corresponding source-side label. Scoring does not modify it.

## Technical gate

- Generations/parser: 18/18 successful records out of 18.
- Candidate measurement scores: 18/18 complete using exact-string teacher forcing. Multi-token labels are scored by summed and mean token log probabilities; primary probabilities use softmax of mean token log probability, with softmax of summed scores as length-sensitive sensitivity.
- Candidate score measurements: normalized entropy, top-1/top-2 and margin, source-label probability, and greedy/parser versus score argmax agreement are recorded per technical-gate row only.
- V1.1 repeat: 18/18 parsed labels match; raw outputs exact for 18, whitespace-only difference for 0.
- V1.1 runner and prior results hashes unchanged: True.

## Scientific status

- `EMOTIONTALK_SCIENCE_STATUS = NOT_RUN`
- `SCIENTIFIC_METRICS_COMPUTED = FALSE`
- `FULL_PHASE1_STARTED = FALSE`
- `NEXT_STEP = EMOTIONTALK_PHASE1_COMPETENCE_FULL_RUN_V1_2`
