# 04_TRANSFER_FROZEN_EVIDENCE_REGISTER

POST_HOC_EXPLORATORY — CPU-only; frozen source models, thresholds, scalers, predictions and raw archives unchanged.

## Frozen chain and version resolution

Authoritative release checkout: `/root/autodl-tmp/affective-conflict-eri1/repo`, binding commit `34aa1b0340d906e5d625db7cb4a3def9199fa06e`. Every locked release asset was checked against `git show COMMIT:path`, not merely the working file name. The historical root has no Git runtime identity; original report/scaler/consumer hashes were separately matched to the binding. No fetch/reset/checkout or branch mutation was performed.

Source chain: Phase2 attempt002 2132 records →696 conflict order records→663 resolved source-fit records, 274 utterances (AT116/61, AV284/146, VT263/139 rows/utterances). The frozen pooled M3a/M3b use pair intercepts and shared strength/entropy/order slopes. They are not separately fitted AT or AV models. Later R1 publication cross-validation and posthoc entropy-only fits do not replace these historical transfer parameters. Source fitting/scaling used663 order rows; inference uncertainties cluster the underlying source item. R1 within-source prediction is not an external-transfer validation.

Original `protocols/emotiontalk/CROSS_REGIME_TRANSFER_SPEC_V1.*` names LISTEN and CA-MER; MCR enters the later zero-refit spec and remains a later-added exploratory label-assertion regime. The original zero-refit spec's displayed scaler values are superseded by the executed fit-time scaler provenance resolution. Replay uses the exact frozen binding and fit-time 663-row population, never its broader diagnostic population scalers. The model-freeze prose describes pair-specific order but the authoritative executed coefficient/consumer binding uses a shared order coefficient; this previously resolved distinction is explicitly retained.

Corrected measurement protocol, sequence assignment, evaluation plan and technical Amendment001 are registered below. They identify6354 scientific measurements/5515 acquired forwards. No16class target probabilities are present. The corrected B3 seven-class teacher-forced scores are distinct from discrete task generation and from historical stale feature columns. Both raw corrected JSONL copies match SHA256 `0ad7785530a52923dabdf3ec6b3c5afe27e68d87be61e1b5f4465fde79fad450`.

POST_AUDIT closure provides9219 row predictions and source-fixed comparisons with paired cluster percentile CIs (seed20261008,2000 replicates). Its scientific ruling is `REQUIRES_INTERPRETATION`: an executable binary acceptance rule was not predeclared. Historical `SURVIVES_WITH_CORRECTION` author interpretation is not recast as a confirmatory decision. This analysis reports metric-specific conclusions against lawful M0.

