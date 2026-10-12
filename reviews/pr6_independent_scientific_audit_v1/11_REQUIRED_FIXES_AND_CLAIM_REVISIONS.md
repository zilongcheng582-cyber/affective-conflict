# 11 必需修复与主张修订

所有修复都是**文档或元数据补充**：不改任何冻结数据、协议、manifest、sigma/SNR，不重算，不需要 GPU。

## 合并前必须完成（关键 P2）

### R1 — F02：披露 E1 V1→V2 主终点修订，并补充冻结时间证据

在 `results/emotiontalk_e1_video_v2/README.md`（或新增一个 `PREDECLARATION_HISTORY.md`）中写明以下内容：

- V1 计划（`e1e2_pipeline.py:23`）以 SIDE_V 为唯一主终点，并规定 E1+ERI1 联合 Holm。
- V1 在第一次 FFmpeg 调用时失败，没有产生任何 E1 媒体或模型输出。
- V2 的 `DESIGN_SPEC_PRE_MEDIA` 改为三个共同主终点加 Holm-3。修订发生在 ERI1 和 E2 结果已知之后、任何 E1 结局出现之前。

同时公开以下字段（不含私有路径，只需哈希和时间）：

- `DESIGN_SPEC_PRE_MEDIA.json` 与 `RUN_PROTOCOL.json` 的 SHA256 和 `frozen_unix`
- 第一个 Pilot attempt 与第一个 Full attempt 的 `wall_started_unix`
- 证明 `sha256(RUN_PROTOCOL) = 03d201f1…`

把 OTHER 的 +3.77 pp 标注为：“V2 计划下的边缘结果（精确 p = 0.042）；在原 V1 计划下为次级终点，不显著（Holm p = 0.169）”。

如果无法提供时间证据，`protocol.json` 中的 PRIMARY_3_HOLM 应标注为 `PREDECLARATION_NOT_PUBLICLY_VERIFIED`。

### R2 — F01：限定 V_ONLY 操纵核查的含义

在 E1 README 或报告中加入 V_ONLY 按 y_V 的输出表，并说明以下三点：

- L2/L3 下 V_ONLY 有 141/146 和 142/146 回答 neutral；L3 的 50.7% 匹配等于 neutral 基率，非 neutral 的 y_V 命中 0/69。
- L2/L3 应称为“视觉情绪信息基本被移除”。
- RECODE 下 100% 是 DualReadable 筛选造成的。

### R3 — F03：限定 E2 的音频 RECODE 对照

在 `audio_manipulation_check.md` 和 E2 README 中加入 A_ONLY 的 CLEAN（225/225）与 RECODE（202/225）对比，说明 RECODE 管线本身降低单模态音频匹配 10.2 pp（ERI1 同样如此），主对比 SNR00−RECODE 仍然有效。

## 建议（P3，不阻止合并）

- F07：给 `replay.py` 增加以下检查：`visual_input_contract.csv` 的契约不变量（采样字段 5 个条件相同、token/grid 相同、arm 间 tensor SHA 相同、sigma = fraction×短边）、媒体身份不变量（E1 音频、E2 视频恒定）、由 `parsed_label` 推导结局。在 PR 正文中说明 3,609 项检查来自同一个 replay 实现。
- F11：把 p = 9.9999e−6 写为 “p < 1e−4（Monte Carlo 分辨率）”。
- F05：报告三类结局在每个 item 上的和为 0，说明 OTHER 不是独立证据。
- F15：报告 E2 冻结协议中 E1+ERI1 联合 Holm 的执行结果。
- F16：把梯度能量的严格单调（146/146）作为物理操纵核查，并说明 Laplacian 代理在 L3 已饱和。
- F08、F10、F12、F13、F14：在 README 的局限性中各写一句。
- F09：今后的执行代码用显式 `raise` 代替 `assert` gate。

## 科学主张的推荐措辞

**E1（主张 A+B）：**

> 在 146 个预选的、对 Qwen2.5-Omni-7B 两种模态都可读的 EmotionTalk AV 冲突 item 上，对无声视频施加强高斯模糊（σ = 短边 12%，相对重编码对照），使联合判断与视频源标签一致的比例从 54.5% 降到 13.7%（−40.8 pp，95% CI −47.6 至 −33.9）。流失的选择中约 90% 转向音频源标签。在此强度下，单模态视频判断已退化为恒定的 “neutral”。较轻的模糊（σ = 1%）产生 −17.1 pp 的部分效应。

**E2：**

> 在 225 个 A=V 一致的 item 上，0 dB 白噪声（相对重采样对照）使联合判断保持共同标签的比例从 99.1% 降到 93.8%（−5.3 pp，95% CI −8.0 至 −2.9）。被替换的回答主要是 sad/angry，与噪声对单模态音频判断的偏移方向一致。

**禁止：**

- “模型识别证据可靠性并重新加权”
- 音视频对称或不对称
- ERI1 效应的损伤/仲裁分解
- entropy 中介
- 跨模型或推广到全体 EmotionTalk
