# MCR Controlled Arbitration Analysis Specification V2

Status: frozen as a protocol artifact after CPU static validation and the bounded implementation gate. No scientific 3636-record run is performed by this handoff.

## Scope and denominator

The denominator is the frozen 909-record MCR SER arbitration pool represented by the V2 manifest. Each original sample has exactly four model calls: `A_ONLY`, `T_ONLY`, `A_THEN_T`, and `T_THEN_A`, for 3,636 records. The two joint calls for one sample are an order pair, not two IID observations.

The canonical ontology is unchanged: `sad`, `happy`, `fearful`, `angry`, `surprised`, `disgusted`, `neutral`. The parser is the frozen `mcr_ser_parser_v1.py`; a response is usable only when the parser returns `PARSE_OK` and exactly one canonical label.

## Evidence and prompt isolation

The prompt has no `Text evidence:` or `Audio evidence:` headings. Model-visible content is built as structured user content in this exact order:

| Arm | Structured content order |
|---|---|
| `A_ONLY` | audio, classification instruction + candidates |
| `T_ONLY` | text evidence, classification instruction + candidates |
| `A_THEN_T` | audio, text evidence, classification instruction + candidates |
| `T_THEN_A` | text evidence, audio, classification instruction + candidates |

The classification instruction is always the final content item. It requests exactly one canonical class, contains no chain-of-thought request, and contains none of the forbidden framing terms: conflict, adversarial, misleading, reliability, ground truth, trust, prefer, priority, bias, audio is correct, or text is correct. Gold labels, source indices, sample identifiers, filenames, sequence identifiers, and arm names are never passed to the model as prompt content.

## Candidate-order control

Candidate sequence IDs are `C0` through `C6` and `R0` through `R6`. Let `B = [sad, happy, fearful, angry, surprised, disgusted, neutral]`; `Ck` is the left rotation of B by k and `Rk` is its reverse. For each unequal directional stratum `(y_audio, y_text)`, records are sorted by `SHA256(SALT|SAMPLE|sample_id)`. A stratum hash sets `k0` and a fixed reverse-first bit; ranks 0/1, 2/3, ... receive mirror pairs `Ck/Rk` or `Rk/Ck`, with `k = (k0 + pair_index) mod 7`. The final odd record, if present, is the only permitted one-record imbalance. No RNG, original source order, or model output participates in assignment. The same sequence is used for all four arms of one sample.

For every unequal directional stratum, report `audio_before_text`, `text_before_audio`, and ties, and require `abs(audio_before_text - text_before_audio) <= 1`. Report candidate sequence IDs and candidate positions for every original sample.

## Readability and primary estimands

For each original sample:

* `readable_audio = A_ONLY PARSE_OK` with a parsed canonical label.
* `readable_text = T_ONLY PARSE_OK` with a parsed canonical label.
* `dual_readable = readable_audio AND readable_text`.

The primary estimand is computed on the Dual-Readable subset. The full-pool sensitivity analysis is reported separately and never silently substitutes for the primary denominator. Both tables must report N and coverage against the 909-sample denominator, plus `y_audio`, `y_text`, dialogue-cluster counts, candidate sequence IDs, candidate positions, and relative precedence.

## Joint-arm classification and order averaging

For each usable joint arm, compare the parsed label with the original sample labels:

* `SIDE_AUDIO`: parsed label equals `y_audio` and not `y_text`;
* `SIDE_TEXT`: parsed label equals `y_text` and not `y_audio`;
* `OTHER`: a usable canonical label matching neither side (including the same-label case handled by the predeclared tie rule);
* `PARSE_FAIL`: parser did not return one usable canonical label.

If `y_audio == y_text`, a usable matching label is a `SAME_LABEL` diagnostic and is not counted as evidence for either side. Joint order-averaged shares are calculated over original samples using the pair of `A_THEN_T` and `T_THEN_A` calls, never by treating the two calls as 1,818 independent samples. Require both joint arms to be present and usable before classifying a sample as `OS_RESOLVED`; `OS_RESOLVED` is true only when both joint calls resolve to a side (`SIDE_AUDIO` or `SIDE_TEXT`) or to the predeclared same-label diagnostic.

## Stability categories

Among samples with both joint arms usable, assign exactly one category:

* `STABLE_AUDIO`: both orders are `SIDE_AUDIO`;
* `STABLE_TEXT`: both orders are `SIDE_TEXT`;
* `RECENCY_FLIP`: `A_THEN_T` is `SIDE_TEXT` and `T_THEN_A` is `SIDE_AUDIO`;
* `PRIMACY_FLIP`: `A_THEN_T` is `SIDE_AUDIO` and `T_THEN_A` is `SIDE_TEXT`;
* `OTHER_OR_INVALID`: anything else, including a missing/unusable member or a non-side result.

Do not infer a psychological mechanism from these labels. They are protocol-defined response-pattern categories.

## Dependence and bootstrap

Dialogue IDs are recovered from the frozen audio paths. The deterministic missing-ID rule is frozen before any results: a missing or unparseable dialogue ID becomes a singleton cluster named `UNRESOLVED_<first 16 hex of SHA256(sample_id|source_index)>` and is never merged with another record. The primary uncertainty procedure is dialogue-cluster bootstrap, resampling complete dialogue clusters and preserving all four arms and the two-member joint order pair for every retained original sample. Report the number of clusters, singleton clusters, and the exact resampling seed/algorithm in any future results artifact.

## Required diagnostics and stopping rule

Every future scientific result must include: Dual-Readable N and coverage; full-pool sensitivity; coverage by `y_audio` and `y_text`; directional-pair counts; dialogue-cluster counts; candidate sequence IDs; candidate positions; relative precedence; joint-arm parse statuses; order-averaged shares; stability categories; and the predeclared bootstrap details. The protocol is frozen only after the static audit passes and the bounded 12-generation implementation gate passes. The bounded gate is technical only and must not be reported as a scientific result.
