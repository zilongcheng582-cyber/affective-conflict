# 07 科学声明与文档一致性

## Claim–Evidence Matrix（`results/recovered_evidence_scientific_analysis_v1/CLAIM_EVIDENCE_MATRIX.csv`）

25 条声明，6 个类别：Recovered Native Experiments 14、Frozen Transfer 4、Transfer Failure Explanation 4、R1 1、R2 1、ERI1 1。状态分布：NOT_ESTABLISHED 7、NEW_EXPLORATORY_RESULT 6、ALREADY_SUPPORTED 4、MEASUREMENT_INCOMPATIBLE 2、INSUFFICIENT_EVIDENCE 2、NOT_IDENTIFIABLE 2、CONTRADICTED 2。

| 类别 | 已核数字（独立重算 / 对照冻结源） | 分母 | 措辞 | 结论 |
|---|---|---|---|---|
| R1 Source Prediction | AUROC .803 引自 main `R1_MODEL_COMPARISON.csv`；未重新拟合 | 663 行 / 274 话语 | 引用，未重复声称新贡献 | ✅ |
| R2 Compositionality | 引用 main 的 R2 / POST_AUDIT 回放 | 402/294/268 | NOT_ESTABLISHED | ✅ |
| Frozen Transfer（T_MCR_RANK、T_LISTEN、T_CA_SUPPORT、T_CA_MARGIN） | 全部与 06 一致，CI 与 main 一致 | ✅ | “ranking” 与 “probability loss” 分开 | ✅ |
| ERI1 (X2) | −10.96 pp 引自 ERI1 closure | 146 | ALREADY_SUPPORTED | ✅（见 F10） |
| Recovered Native（M1–M5、C1–C5、L1–L4、X1） | M1–M3 数字见 03；C1（316=108+208）见 05；L1–L3（22 ridicule）见 04 | ✅ | 均为 post hoc，无因果措辞 | ✅ |
| Transfer Failure（F_MCR_THRESHOLD、F_LISTEN_SELECTION、F_CA_ENTROPY） | TP0/FN107/TN1627，mean p .019427 vs .061707；strict 0.759 / LL .7985 vs .6958；.715960/.513616 —— 全部重算一致 | ✅ | “algebraic explanation, not unique causal mechanism” | ✅ |

逐项检查：
* 命题与数字一致 ✅；总体与分母正确 ✅。
* 引用文件存在：在 `source_and_code_trace` 列中，只有 L1 引用改名前的 `03_LISTEN_MATCHED_SOURCE_LABEL_DIAGNOSTICS.csv`（公开版是 `.public_projection.csv`）→ F12 (P3)。
* 因果措辞：在全部新报告中检索 causal/prove/confirm/因果/证明，每处都带有否定或限定（“not causal”“neither proves”…）✅。
* exploratory 与 confirmatory：**25/25 都标为 `analysis_origin=POST_HOC_EXPLORATORY`**，包括 ERI1 预注册的确认性效应（X2，`previously_reported` 列写的是 “Frozen ERI1 confirmatory effect”）以及冻结 Transfer 指标。这个列混合了“本矩阵的产生方式”和“证据本身的性质”，验证器（`validate_migration.py:57`）还强制要求所有行都是该值 → **F10 (P3)**：方向保守，不夸大，但会弱化 ERI1 的确认性地位；建议增加一个 `evidence_origin` 列。
* 外部效度没有被扩大 ✅（LISTEN 22、CA 支持子组都明确限定）。

## GPU / NEXT_STEP 决策文档 —— **F02 (P2)**

