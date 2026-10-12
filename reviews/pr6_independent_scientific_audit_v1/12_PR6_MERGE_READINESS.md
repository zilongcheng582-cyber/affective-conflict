# 12 PR #6 合并就绪判定

| 字段 | 值 |
|---|---|
| PR6_HEAD_SHA | `5cebd143e5c2c5e31df260383a96b45ab780efee`（远端于 2026-10-12 重新确认；审查期间未变化） |
| P0_COUNT | **0** |
| P1_COUNT | **0** |
| P2_COUNT | **4**（F01、F02、F03、F04；其中 F01–F03 阻止合并，F04 只约束机制主张） |
| P3_COUNT | **12** |
| E1_CODE_AUDIT | PASS_NO_CONFIRMED_BUG（静态审查 + 24 项合成回归测试；F09/F10 为防护强度问题） |
| E2_CODE_AUDIT | PASS_NO_CONFIRMED_BUG（F14 不可达） |
| E1_INPUT_CONTRACT | PUBLIC_CONTRACT_INTERNALLY_CONSISTENT（730/730）；SOURCE_MEDIA_CONTRACT_NOT_INDEPENDENTLY_VERIFIED |
| E2_INPUT_CONTRACT | PUBLIC_MEDIA_IDENTITY_CONSISTENT（视频恒定，噪声种子推导正确）；SOURCE_MEDIA_NOT_INDEPENDENTLY_VERIFIED；RECODE_NOT_NEUTRAL_FOR_A_ONLY（F03） |
| STATISTICAL_REPLAY | PUBLIC_REPLAY_PASS（第三方独立实现；POINT 79/79，BOOTSTRAP 100/100，误差 ≤1e−12；精确 sign-flip 一致） |
| PREDECLARATION_INTEGRITY | E1：PREDECLARATION_NOT_VERIFIED（公开层面；代码逻辑支持“结局前”；V1→V2 修订未披露，F02）。E2：SUPPORTED_BY_CODE_ORDER，冻结字节为私有 |
| CAUSAL_ESTIMAND_VALIDITY | SUPPORTED_WITH_LIMITATIONS（限于特定处理、特定模型、固定预选 item） |
| MECHANISM_CLAIM_VALIDITY | NOT_ESTABLISHED |
| PUBLIC_EVIDENCE_PROVENANCE | SHA256SUMS 77/77 PASS；78 个文件全部为新增，没有修改历史文件；投影 → 私有源的 lineage 已登记但无法复核 |
| SOURCE_ACCESS_LIMITATIONS | 无 AutoDL 访问；没有原始/派生媒体、原始生成、逐 token logprob、RUN_PROTOCOL 字节和时间戳；未执行 GPU |
| **MERGE_READINESS** | **CHANGES_REQUIRED** |

## 四层科学判定

| 层 | E1 | E2 |
|---|---|---|
| Level 1 Numerical validity | **SUPPORTED** | **SUPPORTED** |
| Level 2 Experimental validity | **SUPPORTED_WITH_LIMITATIONS**（代码与协议一致；源媒体未独立核验；终点修订未披露） | **SUPPORTED_WITH_LIMITATIONS**（音频 RECODE 非中性） |
| Level 3 Causal identification | **SUPPORTED_WITH_LIMITATIONS**（特定模糊处理 → 联合选择变化；L2/L3 是信息移除） | **SUPPORTED_WITH_LIMITATIONS**（0 dB 白噪声 → 共同标签保持下降，含标签偏移成分） |
| Level 4 Mechanistic interpretation | **NOT_ESTABLISHED** | **NOT_ESTABLISHED** |

## 未满足的准入条件

- “没有未处理的关键 P2”：F01、F02、F03 均未处理，合并前需要按 11 中的 R1–R3 补充文档。
- 其余条件已满足：P0 = 0；P1 = 0；主要实验身份和分析正确；PR 自身文本没有扩大到机制主张；公开资产合规（SHA 校验通过；本审查独立扫描 78 个文件，未发现凭证、个人路径、二进制或媒体载荷，也没有原始文本字段，只有 `text_sha256`）；必需复算通过；head 未变化。

R1–R3 完成且 head 更新后，应在新 head 上重新运行 `review_scripts/independent_replay.py`。若仍全部通过，可以改判为 READY_FOR_HUMAN_MERGE_REVIEW。

本审查没有修改 PR #6，没有把 Draft 转为 Ready，也没有合并。
