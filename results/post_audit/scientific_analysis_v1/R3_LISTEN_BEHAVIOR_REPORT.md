# R3 — LISTEN 3A/3B/3C Behavioral Diagnostics

Analysis origin: `POST_AUDIT_SCIENTIFIC_ANALYSIS_V1`. Code: `analyses/post_audit/sci_r3_listen_behavior.py`.
Seed `20261008`; 2,000-replicate item-cluster bootstrap. The clusters are underlying LISTEN items, matched across conditions.
Descriptive and associational only. No target-specific model is fitted, and the frozen population is unchanged. The corrected B3 transfer metrics are
cited from `results/post_audit/closure_v1/LISTEN_*` and are not recomputed.

**Construct note.** Outcome classes are *label-match classes*. SIDE_A means the output equals the audio-side (implicit) source label.
SIDE_T means it equals the text-side (explicit) label. OTHER means it matches neither. In 3A (text only) and 3B (audio only), the model never
receives the other modality, so a SIDE_A in 3A or a SIDE_T in 3B is not evidence of modality use. Each condition also has its own prompt
instruction (`MODALITY_INSTRUCTIONS`), its own per-item seeded option shuffle, and its own LISTEN ground truth (explicit label for 3A, implicit label for 3B/3C).

## R3.1 Complete outcome accounting (conflict rows; `R3_OUTCOME_ACCOUNTING.csv`)

| Condition | Input | N | SIDE_A | SIDE_T | OTHER | OTHER rate [95% CI] | Binary-resolvable | SIDE_A share among binary [95% CI] |
|---|---|---:|---:|---:|---:|---|---:|---|
| 3A | text only | 383 | 75 | 107 | 201 | 0.525 [0.478, 0.574] | 0.475 | 0.412 [0.344, 0.485] |
| 3B | audio only | 378 | 139 | 30 | 209 | 0.553 [0.500, 0.601] | 0.447 | 0.822 [0.766, 0.877] |
| 3C | audio→text | 378 | 102 | 65 | 211 | 0.558 [0.508, 0.606] | 0.442 | 0.611 [0.535, 0.681] |
| All | mixed | 1139 | 316 | 202 | 621 | 0.545 [0.506, 0.583] | 0.455 | 0.610 |

The technical-missing count is 0 in every condition, so **OTHER is a scientific outcome, not missingness**. The 10 SAME_LABEL rows (4/3/3) are all OTHER and are reported separately.
The OTHER rate does not differ by condition (item-clustered logistic: 3B vs 3A +0.11 [−0.14, +0.36]; 3C vs 3A +0.14 [−0.10, +0.37]).

## R3.2 Matched-condition transitions (`R3_MATCHED_CONDITION_TRANSITIONS.csv`)

Matches use exact identity: the same underlying item, identical modality-1 and modality-2 measurement IDs, identical evidence SHA256s and identical source labels.
3B↔3C share `source_item_id`. 3A uses a `_u_3A` id whose base matches, and its measurement IDs and hashes are identical. No item was force-joined.

| Comparison | Items in both | Exact-matched | Both conflict (analysed) | Unmatched |
|---|---:|---:|---:|---|
| 3B→3C | 381 | 381 | 378 | 0 |
| 3A→3C | 244 | 244 | 242 | 143 3A-only, 137 3C-only items (not in both conditions) |
| 3A→3B | 244 | 244 | 242 | 143 / 137 |

| Comparison (matched N) | Same outcome | OTHER→SIDE | SIDE→OTHER | A→T | T→A | ΔSIDE_A | ΔSIDE_T | ΔOTHER | ΔA-share among binary | Stuart–Maxwell |
|---|---|---|---|---|---|---|---|---|---|---|
| 3B→3C (378) | 0.783 | 0.082 [0.056, 0.111] | 0.087 [0.061, 0.116] | 0.045 | 0.003 | −0.098 [−0.132, −0.063] | +0.093 [+0.058, +0.130] | +0.005 [−0.037, +0.045] | −0.212 [−0.278, −0.147] | χ²=38.5, p=4e-9 |
| 3A→3C (242) | 0.690 | 0.120 [0.079, 0.165] | 0.136 [0.095, 0.182] | 0.004 | 0.050 | +0.091 [+0.037, +0.145] | −0.107 [−0.161, −0.058] | +0.017 [−0.045, +0.079] | +0.210 [+0.124, +0.301] | χ²=20.5, p=4e-5 |
| 3A→3B (242) | 0.591 | 0.149 | 0.165 | 0.004 | 0.091 | +0.182 | −0.198 | +0.017 | +0.404 | χ²=51.6, p=6e-12 |

- Adding text to audio (3B→3C) moves SIDE_A outputs to SIDE_T (17 of 139) and to OTHER (25). It moves OTHER to SIDE_T (27). The binary
  audio share therefore falls from 0.82 to 0.61. Adding audio to text (3A→3C) moves the matched outputs toward SIDE_A. **3C sits
  between the two unimodal conditions in the A/T split, while the OTHER rate stays almost constant.**
