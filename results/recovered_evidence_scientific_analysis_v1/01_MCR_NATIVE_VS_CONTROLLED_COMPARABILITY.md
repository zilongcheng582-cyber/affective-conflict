# 01_MCR_NATIVE_VS_CONTROLLED_COMPARABILITY

POST_HOC_EXPLORATORY — recovered historical outputs; CPU analysis only.

All909 controlled source indices have exact matching native sample provenance, source label and audio SHA; native-only91, controlled-only0. Native adversarial matches the audio source4/909 on this intersection. Native Description sentence equals controlled bare text909/909, but full source_text/prompt equals0/909. Per-item linkage and all outputs are in `intermediate/MCR_NATIVE_CONTROLLED_PER_ITEM_JOIN.csv`.

| Controlled arm (separate909 protocol) | Audio-source match | Explicit-text match | Same label as native adversarial |
| --- | --- | --- | --- |
| A_ONLY | 466/909 | 90/909 | 97/909 |
| T_ONLY | 0/909 | 909/909 | 901/909 |
| A_THEN_T | 22/909 | 876/909 | 875/909 |
| T_THEN_A | 85/909 | 751/909 | 758/909 |

Native system wrapper + fixed candidate order + warning; controlled no system, bare assertion, instruction last, item-specific candidate schedule. Native and controlled free-label parsers/greedymax16 settings are aligned at configuration level. Historical weight bytes across runs remain unproven, even though Qwen repo/path/processor class coincide. Candidate order differs; text placement and warning are different. The controlled909 is a pool after76 conflicting-path exclusions and15 duplicate-path representatives, not a random native subsample. Retained905SHA groups include a three-label ambiguity.

**Permitted:** descriptive matched-item comparison of complete protocol packages; audio/content join; agreement counts; separate native and controlled totals. **Not permitted:** pooling3636+4000 trials as oneexperiment; treating native adversarial versus controlled A_THEN_T as only order/warning effect; combined accuracy or conditional arbitration denominators; independent-model replication claim. Controlled T_ONLY909/909 assertion match is a different arm, not proof faithful native uses its audio. No new tests of protocol contrasts were promoted to causal inference.
