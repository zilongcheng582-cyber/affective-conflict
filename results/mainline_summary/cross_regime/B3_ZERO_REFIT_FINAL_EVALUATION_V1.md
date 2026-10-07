# B3_ZERO_REFIT_FINAL_EVALUATION_V1

Final ruling: **SURVIVES_WITH_CORRECTION**. QWEN_MAINLINE_SCIENCE = CLOSED.

Corrected measurement closeout PASS: 6354/6354 measurements and 5515/5515 sequence-aware forwards; zero failed or missing. Assignment and paired-modality sequence identity, seven-candidate probability integrity, scalar CPU recomputation, cache identity and official hashes all PASS. No GPU was executed in this evaluation.

The frozen historical source M3a/M3b coefficients, source scaler and threshold 0.5 were applied unchanged. Historical log loss is the primary metric; AUROC, balanced accuracy and Brier are prespecified secondary metrics. Only corrected feature deltas replaced historical measurement features; joint outcomes, record identities, presentation order, support membership and accounting remain frozen. Source-probability is null outside the seven-label ontology. Historical Attempt002 metrics were read, never recomputed.

| Frozen role | Evaluated / prespecified conflict N | Coverage | Log loss | AUROC | Balanced accuracy @0.5 | Brier |
|---|---:|---:|---:|---:|---:|---:|
| MCR_AT_PRIMARY | 1734 / 1818 | 0.953795380 | 0.245884161 | 0.727558892 | 0.500000000 | 0.058506015 |
| MCR_AT_MARGIN_SENSITIVITY | 1734 / 1818 | 0.953795380 | 0.243252522 | 0.739397664 | 0.500000000 | 0.058279372 |
| LISTEN_AT_MARGIN_SENSITIVITY | 518 / 1139 | 0.454784899 | 0.969592965 | 0.522637549 | 0.489190375 | 0.350149652 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | 416 / 672 | 0.619047619 | 0.768851458 | 0.686393597 | 0.595715631 | 0.269758734 |
| CAMER_AV_MARGIN_SENSITIVITY | 1350 / 2000 | 0.675000000 | 0.800208296 | 0.573999074 | 0.539941342 | 0.283971706 |
| LISTEN_AT_PRIMARY (STRUCTURALLY_UNSUPPORTED_UNDER_FROZEN_ONTOLOGY) | Undefined / 1139 | Undefined | Undefined | Undefined | Undefined | Undefined |
| CAMER_AV_FULL_PRIMARY (NOT_DEFINED_FOR_FULL_TARGET_POPULATION) | Undefined / 2000 | Undefined | Undefined | Undefined | Undefined | Undefined |

CA-MER supported source-probability is supplementary: 1434 planned supported joint slots, 672 supported conflict slots and 416 evaluable binary outcomes. Its coverage 416/672 is conditional on frozen support, not full-population primary coverage. Full-population margin coverage is 1350/2000. LISTEN margin coverage is 518/1139; 10 same-label rows are excluded from the 1149 planned slots. Coverage reflects frozen joint outcomes and is not the GPU acquisition completion rate. All populations and coverage are unchanged by correction.

