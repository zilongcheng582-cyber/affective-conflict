# 02 E1 视频干预与模型输入契约

状态：

- `INPUT_CONTRACT_AUDIT` = **PUBLIC_CONTRACT_INTERNALLY_CONSISTENT**（730 行全量，0 个问题）
- `SOURCE_MEDIA_CONTRACT_NOT_INDEPENDENTLY_VERIFIED`（原始/派生 MP4 不可访问，无法重新解码）

## 5.1 FFmpeg 与物理视频（静态审查 `e1v2_cpu_gate.py`）

| 要求 | 代码证据 | 判定 |
|---|---|---|
| sigma 按每条视频原始短边计算 | `:94` `sigma_native = fraction*min(width,height)`，meta 取自原视频 ffprobe | 正确。独立复算 730 行 `sigma_native == fraction×min(w,h)`，0 偏差 |
| sigmaV、planes 生效 | `:99` `gblur=sigma=s:sigmaV=s:steps=3:planes=15`（15 = 全部平面） | 命令正确；实际效果仅能由 `model_frames_sha256` 与 RECODE 不同来间接证实（730 行中 438 个模糊行全部不同） |
| RECODE 与模糊走同一非模糊流程 | `:98-100`：同一命令模板，仅模糊条件多一个 `-vf` | 正确 |
| 隐藏缩放/裁剪/补帧/丢帧 | `:108-110`：所有帧 PTS 与原视频差 ≤1e-6，帧数、宽、高、`r_frame_rate`、`nb_frames`、时长都断言相等 | 由代码保证。公开 contract 中 5 个条件的采样字段完全相同 |
| 时间戳修复改变抽帧位置 | `:111`：qwen reader 的 `frames_indices`、总帧数、`sample_fps` 必须与原视频一致 | 由代码保证；公开字段一致 |
| 音轨重复输入 | `-an`；`probe` 断言 0 条音频流；`use_audio_in_video=False` | 无 |
| ffprobe PASS 但 Qwen 实际消费帧不同 | runner `:52-61` 在推理时对实际 4D 帧张量做 SHA 比对；verify `:46` 复核所有非 A_ONLY 记录 | 运行时防护存在。公开层面只能检查收据（原件不可得） |
| 重编码改变颜色/位深 | `yuv420p` + CRF 0（libx264 8-bit 无损） | **F08 (P3)**：146 个 item 中 144 个的 CLEAN 与 RECODE 模型帧 SHA 完全相同；2 个不同：`G00003_16_02_009`（源 1080×1922）、`G00003_54_02_002`（源 608×1080）。差异极小（锐度代理差 <1e-2），两者的 V_ONLY/联合标签相同。RECODE 才是正确基线，所以主对比不受影响 |
| L3 是否应描述为“信息破坏” | 见下文 | **是（F01）** |

### 模型输入尺度下的模糊强度（由公开 contract 计算）

全部 146 个 item 的模型帧尺寸为 `[T,3,1008,560]`。把 native sigma 换算到模型输入像素（缩放比 = 560/短边）：

| 条件 | sigma（模型像素，短边 560） | 占短边比例 |
|---|---|---|
| BLUR_L1 | 5.6 | 1% |
| BLUR_L2 | 22.4 | 4% |
| BLUR_L3 | 67.2 | 12% |

Qwen2.5-Omni 的视觉 patch 为 14 px（合并后 28 px）。L3 的 sigma 约为 2.4 个合并 patch，有效核宽（±3σ）约 400 px，接近整幅画面宽度。

V_ONLY 的输出直接说明了 L2/L3 的性质：

| 条件 | V_ONLY 输出中 "neutral" 的比例 | V_ONLY 源标签匹配 |
|---|---|---|
| RECODE | 77/146 | 146/146 |
| BLUR_L1 | 104/146 | 99/146 (67.8%) |
| BLUR_L2 | **141/146** | 73/146 (50.0%) |
| BLUR_L3 | **142/146** | 74/146 (50.7%) |

