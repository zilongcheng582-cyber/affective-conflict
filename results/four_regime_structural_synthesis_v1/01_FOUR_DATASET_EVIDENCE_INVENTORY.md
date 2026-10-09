# 01 四数据集 Evidence Inventory

分析来源标签：`POST_HOC_EXPLORATORY_FOUR_REGIME_SYNTHESIS_V1`。这是新建的事后探索性 CPU 综合，不扩充任何原预注册假设。
基线：`main` = `544ca0efae158df369a7b25dd110dc4254f67a7d`（ERI1 科学封版合并提交；已 `git fetch` 确认 origin/main 即此提交。本机本地 `main` 分支落后于此，故分析分支直接建自 `origin/main`）。
分支：`analysis/four-regime-structural-synthesis-v1`。只写入 `results/four_regime_structural_synthesis_v1/` 与 `analyses/four_regime_synthesis_v1/`；`git status` 仅显示这两个新目录。未启动 GPU、未加载模型、未拟合任何冻结迁移模型。

逐条计数矩阵见 `01_DATASET_CONDITION_MATRIX.csv`（37 行，计数由行级文件现算，不是抄报告）。统一行级长表：`intermediate/JOINT_LONG_V1.csv`（Phase2、ERI1 与三个目标集的联合试次，逐行可追溯到来源文件与 target_record_id）。

## 0. 检查过的目录与可用性

| 目录 / 文件 | 状态 |
|---|---|
| `manifests/{emotiontalk,mcr,listen,camer,cross_regime}/` | 存在。`cross_regime/measurement_tasks.json` 只是 B3 测量任务清单（不含结果） |
| `results/post_audit/scientific_analysis_v1/` (R1–R3) | 存在，仅引用 |
| `results/post_audit/closure_v1/` 与 `corrected_replay/` | 存在，含 B3 校正后的 zero-refit 预测（9219 行）与基线对照 |
| `results/eri1_scientific_closure_v1/` | 存在，含 2336 行试次投影 |
| `evidence/b3/`（6354 条校正 B3 测量，含完整 7-label 概率向量）、`evidence/emotiontalk/`（Phase2 2132 行、Phase3 402 行） | 存在 |
| 原始媒体、模型权重、各目标集的**原始生成文本**（MCR 全量 jsonl、LISTEN 随机选项表、Phase1 raw generation） | **不在仓库**，全部标为不可用，未补造 |

## 1. 各数据集概览

| | EmotionTalk | MCR | LISTEN | CA-MER |
|---|---|---|---|---|
| 独立样本 | 1500 panel；Phase2 706 条话语；ERI1 146 条（134 个对话簇） | 909 条音频 | 768 个底层条目（3A 387 / 3B 381 / 3C 381 行；并集 524 个 base id，三者交集 244） | 1500 个样本（audio-aligned / video-aligned / consistent 各 500） |
| 实际试次 | Phase2 2132；Phase3 402（67 话语×6 序）；ERI1 2336 | 受控 V2 共 3636 次调用（4 arm×909），**仓库内仅 1818 行联合试次行级结果** | 1149 行 | 联合 3000 行（2884 有结果，116 行 `CUDA_OOM`） |
| 模态对与顺序 | AT/AV/VT 两序；Phase3 六序；ERI1 AV 两序 + A_ONLY | A+T：`A_THEN_T`/`T_THEN_A`；另有 A_ONLY/T_ONLY | 3A 仅文本 `T_ONLY`、3B 仅音频 `A_ONLY`、3C 仅 `A_THEN_T` | A+V（静音视频）：`A_THEN_V`/`V_THEN_A` |
| 冲突类型 | **自然**：各模态独立人工标注不一致 | **人工命题型**：文本断言一个与 GT 不同的竞争标签；"音频标签"= benchmark GT，并非独立标注 | **构念型**：隐含（音频，如 ridicule/frustration）对显式（文本） | **自然伪标签冲突**：官方 `audio_pseudo_label` 对 `video_pseudo_label`；**非 ground truth** |
| 标签空间 | 7 类 | 7 类 | 音频 5 类 / 文本 8 类；响应为原生选择题字母（原生选项 + 8 个增补情绪，逐条随机序） | 16 类源本地并集（10 类不在 7-label B3 空间；音频侧 31.7%、视频侧 42.9% 的冲突标签在 7 类之外） |
| 单模态已有结果 | Phase1 T/A/V 各 1500（解析标签、熵、margin） | 仅聚合表（466/909 音频可读，909/909 文本可读）；B3 单模态各 909 | 3A/3B 即单模态；B3 单模态各 768 | **A_ONLY/V_ONLY 受控臂：仓库内无输出（静态 manifest 标 NOT_RUN）**；B3 单模态（7 类）各 1500 |
| 配对身份键 | `utterance_id`+arm | `sample_id`+order | base item id；3A 带 `_u_3A` 后缀，靠相同证据哈希匹配 | `sample_id`+order |
| OTHER 是否可还原 | **可**（解析标签在 jsonl / 投影中） | **不可**（只有类别） | **不可** | **可**（`observed_outcome` 是所选标签） |
| PARSE_FAIL / 技术失败 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 116（CUDA_OOM：audio-aligned 20、video-aligned 42、consistent 54 个试次；在分布表中单列为 TECH_MISSING） |

