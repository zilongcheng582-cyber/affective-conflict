# 02 代码 Bug 审查

方法：先阅读代码与输入输出契约，再做 AST 级 import 安全检查，然后 (a) 在独立副本上实际运行可移植代码，(b) 用公开投影独立重算不可移植代码的输出，(c) 新增 29 个边界测试（`review_tests/test_pr4_review_boundaries.py`，29/29 通过，每个“FINDING”测试都把缺陷作为可复现行为固定下来）。

## 结论摘要

**未发现会改变任何已报告科学数字的代码 bug**：所有可检查的 join、分母、标签映射、方向编码和指标都已独立复现（见 03–06）。发现的问题集中在**验证器本身的健壮性**和若干次要一致性问题上。

## 逐模块审查记录

### `analyses/transfer_failure_integration_v1/phase4_transfer.py`（核心，静态审查 + 输出重算）
* 特征来源：`B3=.../amendment_001/outputs/B3_MEASUREMENTS_V1.jsonl`，并断言与仓库 `evidence/b3/B3_MEASUREMENTS_V1.jsonl` 哈希相同（L72）；L89–93 用 7 类概率向量重算熵、margin、源标签概率（容差 1e-12）。本审查确认：该 jsonl 与 `B3_CORRECTED_MEASUREMENTS_V1.csv` 的三个特征 6354/6354 完全相同，**使用的是 corrected B3**，没有使用 `manifests/*/frozen_joint_outcomes.csv` 中的过时特征（过时特征与 corrected 在 92.8–93.1% 的行上不同，见 `MANIFEST_FEATURE_STALENESS_AUDIT.csv`）。
* join：`bm[(dataset, source_item_id, modality)]` 唯一（断言 6354 个唯一键，L87），另外交叉校验 evidence SHA 与源标签（L99）、候选序列相等（L100）。没有按行号 join；`target_record_id` 唯一（L96）。
* `out()`（L42–50）：TECH_MISSING 的判断先于 SAME_LABEL；PARSE_FAIL 原样保留，不进入二分类分母；OTHER 仅指未匹配任何源标签的有效输出。边界测试覆盖 9 种情形 ✅。标签比较区分大小写（`'Angry'`→OTHER）——数据中 0 次出现，记为已知行为而非 bug。
* `metric()`：AUROC 用 rankdata 的 Mann–Whitney 公式，方向是 SIDE_A=1；单类时 AUROC/BA 返回 None；log loss/Brier 按 y∈{0,1} 定义，阈值 0.5 含等号。与成对比较算法一致（误差 <1e-12）✅。
* `subgroup_ci()`（L113–120）：整簇重采样（按 `source_item_id`），保持两种呈现顺序在簇内配对 ✅；去掉单类 replicate 后得到的是条件 CI（已在文档中披露）。**种子由 `tag` 哈希派生** → 同一总体在不同标签下得到不同 CI（**F07**）。
* L111 `TARGET_PREVALENCE_ORACLE_DIAGNOSTIC` 使用了目标标签——已明确标注为 oracle 诊断，文档中没有把它当作竞争基线 ✅。
* L136–138：三个基线（冻结 M0、post-audit M0+ORDER、冻结 M3a/b）分别对照 main 的 `ZERO_REFIT_BASELINE_COMPARISON_V1.csv` 校验，没有混用 ✅。

### `analyses/transfer_failure_integration_v1/validate_migration.py`（实际运行）
* 在 head 上运行：PASS，259 文件，18 组指标，最大误差 2.22e-16 ✅（`logs/validate_migration.stdout`）。
* **F04 (P2)**：全部检查都是裸 `assert`（L32、38–40、44、47、56–57、66–76、79–80、87–89、102、104）。用 `python -O` 运行时 assert 被剥离，验证器会对**已损坏**的 checkout 打印 `"status": "PASS"`。复现：`test_validator_reports_pass_on_corruption_under_python_O`（在一次性 clone 中给 `04_TRANSFER_CLAIM_BOUNDARY_MATRIX.md` 追加 1 个字节 → 返回码 0、输出 PASS）。PR 把这个验证器当作 clean checkout PASS 的证据，所以这是验证逻辑缺陷，不只是代码风格问题。
* **F09 (P3)**：(a) 不检查清单覆盖率：一个已提交、但不在 SHA256SUMS 中的额外文件仍然 PASS（`test_validator_does_not_detect_unlisted_new_files`）；(b) `metrics()` 遇到单类时抛 `ZeroDivisionError`，而不是报告“未定义”（`test_single_class_validate_migration_crashes`）；(c) L43–44 断言 `base..HEAD` 全部是 `A`——PR 合并后，只要 main 上之后的任何提交修改了文件，这个验证器就会失败（合并后的复用性问题）。
* 指标：BA 阈值 `>=.5`；log loss clip 1e-12；与独立实现结果一致 ✅。

