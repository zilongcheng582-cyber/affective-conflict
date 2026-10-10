# 02_CAMER_UNIMODAL_JOINT_STRUCTURE

POST_HOC_EXPLORATORY — recovered historical outputs; CPU analysis only.

## Executed availability and eligibility

| Arm | Planned | Generated | Scientifically available | Technical missing | Parse fail |
| --- | --- | --- | --- | --- | --- |
| A_ONLY | 1500 | 1500 | 1499 | 0 | 1 |
| V_ONLY | 1500 | 1442 | 1442 | 58 | 0 |
| A_THEN_V | 1500 | 1442 | 1442 | 58 | 0 |
| V_THEN_A | 1500 | 1442 | 1442 | 58 | 0 |

6000 actual unique task keys,5825 scientifically usable. The same58video-containing items failed across V_ONLY and both joint orders:174 technical slots, not174 independent items. One audio parse failure; all generation outputs and technical flags are preserved. Two joint scientific arms are complete on1442 paired items (969conflict,473consistent). One thousand planned conflict IDs remain in the full analysis, including31joint-missing items/order. Discrete source matching: A702/1500, V639/1500; source pseudo-label semantics differ from human correctness.

The recovered316dual source-label matches comprise **108conflicts +208consistent controls**, not316 conflicts. Define `OBSERVED_DUAL_SOURCE_LABEL_MATCH` only when both valid A/V outputs match their respective pseudo-labels. On1000conflicts:108dual,273A-only,244V-only,343neither,32unobservable (31video OOM +1Aparse fail). Thirteen of the unobservable items have observed matching audio; they are not falsely counted as “neither”. This posthoc projection restores a protocol-defined evaluation-time property, but was not a gate that selected the historical joint execution.

| Support | Order | N | Full outcomes | Binary coverage | Conditional A share | Item-bootstrap95%CI |
| --- | --- | --- | --- | --- | --- | --- |
| FULL_CONFLICT | A_THEN_V | 1000 | A=369, SIDE_V=301, OTHER=299, PARSE_FAIL=0, TECH_MISSING=31, SAME_LABEL_MATCH=0 | 670/1000 (67.00%) | 55.07% | [51.30, 58.75] |
| FULL_CONFLICT | V_THEN_A | 1000 | A=385, SIDE_V=295, OTHER=289, PARSE_FAIL=0, TECH_MISSING=31, SAME_LABEL_MATCH=0 | 680/1000 (68.00%) | 56.62% | [52.88, 60.40] |
| CONFLICT_DUAL_MATCH | A_THEN_V | 108 | A=53, SIDE_V=49, OTHER=6, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 102/108 (94.44%) | 51.96% | [42.42, 61.76] |
| CONFLICT_DUAL_MATCH | V_THEN_A | 108 | A=55, SIDE_V=49, OTHER=4, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 104/108 (96.30%) | 52.88% | [43.27, 62.26] |
| CONFLICT_A_ONLY_MATCH | A_THEN_V | 273 | A=222, SIDE_V=10, OTHER=41, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 232/273 (84.98%) | 95.69% | [92.83, 98.23] |
| CONFLICT_A_ONLY_MATCH | V_THEN_A | 273 | A=213, SIDE_V=5, OTHER=55, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 218/273 (79.85%) | 97.71% | [95.41, 99.54] |
| CONFLICT_V_ONLY_MATCH | A_THEN_V | 244 | A=11, SIDE_V=192, OTHER=41, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 203/244 (83.20%) | 5.42% | [2.48, 8.78] |
| CONFLICT_V_ONLY_MATCH | V_THEN_A | 244 | A=23, SIDE_V=193, OTHER=28, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 216/244 (88.52%) | 10.65% | [6.70, 15.00] |
| CONFLICT_NEITHER_MATCH | A_THEN_V | 343 | A=82, SIDE_V=50, OTHER=211, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 132/343 (38.48%) | 62.12% | [53.51, 70.23] |
| CONFLICT_NEITHER_MATCH | V_THEN_A | 343 | A=93, SIDE_V=48, OTHER=202, PARSE_FAIL=0, TECH_MISSING=0, SAME_LABEL_MATCH=0 | 141/343 (41.11%) | 65.96% | [57.89, 73.81] |
| CONFLICT_UNOBSERVABLE | A_THEN_V | 32 | A=1, SIDE_V=0, OTHER=0, PARSE_FAIL=0, TECH_MISSING=31, SAME_LABEL_MATCH=0 | 1/32 (3.12%) | 100.00% | [100.00, 100.00] |
| CONFLICT_UNOBSERVABLE | V_THEN_A | 32 | A=1, SIDE_V=0, OTHER=0, PARSE_FAIL=0, TECH_MISSING=31, SAME_LABEL_MATCH=0 | 1/32 (3.12%) | 100.00% | [100.00, 100.00] |

