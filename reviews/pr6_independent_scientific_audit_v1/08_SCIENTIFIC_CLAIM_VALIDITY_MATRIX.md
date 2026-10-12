# 08 科学主张有效性矩阵

等级：SUPPORTED / SUPPORTED_WITH_LIMITATIONS / NOT_ESTABLISHED / CONTRADICTED / INSUFFICIENT_EVIDENCE

| 主张 | 判定 | 依据 | 允许的表述 | 不允许的表述 |
|---|---|---|---|---|
| **A** 视频退化导致视频侧选择减少 | **SUPPORTED_WITH_LIMITATIONS** | 干预只改视频文件（音频 SHA 恒定，帧采样/几何/token 契约相同，RECODE 基线）；同一模型确定性解码，条件内配对比较；SIDE_V −40.75 pp，精确 p ≈ 1e−22，聚类稳健；SIDE_V 在 V1 和 V2 计划下都是主终点 | “在 146 个预选的 DualReadable AV 冲突 item 上，对 Qwen2.5-Omni-7B 的无声视频施加 FFmpeg 高斯模糊（σ = 短边 12%，相对 RECODE），使联合输出与视频源标签一致的比例下降 40.8 pp（95% CI −47.6 至 −33.9）。” | “视频可靠性下降导致……”（L3 是视觉信息基本被移除，F01）；外推到全部 EmotionTalk 或其他模型 |
| **B** 减少的视频侧选择主要转向音频 | **SUPPORTED_WITH_LIMITATIONS** | 配对毛转移 SIDE_V→SIDE_A = 111/292 slot，占 SIDE_V 流出的 90.2%；SIDE_V→OTHER 12；净 SIDE_A +36.99 pp，含 5 个 OTHER→SIDE_A 和 8 个反向流出 | “SIDE_V 流出的 90% 流向 SIDE_A（GROSS 38.0 pp），NET_SIDE_A_GAIN = 36.99 pp。” | 把 36.99 pp 写成转移记录数；把 OTHER +3.77 pp 写成独立的第三个确认性发现（F02/F05） |
| **C** 可靠性敏感的仲裁 | 行为层：**SUPPORTED_WITH_LIMITATIONS**；内部仲裁 / 最优加权 / entropy 中介：**NOT_ESTABLISHED** | ERI1（音频退化 → SIDE_A −10.96）与 E1（视频退化 → SIDE_V −40.75）方向一致：被退化的一侧被选得更少。但 (1) 退化同时改变单模态可读性（V_ONLY 坍缩为 neutral，A_ONLY 偏向 angry/sad，F04）；(2) 输入 OOD；(3) entropy 不单调（F06）；(4) 没有对内部表征的干预 | “输入质量敏感的观察行为”；“具体干预导致的联合选择变化”；“模态间的方向性重分配” | “模型主动识别证据可靠性并重新加权”“最优/贝叶斯加权”“entropy 中介” |
| **D** 音视频可靠性响应对称/不对称 | **NOT_ESTABLISHED** | ERI1 的 SNR 0 dB 与 E1 的 σ = 12% 没有共同的可靠性尺度。L3 的 V_ONLY 已坍缩（视觉信息约等于 0），而 ERI1 SNR00 的 A_ONLY 仍有 61%（89/146）匹配。两种退化强度显然不等价 | 定性方向比较：“两种退化都减少了被退化模态一侧的选择” | “视频权重响应是音频的约 4 倍”“高度不对称” |
| **E** E2 排除了通用输入损伤解释 | **NOT_ESTABLISHED**（作为排除论证）；E2 自身效应 **SUPPORTED_WITH_LIMITATIONS** | E2 显示在一致样本中也存在 −5.33 pp 的退化效应（基线 99.1%，天花板）。总体（225 个一致 vs 146 个冲突）和终点（共同标签保持 vs 冲突侧选择）都不同；音频 RECODE 本身降低 A_ONLY 10 pp（F03）；噪声引入 angry/sad 偏移（F04） | “在一致样本中，0 dB 噪声也使共同标签保持率下降 5.3 pp，所以一般性的输入损伤至少部分存在。” | “ERI1 中 5.33 pp 属于一般损伤，剩余 5.63 pp 属于纯粹仲裁”；“E2 已控制一切输入分布变化” |
| **F** 推广到全部 EmotionTalk | **NOT_ESTABLISHED** | panel 1,500 → AV 冲突 900 → DualReadable 冲突 146（16.2%）；AV 一致 600 → DualReadable 225（37.5%）。DualReadable 是按模型的单模态正确性筛选的，属于模型条件化的子总体；只有 15 个录制组 | “固定的 146 个（或 225 个）模型可读 item 的 ITT” | 推广到自然 AV 冲突、全部 EmotionTalk、其他数据集 |
| **G** E1/E2 提供独立的通用机制复现 | **NOT_ESTABLISHED** | 同一模型、同一数据集、同一代码库、同一 prompt。E1 与 ERI1 是同一总体上的**互补干预**（不同模态），E2 是**补充对照**（不同总体）。没有跨模型或跨数据集证据 | “同一模型内的 intervention replication（方向）+ complementary control” | “cross-model generalization”“机制复现” |

## 关于 E1 OTHER 与“三个显著主终点”

- OTHER 在每个 item 上等于 −(ΔSIDE_V + ΔSIDE_A)。
- 它的精确 p = 0.0423，在 V1 计划下 Holm p = 0.169。
- 它的确认性地位依赖未披露的终点修订（F02）。

所以应写成：“SIDE_V 与 SIDE_A 的变化在任何预设计划下都显著；OTHER 的小幅增加（+3.8 pp）只在 V2 计划下边缘显著。”
