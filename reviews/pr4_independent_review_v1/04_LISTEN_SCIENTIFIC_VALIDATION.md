# 04 LISTEN 科学正确性验证

脚本：`review_scripts/r04_listen.py` → `logs/r04_listen.json`。

| 检查 | 独立结果 | 结论 |
|---|---|---|
| V3、V4 各 1,149 条安全投影 | 各 1149 行、键唯一；条件 3A 387 / 3B 381 / 3C 381；只有这三种条件（**投影中不存在 T_THEN_A**） | ✅ |
| 选项/标签恢复 | `parsed_label_recovered` 100% 在候选集中；字母→标签映射 0 不一致；`source_label_correct` 0 不一致；无空解析 | ✅ |
| V3/V4 身份 join | 1149/1149 音频与文本 SHA 相同；候选**集合**相同 1149，候选**顺序**相同 0；prompt hash 相同 0；`scientific_pooling_allowed=False` 1149 | ✅ 不可合并已被正确执行 |
| 历史九条件 vs 3A/3B/3C | `LISTEN_PLANNED_VERSUS_EXECUTED_STAGE_V2.json` 把 V1/V2 manifest 标为 BLOCKED 占位，不当作已执行试次 | ✅ |
| 单模态门控的真实定义 | V3/V4 的 3C 行 `actual_joint_eligibility` 均为 `TECHNICAL_GATE_PASS_ONLY`（381+381）：历史门控只是技术门控，不是正确性门控；报告如实说明 | ✅ |
| T_THEN_A 缺少执行证据 | 投影只有 3A/3B/3C；Transfer 预测中 3C 全部为 `A_THEN_T`；报告写明“no legitimate item-paired reverse” | ✅ |
| OTHER 恢复为候选标签 | 3C 冲突中的 211 个 OTHER 都是有效选项，0 个等于 y_A/y_T；分布 ridicule 124、frustration 25、neutral 20…（与“124 ridicule/211 OTHER”一致） | ✅ |
| 3C 总体 | 381 行 / 378 冲突 / 二元 167（102 A / 65 T）/ OTHER 211；outcome 重算 0 不一致 | ✅ |
| 资格组 | DUAL 22 / A-only 71 / T-only 46 / NEITHER 103 / UNOBSERVABLE 136；共同支持 242；分组重算 0 不一致 | ✅ |
| 严格双侧匹配 22 条，全部为 ridicule | 22/22 y_A=ridicule；strict 内容支持 22/22；21 条二元（12 A / 9 T）+ 1 OTHER | ✅ |

## 推广风险审查

* 22 条子组的 AUROC 0.759 **没有**被推广：`04_TRANSFER_FAILURE_DECOMPOSITION.md` 写明“tiny selected group neither proves an improvement in probability loss nor repairs the original full-population transfer. It is not a new zero-refit success”；同一子组 LL 0.7985 > M0 0.6958（更差）也已报告；Claim `F_LISTEN_SELECTION`=NOT_ESTABLISHED，`L2`（非 ridicule 双侧可读）=INSUFFICIENT_EVIDENCE（0/22）。✅
* V3 与 V4 没有被合并用来计算输入顺序效应 ✅。
* 与冻结 Transfer 一致：3C 167/378、LL 0.981644、M0 0.697116、oracle 0.668399、TP/FP/FN/TN 11/5/91/60，均独立复现（06）。

## 问题

* **F07 (P3)**：DUAL_MATCH 与 STRICT_DUAL_CONTENT_MATCH 是**完全相同的 22 行**（点估计一致），却报告了两套 CI：[0.500, 0.964] 与 [0.490, 0.956]（`TRANSFER_FAILURE_SUBGROUPS.csv`），原因是种子取自 tag 哈希。文档只引用了后者。建议合并为同一 CI，或者注明两组成员相同。
* 背景备注（main 遗留，不属于本 PR）：`LISTEN_ALL_MIXED_HISTORICAL` 把 3A(T_ONLY)/3B(A_ONLY) 单模态试次放进“冲突仲裁”路线，M0+ORDER 对 A_ONLY 也赋 `FIRST_IS_MODALITY1=1`；PR 已把这条路线标为 historical 并与 3C 分开，处理是正确的。