| Role | Metric | Historical | Corrected | Signed delta | Absolute delta |
|---|---|---:|---:|---:|---:|
| MCR_AT_PRIMARY | log_loss | 0.242113305 | 0.245884161 | +0.003770855 | 0.003770855 |
| MCR_AT_PRIMARY | AUROC | 0.727805892 | 0.727558892 | -0.000247000 | 0.000247000 |
| MCR_AT_PRIMARY | balanced_accuracy | 0.500000000 | 0.500000000 | +0.000000000 | 0.000000000 |
| MCR_AT_PRIMARY | Brier_score | 0.057814112 | 0.058506015 | +0.000691903 | 0.000691903 |
| MCR_AT_MARGIN_SENSITIVITY | log_loss | 0.239555598 | 0.243252522 | +0.003696924 | 0.003696924 |
| MCR_AT_MARGIN_SENSITIVITY | AUROC | 0.741770014 | 0.739397664 | -0.002372350 | 0.002372350 |
| MCR_AT_MARGIN_SENSITIVITY | balanced_accuracy | 0.500000000 | 0.500000000 | +0.000000000 | 0.000000000 |
| MCR_AT_MARGIN_SENSITIVITY | Brier_score | 0.057624342 | 0.058279372 | +0.000655030 | 0.000655030 |
| LISTEN_AT_MARGIN_SENSITIVITY | log_loss | 1.020966453 | 0.969592965 | -0.051373488 | 0.051373488 |
| LISTEN_AT_MARGIN_SENSITIVITY | AUROC | 0.478490412 | 0.522637549 | +0.044147136 | 0.044147136 |
| LISTEN_AT_MARGIN_SENSITIVITY | balanced_accuracy | 0.462855621 | 0.489190375 | +0.026334754 | 0.026334754 |
| LISTEN_AT_MARGIN_SENSITIVITY | Brier_score | 0.369164904 | 0.350149652 | -0.019015252 | 0.019015252 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | log_loss | 0.819707038 | 0.768851458 | -0.050855580 | 0.050855580 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | AUROC | 0.658804143 | 0.686393597 | +0.027589454 | 0.027589454 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | balanced_accuracy | 0.573352166 | 0.595715631 | +0.022363465 | 0.022363465 |
| CAMER_AV_SUPPORT_LIMITED_SOURCEPROB | Brier_score | 0.287934283 | 0.269758734 | -0.018175548 | 0.018175548 |
| CAMER_AV_MARGIN_SENSITIVITY | log_loss | 0.822494000 | 0.800208296 | -0.022285704 | 0.022285704 |
| CAMER_AV_MARGIN_SENSITIVITY | AUROC | 0.564864348 | 0.573999074 | +0.009134727 | 0.009134727 |
| CAMER_AV_MARGIN_SENSITIVITY | balanced_accuracy | 0.527070390 | 0.539941342 | +0.012870952 | 0.012870952 |
| CAMER_AV_MARGIN_SENSITIVITY | Brier_score | 0.293341673 | 0.283971706 | -0.009369967 | 0.009369967 |

LISTEN margin AUROC changes by +0.04415 and supported CA-MER AUROC by +0.02759; their log losses improve by about 0.051. These changes warrant corrected numbers and explicit correction disclosure. MCR remains strongest in ranking, CA-MER remains partial/support-limited, and LISTEN remains weak with structurally unsupported primary. The descriptive LISTEN AUROC crossing is acknowledged, but does not establish a new strong-transfer result. No post-hoc numerical materiality cutoff, significance test, or new analysis was introduced.

**MCR: MINOR.** Primary AUROC remains about 0.728 and sensitivity AUROC about 0.739; frozen-threshold balanced accuracy remains 0.5. Strongest ranking transfer among these frozen routes persists, without claiming improved threshold classification.

**LISTEN: MATERIAL.** Source-probability primary remains structurally unsupported. Margin sensitivity is now slightly above chance in AUROC, with balanced accuracy 0.48919 and coverage 518/1139. Weak transfer interpretation persists; the old below-chance AUROC wording must change.

**CA-MER: MATERIAL_IN_SUPPORTED_SUPPLEMENTARY_ROUTE.** Supported supplementary AUROC rises from 0.65880 to 0.68639; balanced accuracy from 0.57335 to 0.59572. Full-population margin sensitivity remains weaker (AUROC 0.57400). Full-population source-probability primary remains undefined; partial/support-limited interpretation persists.

Interpretation limits: these are descriptive frozen-route comparisons. Raw log losses across datasets have different outcome prevalence and do not alone measure relative transfer strength. MCR strongest transfer refers to the retained ranking result, not superior balanced accuracy at the frozen threshold. LISTEN AUROC crossing is numerical and no statistical significance claim is made. No causal separation of ordering from other frozen measurement differences was attempted. Historical CA-MER support-only role metadata is preserved in the comparison file while its corrected scientific role is explicitly supplementary.

No target refit, target scaler fit, threshold tuning, calibration, new subgroup, order robustness, prompt robustness, second model or supplementary experiment was performed. The row-level prediction CSV records the prespecified evaluation only. Original GPU outputs and historical Attempt002 remain unchanged.

Provenance and closeout JSON files contain input hashes, source bindings, analysis script hash and no-refit flags. B3_FINAL_HASHES_V1.txt covers all final artifacts except itself. The analysis source is included for review; docs record final state and decisions.
