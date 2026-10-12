# 06 预先冻结与 Pilot 隔离

## E1：主终点历史（关键）

### 证据 1：原 E1（V1）计划是 SIDE_V 唯一主终点

`analyses/emotiontalk_e2_consistent_audio_v1/source_archive/e1e2_pipeline.py:23`（同一个 `freeze()` 模板，E2 用它冻结了 `E2_FROZEN_PROTOCOL`，代码本身已列入 E2 冻结协议的 `locked_files`）中有：

- `'primary': 'P(SIDE_V|V_BLUR_HIGH)-P(SIDE_V|V_RECODE)' if exp=='E1'`，`primary_expected_direction: NEGATIVE`。
- `joint_claim_FWER.E1_plus_ERI1 = HOLM_TWO_PRIMARY_P_VALUES_AT_0.05`。
- `secondary_family` 为单一 Holm family：其他类别、clean-recode、顺序交互、低/中强度、斜率、单模态匹配、entropy。E2 的 `protocol.json` 中可以看到该规则的冻结副本。

### 证据 2：V1 在第一次 FFmpeg 调用时就失败，没有任何 E1 媒体或模型输出

`results/emotiontalk_e2_consistent_audio_v1/historical_e1_failed_gate.json`：失败命令是第一个 item `G00001_02_02_020` 的 `V_RECODE`，原因是 `-fps_mode` 不受支持。E1 V1 的 `freeze()` 只在 gate PASS 后执行（`e1e2_pipeline.py:66`），所以 V1 没有冻结过 E1 协议，也没有 E1 推理。`e1v2_cpu_gate.py:62` 记录 “zero prior E1 media or model results”。

`ffmpeg_cpu_regression.json` 显示，恢复阶段对 3 个片段生成过模糊视频，`selection_basis: "timestamp fidelity only; no model outputs available"`。

### 证据 3：V2 设计改为三个共同主终点

`e1v2_cpu_gate.py:53`（`prepare()`）写入 `DESIGN_SPEC_PRE_MEDIA.json`：`endpoints: [SIDE_V, SIDE_A, OTHER]`，`multiplicity: Holm across three`。若文件已存在则断言内容相等（`:60`，不可变）。之后 `gate()` 生成媒体，`freeze()` 以 `spec.update(...)` 生成 `RUN_PROTOCOL.json` 并断言该文件此前不存在（`e1v2_pipeline.py:65-66`）。runner 每个 attempt 都写入 `sha256(RUN_PROTOCOL)` = `03d201f1…`，公开 attempts.csv 中 2336/2336 都是这个值，与 `protocol.json.source_protocol_sha256` 相等。

### 判定

- **按代码逻辑的时间顺序**：V2 的三终点设计写在媒体生成和任何 E1 模型调用之前。这是一次**发生在 E1 结局出现之前的修订**，但发生在 ERI1（SIDE_A −10.96 pp，SIDE_V +5.82，OTHER +5.14）和 E2 结果都已知之后。
- **公开可验证性**：`RUN_PROTOCOL.json`、`DESIGN_SPEC_PRE_MEDIA.json` 的字节和 `frozen_unix` 时间戳都不在 PR 中。公开的 `protocol.json` 是审阅后的字段投影，没有冻结时间。哈希链（attempt 指纹 → protocol 哈希）存在，但在公开层面无法闭合。
- **PREDECLARATION_INTEGRITY（E1）= PREDECLARATION_NOT_VERIFIED（公开层面）**。代码逻辑支持“结局前冻结”，但需要发布时间戳和哈希证据才能确认。

### 修订对结论的影响（`review_scripts/predeclaration_sensitivity.py`，精确 p）

| 终点 | V2 计划（PR） | V1 计划（原始） |
|---|---|---|
| SIDE_V | 主终点，Holm p 3.3e−22 | 唯一主终点，p 1.1e−22；E1+ERI1 联合 Holm：2.2e−22 和 0.00172，均通过 |
| SIDE_A | 主终点，Holm p 1.1e−18 | 次级终点（11 项 Holm），p 4.3e−18 |
| OTHER | 主终点，Holm p **0.0423** → “INCREASE” | 次级终点，Holm p **0.169**，**不显著** |

SIDE_V 和 SIDE_A 的结论在两种计划下都不变。**OTHER 增加的“确认性”完全依赖 V1→V2 的修订**，而 PR 没有说明这次修订（`protocol.json` 写着 `protocol_not_modified: true`，指的只是 V2 协议本身）→ **F02 (P2)**。

此外，E2 冻结协议中的跨实验规则 `E1_plus_ERI1` Holm，在 V2 closure 中没有执行。按上表执行后也能通过（F15, P3）。

## E1：其余冻结要素

均在 `DESIGN_SPEC_PRE_MEDIA` / `RUN_PROTOCOL` 中（公开投影 `protocol.json` 可见），且与代码一致：

- 146 item（与 ERI1 UID 集合相同，main 交叉验证 PASS）
- 5 个条件，gblur sigma 0.01/0.04/0.12，CLEAN 与 RECODE
- 模型 revision `ae9e169…`，processor 与模型同一快照
- 七候选、两种联合顺序、V_ONLY、A_ONLY CLEAN
- 主估计量（item 等权，两种顺序平均）
- bootstrap 10,000 次，sign-flip 100,000 次，种子规则 base+100+10i（独立确认 14 个种子符合）
- 技术失败与重试规则

## Pilot 隔离

- Pilot ID 由规则决定：排序后的前 6 个 UID（`e1v2_cpu_gate.py:53`）。不是按结局挑选的。
- Pilot 使用同一个已冻结的 RUN_PROTOCOL（指纹断言），写入独立目录 `03_pilot`。分析只读取 `04_full/attempts` 且 `phase=='full'` 的记录（`e1v2_analysis.py:23-24`）。公开 attempts.csv 中 2336/2336 为 `full`。
- Pilot 的 6 个 item 也在 Full 的 146 个中，Full 重新执行了它们，没有合并 Pilot 输出（`pilot_pooled_with_full: false`）。
- Pilot 只做技术验收：24/24 个 CLEAN slot 与历史 Phase 1/Phase 2 原始输出逐字一致（`pilot_clean_reproduction.csv`）。
- 模糊参数在 Pilot 之前写入不可变的 spec，Pilot 不可能改变它（`blur_strength_selected_using_outcomes: false`，且协议哈希锁定）。
- 判定：**PILOT_ISOLATION = SUPPORTED_BY_CODE_AND_PUBLIC_ROWS**。时间顺序同样依赖私有日志。

## E2

- 冻结模板 `e1e2_pipeline.py:23`：`status: PROSPECTIVE_FROZEN_BEFORE_ANY_GPU_TRIAL`，唯一主终点为共同标签保持，225 item 的 ITT，两种顺序，missing-data 规则 `HIGH=SUCCESS_BASELINE=FAILURE`，对话聚类，secondary Holm，无 Pilot。
- `freeze()` 断言目标文件不存在；runner 每个 attempt 写入指纹 `90362b7c…`，3375/3375 一致，并等于 `protocol.json.source_protocol_sha256`。
- 公开的 `protocol.json` 字段与分析代码一致（seed 2026101210 = 2026101110 + 100）。
- 判定：**SUPPORTED_BY_CODE_ORDER；冻结字节和时间戳为私有，公开层面 PREDECLARATION_NOT_INDEPENDENTLY_VERIFIED**。E2 没有发现主终点修订。