L3 的 74 次匹配，几乎全部来自 y_V = neutral 的 77 个 item（命中 96.1%）；69 个 y_V ≠ neutral 的 item 命中 **0/69**。所以 L3 的 “50.68% 源标签匹配”就是“总是回答 neutral”的基率（77/146 = 52.7%），不是“可读性降到一半”。

结论：**L2 和 L3 应描述为视觉情绪信息基本被移除（V_ONLY 退化为单一回答），而不是一般自然场景中的“可靠性下降”。L1 是唯一的分级退化水平。**

锐度代理：Laplacian 方差在 L3 有 70/146 个 item 被标记为非单调（中位数 L2 = 1.052，L3 = 1.048，已到地板）。梯度能量在 146/146 个 item 中严格单调（L3 < L2）。这说明物理退化确实单调，Laplacian 代理只是饱和了。V1 gate 中原有的严格单调断言（`E2/e1e2_media_gate.py:121`）在 V2 被改为描述性标记（`e1v2_cpu_gate.py:58,116`）。这一改动在媒体生成前写入 `DESIGN_SPEC_PRE_MEDIA`，**F16 (P3)**。

## 5.2 模型实际消费的帧（`visual_input_contract.csv` 全量 730 行）

独立检查（`review_scripts/independent_replay.py::visual_audit`）：

| 检查 | 结果 |
|---|---|
| 730 = 146×5 行，唯一 | PASS |
| contract 中的 `video_sha256` 与 manifest 对应条件一致 | 0 不一致 |
| 5 个条件间 `sampled_frame_indices`、`model_sampled_timestamps`、`model_frame_shape`、`sample_fps`、`duration`、源宽高、`time_base` 完全相同 | PASS |
| 每个 arm（V_ONLY/A_THEN_V/V_THEN_A）的 `tokens`、`video_grid_thw`、`visual_tensor_shape` 与 RECODE 相同 | 0 不一致 |
| 同一条件内三个 arm 的 `visual_tensor_sha256` 相同 | PASS |
| `audio_input_count`：V_ONLY 为 0，联合 arm 为 1 | PASS，但这个值是**写死**的（`e1v2_cpu_gate.py:122`），不是测量值（F10, P3） |
| 模糊帧 SHA ≠ RECODE | 438/438 |
| 采样时间戳在时长范围内 | PASS |
| 每段视频的帧数 | 4 帧：76 个 item（52%）；6–26 帧：其余 70 个 |

区分：

- **A. CLEAN vs RECODE**：144/146 的帧张量与 visual tensor 逐位相同，2/146 有微小差异（F08）。联合与 V_ONLY 的标签 292+146 个 slot 全部相同。
- **B. RECODE vs BLUR 的非模糊契约**：抽帧数、时间点、几何、token 数、grid 全部相同。没有发现非预期差异。
- **C. 预期的像素内容差异**：438/438 不同，符合预期，不视为失败。

注意：52% 的 item 只有 4 帧，也就是 2 个时间 grid。在这些短片上，模型的视觉证据本来就很少。

## 5.3 V_ONLY

- 目标标签是冻结的 y_V（`e1v2_analysis.py:46`）。146/146 个 item 与 main 的 `source_measurements.csv` 一致。
- RECODE/CLEAN 下 100% 匹配是**选择造成的**：样本是历史 DualReadable_AV（Phase 1 中 V_ONLY 判对），再加上贪心解码和逐位相同的输入。E1 V2 的 CLEAN 结果与 ERI1 的 CLEAN 结果逐 item、逐 arm 完全一致（584/584 slot，`logs/predeclaration_sensitivity_result.json`），这一点得到了直接证实。
- 各条件之间的候选列表、prompt 和解析器都不变（同一个 UID 绑定序列，同一个 `build_messages`）。
- 可读性测量和联合选择分别从不同 arm 独立计算。
- entropy 来自七候选连续评分，见 05。

**不得把 V_ONLY 源标签匹配率称为无条件的视频情绪识别准确率。** 它是一个对已选样本的条件测量：基线 100% 是选择造成的，L2/L3 的约 50% 是 neutral 的基率。