- OTHER is **item-persistent**. 178 of 209 3B-OTHER items stay OTHER in 3C (85%). 85 of the 242 triple-matched items (35%) are OTHER in all three conditions.
  3C OTHER is strongly associated with matched 3A OTHER (+1.93 log-odds) and 3B OTHER (+3.35).
- Because the prompts differ between conditions (input set, instruction and option order), these transitions are condition contrasts.
  They are **not causal modality contributions**.

## R3.3 OTHER associations (`R3_OTHER_ASSOCIATIONS.csv`)

The source label category dominates:

| Audio (implicit) label | 3A OTHER | 3B OTHER | 3C OTHER | 3B SIDE_A | 3C SIDE_A |
|---|---:|---:|---:|---:|---:|
| ridicule (n≈140) | 0.45 | **0.06** | **0.23** | 124/140 | 85/140 |
| frustration (n≈87) | 0.46 | 0.75 | 0.64 | 13/87 | 14/87 |
| disgust (n≈80) | 0.65 | 0.88 | 0.78 | 2/80 | 2/80 |
| anger (n≈58) | 0.60 | 0.91 | 0.83 | 0/58 | 1/58 |
| sadness (n≈13–16) | 0.69 | 0.92 | 1.00 | 0/13 | 0/13 |

- 89% of 3B SIDE_A and 83% of 3C SIDE_A outputs come from *ridicule* items (MUStARD sarcasm). For every other implicit label, the model
  almost never outputs the implicit label from audio. In a pooled item-clustered logistic model, OTHER is associated with
  "audio label is ridicule" (−2.18 [−2.53, −1.83]) and "text label is neutral" (−0.49 [−0.83, −0.14]). Condition and
  B3 unimodal features add little: only Δ text entropy is nominally associated (+2.30 [+0.30, +4.29]).
- **In every per-condition model, B3 unimodal entropy and margin features (alone or as A−T differences) are not associated with OTHER.**
  These features are computed over the 7-label EmotionTalk candidate space. That space does not contain the LISTEN labels ridicule, frustration or excitement,
  which is why source-label probability is undefined for every LISTEN row.
- The MUStARD sub-collection (PRO/ILL/EMB) shows no strong OTHER difference.
- **Not executable:** the identity of the label chosen under OTHER, and per-item option-list availability. Raw LISTEN generations and
  randomized choice lists are not published in this repository, so no claim is made about which labels OTHER contains or why.

## Interpretation

The 44% binary-resolvable rate in 3C is **not a 3C-specific joint-arbitration phenomenon**. OTHER rates are about 53–56% in all three conditions,
and OTHER is persistent for the same items. Two things are associated with it: (i) the implicit-label category, where outside sarcasm/ridicule the model rarely produces
the implicit label even from audio alone; and (ii) neutral text labels being easier to reproduce. A plausible reading is a
label-vocabulary/construct mismatch between LISTEN's implicit-affect labels and what the model expresses. This is an association, not an established cause.
The available data cannot separate model recognition failure from option presentation effects.

## R3.4 Evaluation implications

- **Pooled 518-row AUROC is not joint arbitration.** It pools 3A (text only) and 3B (audio only) rows, where only one modality was
  presented, with 3C rows. Their SIDE_A shares (0.41 vs 0.82 vs 0.61) differ systematically by condition. A pooled metric therefore mostly
  reflects condition composition (published pooled M3b AUROC is 0.523).
- **3C-only 167/378 is a conditional binary estimand.** It is defined only on the 44% of conflicts where the output matched one side.
  That subset is selected by an item-persistent, label-dependent process (ridicule items are over-represented among SIDE_A), so it does not describe how the model
  handles all joint conflicts.
- **The full-378 OTHER rate (0.558 [0.508, 0.606]) deserves separate reporting.** It is the majority behaviour and it is stable across conditions.
  Any LISTEN arbitration claim has to state it.
- **The order effect is not identifiable.** Every 3C row is A_THEN_T, so `FIRST_IS_MODALITY1` is constant. The frozen source order coefficient
  (−0.856, which encodes EmotionTalk's pair-specific recency) acts as a fixed offset against SIDE_A, while 61% of 3C binary outcomes are SIDE_A.
  Consistent with this, the source-fixed M0+ORDER baseline is already worse than M0 on 3C (log loss 0.749 vs 0.697).
- **Log loss 0.982 vs M0 0.697 rules out successful probability transfer.** The published paired difference is +0.285 [+0.168, +0.402]. AUROC 0.606
  [0.514, 0.697] shows weak ranking at best, and balanced accuracy is 0.515. The transferred probabilities are worse than a constant.

**R3 verdict:** LISTEN is a useful **behavioral diagnostic**: label-dependent and item-persistent OTHER, and an intermediate 3C A/T split between the unimodal conditions.
It is a **transfer limitation**, not evidence of joint-arbitration transfer. All condition contrasts are associational.
