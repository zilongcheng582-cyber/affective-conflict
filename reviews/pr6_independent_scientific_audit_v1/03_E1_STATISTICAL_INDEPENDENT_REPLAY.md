# 03 E1 统计独立复算

实现：`review_scripts/independent_replay.py`（新写，不导入 PR 的任何代码）。日志见 `logs/independent_replay.log`，完整数值见 `logs/independent_replay_result.json`。

做法：结局由 `parsed_label` 对冻结的 y_A/y_V **重新推导**，不读取 PR 的 `outcome` 列（之后再与之比对）。剂量斜率用 `np.polyfit`，聚类和用 `np.add.at`，sign-flip 分块为 4×25,000（原代码为 100×1,000），以检验 RNG 流的分块不变性。另外实现了**精确**配对 sign-flip（对 2^146 个符号向量做动态规划，不用随机数）。

## 7.1 主结果

| 终点 (L3−RECODE) | 估计值 | item CI（合同复算） | 对话 CI | MC p | **精确 p** | Holm（MC） | Holm（精确） |
|---|---|---|---|---|---|---|---|
| SIDE_V | −0.4075342466 | [−0.4760, −0.3390] | [−0.4764, −0.3379] | 1.0e−5（MC 下限） | **1.1e−22** | 3.0e−5 | 3.3e−22 |
| SIDE_A | +0.3698630137 | [0.3014, 0.4384] | [0.2986, 0.4433] | 1.0e−5（MC 下限） | **5.4e−19** | 3.0e−5 | 1.1e−18 |
| OTHER | +0.0376712329 | [0.0068, 0.0719] | [0.0067, 0.0719] | 0.04168 | **0.04230** | 0.04168 | 0.04230 |

全部与 PR 的数值在 ≤1e−12 内一致。点估计、CI、p、Holm 共 100 项 BOOTSTRAP_REPLAY 检查全部通过。

- 换用 seed 777、20,000 次重抽样的替代 bootstrap：SIDE_V 对话 CI [−0.4757, −0.3378]，说明 CI 在 Monte Carlo 意义上稳定。
- 技术缺失 bounds：0 个技术失败，因此 bounds 退化为点估计（已独立确认）。

### 原始计数（每个顺序 146 个 slot）

| 条件 | A_THEN_V (V/A/O) | V_THEN_A (V/A/O) | V_ONLY 源标签匹配 |
|---|---|---|---|
| CLEAN | 86/54/6 | 73/71/2 | 146 |
| RECODE | 86/54/6 | 73/71/2 | 146 |
| BLUR_L1 | 59/75/12 | 50/85/11 | 99 |
| BLUR_L2 | 16/122/8 | 31/105/10 | 73 |
| BLUR_L3 | 14/126/6 | 26/107/13 | 74 |

剂量轨迹（两种顺序等权的 SIDE_V 率）：54.45% → 37.33% → 16.10% → 13.70%。已独立复现。

### RECODE→L3 配对转移（slot 级，292 个配对 slot）

| 转移 | A_THEN_V | V_THEN_A | 合计 |
|---|---|---|---|
| SIDE_V→SIDE_A | 70 | 41 | **111** |
| SIDE_V→OTHER | 4 | 8 | 12 |
| SIDE_V→SIDE_V | 12 | 24 | 36 |
| SIDE_A→SIDE_V | 2 | 2 | 4 |
| SIDE_A→OTHER | 0 | 4 | 4 |
| SIDE_A→SIDE_A | 52 | 65 | 117 |
| OTHER→SIDE_A | 4 | 1 | 5 |
| OTHER→OTHER | 2 | 1 | 3 |

**净变化与毛转移的区别：**

- SIDE_V：毛流出 123，毛流入 4，净 −119/292 = **−40.75 pp**。
- SIDE_A：毛流入 116（111 来自 SIDE_V，5 来自 OTHER），毛流出 8，净 +108/292 = **+36.99 pp**。
- GROSS_SIDE_V_TO_SIDE_A = 111/292 = **38.0 pp**。在全部 SIDE_V 流出中，90.2%（111/123）流向 SIDE_A，9.8%（12/123）流向 OTHER。
- NET_SIDE_A_GAIN（36.99 pp）与毛转移 SIDE_V→SIDE_A（38.0 pp）数值接近，但不是同一个量。“36.99 pp 全部来自 SIDE_V→SIDE_A”的说法不成立：其中有 5 个来自 OTHER，并有 8 个反向流出。“视频侧选择主要转向音频侧”在 slot 级配对转移上得到支持。

基线结构（RECODE 时每个 item 的 SIDE_V 率）：

- 0：51 个 item。这些 item 的 SIDE_V 已在地板，不可能下降。
- 0.5：31 个 item。
- 1：64 个 item。