| 文档 | 头部决策 | 被取代标记 | 关键内容 |
|---|---|---|---|
| `four_regime/05_QWEN_GPU_EXPERIMENT_DECISION.md` | `ONE_FINAL_QWEN_EXPERIMENT_REQUIRED` | ✅ 顶部有“已被取代（Revision V2）” | 要求在 GPU 上运行“仓库中无输出的” CA-MER A_ONLY/V_ONLY |
| `four_regime/06_SCIENTIFIC_SYNTHESIS_EXECUTIVE_SUMMARY.md` | 正文仍写 `ONE_FINAL_QWEN_EXPERIMENT_REQUIRED` | 顶部提示“以 **08** 为准” | 第 17 行：MCR“另三种文本关系条件从未运行”；“受控 A_ONLY/V_ONLY 缺失” |
| `four_regime/08_QWEN_GPU_EXPERIMENT_DECISION_V2.md` | `CPU_ANALYSIS_INCOMPLETE` | ❌ **没有被取代标记** | 第 12 行：归档不可访问，A_ONLY/V_ONLY 未取得；第 18 行：“**否**，现在不应运行 CA-MER 16 类测量，也不应作为下一个 Qwen 实验” |
| `historical_reconciliation_v2/QWEN_GPU_PRIORITY_REVISED_V2.md` | 无代码 | — | 07/08 中“未取得 A_ONLY/V_ONLY”应改为“已执行”；CA-MER 16 类是“条件性新测量缺口”，优先级低于 CPU |
| `historical_reconciliation_v2/FOUR_REGIME_SYNTHESIS_ERRATA_V2.json` | — | — | 5 条勘误（A/V 已执行；MCR native 4000 已存在；909→905；V3/V4 不可合并…） |
| `recovered/06_QWEN_NEXT_EXPERIMENT_DECISION.md` 与 Phase4 `RUN_PROVENANCE`、`PHASE4_COMPLETION_RECEIPT` | `NEXT_STEP = CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION` | 宣布“previous default SECOND_MODEL is superseded” | Qwen 优先级 **#1 = CA-MER 16 类连续测量**（条件性、先 CPU 冻结） |

问题：
1. 读者在 `four_regime_structural_synthesis_v1/` 中会被 06 的提示引向 08，把它当作当前决定；但 08 的事实前提（归档不可访问、A/V 未取得）已经被同一 PR 中后来的证据推翻，而且 08 对 CA-MER 16 类的建议（“否”）与当前 `06_QWEN_NEXT`（“优先级 1，条件性”）相反。08 和 06 都没有指向后续文档的被取代标记。
2. `four_regime` 的 02/06/07 中仍有“MCR 只运行了对抗型文本”“A_ONLY/V_ONLY 不在仓库”等已撤回的说法；勘误只在另一个目录的 JSON 中。
3. 好的方面：任何文档都**没有**把 CA-MER 16 类实验写成必须执行；`QWEN_GPU_PRIORITY_REVISED_V2.md` 明确“既有 3000 个 A/V 生成不需要重复”；没有把新的 16 类连续评分当作已有数据（`entropy16: NOT_MEASURED`）。
4. 当前有效的 NEXT_STEP 只有一个：`CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION`（建议，非授权），但文件层级没有表达出来。

最小修复（不改历史文件字节）：在 `results/four_regime_structural_synthesis_v1/` 增加一个**目录专用**的 `STATUS_AND_SUPERSESSION.md`（或替换掉通用 README），列出：05→08→`QWEN_GPU_PRIORITY_REVISED_V2`→`06_QWEN_NEXT_EXPERIMENT_DECISION` 的取代链；每条已撤回声明与 errata 条目的对应关系；唯一的当前 NEXT_STEP。`docs/RECOVERED_EVIDENCE_MIGRATION_V1.md` 也应链接到它。

## 其他文档一致性

* **F11 (P3)**：大量报告与 Claim 矩阵的正文中，空格在数字和单词之间被系统性删除（如 “recovered316dual”“all177science”“cleanERI1worktree”“Resolvedmatch.912”），影响可读性，也容易读错数字。
* 通用 README 被复制到 16 个目录（F08），没有目录专用的导航。
* `MIGRATION_VALIDATION_REPORT.md` 的过时数字（F01）。
