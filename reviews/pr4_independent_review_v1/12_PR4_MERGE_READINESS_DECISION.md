# 12 PR #4 合并就绪决定

绑定：PR #4，head `18b99caa5c11c3719e67ccbd3a0c71a0d70a77d7`，base `544ca0efae158df369a7b25dd110dc4254f67a7d`（审查结束时已再次核实，未变化）。

```
MERGE_READINESS             = CHANGES_REQUIRED
P0_COUNT                    = 0
P1_COUNT                    = 0
P2_COUNT                    = 5   (F01, F02, F03, F04, F05)
P3_COUNT                    = 12  (F06–F12, F14–F18)
FROZEN_ARTIFACT_INTEGRITY   = PASS   (260 个纯新增；main 文件 0 修改；86/86 个 main 冻结资产一致；222/222 个 payload 哈希一致)
TRANSFER_REPLAY_STATUS      = GITHUB_CLEAN_CHECKOUT_REPLAY_PASS (18/18 组点估计、身份、分母；误差 0.0)；bootstrap CI 未重新生成；AUTODL_RESTRICTED_SOURCE_REPLAY = NOT VERIFIED
SCIENTIFIC_CLAIM_AUDIT      = CHANGES_REQUIRED (数字与分母全部核实正确；当前研究状态 / NEXT_STEP 的版本链冲突 F02)
SECURITY_AUDIT              = PASS_WITH_NOTES (无密钥 / 个人信息 / 媒体；1 处脱敏规则执行不一致，无新增暴露)
CLEAN_CHECKOUT_TEST_STATUS  = PASS (36/36 现有测试；29/29 审查测试；四区制重跑逐字节一致；完整套件中 4 个失败在 base 上同样存在，属于环境问题)
```

## 理由

* 未发现 P0/P1：没有敏感数据泄漏，冻结历史没有被改变，没有计算错误、分母错误、join 错误或方向错误；18 组 Transfer 指标和各数据集的关键计数都被独立复现。
* 但按准入规则，“涉及科研证据身份或结论解释的 P2 必须修正后才能合并”：
  * **F01**（迁移验证报告里的身份数字过时、而且抄错；最终 head 没有回执）
  * **F05**（排除登记的机器状态列与实际不一致）
  * **F02**（多个相互冲突的当前 GPU / NEXT_STEP 决定，旧文档没有取代标记）
* F03、F04 是低成本的可复现性 / 验证器修复，建议同一轮完成。

修复完成并产生新 head 后，需要针对新 head 重新进行审查，至少要重跑：r01 完整性、`validate_migration`（含 `-O` 用例）、r06 复算，以及 F02 的状态索引检查。届时如果 P2 已清零，可以标记为 `READY_FOR_HUMAN_MERGE_REVIEW`。即使到那时，**也只是人工合并审查的准入，不是自动合并授权**。

本轮没有修改 PR 分支，没有提交修复，也没有合并。等待用户决定。
