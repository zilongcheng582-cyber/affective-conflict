# 07_FINAL_SCIENTIFIC_EXECUTIVE_SUMMARY

POST_HOC_EXPLORATORY — CPU-only; frozen source models, thresholds, scalers, predictions and raw archives unchanged.

强制 Phase4已完成，新增分析均为POST_HOC_EXPLORATORY。没有GPU、模型加载、重拟合、阈值调整、冻结结果修改或GitHub合并。

- 6354条corrected测量独立复核；9219条冻结预测全部匹配，最大绝对误差1.6653e−16；18组路线/基线报告的身份、样本数和指标通过1e−12容差；5199条恢复记录严格链接；6个CPU重放产物逐文件SHA一致。
- MCR：AUROC.727559，BA.50源于1734个预测全部低于.5；logloss.245884优于合法源固定M0.678181，不能将它概括为“迁移完全失败”。排序、概率损失和阈值分类分别报告。
- LISTEN3C：167/378二元可评估，211OTHER；AUROC.605732但logloss.981644差于合法M0.697116，差+.284528，95CI[+.168351,+.402273]。该M0不是targetoracle。双侧严格匹配仅22条、全部ridicule，选后AUROC.759259不能宣称新迁移成功。
- CA：支持本体诊断AUROC.686394但概率优势未建立；完整marginAUROC.573999且logloss差于M0。双侧匹配206/216可评估仍未挽救margin概率表现。七类与十六类测量不匹配、单模态源标签读出失败、选后总体变化和真实行为差异仍需分开，未保存十六类概率意味着完整熵解释未识别。

**What transferred：**有限的外部排序信息，及MCR相对合法M0的概率损失改善。

**What failed to transfer：**LISTEN3C和CA完整margin的概率损失优势；MCR固定阈值下音频召回。支持限定或结构未定义的路线不能冒充完整目标成功。

**What remains unidentified：**本体、可读性、顺序、输入契约、选择性覆盖和跨域行为各自的因果贡献；CA十六类连续特征、LISTEN非ridicule双侧支持等。

综合矩阵现分列R1、R2、FrozenTransfer、ERI1、RecoveredNative、FailureExplanation六类。若下一目标是解释迁移失败，优先建议CPU测量/支持方案冻结，潜在QwenGPU首位为CA十六类连续评分验证，LISTEN反序须先解决本体和支持；若仅写有限结论论文，可停止新增Qwen并另行考虑第二模型。未自动开始任何后续工作。

完整证据路径、SHA、记录数见04_TRANSFER_FROZEN_EVIDENCE_REGISTER.md；全部最终产物见SHA256SUMS.txt。本轮原始归档与冻结结果保持只读；仅按AGENTS既有授权追加三个导航docs，旧结论和修订前报告保留快照。