### `analyses/recovered_evidence_scientific_analysis_v1/analysis.py`（静态审查 + import + 输出重算）
* MCR：`y_text_adversarial` 由 adversarial 提示文本用正则抽取（L98），并断言 ≠ GT——**不存在**用目标标签定义文本条件的循环定义 ✅。四条件完整性、音频 SHA 一致性均有断言。聚类单位是音频 SHA（943 簇），重复音频不被当作独立样本 ✅。
* `cluster_ci`：按簇求和后求比率，重采样整簇 ✅；`equal_cluster` 是另一个 estimand，文档已说明 ✅。
* `paired(..., cluster_null=True)`：对簇和做符号翻转，p=(k+1)/(B+1)，有 Monte Carlo 下限 ✅；`holm` 与手算一致 ✅（测试）。
* CA-MER（L142–202）：item bootstrap，没有声称说话人簇 ✅；`zero_binary_bootstrap_draws` 已披露。
* LISTEN（L203–）：Fisher 精确检验 + 独立 bootstrap，标注为“选择关联，非因果” ✅。
* `truth()` 与 phase4 的 `truth()` 对 `'1'` 判断不一致 → **F14 (P3)**（当前数据中未触发）。

### `analyses/four_regime_synthesis_v1/*`（实际完整重跑）
* `python -m analyses.four_regime_synthesis_v1.run_all` 在独立 clone 中运行（约 48 秒，CPU）：**61/61 个科学输出与已提交版本逐字节一致**；只有 `RUN_PROVENANCE_V2.json`（时间、平台、HEAD）和 `OUTPUT_MANIFEST_V2.json`（多扫入了后加的 README）不同 ✅。说明结果确定、可复现。
* 特征：`a01_build_tables.py` 明确从 `B3_CORRECTED_MEASUREMENTS_V1.csv` 取特征，并输出过时特征审计 ✅。
* `common.normalized_entropy_from_probs` 除以 log(7)，只适用于 7 类向量；代码中没有用于 16 类（测试固定了这一点）✅。
* `RUN_PROVENANCE` 字段 `base_commit_main` 实际记录的是 `HEAD` → **F18 (P3)** 命名问题。

### 历史归档脚本（`historical_evidence_reconciliation_v2/*_original/*`、`finalize.py`、`phase4_finalize.py` 等）
* 多数在模块顶层执行：会遍历 `/root/autodl-tmp/affective-conflict`，写 `O/` 目录，并**追加修改 AutoDL 的 `docs/PROJECT_STATE.md` 等导航文件**（`phase4_finalize.py:208–209`、`finalize_expanded.py:49–52`）。在 clean checkout 中路径不存在，会立即失败，不会造成破坏；README 已警告“不要执行 finalizer”。→ **F16 (P3)** 安全备注。
* 未发现：网络访问、`torch`/`transformers`/`from_pretrained`/CUDA、`rmtree`/`os.remove`、`eval/exec`、`pickle`。

## 可安全导入的 CPU 模块

在空的 sandbox 目录中 import（`-B`，无副作用）：`analysis`、`phase4_transfer`、`phase4_finalize`、`phase4_seal`、`phase4_supplement`、`validate_migration` —— 6/6 OK，与 PR 声明一致。

## 4.1/4.2 清单逐项结果

| 检查项 | 结果 |
|---|---|
| 错误 join key / many-to-many | 无。MCR 纯音频 SHA join 本来会对 3 个哈希产生歧义（7 个条目），但代码使用 source_index+路径+哈希+标签 join（909/909 `identity_match`）✅ |
| 重复记录膨胀 | 无（所有键唯一性都有断言，并独立复核） |
| 不稳定排序 / 行号 join | 无（按 ID join；输出排序基于 sorted 键；四区制重跑逐字节一致） |
| dtype 混用 | CSV 中的布尔字符串经 `truth()` 处理；数值字符串被 numpy 强制转换（测试）✅ |
| source-label 与 observed-label 混淆 | 无（重算 0 不一致） |
| 顺序编码取反 | 无：`FIRST_IS_MODALITY1 = presentation_order` 以 `A_` 开头；MCR 均值项 −0.4433 精确复现 |
| 候选顺序与预测错配 | 无（L100 断言 A/V 候选序列相同） |
| missing 被自动丢弃 | 否：TECH_MISSING / PARSE_FAIL / OTHER 留在冲突分母中，coverage 显式报告 |
| 技术失败被记为 OTHER | 否（CA-MER 116 个 OOM → TECH_MISSING，独立重算 0 不一致） |
| PARSE_FAIL 被当作有效预测 | 否 |
| 同一 item 跨条件被当作独立样本 | Transfer 按 item 簇；MCR 按音频 SHA 簇；LISTEN 混合路线沿用 main 冻结的 UID 簇定义 ✅ |
| bootstrap 后仍沿用原始权重 | 否（基于索引重采样） |
| 极端不平衡 / 单类 | phase4 返回 None；validator 崩溃（F09） |
| 先筛选后当确认性检验 | 新分析全部标为 POST_HOC_EXPLORATORY；子组明确“cannot redefine success” ✅ |
