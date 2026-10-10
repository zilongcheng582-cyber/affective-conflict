# 03 MCR 科学正确性验证

脚本：`review_scripts/r03_mcr.py` → `logs/r03_mcr.json`（全部基于 PR 内公开投影，GitHub clean checkout）。

| # | 检查 | 独立结果 | 结论 |
|---|---|---|---|
| 1 | 4,000 条构成严格四条件配对 | 4000 行 / 4000 唯一 (item,condition)，0 重复；1000 个 item 均恰好有 {neutral, faithful, adversarial, irrelevant}；每个 item 内音频 SHA 与 GT 一致 | ✅ |
| 1b | 解析失败 | 仅 irrelevant 有 5 个 `PARSE_FAIL_NO_LABEL`；PARSE_OK 的标签 100% 在 7 类内；失败行无标签 | ✅ |
| 2 | 原生 prompt 理解 | 报告正确说明：neutral 只有问题；faithful/adversarial 声称某种情绪；irrelevant 使用相同包装 + 无关描述。代码从 adversarial 提示中用正则抽取 y_T，并断言 y_T ≠ GT（0/1000 相等） | ✅ |
| 3 | Native 与 Controlled 混为同一总体？ | 否。native 1000 与 controlled 909 分开报告；`01_MCR_NATIVE_VS_CONTROLLED_COMPARABILITY.md` 明确禁止合并 3636+4000；Transfer 分母保持 1818 | ✅ |
| 4 | 音频 SHA join 准确性 | 909/909 native↔controlled 音频 SHA 相等，`source_index_path_hash_label_match`=True。**注意**：纯 SHA join 会在 3 个哈希上出现歧义（MCR_SER_138/537、199/204、692/752/838）；PR 用 source_index 作为 join 键，避免了 many-to-many | ✅ |
| 5 | 重复音频被当作独立？ | native 1000 → 943 个唯一 SHA（56 个重复组）；controlled 909 → 905。主要 CI 使用 943 个音频 SHA 簇；另有等权哈希敏感性分析 | ✅ |
| 6 | 同音频不同 GT 冲突组 | 39 个冲突 GT 哈希组（79 个记录）；controlled 内保留 1 个三标签组 `d6a4044b…`（happy/angry/neutral），已在报告中逐项披露；有“排除全部冲突组”的敏感性分析（921/904） | ✅ |
| 7 | 循环定义 | 无（文本条件来自提示文本，而不是目标标签） | ✅ |
| 8 | estimand 是否有意义 | 主 estimand = 音频源标签匹配率之差（paired）；neutral/irrelevant 的“文本准确率”定义为 NOT_DEFINED，faithful 的文本匹配=音频匹配，并注明无法区分 | ✅ |
| 9 | 对无显式情绪标签的文本强行构造 SIDE_T？ | 否：neutral/irrelevant 没有 text side；OTHER 定义已适配 | ✅ |
| 10 | 被解释为因果的模态权重变化？ | 否：“bounded evidence of assertion-following in this prompt, not universal text preference”；“Conditions were not randomized” | ✅ |

## 数值复核（报告值 vs 独立重算）

| 数值 | 报告 | 重算 |
|---|---|---|
| neutral / faithful / adversarial / irrelevant 音频匹配 | 445 / 994 / 6 / 432 | 445 / 994 / 6 / 432 ✅ |
| adversarial 跟随文本 | 988/1000 | 988 ✅ |
| 909 交集：controlled T_ONLY 跟随文本 / native adversarial 文本 / 音频 | 909 / 901 / 4 | 909 / 901 / 4 ✅ |
| controlled A_ONLY 音频匹配 = Transfer DUAL_MATCH item 数 | 466 | 466（=932 行/2）✅ |
| 唯一音频 native / controlled | 943 / 905 | 943 / 905 ✅ |

## 问题

* **F07 (P3)**：同一个 estimand 出现两套不同的 bootstrap CI。`01_MCR_NATIVE_FOUR_CONDITION_REPORT.md` 中 adversarial−faithful 为 [−99.49, −98.02]，`01_MCR_DUPLICATE_SENSITIVITY.md` 中同一总体、同一加权（released1000/released_item）为 [−99.49, −98.07]；irrelevant−neutral 为 [−5.03, 2.51] vs [−5.05, 2.69]。原因是 `analysis.py` 的种子取自 tag 哈希。不影响结论，但同一数字应只有一个 CI，或者注明 Monte Carlo 误差。
* 909 总体没有被修改；未发现统计单位错误，不需要重算。
