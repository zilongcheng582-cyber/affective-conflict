# 04 E2 实现与统计审查

估计量：P(pred == shared | A_SNR00) − P(pred == shared | A_RECODE)，225 个 item，两种顺序等权。

## 身份与实施

| 项 | 结果 |
|---|---|
| 225 个 item 与 main `EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json` 的 `consistent_utterance_ids` 一致 | PASS |
| y_A == y_V（225/225）；y_A/y_V/y_T/候选序列与 main `source_measurements.csv` 一致；DualReadable_AV 全部为 TRUE | PASS |
| 127 ALL_SAME（y_A = y_T）/ 98 A_EQ_V_NE_T | PASS |
| 225×15 = 3375 个唯一 slot；attempts 全部 1 次，0 失败 | PASS |
| 177 个对话簇 = UID 前两段；源 gate 由官方 `mm.csv` 路径构造（`e1e2_media_gate.py:81-85`） | PASS |
| 视频 SHA 在全部条件下恒定（每个 item 1 个） | PASS |
| 每个 item 有 5 个不同的音频文件；`target_snr_db` 标签为 ''/''/20/10/0 | PASS |
| 每个 item 一个噪声种子（嵌套设计），等于 `design.derived_seed('E2_AV_CONSISTENT_AUDIO_DEGRADATION_CONTROL_V1', uid, 'AUDIO_WHITE_NOISE_V1')`，且与 ERI1 的种子不相交 | PASS（用 main 的冻结 `design.py` 独立重算） |
| SNR 读回 | gate 断言 \|实测 − 目标\| < 1e−4 dB（`e1e2_media_gate.py:132`）。公开投影不含波形，所以 UNVERIFIED_DUE_TO_SOURCE_ACCESS |
| A_ONLY 测量只用于测量，不参与样本筛选 | 是（分析中只作为 secondary；没有任何筛选逻辑使用它） |

## 独立复算（`logs/independent_replay_result.json`）

| 终点 | 估计值 | item CI | 对话 CI | MC p | 精确 p |
|---|---|---|---|---|---|
| **PRIMARY** shared retention SNR00−RECODE | **−0.0533333333** | [−0.0800, −0.0289] | [−0.0815, −0.0284] | 3.0e−5 | 2.9e−5 |
| OTHER SNR00−RECODE | +0.0533 | [0.0289, 0.0800] | — | 2.0e−5 | 2.9e−5 |
| CLEAN−RECODE（联合，pipeline） | +0.0044 | [−0.0044, 0.0133] | — | 0.625 | 0.625 |
| ORDER_INTERACTION | +0.0444 | [0.0133, 0.0800] | — | 0.0127 | 0.0129（Holm 0.076） |
| SNR10−RECODE | −0.0200 | [−0.0378, −0.0044] | — | 0.0305 | 0.0313（Holm 0.153） |
| SNR20−RECODE | −0.0044 | — | — | 0.747 | 0.75 |
| 序数斜率 | −0.0176/级 | [−0.0267, −0.0096] | — | 1e−5 | 1.3e−5 |
| A_ONLY 源标签匹配 SNR00−RECODE | −0.1867 | [−0.2578, −0.1156] | — | 1e−5 | 6.5e−7 |
| A_ONLY entropy | +0.0356 | [0.0184, 0.0532] | — | 4e−5 | 连续值，未做精确计算 |

全部与 PR 报告值在 1e−12 内一致。

- 共同标签保持率轨迹：CLEAN 99.56% → RECODE 99.11% → SNR20 98.67% → SNR10 97.11% → SNR00 93.78%。
- 配对转移 RECODE→SNR00：A_THEN_V 中 SHARED→OTHER 8、OTHER→SHARED 1；V_THEN_A 中 SHARED→OTHER 17。
- 分层（描述性，精确 p 未校正）：ALL_SAME −3.15 pp（p = 0.031）；A_EQ_V_NE_T −8.16 pp（p = 0.0013）。
- 事后按 15 个录制组做 cluster bootstrap：[−0.081, −0.029]，结论稳健。

### 互补记账

PARSE_FAIL = TECH_FAILURE = 0，所以每个 item 都有 ΔSHARED ≡ −ΔOTHER（已独立确认）。−5.33 pp 与 +5.33 pp 是**同一个量的两面**，不能作为两条独立的机制证据。

OTHER 的分类：`parsed_label != y_A` 且属于合法的 7 个标签时归为 OTHER（`e1e2_analysis.py:17`）；解析失败单独归为 PARSE_FAIL（测试 `test_shared_other_parsefail_tech`）。SNR00 下联合 arm 的 28 个 OTHER slot 中，`sad` 12 个、`angry` 10 个，只有 6 个等于 y_T（文本本身并未输入模型）。

## 发现

### F03 (P2, CONFIRMED_DESIGN_LIMITATION)：音频 RECODE 不是单模态中性的管线对照

| A_ONLY 源标签匹配 | 计数 |
|---|---|
| A_CLEAN | **225/225 (100%)** |
| A_RECODE | **202/225 (89.8%)** |
| A_SNR20 | 205/225 |
| A_SNR10 | 191/225 |
| A_SNR00 | 160/225 (71.1%) |

单是 RECODE 管线（重采样到 16 kHz、单声道、float32 WAV，`reliability_v1/audio.py`）就让 A_ONLY 匹配下降 10.2 pp。main 上 ERI1 的冻结数据同样如此（CLEAN 146 → RECODE 132）。所以这是继承自冻结音频规范的已有性质，不是 PR #6 引入的 bug。

影响：

- 主对比 SNR00−RECODE 的定义本来就是“在 RECODE 管线之上加噪声”，**数值和因果对比都不受影响**。
- 但 `audio_manipulation_check.md` 只报告 SNR00−RECODE（−18.67 pp），不能据此说 RECODE 是与 CLEAN 等价的对照。联合 arm 的 CLEAN−RECODE 只差 +0.44 pp，是因为一致的视频在联合判断中掩盖了音频的变化。
- 需要文档限定，不需要重算。

### F04 (P2, CONFIRMED_DESIGN_LIMITATION)：噪声引入系统性的标签偏移

A_ONLY 输出分布（RECODE → SNR00）：angry 26 → 46，sad 29 → 46，happy 61 → 26，neutral 102 → 101。白噪声不只是去除信息，还把输出推向 angry/sad。所以 E2（以及 ERI1）的音频退化效应 = 信息丢失 + 输出类别偏移，不能解释为纯粹的“可靠性”操纵。

## 判定

- `E2_CODE_AUDIT`：未发现 bug。
- 数值层面全部复现。
- E2 的主终点与冻结协议一致（single primary，`e1e2_pipeline.py:23`，`protocol.json` `source_protocol_reviewed_fields.primary`）。

E2 证据只支持一句话：在 225 个预选的 A=V 一致 DualReadable item 上，对音频加入 0 dB 白噪声（相对 RECODE）使联合输出与共同标签一致的比例下降 5.3 pp（基线 99.1%，接近天花板）。