可能的最大下降为 54.45 pp，观测下降为其 75%。

## 7.2 统计推断审查

| 问题 | 结论 |
|---|---|
| sign-flip 以 item 为单位 | 是。两种顺序先在 item 内平均，再翻转符号（`e1v2_analysis.py:33,9`） |
| 两个 order 是否被当成独立观测 | 否 |
| item bootstrap 是否保持整条 item | 是（对 item 差值向量重抽样） |
| dialogue bootstrap 是否保留簇内全部 item | 是。比值估计 Σ簇和/Σ簇大小 是按 item 加权的估计量（测试 `test_cluster_ratio_is_item_weighted`） |
| 134 个簇是否来自官方元数据 | 是。与 main 的 ERI1 `DIALOGUE_CLUSTER_MAP_V1.csv`（`mapping_source_sha256 = ad791…` 即官方 `mm.csv`）逐 item 一致 |
| 演员/录制组重复 | 134 个对话嵌套在 **15 个顶层录制组**（G000xx）中，统计没有处理组/演员层的依赖。事后（非冻结）按 15 组做 cluster bootstrap：SIDE_V CI [−0.481, −0.340]，SIDE_A [0.304, 0.448]，OTHER [0.0074, 0.0736]。结论稳健（F12, P3） |
| sign-flip 零假设条件 | 配对差在 H0 下关于 0 对称（条件可交换）。对确定性模型和固定输入，这是一个关于“处理标签可交换”的随机化型假设。这里没有真正的随机分配，只是条件内比较，所以 p 值应解释为对这 146 个固定 item 的条件推断 |
| Monte Carlo 与精确 | PR 报告的 p = 9.9999e−6 是 MC 分辨率下限 1/(100000+1)，不是精确 p。精确 p ≈ 1e−22。建议写成“p < 1e−4（MC 分辨率）”（F11, P3）。OTHER 的 MC p 0.0417 与精确 0.0423 一致 |
| Holm family 与冻结协议一致 | 与 V2 冻结协议一致（3 个主终点 + 11 个次级终点）。与 V1 计划不一致，见 06 / F02 |
| CI 与 p 的口径 | CI 为百分位 bootstrap，p 为 sign-flip，二者口径不同但方向一致。OTHER 的 item CI 下界 0.0068 > 0，与 p = 0.042 一致 |
| 三类之和 | 每个 item 的 ΔSIDE_V+ΔSIDE_A+ΔOTHER ≡ 0（因为 PARSE_FAIL 和 TECHNICAL_FAILURE 均为 0）。OTHER 是前两者的线性函数，所以三个“显著主终点”**不是三个独立发现**（F05, P3） |
| PARSE_FAIL 是否被排除 | 没有排除。实际 0 个 |
| 缺失 bounds 是否保守 | lower = d − TF(RECODE)，upper = d + TF(L3)，对每个类别都是正确的最坏/最好情形。实际 0 缺失 |

## 7.3 剂量与顺序

- 序数斜率定义为对 x = 0,1,2,3（RECODE, L1, L2, L3）的 item 内 OLS 斜率，等价于 `(y·[−1.5,−0.5,0.5,1.5])/5`（已用 polyfit 独立验证）。SIDE_V 斜率 = −0.1435/级。这是**每个序数级**的变化。三个级别的物理 sigma 不等距（1%、4%、12%），L2→L3 已饱和（V_ONLY 都回答 neutral），所以不能解释为“每单位物理可靠性的因果效应”。
- 顺序交互：定义为 (L3−RECODE | A_THEN_V) − (L3−RECODE | V_THEN_A)，SIDE_V = −0.1712（A_THEN_V −49.32 pp，V_THEN_A −32.19 pp），符号方向已核对。MC p = 5.9e−4，精确 p = 7.4e−4。11 项 secondary Holm 后：MC 0.00354（PR 报告值）；用精确 p 计算约 0.0045，仍 < 0.05。
- 两种顺序的候选映射：候选序列在指令末尾、两种顺序相同（`core.build_messages` 中候选与模态顺序无关）。
- 描述性的分顺序效应（`order_effects.json`）全部复现。A_THEN_V 中 SIDE_V −49.3 pp 全部转为 SIDE_A（+49.3），OTHER 0；V_THEN_A 中 SIDE_V −32.2，SIDE_A +24.7，OTHER +7.5。

## 7.4 交叉实验一致性

E1 V2 的 CLEAN 与 main 上 ERI1 的 CLEAN 在 146 item × 4 arm = 584 个 slot 上**逐一相同**（`review_scripts/predeclaration_sensitivity.py`）。这是一项独立的执行可重复性证据：同一模型、同一原始媒体、同一代码在不同实验中给出完全相同的结果。
