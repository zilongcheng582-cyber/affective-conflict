# B3 CORRECTED MEASUREMENT FREEZE V1

B3_PROTOCOL_STATUS = FROZEN_READY_FOR_REMOTE_EXECUTION
GPU_EXECUTION_PERFORMED = NO

## Scientific scope and measurement correction
MCR 909 scientific samples; LISTEN authoritative V4 1149 condition records / 768 exact scientific IDs; CA-MER 1500 controlled samples. Preserve every label, competitor, duplicate disposition, media byte identity, historical joint outcome and support/accounting definition. EmotionTalk Phase1/Phase2 remain immutable. Frozen population bytes and source hashes are in execution config and canonical/. Primary acquisition is 3177 scientific samples x two modalities = 6354 measurement identities, including shared evidence across distinct scientific IDs; forward deduplication is sequence-aware.

RAW/CANONICAL POPULATION IDENTITY = PASS
HISTORICAL B3 CANDIDATE SEQUENCE = MEASUREMENT-NONEQUIVALENT
CORRECTED B3 CANDIDATE SEQUENCE = SOURCE-EQUIVALENT FROZEN ASSIGNMENT
Historical target B3 did not preserve the source-equivalent candidate order in measurement/cache identity. Corrected candidate_sequence and candidate_sequence_id are expected measurement input changes, not canonical population changes. Historical 4961 evidence-level measurement identities remain bound for evidence and label comparison, rather than reused as corrected sample-level assignment.

## Candidate sequences and assignment
EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json SHA256 = b249c68e92fa16ec7c41f617baffd1d293db8807b01b9c0f5d8490d41b790750
Exactly 14 distinct complete permutations of the seven source labels. No order redesign. Use the locally regression-tested b3_protocol.assign_sequences unchanged: lexical sorted complete scientific IDs, sequence-major floor(N/14) quotas, append first N%14 sequence IDs, fresh random.Random(42).shuffle for each dataset, then zip. Source acquisition reproduction is verified against the frozen 1500 source assignments. One sequence per scientific sample; shared Audio/Text for MCR and LISTEN, Audio/Video for CA-MER. Assignment uses IDs only, never labels, predictions, correctness or performance. No temporary seed. Assignment SHA256 = 65069110f64ba2e518c411b784c8b9aa581d2dd8154d7dcb0e23111d436dde35. No secondary robustness panel is created or mixed into primary.

## Cache and scoring
Cache identity: dataset, modality, evidence SHA256, candidate_sequence_id, full candidate_sequence, prompt file/content hashes, immutable model/processor revisions and content manifests, scoring implementation SHA256. Same evidence plus same sequence allows reuse; different sequence prohibits reuse. Scientific sample IDs remain separate measurement identities. Raw source label is excluded from forward inputs/cache and is joined after scoring only.
Prompt SHA256 = ba6b71f080ea186a1494a54a0990a5740fc0aea69f008622618102f39efe55f8
Runner SHA256 = 151efafa88992aa2200a04fcd3093a016cc4d71ed9191c110034575539600c2a
Scoring implementation SHA256 = 3246b9ee0fea14948c0ac894181cf513322df7d969b87d6b8af92b17ce120e17
Per-function SHA256 and AST equivalence to authoritative historical source: B3_SCORING_FUNCTION_BINDING_V1.json. Historical tokenizer boundary, candidate continuation, model.thinker teacher forcing and token log_softmax unchanged. Primary p=softmax(mean token log probability); sum-token softmax remains sensitivity only. Normalized entropy=-sum(p*ln(p))/ln(7), zero terms omitted. Margin=largest p minus second-largest p. Source-label probability=p at exact raw source label iff in the source ontology, else null; no label remapping. No model.generate, no 14-order average or best-order selection.

## Immutable runtime
Qwen/Qwen2.5-Omni-7B model commit = ae9e1690543ffd5c0221dc27f79834d0294cba00
Processor commit = ae9e1690543ffd5c0221dc27f79834d0294cba00
Existing historical snapshot, local_files_only=True; no downloads, pull, upgrades or main/latest. Model manifest SHA256=8240abe64f8df444e7a4ebbcb636f51e6ef7e6833b62cf60adec0b2d14125a09; processor manifest SHA256=e471b7e2830ec4f53ee249b2a6707480858e357b30b4dc1616e718ef6fe18d41. All 17 inference-relevant model files (five indexed shards) and nine processor files are bound. Retained HF commit/ETag verification is recorded; no retrospective historical runtime checksum is claimed. Critical Python/dependency versions are frozen in B3_EXECUTION_CONFIG_V1.json. Model torch_dtype=auto, device_map=cuda, attn_implementation=flash_attention_2, use_audio_in_video=False, identical to retained historical B3 loading.