## Frozen coefficients, scalers and baselines

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
  "baselines": {
    "M0": {
      "analysis_origin": "POST_AUDIT_REANALYSIS",
      "fit_identity": "HISTORICAL_FROZEN_COEFFICIENTS_NOT_REFITTED",
      "fit_population": "EMOTIONTALK_SOURCE_RESOLVED_CONFLICT_663",
      "parameters": {
        "intercept_AT": -0.034486176071169515,
        "pair_AV": -0.20610428884676107,
        "pair_VT": 0.04209077545638878
      },
      "role": "EARLIER_DECLARED_SOURCE_FIXED_CONSTANT_PREFERENCE",
      "source_records_sha256": "8fb93aadd79eac9597677bd3409666ec2a31311762e0c6850673fb50f4129a13",
      "target_fit": false,
      "threshold": 0.5
    },
    "M0_PLUS_ORDER": {
      "algorithm": "Historical unpenalized Newton/IRLS design [AT intercept, AV/VT offsets, FIRST_IS_MODALITY1]",
      "analysis_origin": "POST_AUDIT_REANALYSIS",
      "fit_identity": "POST_AUDIT_SOURCE_ONLY_FIT",
      "fit_population": "EMOTIONTALK_SOURCE_RESOLVED_CONFLICT_663",
      "iterations": 4,
      "parameters": {
        "FIRST_IS_MODALITY1": -0.6220566258185027,
        "intercept_AT": 0.2648040212822552,
        "pair_AV": -0.20464884024674596,
        "pair_VT": 0.040794790587748125
      },
      "role": "POST_AUDIT_DIAGNOSTIC_SOURCE_ONLY_BASELINE",
      "source_records_sha256": "8fb93aadd79eac9597677bd3409666ec2a31311762e0c6850673fb50f4129a13",
      "target_fit": false,
      "threshold": 0.5
    }
  }
}
```

M0 is the earlier frozen source preference. M0+ORDER is the existing POST_AUDIT source-only fit on663 source records; its coefficients are read unchanged, not refitted here. Target-prevalence oracle constants are new diagnostics and are never lawful zero-refit competitors. Threshold0.5 and all inclusion rules remain fixed.

## Exact evidence register

| path | sha256 | records | git_blob_check |
| --- | --- | --- | --- |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/08_M0_M3_model_results.csv | bd576a092eda349cccc34965468fd6d003de1da61118eef337ab6cd94e701426 | 33 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/B3_MODEL_PROCESSOR_IDENTITY.json | f911d829077ec32bc0633f97ab52010c85ecc5d6fea4912cc328af71a38888f7 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/B3_SOURCE_MODEL_BINDING_ORIGINAL.json | 2774b1dab0e93912a3795ca3d1994c087213a01f04b9e4280981cd4430e2a887 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/EMOTIONTALK_PHASE2_PAIRWISE_MODEL_FREEZE_V1.json | 2f5e5e639ce22d79452aa54ca599fd0e14bc525cf874042b04065edadeed5019 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/EMOTIONTALK_PHASE2_SCALER_PROVENANCE_RESOLUTION_V1.json | cd90c4238cb59096418d57eedc3da83f25e98be0ec4870e9662e8ce289410bb4 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/EMOTIONTALK_PHASE2_SCIENTIFIC_ANALYSIS_V1_SUMMARY.json | e2d58be3cdfcf0089bf18edf6c080ad997c98405843b045cbbe94926dcaf1be9 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/HF_COMMIT_CONTENT_VERIFICATION.json | 8bbb419343bbf7cacf6d3444f5f382b229bee75db1ebd8ceee578215b9af874e | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/HF_LOCAL_METADATA_IDENTITY.json | dd17b8464534b4d9542f94daa0d790098db42c4745b53cf3c4a46ec7f0275451 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/HISTORICAL_B3_FORWARD_IDENTITY.csv | 1834d4929aa6dab46c39dc7a455ebae7b64e319c10081d64282ee85c2ec2f5f1 | 4959 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/HISTORICAL_B3_MEASUREMENT_IDENTITY.csv | a93f3bb76dbc02f65c168fca740147f466aad902b20b8a66a4cb4cf9e5740e1b | 4961 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/PROCESSOR_LOADING_PROVENANCE.json | 54063c8a8494f91cf3bf4586df4f1d2d3d333bdb1954b2b3e04146ca043791bd | 72 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/REPRODUCIBILITY_BOUNDARY_STATEMENT_V1.md | 771bf1fd1243e2bc5db2a2e31af087bac3ecd0e1f7ac388a7e6ca4df4158450a | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/binding.json | 642c2ed7b023aea8c6bd762891ff436f0f3eff6a95a58e56bf6f8c4b5d41dd20 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/publication_cv_input_provenance.json | 20668a2def6787c8e5069304bbec6c89058e2aa9d2c91df2adb6540714c7b613 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/frozen/source_model/publication_cv_records.json | 8fb93aadd79eac9597677bd3409666ec2a31311762e0c6850673fb50f4129a13 | 663 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/LISTEN_CONDITION_DIAGNOSTICS.csv | 9a7e88bfb6e1e966339d779d6cb6430b73f064fd60885a369f149fd9a0380e27 | 12 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/LISTEN_JOINT_ONLY_REPORT.csv | 00f02c5af41e538544e144df6a8fd5a11f5880675376b3ec4f8516e13099f3b8 | 3 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/MCR_CONTENT_DUPLICATE_AUDIT_V1.csv | 692250f603e49eb46690f4a8f9e2e1e5b2ba8f3896a6933398b43dbf8caccf6a | 7 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/MCR_CONTENT_DUPLICATE_SENSITIVITY_V1.csv | eb97118a2d5b6dd986a49a662607fb4be8620f824aab8abccc3ce4e8bc057f0b | 4 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/PHASE2_RECONSTRUCTED_SOURCE_RECORDS_V1.csv | 6ae60be040e169cb49f7456a1ab3f1e6599d881a5a6dd081a84648e0cb0146af | 663 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/PHASE3_ROW_LEVEL_VERIFICATION_V1.csv | 4ce59f29e4cdab91054a21e49af676d5e50813f7fb08d06a9cb803c5906cf17e | 402 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/POST_AUDIT_CPU_REPLAY_V1.json | ac372573f817ede3e7996d551287b69c4c7410def85b922279906504b00961e2 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/SOURCE_BASELINE_BINDING_V1.json | 98f21865e84da6031a80881db867306688d114d867de445cdcdbd8a73148b945 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/ZERO_REFIT_BASELINE_COMPARISON_V1.csv | 526014bb2c470e3a181b354b000cd9802751fdd28cf9280d8bcc2fb5c5df11fc | 24 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_DATASET_METRICS_V1.csv | b6f0892cb2ec799cdeaf5413ce31bad554ca3dfa7d7713a080b5e3c806788b6b | 7 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_MEASUREMENT_CLOSEOUT_V1.json | 00af7cee140aa96438998d2533eba54283d4b8bc60614263b1cf0490696796db | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv | c497629d50291005f2bc7936c23e154c4f194dad22c65e5ad1714e54d79c7e9a | 9219 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/corrected_replay/B3_FINAL_HASHES_V1.txt | 51f1835ee8a0f7b1b8202b50c588c96e15a3c497dcb3ee21af941c3900060d51 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/corrected_replay/B3_OLD_VS_CORRECTED_COMPARISON_V1.csv | e07cdd2d2a749e1fe39e57c587e6a15e47fb3c85e1e135f307a5b158c4fb0423 | 28 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/corrected_replay/B3_ZERO_REFIT_FINAL_EVALUATION_V1.json | d8bd54b07c277f04292a6ed69544ba4748acdaf9213af6dc584aae080121dced | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/corrected_replay/B3_ZERO_REFIT_FINAL_EVALUATION_V1.md | 04c0ddbf442f2e457cd79e502cb48a5f4814e2cee860dd4fad7f818cb9730a5e | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/closure_v1/corrected_replay/B3_ZERO_REFIT_PROVENANCE_V1.json | c9abde277e77d4f114c9e3e05c4a66c101d29f1df06568f8808f0956ad0e4c24 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R1_MODEL_COMPARISON.csv | 4919a4eade576c889a95ce977bc1aed0a0943d94b5d1217197a5b815ed1e10ba | 176 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R1_OUT_OF_FOLD_PREDICTIONS.csv | e3ad37422ef40975670f01c7e1c96d2d0159432d67c14559723e3ed7f71263a8 | 663 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R1_PAIRED_UNCERTAINTY.csv | fcef1081ec83a0575e863d1a46de9b1ec8c641cff055727467b15bacfd0d3feb | 176 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R1_PAIR_HETEROGENEITY.csv | 54ad053d9c1ef75cd38e41279cf10c8af627414115ca35c2d31890629fcb298e | 97 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R1_RUN_METADATA.json | 8e99a9016e1aada589bbc7d373b9aa45591ce636cc2572ce1e78031b16501b8b | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R1_SOURCE_STRUCTURE_REPORT.md | 80f803b4e0faf1abb1280a592b92ae00d5ed35a2a3a67950039a7ded9394c904 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R2_BASELINE_COMPARISON.csv | 4157c63a1b04d3789a7e88a8fe18b2a5740b46a91bafb782e901655204df4715 | 15 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R2_CLUSTERED_UNCERTAINTY.csv | ab469263e1ec0d1a789cb4863b0535129ba08a1ac7c383f8a272727ed4087fc4 | 47 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R2_COMPOSITIONALITY_REPORT.md | 6288bed1bc3929142772be3eb8ec3bd20c8d03572d99636d1a1dfec7daa74a96 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R2_PAIRWISE_VS_BASELINES.csv | 0209837b02a0a8e7cfe50d2821c64d81fab0ed46e8accbc248c333cde9501c2f | 402 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R2_PER_UTTERANCE.csv | 472f7022265d5cd1aff8f2f9beec0f1e158fb8bf86a18f6fc9c1d92ed36d5bab | 67 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R2_RUN_METADATA.json | e7df41486d420db146203509b8d32aff7b3590b8a24baf5eb9e2041b861eb542 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R2_SHUFFLE_DISTRIBUTION.csv | 3cc6a3b667e16bc6fbc5f2288c863e7e10786cb0a3be69d7e083b4398b37f70a | 2000 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R3_LISTEN_BEHAVIOR_REPORT.md | 54adc57f4a6f8d4d71f991bb5500147c136806a66780cc1e7637a43c5d1be108 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R3_MATCHED_CONDITION_TRANSITIONS.csv | ffb1b6f474a0acddcd36d0fb6ca37b5b6a374eec6cc3cc8ec8719a91f198a8eb | 80 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R3_OTHER_ASSOCIATIONS.csv | 2f4a7339c763cc2d01d53e02ac3719d3723642f74631f29cbf8172adcfdc0b6e | 155 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R3_OUTCOME_ACCOUNTING.csv | e58ccc254a47084f37344e580ad743dc0d4fcf0f3bd2e32d3b42f59f3040587c | 7 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/R3_RUN_METADATA.json | b1107e3e4d13649db63c64970bbd28bf7f850733507c4e2bd2957ea35a006ccb | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/SCIENTIFIC_ANALYSIS_V1_FINAL_REPORT.md | 593da3df9abcd966b2af9d4eab9fcac47d64cfaf696399817e35e65e1ef4508c | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/results/post_audit/scientific_analysis_v1/STAGE_A_ACCEPTANCE_V1.md | fe41c025311e7c8b5cfe555f5ab69f92b4de6eb60242937df1915f17fe9c4999 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/CROSS_REGIME_TRANSFER_SPEC_V1.json | 73495ba69b346db05323179683e16cf7abdf88be86d26e9224d79050c50e0714 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/CROSS_REGIME_TRANSFER_SPEC_V1.md | 17a1e2fb8d8265289ec82704756c9844e98a47157def74b8b1fd3252c98866b9 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_CANDIDATE_ORDER_AUDIT_V1.csv | 6f886a747835d5326180f89ae3f0b0650eb20a8134653d16ce3d6eab84528d4f | 5047 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json | b249c68e92fa16ec7c41f617baffd1d293db8807b01b9c0f5d8490d41b790750 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_COMPOSITIONALITY_SPEC_V1_1.json | 91de88c803eb91280f4d25852ffb4fe7e70f89ea1c5abdbacef863f2919ef2dc | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_COMPOSITIONALITY_SPEC_V1_1.md | 6afd7395345eda4c3be8dc9e3b295561d9a2ef9e628cb7b85ef330845cf4eceb | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_CONTROLLED_PROTOCOL_V1.json | 3c66b0a379fac6ce7aef8e27d589b9901825ec3c8db54dcda3e3b16772e60837 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_CONTROLLED_PROTOCOL_V1.md | 949c51d55144e7b0df43dc59b0e696512d294ba7c06db3879f758a978eeae2d3 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_MEASUREMENT_SPEC_V1_2.json | e65eb6aa3fc1f7aafef4c7390dcf78443fa9dc8f7791e76af311e7734f117c18 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_MEASUREMENT_SPEC_V1_2.md | 03ade2a4a6763f0736cb3a54161c3cc1c27ecddacdb06be2af199e7659afecc6 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_MEDIA_FREEZE_V1.json | 02e8127e80e87a529ac713a006d04971b63d13b943e103efcf1d24f305725883 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_MEDIA_FREEZE_V1_PROVENANCE.json | 2d0ad33483ba955c9c13d4c699c2ee1e387b07411f09ba2b767279c840a7f6ad | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_PHASE1_COMPETENCE_FULL_V1_2.json | 4890dc0b1c96cb7cc638ce8ed3483548d0aaf02c2de3b929e03b06f8a6be7b85 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2.json | 5823abd732a60d5f0f9ed90ad6ef2e53463e4d159758ca12e7cdf94ec0e60d7a | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2.md | a7ed5050fa7c48c9921c580d088706bb52cf119f8daed8688504bc98ffcab5ab | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2_PROVENANCE.json | fdd8b75a8803ad52f6a72b15e4799066d27afe29a6109fa8524b58962d478ed1 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_PHASE1_MEASUREMENT_GATE_V1_2_SHA256SUMS.txt | e8e550a9587fd891fd94cac6cfef5210befa4e203accbe1d01352b5472f469fe | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_PHASE3_COMPOSITION_RULE_FREEZE_V1.json | fe1623e42402d32f2ebebda8c5d8b1feaad69a852a0391e7ad2c2030dfd4d3b6 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_PHASE3_FULL_V1_FREEZE.json | e2e9e0dbf54d91c1471bee473439a7e6970bc3890598562c39438f4cc1ccf783 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_POPULATION_TUPLE_SUPPORT_V1_2.csv | c78c0ac57866a663d05895a83649de354826d8bf21140b13101a167d81362662 | 316 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_POPULATION_WEIGHTING_SPEC_V1.json | 423c872dd9052f0d099db45d8564e96a565d0bb3dcd7bd2e1a0b9ee6fd105387 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_PREAUDIT_STATIC_V1_2.json | 9654727cd6164f52e5d1e4efacf3dc46c5337cf175a4c50d5626ed4f50096765 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/protocols/emotiontalk/EMOTIONTALK_V1_1_V1_2_GATE_REPEAT_COMPARISON_V1_2.csv | 5d5f01c22993ce04a0ba093f27ed62b4ba1982d57f23b653cdb83582b7dfd1a9 | 18 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/docs/SCIENTIFIC_CLAIM_STATUS_V1.md | e62da9dfb5913395ea84a7ac50cda739193cad4fb53189a1244cd8e9ea7924fb | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/evidence/provenance/CROSS_REGIME_ZERO_REFIT_SPEC_V1.json | aa603f9258bde8c0ef7dd38fd69178876e2d8aa5ea748939a2a0589545847178 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/analyses/post_audit/replay.py | 0f5088d84a129171b5b04bba1fe8925ce533a6d265887640ab3ae9aecba84f39 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/src/cross_regime/zero_refit/metrics.py | 374618ae7d3045adf712f4c798f4fd372f335e89a767115aaaff2fe2eba1ef1c | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/src/cross_regime/zero_refit/evaluate.py | bccd20d5e6bbac0969aa333096f9c33b96279463614419ab73beb2e4a5f54c23 | not row data | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/RELEASE_MANIFEST_V1.json | c249cc1e8825fbb86ef4c5c598d8c6664ca68080d59b2992c7f02feb3deea9c8 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/POST_AUDIT_REPAIR_MANIFEST_V1.json | 570f7e84f34f4eb32f8131ffbc76d293d12c4db3676010dacd190c33c273fad3 | JSON object | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/manifests/mcr/frozen_joint_outcomes.csv | 789261e4fce394e6466bb67c0e55a3e0dce49c3d8b37ed76308c075660329266 | 1818 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/manifests/listen/frozen_joint_outcomes.csv | cc145efa4b187deab567b547ab8b71b6456da6484820d96ec49810742b77aced | 1149 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/manifests/camer/frozen_joint_outcomes.csv | 57ed776d5009ba50b3e07bcb7b78c4323a66b08e960e65bee20ecbfef82abd13 | 3000 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict-eri1/repo/evidence/b3/B3_MEASUREMENTS_V1.jsonl | 0ad7785530a52923dabdf3ec6b3c5afe27e68d87be61e1b5f4465fde79fad450 | 6354 | MATCH_BINDING_COMMIT |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/outputs/B3_MEASUREMENTS_V1.jsonl | 0ad7785530a52923dabdf3ec6b3c5afe27e68d87be61e1b5f4465fde79fad450 | 6354 | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict-recovered-science-v1/03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv | 9f911d474023821af25a9fb651192ac1aa14a1b7c0813df5dc9c4100e2b4aea7 | 381 | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict-recovered-science-v1/intermediate/CAMER_ITEM_ELIGIBILITY_IDENTITY.csv | 28b5d70b996633adf00a476be926f31c976112f46d975a52595dd3ab0abe79dc | 1500 | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict-recovered-science-v1/intermediate/MCR_NATIVE_CONTROLLED_PER_ITEM_JOIN.csv | 77f7525fec4a43ab028a082b46223df3ce38ccc389837ef6e423e95679c35d16 | 909 | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict-recovered-science-v1/numeric/MCR_RESULTS.json | 0d2d729391f49359047223f14c534c8417525e7f5d2a83dd0e1ae4367a1925bd | JSON object | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict-recovered-science-v1/numeric/CAMER_RESULTS.json | 675de252be8f61e24af33b9d3fb52eddebd4badd52a491844a61e33e7477f49a | JSON object | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict-recovered-science-v1/numeric/LISTEN_RESULTS.json | f15872542487e6a96e4c6dbf2954034cc9fc796df2220c50c6da254127df59b6 | JSON object | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict/docs/PROJECT_STATE.md | fe0d5df5a1d03f3661b9cbb5b5ed7f22b7b3c81628c2dede809e28692429de38 | not row data | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict/docs/FILE_MAP.md | 0f23c77b857b125776ed2b62b62474acb1fb9799fb7dd715a15b8faab9a10b6d | not row data | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict/docs/DECISIONS.md | 269628105fa1228eea57f7460620831e6093a4b9f3db0f91ad8e5e10fa319792 | not row data | NOT_GIT_ASSET |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_SOURCE_MODEL_BINDING_V1.json | 642c2ed7b023aea8c6bd762891ff436f0f3eff6a95a58e56bf6f8c4b5d41dd20 | JSON object |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_EVALUATION_PLAN_V1.json | 6b52298a6d0bc1c62b837e170226be67b91b3153e47812e5df4ee10683724266 | JSON object |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_CORRECTED_MEASUREMENT_FREEZE_V1.md | 9cc035d639333a7478ebfc60ff3d5662ba30d7c8873d776349fa01aebbb89f9b | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json | 65069110f64ba2e518c411b784c8b9aa581d2dd8154d7dcb0e23111d436dde35 | JSON object |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/EXECUTION_PACKAGE_MANIFEST.json | 5a50bea4c8815cf293134fcf74afd0e87c9922cdddced76cb1ee1b5c7de430f7 | JSON object |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/b3_protocol.py | 5f0ad0066088f870a47bbbaa3f20994b3597cc4f98843db5e0601c51d3f8552a | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/run_b3_corrected_measurement.py | 151efafa88992aa2200a04fcd3093a016cc4d71ed9191c110034575539600c2a | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/verify_b3_execution_environment_v1_1.py | ba9149060692e3e17146c87d118b148517baf38ba03d5b210d2626a05e97c963 | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/run_b3_corrected_execution_v1_1.py | 5b12e92d89c96c1809f7a044be3c61bdfc46a70a6fd4a2f039a68c50915f233c | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/B3_EXECUTION_TECHNICAL_AMENDMENT_001.json | 5e6b984b2a3e2511bd02a6faf6df3d8e2e320522b74d40aa6436b038da49e701 | JSON object |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/B3_EXECUTION_VERIFIER_TECHNICAL_AMENDMENT_001.json | 5e6b984b2a3e2511bd02a6faf6df3d8e2e320522b74d40aa6436b038da49e701 | JSON object |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/B3_MINIMAL_PREFLIGHT_LOG.txt | 2be232fb2efee1315ef2eb27f1e9f169e980b55b1d1ae8a3dd4cddb592843e7b | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/B3_REMOTE_EXECUTION_MINIMAL_PREFLIGHT_V1.json | 73bcfb27a323fb08bcdf5f9cce58f8c8707eec3415df805e83ca39eddb86e867 | JSON object |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/b3_execution_amendment_monitor_v1.py | b9d89d6a35e0ddb2e53b4e6ddd16a6036d499b381e65abe1569beaf2c1166be6 | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/B3_MONITOR_LOG.txt | 01d0ea1cff5c662b3bba001ced019beab5e9a4435005d4ba60b19b5b4d54fd25 | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/B3_MONITOR_PID.txt | 5d1b67c4f5ebfbc63dd15285fa79e490cbc37c4c479a44f8e6646e0f7d65b5da | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/b3_shutdown_on_completion_v1.py | 7569df3c90f7f961d30786d333b8be299c25e5f7051ab8a3c11b5a2ef7466461 | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/b3_amendment_output_finalize_v1.py | 6d104fd4da5d54aac7b76750d492e6268c1bbc0388cd0c978f63f69e5cab95fd | not row data |  |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/B3_OUTPUT_HASH_RECHECK_V1.json | 208f29ebb4f940d1d0ac323930ace0562f0be9bdc004e88d611fc93f5fd412cf | JSON object |  |
| /root/autodl-tmp/affective-conflict/audit/EMOTIONTALK_CONTROLLED_V1/phase2_scientific_analysis_v1/08_M0_M3_model_results.csv | bd576a092eda349cccc34965468fd6d003de1da61118eef337ab6cd94e701426 | 33 | ORIGINAL_BINDING_EXACT_HASH |
| /root/autodl-tmp/affective-conflict/audit/EMOTIONTALK_CONTROLLED_V1/phase2_scientific_analysis_v1/EMOTIONTALK_PHASE2_SCIENTIFIC_ANALYSIS_V1_SUMMARY.json | e2d58be3cdfcf0089bf18edf6c080ad997c98405843b045cbbe94926dcaf1be9 | bound historical source | ORIGINAL_BINDING_EXACT_HASH |
| /root/autodl-tmp/affective-conflict/audit/EMOTIONTALK_CONTROLLED_V1/phase2_scientific_analysis_v1/EMOTIONTALK_PHASE2_SCALER_PROVENANCE_RESOLUTION_V1.json | cd90c4238cb59096418d57eedc3da83f25e98be0ec4870e9662e8ce289410bb4 | bound historical source | ORIGINAL_BINDING_EXACT_HASH |
| /root/autodl-tmp/affective-conflict/audit/EMOTIONTALK_CONTROLLED_V1/phase2_scientific_analysis_v1/EMOTIONTALK_PHASE2_PAIRWISE_MODEL_FREEZE_V1.json | 2f5e5e639ce22d79452aa54ca599fd0e14bc525cf874042b04065edadeed5019 | bound historical source | ORIGINAL_BINDING_EXACT_HASH |
| /root/autodl-tmp/affective-conflict/audit/CROSS_REGIME_TRANSFER_V1/attempt002_gate_v1/run_cross_regime_transfer_attempt002_gate_v1.py | 3afecef20ccf13908e8a924a2ec9b6f2ee1d51535aa551fcd7a8fd78f47a9b18 | bound historical source | ORIGINAL_BINDING_EXACT_HASH |


## Technical Amendment001 and execution identity closure

The actual Amendment001 fixes Windows/Linux `sorted(Path)` inventory-order comparison; it changes only verifier dependency/wrapper, with scientific_fields_affected=[] and frozen population/model/processor/assignment/source model unchanged. Every listed unchanged scientific byte hash was independently rechecked. It is a technical amendment, not a revised Transfer hypothesis or target-fitted model. Corrected model contentSHA8240abe64f8df444e7a4ebbcb636f51e6ef7e6833b62cf60adec0b2d14125a09, processorSHAe471b7e2830ec4f53ee249b2a6707480858e357b30b4dc1616e718ef6fe18d41, model/processorrevisionae9e1690543ffd5c0221dc27f79834d0294cba00. The scoring implementation bindingSHA3246b9ee0fea14948c0ac894181cf513322df7d969b87d6b8af92b17ce120e17 is distinct from scorer module byteSHA; neither is silently substituted.

| path | SHA256 | actual records |
| --- | --- | --- |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_CORRECTED_MEASUREMENT_FREEZE_V1.md | 9cc035d639333a7478ebfc60ff3d5662ba30d7c8873d776349fa01aebbb89f9b | not row data |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_EXECUTION_CONFIG_V1.json | 3fce0635937e51c6833d3755c8fe250feffda323cd5db3e2c244cad3d2e3ca05 | JSON object |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_MODEL_IDENTITY_BINDING_V1.json | a8b1c73a04896d0be47936abef2f0d66678b752ff66278bb07b3575f2049673f | JSON object |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_PROCESSOR_IDENTITY_BINDING_V1.json | 9af99deaaf6ec18adfb2b71129d05f9cc2ec00dcb634f4be05b611ddb574a102 | JSON object |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_SOURCE_MODEL_BINDING_V1.json | 642c2ed7b023aea8c6bd762891ff436f0f3eff6a95a58e56bf6f8c4b5d41dd20 | JSON object |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_TARGET_MEASUREMENT_MANIFEST_V1.json | 82798a27d5f55707ed1f1b0a76f07f65241989d0acbda1da3af7841011189fef | JSON object |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/B3_TARGET_SEQUENCE_ASSIGNMENT_V1.json | 65069110f64ba2e518c411b784c8b9aa581d2dd8154d7dcb0e23111d436dde35 | JSON object |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/MODEL_FILE_HASH_MANIFEST.csv | 8240abe64f8df444e7a4ebbcb636f51e6ef7e6833b62cf60adec0b2d14125a09 | 17 |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/PROCESSOR_FILE_HASH_MANIFEST.csv | e471b7e2830ec4f53ee249b2a6707480858e357b30b4dc1616e718ef6fe18d41 | 9 |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/b3_protocol.py | 5f0ad0066088f870a47bbbaa3f20994b3597cc4f98843db5e0601c51d3f8552a | not row data |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/b3_scorer.py | 82d7b0b59487147291477987643980476f79a4e8b7c723cbe010fec7963e18ab | not row data |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/canonical/CAMER_POPULATION.jsonl | 929a9734a5099c60f83890544401c09d703e32b728e0b9f4d6afd98b46c7869b | 1500 |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/canonical/LISTEN_CANONICAL.csv | f11685ced0edcc9eb40700da3492eff7e6b43ec58569c3ab7fe8662722d610d6 | 1149 |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/canonical/MCR_POPULATION.csv | c81079ad56ef3957fb978b753d98ee31d0e0cafbe6876eb7489125fd805e0716 | 909 |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/canonical/MCR_TEXT.jsonl | 28bdf75ce211dfb7af7677dabcd25c629e4ec8226ebdb991ee366d9e6ef949e4 | 909 |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/emotiontalk_controlled_prompt_v1.json | ba6b71f080ea186a1494a54a0990a5740fc0aea69f008622618102f39efe55f8 | JSON object |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/run_b3_corrected_measurement.py | 151efafa88992aa2200a04fcd3093a016cc4d71ed9191c110034575539600c2a | not row data |
| /root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/B3_AUTODL_EXECUTION_PACKAGE_V1/source_teacher_forcing.py | 62d50ec5972341f3a33651c3ef30dde39291176e5f0188eb44012c42cc0b4c1b | not row data |
