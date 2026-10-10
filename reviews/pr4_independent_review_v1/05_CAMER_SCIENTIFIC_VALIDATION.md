# 05 CA-MER 科学正确性验证

脚本：`review_scripts/r05_camer.py` → `logs/r05_camer.json`；Transfer 部分见 `r06`/`r07`/`r08`。

| 检查 | 独立结果 | 结论 |
|---|---|---|
| 6,000 个 arm-task 键 | 6000 行 = 1500 item × {A_ONLY, V_ONLY, A_THEN_V, V_THEN_A}，键唯一 | ✅ |
| 5,825 个科学可用结果 | `scientific_available=true` 5825；它们全部 parse_status=OK 且有标签 | ✅ |
| 失败分类 | A_ONLY 1 个 PARSE_UNSCORABLE；V_ONLY / A_THEN_V / V_THEN_A 各 58 个 OOM_SKIPPED（同样 58 个 item；联合 116 个 TECH_MISSING）。175 = 1 + 3×58 ✅ | ✅ |
| 技术失败后总体是否改变 | 否：冲突 1000 / 一致 500 的分母保持不变，UNOBSERVABLE 单独成组（冲突 32、一致 27），**不算作 neither** | ✅ |
| 资格组重算（由 6000 键独立推导） | 1500 个 item 的 eligibility_group 与两个联合 outcome 全部 0 不一致 | ✅ |
| 冲突组拆分 | DUAL 108 / A-only 273 / V-only 244 / NEITHER 343 / UNOBSERVABLE 32 = 1000 | ✅ |
| 316 vs 206/216 | 316 个 DUAL item = 108 冲突 + 208 一致对照（632 行）；冲突 DUAL 行 = 216，其中二元 206、OTHER 10。报告（`02_CAMER_UNIMODAL_JOINT_STRUCTURE.md:16`、Claim C1）已明确区分，并把“316 conflicts”列为 NOT_ESTABLISHED | ✅ 未混淆 |
| 条目级 vs 试次级 | 报告同时给出 item 和 trial（如“31 items/62 trials, 54 binary”） | ✅ |
| 重复计算联合输出 | 否：每个 (item, order) 恰好一行 | ✅ |
| DualReadable 统计 | 由 A_ONLY/V_ONLY 的实际输出定义；静态 manifest 中的 `NOT_RUN` 被说明为规划状态 | ✅ |
| Audio-/Video-Aligned/Consistent 构造身份 | subset 与 conflict 完全对应：consistent 500 全部非冲突，audio-aligned 500 与 video-aligned 500 全部冲突 | ✅ |
| 伪标签 vs ground truth | 报告与代码一致使用“source pseudo-label”；`final_label` 被排除；“No common human ground truth … is established” | ✅ |
| 用 7 类 B3 冒充 16 类熵？ | 否：标签空间 y_A 16 / y_V 11 / 候选 16；报告明确“Sixteen-class continuous probabilities were not saved; seven-class B3 scores are not substituted”；`entropy16: NOT_MEASURED` | ✅ |
| 把 Aligned 差异当作已确认的情绪证据贡献？ | 否：“These constructed populations differ in labels, source-match selection and missingness” | ✅ |
| 隐含目标集训练/重拟合 | 未发现：所有预测都由冻结 binding + 源 scaler 计算；`target_fit=False`；oracle 只作诊断 | ✅ |

## Transfer 中的 CA-MER（独立重算）

| 数值 | 报告 | 重算 |
|---|---|---|
| support-limited sourceprob：二元 / 冲突，AUROC | 416/672，0.686394 | ✅ |
| full margin：1350/2000，AUROC | 0.573999 | ✅ |
| 同一 M3b 公式：支持内 vs 支持外 AUROC | 0.715960 (416) vs 0.513616 (934) | ✅ |
| audio-aligned / video-aligned AUROC，音频占比 | 0.509993 / 0.569317；0.738129 / 0.367939 | ✅ |
| 双侧子集 audio-/video-aligned | 111 → 0.540028；95 → 0.499542 | ✅ |

支持受限的 sourceprob（416/672）与完整 margin（1350/2000）在所有报告与 Claim（T_CA_SUPPORT=NOT_ESTABLISHED，T_CA_MARGIN=CONTRADICTED）中都分开呈现，**没有**用子组 AUROC 代替完整结果 ✅。

## 来源备注（已披露，记录在此）

6000 行全部带有原始 `raw_run_type=TECHNICAL_RESOURCE_SWEEP`、`raw_scientific_result=False`。PR 将其中 5825 行作为科学结果使用，依据是“existing frozen scientific-equivalence decision”（`00_SOURCE_EVIDENCE_LOCK.md:14`）。这个等价性决定文件（`audit/QWEN25_CAMER_CONTROLLED_V1/scientific_equivalence_v1/CAMER_RESOURCE_SWEEP_SCIENTIFIC_EQUIVALENCE_V1.json`，sha `1e4e3fca…`）只在 `00_SOURCE_EVIDENCE_LOCK.md:56` 中以哈希锁定，文件本身不在 PR 或 main 中 → 公开 checkout 无法核实，登记为 `INSUFFICIENT_EVIDENCE（只能在 AutoDL 上核实）`，并入 F17 (P3)。它不是代码错误，但审稿人应当知道这些“科学结果”在历史元数据中的原始类型。
