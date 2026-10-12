# 05 候选评分与 entropy 审查

状态：**SCORING_IMPLEMENTATION_STATIC_ONLY**（静态审查正确；数值归一化已复算；逐 token 原始 logprob 和模型不可得，无法独立重放 teacher forcing）。

## 实现（`main:src/emotiontalk/phase1/execution.py:503-615`，与冻结提交逐字节相同）

| 要点 | 证据 | 判定 |
|---|---|---|
| 七候选来源 | `sample["candidate_labels"]` = UID 绑定的 `candidate_sequence`；断言等于冻结 ontology（`:507-508`） | 正确 |
| 顺序一致 | 概率行按序列中的标签输出；独立核对每个 trial 的标签集合 = 该 trial 的候选序列 | PASS |
| 真实 tokenization | `tokenizer(rendered + label)` 减去前缀 token；断言候选不改变前缀切分（`:514-521`），并断言前缀末尾 16 个 token 与实际模型输入一致（`:511-513`） | 正确 |
| 单 token 与多 token 标签 | 单 token 用前缀最后位置的 logits；多 token 拼接后 teacher forcing，位置 `prefix_len-1+idx`（`:543-562`） | 正确。token 数在 2336 个 E1 trial 和 1125 个 E2 trial 中恒定：happy/neutral/sad = 1，angry = 2，fearful/surprised/disgusted = 3 |
| teacher-forced 目标 token | `token_log_probs[token_id]`，位置 off-by-one 正确（预测第 idx 个 token 用位置 prefix_len−1+idx） | 正确 |
| 答案泄漏 | 前缀是生成时的 rendered chat 模板（含 generation prompt），不含任何答案 | 无泄漏 |
| mean-token log-prob | `raw_score/len`（`:564`）；独立复算 \|sum/token_count − mean\| ≤ 4.4e−16 | PASS |
| softmax | `stable_softmax(mean_scores)`；独立从 mean/sum 列重算主概率和敏感性概率 | PASS（最大误差 4.4e−16） |
| entropy / log(7) | `:581-583`；独立复算 E1 2336 个、E2 1125 个 trial 的 entropy 与 `entropy_normalized` 列一致 | PASS |
| 与生成输出混淆 | 评分与生成是分开的状态（`candidate_scoring_status`），结局只用贪心生成 + 解析器 | 无混淆 |
| 联合 arm 的评分 | runner 用 `'V_ONLY'` 参数调用评分器（`e1v2_runner.py:74`），**只**为了选出源标签字段（y_V），前缀是完整的联合 prompt（`scoring_prefix_contract=FULL_JOINT_PREFIX_NOT_UNIMODAL_PROMPT`） | 正确，但字段名容易误读 |

## 只靠概率总和为 1 无法证明映射正确

对抗 fixture（07）表明：同一个 trial 中把两个**同 token 数**的标签（happy↔sad）对调后，概率总和、entropy 和 token 数不变量**都无法察觉**。PR 的 replay 和本审查的 replay 都检测不到。对调 token 数不同的标签（happy↔fearful）时，本审查的 token 数不变量能检测到，PR replay 检测不到。要验证标签↔分数映射，需要逐 token 的 `token_ids`（只在私有 attempt 记录中，公开投影已删去）。

## 科学含义

- 候选分数是“七个规范标签串的长度归一化 teacher-forced 似然的 softmax”，**不是**模型自然生成的概率。用均值 log-prob 会在长度不同的标签之间引入归一化选择。
- 贪心输出与评分 argmax 的一致率：E1 各 arm/条件为 87–100%，E1 A_ONLY 87%，E2 A_ONLY 79–88%。两者是不同的量。
- **entropy 不单调**（V_ONLY 均值）：RECODE 0.684、L1 0.706、L2 **0.608**、L3 0.761。在 L2，模型（几乎全部回答 neutral）比看清晰视频时**更“确定”**。所以归一化 entropy 不能当作视觉证据可靠性的真实量表，也不能作为中介变量（F06, P3）。PR 已声明不做 entropy 中介，所以这是对未来主张的约束。
- 在联合 arm 中，P(y_V) 的均值从 RECODE 0.33/0.28 降到 L3 0.095/0.115（A_THEN_V/V_THEN_A）。这是联合 prompt 下的评分量，可以作为描述，不能作为机制。