For dual108, binary coverage102/108=94.44% and104/108=96.30%; OTHER6/108=5.56% (Wilson95%CI [2.57, 11.59]) and4/108=3.70% (CI [1.45, 9.14]). This contrasts descriptively with full conflict OTHER299/1000=29.90%,289/1000=28.90%, and binary coverage67.0%/68.0%. It is selection-associated coverage, not a causal effect of making evidence readable. Full planned coverage includes missing rows; available-case outcomes remain explicitly distinguishable.

A-only273 supports audio overwhelmingly among binary outcomes (222/232 and213/218), V-only244 supports video (192/203 and193/216); neither343 produces OTHER211 and202. This is informative alignment between observed single and joint predictions, but the classification rule shares labels/outcomes with its groups, labels can confound, and the selected subgroup is only10.8% of the conflict pool.

## Paired order

| Population | Outcome | V_THEN_A−A_THEN_V /95%CI | Holm p, family6 |
| --- | --- | --- | --- |
| FULL_CONFLICT | SIDE_A | +1.60 pp, 95% CI [-0.70, 3.80] pp | 1 |
| FULL_CONFLICT | SIDE_V | -0.60 pp, 95% CI [-2.70, 1.50] pp | 1 |
| FULL_CONFLICT | OTHER | -1.00 pp, 95% CI [-3.30, 1.30] pp | 1 |
| CONFLICT_DUAL_MATCH | SIDE_A | +1.85 pp, 95% CI [-6.48, 11.11] pp | 1 |
| CONFLICT_DUAL_MATCH | SIDE_V | +0.00 pp, 95% CI [-8.33, 9.26] pp | 1 |
| CONFLICT_DUAL_MATCH | OTHER | -1.85 pp, 95% CI [-7.41, 2.78] pp | 1 |

All six adjusted p=1; no robust net order effect established. This does not prove zero individual changes: transitions are preserved in `02_CAMER_MATCHED_TRANSITIONS.csv`. Exact paired discordance test and item bootstrap assume item independence beyond pairing, which cannot be guaranteed with unknown speaker/source-video grouping. The31 same-item technical absences contribute zero to observed-side indicator differences; no absent outcome is imputed. These are observed-output contrasts, not bounds on unobserved model choices.

Full conflict OTHER persists across orders226/299=75.59%, WilsonCI [70.41, 80.11]; dual support only1/6first-orderOTHERpersists, too small for stable inference. CA discrete results were already executed; no new1500/3000GPU inference is needed for this structural analysis. Complete16-class continuous scores are unmeasured; corrected7-class B3 is not substituted.

Trace: `analysis.py::camer`, raw-row references in recovered6000-keyCSV, item identity/eligibility in `intermediate/CAMER_ITEM_ELIGIBILITY_IDENTITY.csv`. Counts differ from frozen margin-transfer binary1350/2000 only in reporting unit/order or support, not by altering any frozen outcomes.
