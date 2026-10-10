# 11 必需修复与测试

本审查**没有修改** PR 分支。下面只是登记的修复方案，均不改动已冻结或已归档的科学字节。

## 合并前必须修复（科研证据身份 / 结论解释相关的 P2）

### F01 — 修正迁移验证报告中的身份数字，并为最终 head 补回执
* `MIGRATION_VALIDATION_REPORT.md:7`：`16,372,203` → `16,358,604`；注明 16,372,023 是 Windows 换行转换前的快照值。
* `:21`：把“254 then-current”改成快照历史（245 → 254 → 256 → 259），并增加一个绑定到最终 head SHA 的 `CLEAN_CHECKOUT_VALIDATION_FINAL.json`（或把本审查的 259/259 结果作为外部回执引用）。
* 回归测试：`payload_bytes == sum(allowlist.bytes) == sum(actual sizes)`；报告中出现的每个计数都要与机器记录一致。

### F02 — 发布统一的当前研究状态与取代链
* 新增 `results/four_regime_structural_synthesis_v1/STATUS_AND_SUPERSESSION.md`：05 →（取代）08 →（被修正）`QWEN_GPU_PRIORITY_REVISED_V2.md` →（当前）`06_QWEN_NEXT_EXPERIMENT_DECISION.md`；逐条列出已撤回的声明（A_ONLY/V_ONLY “未运行”、MCR “其他文本条件未运行”、909 个独立音频、V3/V4 可合并）及其 errata 条目；写明唯一当前的 `NEXT_STEP = CPU_DESIGN_FREEZE_FOR_TRANSFER_MEASUREMENT_VALIDATION`（建议，不是授权）。
* 从 `docs/RECOVERED_EVIDENCE_MIGRATION_V1.md` 链接过去。历史文件本身保持字节不变。
* 回归测试：任何含有决策标记（`ONE_FINAL_QWEN…`、`CPU_ANALYSIS_INCOMPLETE`、`NEXT_STEP`）的文档，要么就是当前文档，要么在状态索引中被列为已取代。

### F05 — 修正排除登记的 status 列
* 从 gap 状态重新生成 `MIGRATION_EXCLUSIONS.csv` 的 `status`（不能出现 `CANDIDATE`）；随后重新生成 SHA256SUMS。
* 回归测试：每一行的 `status` 都等于 gap 分析中的 hold 状态。

## 建议合并前修复（成本低，属于可复现性 / 验证器）

### F03 — 跨平台换行
* `.gitattributes` 增加：`.gitattributes -text`、`docs/RECOVERED_EVIDENCE_MIGRATION_V1.md -text`；在 README 中写明 `git clone -c core.autocrlf=false`（因为 main 的已有文件也会被转换）。
* 回归测试：用 `core.autocrlf=true` clone 后运行验证器。

### F04 — 验证器不能依赖 `assert`
* 用显式检查 + `raise` 替换 `assert`，或在 `sys.flags.optimize` 时直接退出。
* 回归测试：`python -O` + 损坏的夹具 → 非零退出码（`review_tests` 中已有对应用例，当前固定的是缺陷行为，修复后应把期望值反过来）。

## 后续维护（P3，允许合并后处理，但必须登记）

F06 补全脱敏字段清单；F07 按总体身份确定种子或去重相同子组；F08 去掉重复的机器表，并写目录专用 README；F09 验证器检查清单覆盖率、单类时返回 None、合并后的拓扑；F10 增加 `evidence_origin` 列；F11 恢复报告正文中的空格；F12 写改名映射；F14 统一 `truth()`；F15 相对化路径（可选）；F16 给历史脚本加 DO-NOT-EXECUTE 头；F17 公开 CA-MER 等价性决定 JSON（仅元数据）以及 expanded 包的原始哈希清单；F18 字段改名。

（F13 是审查中途登记的“环境版本不一致”嫌疑，核实后不成立，已撤回。）

## 审查方提供的回归测试资产

* `review_tests/test_pr4_review_boundaries.py`（29 个测试）：覆盖重复/冲突标签、缺失、OTHER、PARSE_FAIL、TECH_MISSING、两种顺序配对（簇 bootstrap）、类别不平衡 / 单类、标签本体（7 vs 16）、行顺序不变性、CSV 字符串类型、确定性、验证器的 `-O` / 覆盖率 / 损坏检测。
* `review_scripts/r0*.py`：可以作为 CI 中的独立复算脚本。