## Frozen source transfer model
B3_SOURCE_MODEL_BINDING_V1.json SHA256=642c2ed7b023aea8c6bd762891ff436f0f3eff6a95a58e56bf6f8c4b5d41dd20
Historical full-source M3a and M3b feature order, intercept_AT, pair_AV/pair_VT offsets, shared FIRST_IS_MODALITY1 coefficient, delta feature source means/SDs and all coefficients are copied exactly and cross-checked against summary/CSV/scaler provenance. Threshold=0.5. Source binding values:
```json
{
  "models": {
    "M3a": {
      "feature_order": [
        "intercept_AT",
        "pair_AV",
        "pair_VT",
        "delta_source_label_probability_per_SD",
        "delta_normalized_entropy_per_SD",
        "FIRST_IS_MODALITY1"
      ],
      "fit_identity": "HISTORICAL_FULL_SOURCE_FIT_NOT_REFITTED",
      "order_coefficient": "SHARED_FIRST_IS_MODALITY1",
      "parameter_values": {
        "FIRST_IS_MODALITY1": -0.8560767556273149,
        "delta_normalized_entropy_per_SD": -1.6501776858506354,
        "delta_source_label_probability_per_SD": -0.10768566922804151,
        "intercept_AT": 0.4957299419812353,
        "pair_AV": -0.3002756093311054,
        "pair_VT": -0.3184049210301859
      },
      "threshold": 0.5
    },
    "M3b": {
      "feature_order": [
        "intercept_AT",
        "pair_AV",
        "pair_VT",
        "delta_top1_top2_margin_per_SD",
        "delta_normalized_entropy_per_SD",
        "FIRST_IS_MODALITY1"
      ],
      "fit_identity": "HISTORICAL_FULL_SOURCE_FIT_NOT_REFITTED",
      "order_coefficient": "SHARED_FIRST_IS_MODALITY1",
      "parameter_values": {
        "FIRST_IS_MODALITY1": -0.8558655386186873,
        "delta_normalized_entropy_per_SD": -1.4451503200171585,
        "delta_top1_top2_margin_per_SD": 0.1202309037249221,
        "intercept_AT": 0.48850059879084057,
        "pair_AV": -0.25864252629703066,
        "pair_VT": -0.34583313013118355
      },
      "threshold": 0.5
    }
  },
  "scalers": {
    "normalized_entropy": {
      "mean": 0.010404252684427913,
      "sd": 0.24060545308601983
    },
    "path": "/root/autodl-tmp/affective-conflict/audit/EMOTIONTALK_CONTROLLED_V1/phase2_scientific_analysis_v1/EMOTIONTALK_PHASE2_SCIENTIFIC_ANALYSIS_V1_SUMMARY.json",
    "sha256": "e2d58be3cdfcf0089bf18edf6c080ad997c98405843b045cbbe94926dcaf1be9",
    "source_probability": {
      "mean": -0.02103924985500564,
      "sd": 0.25324466896447845
    },
    "top1_top2_margin": {
      "mean": -0.020377329894437538,
      "sd": 0.3055869765131503
    }
  },
  "threshold": 0.5
}
```
No source refit, target scaler/fit, threshold tuning, calibration or feature selection. Corrected publication CV does not replace historical full-source transfer coefficients.

## Prespecified evaluation and accounting
B3_EVALUATION_PLAN_V1.json freezes exact joint record identities and conflict/support memberships before GPU. Historical log loss primary; AUROC, balanced accuracy at threshold=0.5 and Brier secondary. Report coverage, N evaluated, N prespecified, feature failures, OTHER/PARSE_FAIL, technical missing, same-label exclusions and ontology support separately. Coverage uses the frozen eligible conflict denominator, never a performance-dependent subset; additionally report historical feature-finite eligible denominator for comparability. Future binary analysis includes only resolved SIDE_A versus SIDE_T/SIDE_V with finite corrected features. No metric is calculated now. MCR historical primary and margin sensitivity roles unchanged; LISTEN sourceprob primary structurally unsupported, margin sensitivity only; CA-MER full-population primary undefined, sourceprob restricted to historical ontology-supported supplementary membership (1434 planned joint slots), margin sensitivity unchanged. Do not expand support or reinterpret the historical shadowed target_dataset column; use the authoritative consumer INPUTS dataset mapping. Binding source rows preserve exact canonical outcomes and accounting.
Outcome ruling remains unassigned until separate authorized post-GPU evaluation: RESOLVED_BOUNDED_IMPLEMENTATION_ISSUE (numeric changes, scientific direction unchanged), SURVIVES_WITH_CORRECTION (material numeric changes, MCR strongest / CA-MER weak-partial / LISTEN unsupported-weak structure preserved), or SCIENTIFIC_IMPACT_ESCALATION (material overturn). Never assume a class before results.

## Output and execution gates
Every measurement retains dataset/sample_id/stable ID/modality, sequence ID/full sequence, prompt/evidence hashes and locator, aligned seven-label probability vector, normalized entropy, margin and supported raw-label probability, model/processor commit/content hashes, scorer hash and execution manifest SHA256. Mean/sum log scores and sum-score sensitivity probabilities are retained, allowing CPU feature recomputation. Forwards retain full cache identity and served measurement IDs; sourceprob is absent until measurement join. Technical failures have explicit status and identity and never count as successful resumable cache. B3_OUTPUT_SCHEMA_V1.json defines required fields.
Runtime manifest SHA256 is appended after freeze, outside manifest contents to avoid circular hashes. Exact payload, roles, sizes and SHA256 are in EXECUTION_PACKAGE_MANIFEST.json; self-exclusions are explicit and the checksum index binds the manifest. Verification rejects any package/runner/protocol/population/assignment/model/processor/dependency/media mismatch before model import. Default runner only prints help; --verify is CPU-only, execution requires a separate future authorization plus --execute-authorized-b3 and output outside immutable historical/package directories.

## Reproducibility boundary and prohibited operations
EmotionTalk raw→canonical = PASS
MCR raw→canonical = PASS
LISTEN raw→canonical = PASS
CA-MER raw→canonical = PASS
CLEAN_CANONICAL_DATA_LAYER_READY = YES
EmotionTalk E7 = MODEL_DERIVED_INFORMATION_NOT_AVAILABLE_FROM_RAW_BY_DESIGN, not a raw-data reconstruction defect. MCR candidate_sequence / candidate_sequence_id changes are corrected B3 measurement inputs, not canonical population changes. Raw reconstruction is closed. Historical source and target assets remain unchanged. No GPU inference, B3 scoring on actual data, transfer evaluation, AUROC/accuracy computation, target fitting, further LISTEN/CA-MER reconstruction, new experiments or second model is performed in this freeze task. All CPU/static tests run twice. No weights, raw dataset/media or full historical repository is included.
