# E1 video degradation V2 scientific closure

FULL_COMPLETE; INDEPENDENT_CPU_REPLAY_PASS. 2336 formal slots; all 146 frozen items retained.

{
  "status": "ANALYSIS_COMPLETE_AWAITING_INDEPENDENT_VERIFICATION",
  "fixed_ITT_items": 146,
  "dialogue_clusters": 134,
  "planned_slots": 2336,
  "all_attempts": 2336,
  "technical_failure_attempts": 0,
  "generation_missing_final": 0,
  "scoring_missing_final": 0,
  "retries": 0,
  "primary": [
    {
      "endpoint": "SIDE_V_L3_MINUS_RECODE",
      "family": "PRIMARY_3_HOLM",
      "effect": -0.4075342465753425,
      "utterance_ci95": [
        -0.476027397260274,
        -0.339041095890411
      ],
      "dialogue_cluster_ci95": [
        -0.47635135135135137,
        -0.33793103448275863
      ],
      "p_two_sided": 9.99990000099999e-06,
      "seed": 2026101203,
      "items": 146,
      "clusters": 134,
      "ITT_denominator": 146,
      "technical_missing_effect_bounds": [
        -0.4075342465753425,
        -0.4075342465753425
      ],
      "complete_case_items": 146,
      "complete_case_effect": -0.4075342465753425,
      "p_holm": 2.999970000299997e-05,
      "ruling": "DECREASE"
    },
    {
      "endpoint": "SIDE_A_L3_MINUS_RECODE",
      "family": "PRIMARY_3_HOLM",
      "effect": 0.3698630136986301,
      "utterance_ci95": [
        0.3013698630136986,
        0.4383561643835616
      ],
      "dialogue_cluster_ci95": [
        0.29859775641025643,
        0.4433415492957746
      ],
      "p_two_sided": 9.99990000099999e-06,
      "seed": 2026101213,
      "items": 146,
      "clusters": 134,
      "ITT_denominator": 146,
      "technical_missing_effect_bounds": [
        0.3698630136986301,
        0.3698630136986301
      ],
      "complete_case_items": 146,
      "complete_case_effect": 0.3698630136986301,
      "p_holm": 2.999970000299997e-05,
      "ruling": "INCREASE"
    },
    {
      "endpoint": "OTHER_L3_MINUS_RECODE",
      "family": "PRIMARY_3_HOLM",
      "effect": 0.03767123287671233,
      "utterance_ci95": [
        0.00684931506849315,
        0.07191780821917808
      ],
      "dialogue_cluster_ci95": [
        0.006711409395973154,
        0.07191780821917808
      ],
      "p_two_sided": 0.04167958320416796,
      "seed": 2026101223,
      "items": 146,
      "clusters": 134,
      "ITT_denominator": 146,
      "technical_missing_effect_bounds": [
        0.03767123287671233,
        0.03767123287671233
      ],
      "complete_case_items": 146,
      "complete_case_effect": 0.03767123287671233,
      "p_holm": 0.04167958320416796,
      "ruling": "INCREASE"
    }
  ],
  "secondary": [
    {
      "endpoint": "SIDE_V_CLEAN_MINUS_RECODE",
      "family": "SECONDARY_HOLM",
      "effect": 0.0,
      "utterance_ci95": [
        0.0,
        0.0
      ],
      "dialogue_cluster_ci95": [
        0.0,
        0.0
      ],
      "p_two_sided": 1.0,
      "seed": 2026101233,
      "items": 146,
      "clusters": 134,
      "p_holm": 1
    },
    {
      "endpoint": "SIDE_A_CLEAN_MINUS_RECODE",
      "family": "SECONDARY_HOLM",
      "effect": 0.0,
      "utterance_ci95": [
        0.0,
        0.0
      ],
      "dialogue_cluster_ci95": [
        0.0,
        0.0
      ],
      "p_two_sided": 1.0,
      "seed": 2026101243,
      "items": 146,
      "clusters": 134,
      "p_holm": 1
    },
    {
      "endpoint": "OTHER_CLEAN_MINUS_RECODE",
      "family": "SECONDARY_HOLM",
      "effect": 0.0,
      "utterance_ci95": [
        0.0,
        0.0
      ],
      "dialogue_cluster_ci95": [
        0.0,
        0.0
      ],
      "p_two_sided": 1.0,
      "seed": 2026101253,
      "items": 146,
      "clusters": 134,
      "p_holm": 1
    },
    {
      "endpoint": "SIDE_V_ORDINAL_DOSE_SLOPE",
      "family": "SECONDARY_HOLM",
      "effect": -0.14349315068493151,
      "utterance_ci95": [
        -0.16815068493150684,
        -0.11883561643835618
      ],
      "dialogue_cluster_ci95": [
        -0.16870748299319727,
        -0.11938721615406725
      ],
      "p_two_sided": 9.99990000099999e-06,
      "seed": 2026101263,
      "items": 146,
      "clusters": 134,
      "p_holm": 0.0001099989000109999
    },
    {
      "endpoint": "SIDE_A_ORDINAL_DOSE_SLOPE",
      "family": "SECONDARY_HOLM",
      "effect": 0.1339041095890411,
      "utterance_ci95": [
        0.10924657534246575,
        0.1582191780821918
      ],
      "dialogue_cluster_ci95": [
        0.10872372529828483,
        0.1591549295774648
      ],
      "p_two_sided": 9.99990000099999e-06,
      "seed": 2026101273,
      "items": 146,
      "clusters": 134,
      "p_holm": 0.0001099989000109999
    },
    {
      "endpoint": "OTHER_ORDINAL_DOSE_SLOPE",
      "family": "SECONDARY_HOLM",
      "effect": 0.00958904109589041,
      "utterance_ci95": [
        -0.0010273972602739727,
        0.02089041095890411
      ],
      "dialogue_cluster_ci95": [
        -0.0007042253521126759,
        0.02074829931972789
      ],
      "p_two_sided": 0.1032089679103209,
      "seed": 2026101283,
      "items": 146,
      "clusters": 134,
      "p_holm": 0.4128358716412836
    },
    {
      "endpoint": "SIDE_V_ORDER_INTERACTION",
      "family": "SECONDARY_HOLM",
      "effect": -0.17123287671232876,
      "utterance_ci95": [
        -0.2671232876712329,
        -0.0821917808219178
      ],
      "dialogue_cluster_ci95": [
        -0.2638888888888889,
        -0.07913669064748201
      ],
      "p_two_sided": 0.0005899941000589994,
      "seed": 2026101293,
      "items": 146,
      "clusters": 134,
      "p_holm": 0.0035399646003539966
    },
    {
      "endpoint": "SIDE_A_ORDER_INTERACTION",
      "family": "SECONDARY_HOLM",
      "effect": 0.2465753424657534,
      "utterance_ci95": [
        0.1506849315068493,
        0.3424657534246575
      ],
      "dialogue_cluster_ci95": [
        0.1527777777777778,
        0.3422818791946309
      ],
      "p_two_sided": 1.999980000199998e-05,
      "seed": 2026101303,
      "items": 146,
      "clusters": 134,
      "p_holm": 0.00013999860001399987
    },
    {
      "endpoint": "OTHER_ORDER_INTERACTION",
      "family": "SECONDARY_HOLM",
      "effect": -0.07534246575342465,
      "utterance_ci95": [
        -0.13013698630136986,
        -0.0273972602739726
      ],
      "dialogue_cluster_ci95": [
        -0.13043478260869565,
        -0.020833333333333332
      ],
      "p_two_sided": 0.013059869401305987,
      "seed": 2026101313,
      "items": 146,
      "clusters": 134,
      "p_holm": 0.06529934700652994
    },
    {
      "endpoint": "V_ONLY_CORRECTNESS_L3_MINUS_RECODE",
      "family": "SECONDARY_HOLM",
      "effect": -0.4931506849315068,
      "utterance_ci95": [
        -0.5753424657534246,
        -0.410958904109589
      ],
      "dialogue_cluster_ci95": [
        -0.5763888888888888,
        -0.4100631994404478
      ],
      "p_two_sided": 9.99990000099999e-06,
      "seed": 2026101323,
      "items": 146,
      "clusters": 134,
      "p_holm": 0.0001099989000109999
    },
    {
      "endpoint": "V_ONLY_NORMALIZED_ENTROPY_L3_MINUS_RECODE",
      "family": "SECONDARY_HOLM",
      "effect": 0.07759423822477898,
      "utterance_ci95": [
        0.054038502380239106,
        0.10187356825315849
      ],
      "dialogue_cluster_ci95": [
        0.0541114827252953,
        0.10284238294278547
      ],
      "p_two_sided": 9.99990000099999e-06,
      "seed": 2026101333,
      "items": 146,
      "clusters": 134,
      "p_holm": 0.0001099989000109999
    }
  ],
  "post_treatment_selection": false,
  "run_fingerprint": "03d201f1b47d966c853da9270219eda6d4fb81f1026bd7b56ea01ae59ed598f6"
}

