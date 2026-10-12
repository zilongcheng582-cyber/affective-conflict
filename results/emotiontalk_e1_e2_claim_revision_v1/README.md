# E1/E2 主张修订 V1：强模糊干预下的方向性选择重分配

English title: *Directional choice reallocation under strong-blur intervention*

本目录对 PR #6 归档的 E1 V2 与 E2 证据做**主张层面的修订**，处理独立审查（`reviews/pr6_independent_scientific_audit_v1/`）中的 P2 发现 F01–F04。

修订不改动任何冻结文件：PR #6 的 78 个文件逐字节不变，冻结数据、协议、manifest、sigma/SNR 都没有改，没有重新拟合，没有模型推理，也没有使用 GPU。本目录的所有表格都由 `analyses/emotiontalk_e1_e2_claim_revision_v1/build_revision_tables.py` 从公开投影确定性生成。

## 1. E1 主结果的正式名称

**强模糊干预下的方向性选择重分配。**

> 在 146 个预选的、对 Qwen2.5-Omni-7B 两种模态都可读（DualReadable）的 EmotionTalk AV 冲突 item 上，对无声视频施加强高斯模糊（σ = 原视频短边的 12%，相对重编码 RECODE 对照）后，联合判断从视频源标签重新分配到音频源标签：
> - 与视频源标签一致的比例从 54.5% 降到 13.7%（−40.8 pp，95% CI −47.6 至 −33.9；精确配对 sign-flip p ≈ 1e−22）；
> - 在 292 个配对 slot 中，离开视频源标签的 123 个 slot 有 111 个（90.2%）转到音频源标签，12 个转到其他标签；
> - 与音频源标签一致的比例净增 +37.0 pp。

使用这个名称的理由：

- **“强模糊干预”**：L3 和 L2 不是一般意义上的“可靠性下降”。在这两个强度下，单模态视频判断已经退化为恒定的 “neutral”（第 2 节），所以效应是对**这一特定强处理**的响应。
- **“方向性选择重分配”**：证据是配对毛转移（`E1_PAIRED_JOINT_TRANSITIONS.csv`），不是两个边际率的差。净增益（+36.99 pp）与毛转移（38.0 pp）是不同的量。
- 不使用“可靠性加权”“仲裁机制”“最优整合”等机制性措辞。这些在现有证据下 NOT_ESTABLISHED（第 5 节）。

L1（σ = 1%）是唯一的分级退化水平：V_ONLY 匹配 99/146，联合 SIDE_V −17.1 pp（精确 p ≈ 5e−7）。它可以作为“部分退化下同方向重分配”的补充证据，但只有一个点，不构成剂量–响应曲线。

## 2. V_ONLY 操纵核查的正确含义（F01）

见 `E1_V_ONLY_OUTPUT_BY_SOURCE_LABEL.csv`。

| 条件 | V_ONLY 回答 neutral | 源标签匹配 |
|---|---|---|
| CLEAN / RECODE | 77/146 | 146/146 |
| BLUR_L1 | 104/146 | 99/146 |
| BLUR_L2 | 141/146 | 73/146 |
| BLUR_L3 | 142/146 | 74/146 |

- L3 的 74 次匹配全部来自 y_V = neutral 的 item（77 个中 74 个）。y_V ≠ neutral 的 69 个 item 匹配 **0/69**。L3 的 “50.7% 匹配”就是“总是回答 neutral”的基率，不是“可读性降到一半”。
- RECODE 下的 100% 是 DualReadable 筛选造成的，不是无条件的视频情绪识别准确率。
- 联合判断在 L3 **没有**跟随单模态的 “neutral” 读数：y_V = neutral 的 item 上，联合 SIDE_V 从 42.9% 降到 14.3%。所以联合效应不能只用“模糊 → neutral 偏置”来解释。

## 3. 预先声明的历史（F02）

