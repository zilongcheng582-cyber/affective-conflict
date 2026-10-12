# 07 独立复算的独立性评估

## 四套实现的关系

| 实现 | 作者/来源 | 输入 | 与原分析的关系 |
|---|---|---|---|
| E1 原分析 `e1v2_analysis.py` | 实验作者 | 私有 attempts | — |
| E1 原 verifier `e1v2_verify.py` | 实验作者 | 私有 attempts + 原分析输出 | 不导入原分析；重新推导结局、核对哈希、journal、实际帧契约。**统计算法完全相同**（同样的 seed、同样的 batch 结构），只是写法不同 |
| E2 原分析/verifier `e1e2_analysis.py`/`e1e2_verify.py` | 实验作者 | 私有 | 同上；verifier 只复算主终点 |
| PR 公开 replay `analyses/emotiontalk_e1_video_v2/replay.py` | 迁移作者 | 公开投影 | **E1 与 E2 共用同一程序**（`emotiontalk_e2_consistent_audio_v1/replay.py` 只是 `runpy.run_path` 调用 E1 的 replay）。所以“E1 2,430 + E2 1,179 = 3,609 项检查”来自同一实现，不是两个独立复现 |
| **本审查** `review_scripts/independent_replay.py` | 第三方 | 公开投影 + main 冻结表 | 不导入、不执行任何 PR 代码；结局由标签重新推导；另外提供与 RNG 无关的精确检验和交叉实验核对 |

注意：要逐位复现 bootstrap CI，就必须使用相同的 RNG 契约（seed、抽样矩阵形状）。本审查从协议文本出发，采用不同的代码组织方式（`np.add.at`、sign-flip 分块 4×25,000），并证明结果与分块方式无关。在此之外，本审查还用**精确枚举 sign-flip**（不用随机数）和**替代 seed bootstrap**，检验了推断结论本身，而不只是比对数字。

## 分层报告（不使用单一 PASS）

| 层 | 本审查结果 | 覆盖与限制 |
|---|---|---|
| POINT_ESTIMATE_REPLAY | **PASS**（79 项） | E1/E2 全部效应、计数、剂量、分顺序效应、类别/标签转移表全部行。结局由 parsed_label 推导，0 处不一致 |
| BOOTSTRAP_REPLAY | **PASS**（100 项，≤1e−12） | 全部主/次终点的 item/dialogue CI、MC p、Holm；种子规则一致；精确 p 与 MC p 在 MC 误差内一致 |
| SCORING_AUDIT | **PASS（数值层面）/ SCORING_IMPLEMENTATION_STATIC_ONLY** | softmax、mean/sum、entropy、覆盖范围、token 数不变量。无法验证 logprob 本身和同 token 数标签的映射 |
| INPUT_CONTRACT_AUDIT | **PASS（公开 contract 内部一致）/ SOURCE_MEDIA_CONTRACT_NOT_INDEPENDENTLY_VERIFIED** | 730 行视觉契约、媒体 SHA 不变量、E2 噪声种子推导。原始媒体不可得 |
| SOURCE_RESULT_LINKAGE | **PASS**（18 项） | UID 集合、y 标签、候选顺序、DualReadable、官方簇、strata 与 main 一致；E1 CLEAN = ERI1 CLEAN（584/584）。公开投影 → 私有源的字节链接（`PUBLIC_PROJECTION_LINEAGE.csv`）只能看到登记的哈希，无法复核 |

PR 的 `SHA256SUMS.txt`：77/77 个条目在 head `5cebd14` 上校验通过（`sha256sum -c`）。

## 对抗 fixture 结果（`review_scripts/adversarial_fixtures.py`，`logs/adversarial_fixtures_result.json`）

对照组：未修改的副本在两套 replay 下都 PASS。

| # | 扰动 | PR replay | 本审查 |
|---|---|---|---|
| 1 | 同一 trial 中同 token 数的候选标签对调（happy↔sad），总和为 1 | **漏检** | **漏检**（公开数据中无法检测，需要 token_ids） |
| 1b | 候选标签对调，token 数不同（happy↔fearful） | **漏检** | 检出（token 数不变量） |
| 2 | 改结局，不改标签 | 检出（统计不符） | 检出（结局重新推导） |
| 2b | 结局与标签同时、自洽地改 | 检出（与冻结 JSON 不符） | 检出 |
| 3 | 删除一个 condition | 检出 | 检出 |
| 4 | 重复一个正式 trial | 检出 | 检出 |
| 5 | OTHER → PARSE_FAIL | 检出 | 检出 |
| 6 | 交换两种顺序的结果 | 检出（交互项） | 检出 |
| 7 | 改一个 dialogue cluster | 检出（簇数） | 检出（与 ERI1 官方映射不符） |
| 8 | 改一个候选概率（总和仍为 1） | 检出 | 检出 |
| 9 | 概率总和为 1，但标签映射错 | 同 #1 / #1b | 同 #1 / #1b |
| 10 | 边际率相同、配对不同 | 检出（CI） | 检出 |
| 11 | 只交换 y_A/y_V 列 | 检出（V_ONLY 正确率） | 检出（结局推导 + main 源表） |
| 12 | 系统性反转 SIDE 映射（自洽） | 检出（与冻结 JSON 不符） | 检出 |
| 13 | 改视觉契约中的帧索引 | **漏检**（replay 不读取该文件） | 检出 |
| 14 | E2 中视频 SHA 随音频条件变化 | **漏检**（不检查媒体不变量） | 检出 |
| 15 | E2 OTHER → PARSE_FAIL | 检出 | 检出 |

无法检测的层次：

1. 同 token 数的标签↔分数映射。
2. 公开投影与冻结 JSON 被**同时**、一致地篡改（只能靠私有源哈希链来防）。
3. 原始媒体内容，以及模型是否真的消费了这些帧（只能靠私有收据）。

PR replay 的覆盖缺口记为 **F07 (P3)**：它没有读取 `visual_input_contract.csv`，没有检查媒体身份不变量，也没有从标签重新推导结局。
