# POST_HOC_ROBUSTNESS_V1: DualReadable selection and external validity

| Accounting | n | Denominator | Proportion |
| --- | --- | --- | --- |
| SOURCE_PANEL | 1500 | 1500 | 100.0000% |
| AV_SOURCE_CONFLICT | 900 | 1500 | 60.0000% |
| AV_ELIGIBLE_DUALREADABLE | 146 | 1500 | 9.7333% |
| ELIGIBLE_AMONG_AV_CONFLICT | 146 | 900 | 16.2222% |
| AV_CONFLICT_EXCLUDED | 754 | 900 | 83.7778% |
| AV_CONFLICT_Readable_A=False_Readable_V=False | 322 | 900 | 35.7778% |
| AV_CONFLICT_Readable_A=False_Readable_V=True | 171 | 900 | 19.0000% |
| AV_CONFLICT_Readable_A=True_Readable_V=False | 261 | 900 | 29.0000% |
| AV_CONFLICT_Readable_A=True_Readable_V=True | 146 | 900 | 16.2222% |

Eligibility is recomputed from source labels, historical technical completion/readability and silent-video certification and agrees with every frozen eligibility row. The 146 selected items span 19 speakers and 134 dialogues. Source-label, trimodal-pattern, speaker, dialogue, split and video-duration distributions for eligible/excluded/all-panel populations are in ERI1_ELIGIBILITY_CHARACTERISTICS_V1.csv. Video duration is available for every frozen panel item; it is not substituted for audio duration. No complete source-panel audio duration variable was recovered from frozen tabular inputs, so no whole-panel audio-length comparison is claimed.

The causal estimand targets the preselected 146 DualReadable audio–video source-conflict items, under the frozen Qwen2.5-Omni-7B setup. Readability selection excludes most source conflicts and depends on the model's pre-intervention unimodal performance. It may enrich easily recognized labels and speakers. This is selection/external-validity limitation, not bias induced by post-intervention filtering: all selected items remain in ITT. No reweighting, outcome-based eligibility change, or extrapolation to all 1500 items, other datasets or other models is made.