- 原 E1 V1 计划（`analyses/emotiontalk_e2_consistent_audio_v1/source_archive/e1e2_pipeline.py:23`）以 **SIDE_V 为唯一主终点**，并规定 E1+ERI1 联合 Holm。
- V1 在第一次 FFmpeg 调用时失败（`results/emotiontalk_e2_consistent_audio_v1/historical_e1_failed_gate.json`），没有产生 E1 媒体或模型输出。
- V2 在媒体生成前写入 `DESIGN_SPEC_PRE_MEDIA`（`e1v2_cpu_gate.py:53`），把主终点改为 SIDE_V/SIDE_A/OTHER 三个共同主终点加 Holm-3。按代码逻辑，修订发生在任何 E1 结局出现之前，但在 ERI1 和 E2 结果已知之后。
- `DESIGN_SPEC_PRE_MEDIA.json` 与 `RUN_PROTOCOL.json` 的字节和 `frozen_unix` 时间戳保存在 AutoDL 私有归档中，本仓库无法复核。**公开层面的状态为 PREDECLARATION_NOT_PUBLICLY_VERIFIED。** 要闭合这一点，需要从私有归档发布这两个文件的 SHA256 和 `frozen_unix`，以及第一个 Pilot/Full attempt 的 `wall_started_unix`。

两种计划下的结论（`E1_PREDECLARATION_PLAN_SENSITIVITY.csv`，精确 p）：

| 终点 | 效应 | V2（实际执行）Holm p | V1（原计划）Holm p | 两种计划下都显著 |
|---|---|---|---|---|
| SIDE_V | −40.75 pp | 3.3e−22 | 1.1e−22（唯一主终点） | 是 |
| SIDE_A | +36.99 pp | 1.1e−18 | 4.3e−18（次级） | 是 |
| OTHER | +3.77 pp | 0.042 | **0.169**（次级） | **否** |

所以 OTHER 的 +3.77 pp 应表述为：“依赖终点修订的边缘结果”。它在每个 item 上都等于 −(ΔSIDE_V + ΔSIDE_A)，不是独立的第三个发现。E2 冻结协议中的 E1+ERI1 联合 Holm 规则执行后为 2.2e−22 和 0.00172，通过。

## 4. E2：音频 RECODE 对照与标签偏移（F03、F04）

见 `E2_AUDIO_CONTROL_AND_LABEL_SHIFT.csv`。

| 条件 | A_ONLY 源标签匹配 | 联合共同标签 slot |
|---|---|---|
| A_CLEAN | 225/225 | 448/450 |
| A_RECODE | **202/225** | 446/450 |
| A_SNR00 | 160/225 | 422/450 |

- 单是 RECODE 管线（16 kHz、单声道、float32）就让 A_ONLY 匹配下降 10.2 pp（ERI1 中同样是 146 → 132）。RECODE 不是单模态中性对照。主对比 SNR00−RECODE 仍然有效，它的含义是“在 RECODE 管线之上加入 0 dB 白噪声”。
- 噪声引入系统性的标签偏移：A_ONLY 中 angry 26→46、sad 29→46、happy 61→26。E2 的效应 = 信息丢失 + 输出类别偏移。
- E2 主结果的正式表述：在 225 个 A=V 一致的 item 上，0 dB 白噪声（相对 RECODE）使联合判断保持共同标签的比例从 99.1% 降到 93.8%（−5.3 pp，95% CI −8.0 至 −2.9）。被替换的回答主要是 sad/angry。

## 5. 主张边界

允许：

- 强模糊干预下的方向性选择重分配（E1）
- 0 dB 白噪声下的共同标签保持下降（E2）
- 与 ERI1（音频退化 → 音频侧选择减少）的方向一致性，作为同一模型内的定性比较

不允许：

- “模型识别证据可靠性并重新加权”或任何内部仲裁/最优整合机制
- 音视频对称或不对称
- ERI1 效应的“损伤 vs 仲裁”算术分解
- entropy 中介（V_ONLY entropy 随模糊不单调：0.684/0.706/0.608/0.761）
- 推广到全部 EmotionTalk（E1 = 900 个 AV 冲突中的 146 个，E2 = 600 个一致 item 中的 225 个，均按模型可读性筛选）或其他模型

## 复现

```bash
python -I analyses/emotiontalk_e1_e2_claim_revision_v1/build_revision_tables.py --repo-root . --output-dir results/emotiontalk_e1_e2_claim_revision_v1
sha256sum -c results/emotiontalk_e1_e2_claim_revision_v1/SHA256SUMS.txt
```
