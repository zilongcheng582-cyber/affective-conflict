# 06 Transfer 独立复算

状态：**`GITHUB_CLEAN_CHECKOUT_REPLAY_PASS`（18/18 组点估计、身份、分母全部精确复现）**；bootstrap CI **未重新生成**（部分可复算）；`AUTODL_RESTRICTED_SOURCE_REPLAY_PASS` **未验证**（无 AutoDL 访问）。

## 方法（与 PR 验证器相互独立）

`review_scripts/r06_transfer_replay.py`（numpy；无拟合；阈值、scaler、系数全部读自冻结文件）：
1. 从 `evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv`（6354 行，6354 个唯一 (dataset, item, modality) 键）**重新推导**每条 MCR/CA-MER 预测的 Δsourceprob、ΔH7、Δmargin，并与冻结预测文件中的特征比较：7548 行，最大误差 **0.0**，0 行缺少测量。
2. 用 `frozen/source_model/binding.json`（M3a/M3b）与 `results/post_audit/closure_v1/SOURCE_BASELINE_BINDING_V1.json`（M0、M0+ORDER）重算概率：5919 条冻结 M3 预测最大误差 1.67e-16。
3. AUROC 用**显式成对比较**（不同于 PR 的秩公式），并计算 log loss、BA（阈值 0.5）、Brier、coverage。
4. 同时对照两个参照：(a) **PR 之前 main 上的** `ZERO_REFIT_BASELINE_COMPARISON_V1.csv`（按 evaluated_identity_sha256 + model 匹配），(b) PR 的 `04_TRANSFER_ROUTE_LEVEL_REPLAY_CHECK.csv`。

## 结果

* 9219 行预测，9219 个唯一 (role, record) 键。
* 18 组的 identity SHA 全部与 PR 一致，且全部能在 main 冻结表中找到对应。
* 指标最大绝对误差：相对 PR **0.0**；相对 main 冻结表 **0.0**。
* 分母（N_planned / N_conflict / N_evaluated / SIDE_A / OTHER / TECH）：全部一致（CA-MER 冲突按 A/V 源标签是否不同重新定义：672/336 item 与 2000/1000 item ✅）。

| route | model | N eval/conflict | SIDE_A | AUROC | BA | LL | Brier | 预测为 A 的数量（p≥.5） |
|---|---|---|---|---|---|---|---|---|
| MCR_AT_PRIMARY | M0 | 1734/1818 | 107 | 0.5000 | 0.5000 | 0.6782 | 0.2425 | 0 |
| | M0+ORDER | | | 0.6664 | 0.6664 | 0.6685 | 0.2379 | 836 |
| | FROZEN M3a | | | **0.7276** | **0.5000** | **0.2459** | 0.0585 | **0**（max p=0.406） |
| MCR_AT_MARGIN | M3b | 1734/1818 | 107 | 0.7394 | 0.5000 | 0.2433 | 0.0583 | 0（max p=0.420） |
| LISTEN_ALL_MIXED_HISTORICAL | M0 / M0+ORDER / M3b | 518/1139 | 316 | 0.5 / 0.3538 / 0.5226 | 0.5 / 0.3538 / 0.4892 | 0.6971 / 0.7650 / 0.9696 | | 0 / 182 / 106 |
| LISTEN_3C_JOINT | M0 / M0+ORDER / M3b | **167/378** | 102 | 0.5 / 0.5 / 0.6057 | 0.5 / 0.5 / 0.5155 | **0.6971** / 0.7486 / **0.9816** | 0.2520 / 0.2774 / 0.3528 | 0 / 0 / 16 |
| CAMER_SUPPORT_LIMITED_SOURCEPROB | M0 / M0+ORDER / M3a | 416/672 | 236 | 0.5 / 0.5308 / 0.6864 | 0.5 / 0.5308 / 0.5957 | 0.7166 / 0.7197 / 0.7689 | | 0 / 211 / 133 |
| CAMER_MARGIN | M0 / M0+ORDER / M3b | 1350/2000 | 754 | 0.5 / 0.5078 / 0.5740 | 0.5 / 0.5078 / 0.5399 | 0.7144 / 0.7249 / 0.8002 | | 0 / 680 / 588 |

## 重点核查

* **MCR**：冻结 M3a 在阈值 0.5 下对 1734 条中的 0 条预测为音频侧（最大 p 0.4056，中位数 0.0120，均值 0.0194，而观测患病率 0.0617）→ BA=0.5 是阈值从未被越过的必然结果；AUROC≈0.728、LL≈0.246、M0 LL≈0.678 全部精确复现。oracle LL 0.231639 ✅；分顺序 A_THEN_T 898（22 A）AUROC 0.699045、T_THEN_A 836（85 A）0.655706 ✅；单独 −ΔH7 的 AUROC 0.673529 ✅；平均 logit 分解 +0.4957 / +0.2895 / −4.6687 / −0.4433 ✅（`r08`）。
* **LISTEN 3C**：167/378、LL 0.9816 vs M0 0.6971 ✅；M0+ORDER 在 3C 中 AUROC=0.5，因为 3C 全部是 A_THEN_T（顺序项是常数）——文档已说明。
* **CA-MER**：support-limited sourceprob 与 full margin 分开；未用子组 AUROC 代替完整结果 ✅。
* **三个基线未混用**：冻结 M0（`EARLIER_DECLARED_SOURCE_FIXED_CONSTANT_PREFERENCE`）、post-audit M0+ORDER（`POST_AUDIT_DIAGNOSTIC_SOURCE_ONLY_BASELINE`，源数据拟合，target_fit=False）、target-prevalence oracle（只在子组诊断中出现，并标注 “target-informed diagnostic, not an authorized competitor”）✅。
* **引用的冻结 CI**：`04_TRANSFER_FAILURE_DECOMPOSITION.md` 中 6 条路线的 AUROC CI 与 LL−M0 CI，以及 M3a−M0+ORDER 的 AUROC 差 CI，均与 main 冻结表逐位一致 ✅。

## 子组（TRANSFER_FAILURE_SUBGROUPS.csv，116 行）

`review_scripts/r07_subgroup_replay.py`：从公开的 `TRANSFER_RECOVERED_ROW_LINKAGE.csv`（5199 行，全部 identity PASS）+ 冻结预测重算每个子组的冲突 N、二元 N、SIDE_A、AUROC、LL：**115/116 精确一致**；剩下 1 行（LISTEN_ALL_MIXED `B3_ONTOLOGY_False`）是因为 linkage 只覆盖 3C，本审查脚本无法重建，属于审查方的限制（LISTEN 全部行的 ontology 支持都是 False，PR 的值 1139/518 符合这一点）。

## 未能独立复算的部分

* 冻结 bootstrap CI（seed 20261008，2000 次配对簇）：没有重新生成，只核对了引用值。
* Phase4 子组 CI（seed 20261010+tag）：没有重新生成。
* 18 组以外的 AutoDL “六个 replay 输出 SHA 匹配”：需要 AutoDL。