## 2. 关键发现（盘点阶段即已出现的结构性问题）

1. **`manifests/{mcr,listen,camer}/frozen_joint_outcomes.csv` 里嵌入的特征列（`normalized_entropy_*`、`delta_*`、`z_delta_*`）是修正前的旧特征，不是校正后的 B3。** 以 `evidence/b3/B3_CORRECTED_MEASUREMENTS_V1.csv` 按 `dataset:source_item_id` + modality 重新联接后，`delta_normalized_entropy_raw` 在 MCR / LISTEN / CA-MER 分别有 98.7% / 93.0% / 92.8% 的行与旧列相差 >1e-6（最大差 0.29 / 0.26 / 0.42）；而重新联接的结果与 `corrected_replay/B3_CORRECTED_ZERO_REFIT_PREDICTIONS_V1.csv` 内的 `delta_normalized_entropy_raw` 在 2.2e-16 内完全一致（见 `intermediate/MANIFEST_FEATURE_STALENESS_AUDIT.csv`）。后果：**本轮所有目标集特征一律用校正后的 B3；任何直接读取 manifest 特征列的分析都应视为作废。** 这只是读取方式的警示，不改写任何历史结论（历史正式指标本就来自校正重放）。注意，同一个 (evidence_hash, modality) 在 MCR/LISTEN 中对应多个候选序列的测量，必须按 `dataset:source_item_id` 联接而不能按证据哈希联接。
2. **MCR 受控 V2 只执行了"对抗型文本断言"一种文本条件。** 1818/1818 联合行的文本侧标签等于 `competitor_emotion`，0 行等于 GT；`faithful`/`neutral`/`irrelevant` 三种文本在 `canonical_arbitration.csv` 里存在，但没有任何 arm 使用它们（完整性报告：4 arm×909=3636，无其他）。缺失实验矩阵见 `tables/MCR_M4_text_condition_execution_matrix.csv`。
3. **MCR 与 LISTEN 的 OTHER 具体输出、LISTEN 的随机选项表、MCR/CA-MER 的行级单模态受控输出，仓库内都没有。** 相关分析标为 `NOT_TESTABLE_WITH_CURRENT_DATA`。
4. **CA-MER 无多模态 ground truth**：`final_label` 在受控协议中被刻意排除，只剩模态伪标签；`audio-aligned`/`video-aligned` 的语义来自官方文件名，本仓库无法独立核验。
5. **ERI1 的 CLEAN 联合行与 Phase2 的 AV 冲突行逐行一致**（292/292 试次结果完全相同），说明在该 146 条上 Phase2→ERI1 无漂移。
6. **与 EmotionTalk 的 Phase1 特征不同，目标集特征全部是 7 类 EmotionTalk 候选空间中的测量。** LISTEN 音频侧的 source-label probability 全部未定义（0/768），CA-MER 约 1/3 未定义——这是一个测量不兼容，不是缺失。

## 3. 当前缺失的科学原始字段（清单）

| 缺失字段 | 影响 |
|---|---|
| MCR / LISTEN 的 OTHER 具体标签、LISTEN 随机选项表与原始生成 | 无法区分"词汇偏好 / 隐含情绪识别失败 / 标签表示不兼容" |
| MCR 受控 A_ONLY/T_ONLY 行级输出 | 无法在 MCR 上做"单模态可读 × 联合选择"的行级分析（仅有聚合表和 B3 近似） |
| CA-MER 受控 A_ONLY/V_ONLY 输出（16 类接口） | CA-MER 上的单模态证据特征只能用 7 类 B3 近似 → 不兼容 |
| CA-MER 多模态 `final_label` | 无法验证 audio-/video-aligned 的含义，也无法区分"跟随构念"与"跟随熵" |
| LISTEN 反向顺序 `T_THEN_A` | 顺序效应不可识别 |
| Phase1 原始生成与完整概率向量 | ET 只能用熵/margin 标量 |

"当前缺失"只代表本仓库没有这些行；它们可能存在于未随仓库发布的私有归档（如 `audit/QWEN25_CAMER_CONTROLLED_V1`、`audit/QWEN25_MCR_CONTROLLED_V3`），**在决定任何 GPU 之前应先核对这些归档**（见 `05_QWEN_GPU_EXPERIMENT_DECISION.md` 的 Step 0）。

## 4. 复算入口

```
python -m analyses.four_regime_synthesis_v1.run_all
```
约 30 秒，纯 CPU，结果两次运行逐字节一致（`OUTPUT_MANIFEST.json` 哈希对照）。输入文件哈希与最近修改提交见 `RUN_PROVENANCE.json`。