## Comparison and limits

{
  "role": "EXPLORATORY_PARALLEL_COMPARISON_NOT_SYMMETRY_TEST",
  "ERI1_frozen": {
    "items": 146,
    "SIDE_A_SNR00_minus_RECODE": -0.1095890410958904,
    "SIDE_V": 0.05821917808219178,
    "OTHER": 0.05136986301369863,
    "source": "/root/autodl-tmp/affective-conflict-eri1/closure_v1/github_evidence/ERI1_PRIMARY_RESULTS_V1.csv"
  },
  "E1_V2": [
    {
      "endpoint": "SIDE_V_L3_MINUS_RECODE",
      "family": "PRIMARY_3_HOLM",
      "effect": -0.4075342465753425,
      "utterance_ci95": [
        -0.476027397260274,
        -0.339041095890411
      ],
      "dialogue_cluster_ci95": [
        -0.47635135135135137,
        -0.33793103448275863
      ],
      "p_two_sided": 9.99990000099999e-06,
      "seed": 2026101203,
      "items": 146,
      "clusters": 134,
      "ITT_denominator": 146,
      "technical_missing_effect_bounds": [
        -0.4075342465753425,
        -0.4075342465753425
      ],
      "complete_case_items": 146,
      "complete_case_effect": -0.4075342465753425,
      "p_holm": 2.999970000299997e-05,
      "ruling": "DECREASE"
    },
    {
      "endpoint": "SIDE_A_L3_MINUS_RECODE",
      "family": "PRIMARY_3_HOLM",
      "effect": 0.3698630136986301,
      "utterance_ci95": [
        0.3013698630136986,
        0.4383561643835616
      ],
      "dialogue_cluster_ci95": [
        0.29859775641025643,
        0.4433415492957746
      ],
      "p_two_sided": 9.99990000099999e-06,
      "seed": 2026101213,
      "items": 146,
      "clusters": 134,
      "ITT_denominator": 146,
      "technical_missing_effect_bounds": [
        0.3698630136986301,
        0.3698630136986301
      ],
      "complete_case_items": 146,
      "complete_case_effect": 0.3698630136986301,
      "p_holm": 2.999970000299997e-05,
      "ruling": "INCREASE"
    },
    {
      "endpoint": "OTHER_L3_MINUS_RECODE",
      "family": "PRIMARY_3_HOLM",
      "effect": 0.03767123287671233,
      "utterance_ci95": [
        0.00684931506849315,
        0.07191780821917808
      ],
      "dialogue_cluster_ci95": [
        0.006711409395973154,
        0.07191780821917808
      ],
      "p_two_sided": 0.04167958320416796,
      "seed": 2026101223,
      "items": 146,
      "clusters": 134,
      "ITT_denominator": 146,
      "technical_missing_effect_bounds": [
        0.03767123287671233,
        0.03767123287671233
      ],
      "complete_case_items": 146,
      "complete_case_effect": 0.03767123287671233,
      "p_holm": 0.04167958320416796,
      "ruling": "INCREASE"
    }
  ],
  "E2_frozen": {
    "estimate": -0.05333333333333334,
    "item_ci95": [
      -0.08,
      -0.028888888888888888
    ],
    "dialogue_cluster_ci95": [
      -0.08149897903234954,
      -0.02843601895734597
    ],
    "two_sided_signflip_p": 2.999970000299997e-05,
    "items": 225,
    "dialogue_clusters": 177,
    "seed": 2026101210,
    "bootstrap_replicates": 10000,
    "signflip_replicates": 100000,
    "ITT_denominator_items": 225,
    "joint_primary_cells": 900,
    "technical_missing_ITT_rule": "NEGATIVE_H1_CONSERVATIVE_HIGH_SUCCESS_BASELINE_FAILURE",
    "technical_failure_conservative_effect_bounds": [
      -0.05333333333333334,
      -0.05333333333333334
    ],
    "complete_case_items": 225,
    "complete_case_effect": -0.05333333333333334,
    "post_treatment_selection": false
  },
  "boundaries": [
    "E1 and ERI1 share frozen conflict population but interventions are not calibrated equivalent",
    "E2 uses 225 distinct consistent items",
    "No percentage-difference proof of symmetry or asymmetry",
    "No entropy causal mediation",
    "No response-guided sigma change"
  ]
}

Historical results unchanged. Negative and non-significant findings use the same reporting standard. No further model, intervention or GitHub merge initiated.
