> **修订提示（Revision V2）**：E3 行中"21/146"是笔误，正确为 14/146（9.6%，132/146=0.904）；该条应表述为选择回归与再编码敏感性的混合。B2 行改为：关联集中在 B3 能表示且读对双方标签的试次，不可归因于标签空间不兼容（`EXPLORATORY_SIGNAL`，收窄）。B4 行："MCR log loss 优势=校准"成立，但不能推出"冻结分数无信息"（重校准后有弱排序信息）；CA-MER/LISTEN 不存在相对 M0 的改善。见 07。

# 04 Claim–Evidence Matrix

状态：`ALREADY_SUPPORTED` / `EXPLORATORY_SIGNAL` / `NOT_ESTABLISHED` / `MEASUREMENT_INCOMPATIBLE` / `NOT_TESTABLE_WITH_CURRENT_DATA`。
所有"本轮新增"数字都是 `POST_HOC_EXPLORATORY`，表见 `tables/`。条目按候选问题 A/B/C 与其他分组。未用"研究者希望得到的结论"筛选：下面把不成立和不可检验的条目与成立条目同等列出。

## 候选问题 A —— 不同冲突构造下，选择"两侧标签之一"的概率有何结构差异？

| ID | 科学命题 | 行级数据与 N | 支持结果 | 统计不确定性 | 替代解释 | 与 R1–R3/ERI1 关系 | 是否重复 | 需新 GPU？ | 什么观察可反驳 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 二选一覆盖率在四个数据集间有大且稳定的差异 | ET Phase2 冲突 696 试次（AT 124/AV 292/VT 280）、MCR 1818、LISTEN 378、CA-MER 2000（排除 OOM 后 1938） | ET 0.94–0.97、MCR 0.954、CA-MER 0.68–0.71、LISTEN 0.442 | 簇 bootstrap；CI 在三组间不重叠（见 X1） | 标签接口（生成/JSON/字母）、候选集大小、提示格式 | LISTEN 的 0.44 为 R3 已报告；CA-MER 全 margin 覆盖率 1350/2000=0.675、支持受限 416/672=0.619 为已封版覆盖率；跨数据集并列为新 | 部分 | 否 | 同一数据集内更换接口后覆盖率不变 | `EXPLORATORY_SIGNAL`（描述性成立，见 A2） |
| A2 | 覆盖率差异**归因于冲突构造类型** | 同上 | 无法检验：构造/接口/候选集三者在数据集间完全共线 | – | 全部替代解释无法排除 | R3 已说明 LISTEN 的 OTHER 是标签词表/构念不匹配的**关联** | 否 | 需要同一数据集内操纵接口（部分在 05 的 optional 里） | – | `NOT_ESTABLISHED` |
| A3 | CA-MER 的 OTHER 是因为 7 类 B3 空间太窄 | CA-MER 冲突 1938 试次 | 反例：两标签都在 7 类内的覆盖率 0.597/0.663 不高于其余 0.751/0.698；85% 的 OTHER 输出是 assertive/worried/doubtful 等 7 类外标签 | Wilson/簇 CI 见 X5 | OTHER 来自候选集中语义相邻标签 | 新 | 否 | 否 | – | `NOT_ESTABLISHED`（"7 类太窄导致 OTHER"被数据否定；"语义相邻标签导致 OTHER"仍只是描述） |
| A4 | 二元条件选择率（P(音频\|二选一)）对选择性覆盖敏感 | LISTEN 3C 378；CA-MER 各 1000 | LISTEN 0.611 → 事后分层 0.450；Manski 界 [0.270, 0.828]；可二分子集中 ridicule 占 64.7%（全体 37.0%） | 簇 bootstrap；界是无假设的 | 缺失非随机、标签内 MAR 不成立 | 补充 R3.4"条件估计量被选择"的定量敏感性 | 部分重复 | 否 | 若 OTHER 的具体标签被恢复，且是二选一偏好的无偏代理 | `EXPLORATORY_SIGNAL` |

## 候选问题 B —— 相对不确定性对选择的预测关联，主要受输入类型、标签体系还是选择覆盖率限制？

| ID | 科学命题 | 行级数据与 N | 支持结果 | 统计不确定性 | 替代解释 | 与 R1–R3/ERI1 关系 | 是否重复 | 需新 GPU？ | 反驳观察 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 | 熵不对称→选择的关联方向在所有 regime 为正 | 二选一试次：ET 116/284/263；MCR 1734；LISTEN 167；CA-MER 695/655 | AUROC：ET 0.74/0.80/0.82，MCR 0.67，LISTEN 0.60，CA-MER 0.51/0.57 | 见 X3 CI；CA-MER AA 的 CI 含 0.5 | 条目难度、标签内容、顺序（顺序内 AUROC 基本不变） | R1 在 ET 内已 `SUPPORTED`；MCR/LISTEN/CA-MER 方向为新增跨 regime 描述 | ET 部分重复 | 否 | CA-MER 16 类特征下 AUROC≈0.5 | `EXPLORATORY_SIGNAL`（跨 regime）；ET 内 `ALREADY_SUPPORTED` |
| B2 | CA-MER 上关联偏弱主要是 7 类特征与 16 类标签体系不兼容，而非 A–V 输入类型 | CA-MER 两标签都在 7 类内 160/256 试次；其余 535/399 | 7 类内 0.638/0.707 vs 7 类外 0.490/0.517；ET 的 A–V 为 0.80 | 子集 CI 宽（[0.48,0.78]、[0.63,0.79]）；分层由标签身份机械决定 | 7 类内子集标签更易读（难度混杂）；子集量小 | 新；回应 ERI1/R1 "generality" 缺口 | 否 | **是**——需要 16 类接口下的单模态读取才能验证（见 05） | 16 类特征下 CA-MER 全集 AUROC≈0.5 | `EXPLORATORY_SIGNAL` |
| B3 | 关联受选择覆盖率限制 | 各 regime 覆盖率 0.44–0.97 | 覆盖率与 AUROC 在 regime 间并不单调（LISTEN 覆盖 0.44/AUROC 0.60 vs CA-MER 0.68/0.51–0.57） | – | 与数据集身份共线 | 新 | 否 | 否 | – | `NOT_ESTABLISHED` |
| B4 | 冻结 source→target 迁移提供了超出流行率校准的概率信息 | MCR 1734；CA-MER 416/1350；LISTEN 167 | 否：与目标流行率常数相比 log loss 差 MCR +0.014 [−0.001,+0.031]、CA-MER +0.085/+0.114、LISTEN +0.313；排序信号存在但弱 | 簇 bootstrap | 常数是事后样本内 | 对"迁移异质而非普遍"的定量分解；与 SCIENTIFIC_CLAIM_STATUS 一致 | 部分 | 否 | – | `ALREADY_SUPPORTED`（"无普遍迁移"）；"MCR log loss 优势=校准"为 `EXPLORATORY_SIGNAL` |
| B5 | 规则 AUROC 的跨数据集排序反映机制强弱 | – | 无 | – | 候选空间、响应格式、流行率均不同 | 与既有"不得做共同机制排名"一致 | 重复 | 否 | – | `NOT_ESTABLISHED` |

## 候选问题 C —— 自然冲突、文本断言冲突、隐含情绪冲突，是否对应不同的可观测行为机制？

| ID | 科学命题 | 行级数据与 N | 支持结果 | 统计不确定性 | 替代解释 | 与已有关系 | 重复 | 需新 GPU？ | 反驳观察 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 三类冲突在可观测"行为签名"上不同（顺序、OTHER 持久性、熵规则、对标签的依赖） | ET/CA-MER（自然）、MCR（断言）、LISTEN（隐含） | 签名确有差异：见 03b X2/X3/X6（例如 MCR 强 recency 且 OTHER 受顺序驱动；LISTEN/CA-MER OTHER 条目持久；ET 低熵规则最强） | 各 CI 见表 | 所有差异都混杂标签接口、候选集、提示、证据格式 | 新（跨 regime 并列） | 否 | 部分可由 05 的 optional 条目触及 | – | `EXPLORATORY_SIGNAL`（签名差异）；"机制不同"`NOT_ESTABLISHED` |
| C2 | 文本断言在 MCR 中主导选择 | MCR 909 对 | A_THEN_T 96.4%、T_THEN_A 82.6% 选文本；配对 recency 68 vs primacy 4 | 簇 CI 见 02 | 复制断言的标签（命题复制）而非"证据权衡" | 与 MCR V2 冻结结果一致 | 重复 | 若要区分"复制"与"权衡"需要 faithful/neutral/irrelevant 文本条件 | – | 描述 `ALREADY_SUPPORTED`；机制 `NOT_TESTABLE_WITH_CURRENT_DATA` |
| C3 | LISTEN 的 OTHER 反映隐含情绪识别/构念问题，而不只是字母选择题格式 | 3B 378；B3 自由 7 类单模态读取 | B3 自由空间里 anger/disgust/sadness 音频 top-1 命中对应标签仅 12.1%/6.2%/7.7%（多读成 surprised/happy）；LISTEN 原生输出这些标签 0–2.5% | n 小（13–80） | 提示/语料特殊性（MUStARD 夸张韵律） | R3 的标签依赖发现的补充证据 | 部分 | 否（选项表缺失只能靠 CPU 无法解决） | 若给定选项表后模型能轻易选出隐含标签 | `EXPLORATORY_SIGNAL`；三种解释的分离 `NOT_TESTABLE_WITH_CURRENT_DATA` |
| C4 | CA-MER 选择跟随构造标记（audio-aligned vs video-aligned） | 695/655 二选一试次 | P(音频\|二选一) 0.738 vs 0.368，CI 不相交 | 簇 bootstrap | "aligned" 的真实含义无法核验（final_label 缺失）；也可能与标签分布差异有关 | 新 | 否 | 间接（16 类单模态特征） | 若标签分布匹配后差异消失 | `EXPLORATORY_SIGNAL`；"跟随真实情感证据"`NOT_TESTABLE_WITH_CURRENT_DATA` |

## 其他候选

| ID | 科学命题 | 数据与 N | 结果 | 不确定性 | 关系 | 重复 | GPU | 反驳 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| D1 | OTHER 条目持久性按标签接口分层：ET/MCR 零星且顺序驱动；CA-MER/LISTEN 条目持久 | X6 | P(全部\|任一) 0.0–0.15 vs 0.49–0.64；独立期望的 2.4–2.7 倍 | 无 CI（计数） | R3 对 LISTEN 已报告 85/242；其余新 | 部分 | 否 | – | `EXPLORATORY_SIGNAL` |
| D2 | 顺序敏感性因数据集/提示而异（同模态对） | X2 | ET-AV −11.6 pp vs CA-MER −1~−2 pp；ET-AT −1.6 vs MCR −6.9 | 簇 CI 见 X2 | R1 已有"顺序效应配对特异" | 部分 | 否 | – | `EXPLORATORY_SIGNAL`（描述）；`MEASUREMENT_INCOMPATIBLE` 作为跨数据集比较 |
| E1 | ERI1：音频熵升高的条目 SIDE_A 降得更多 | 146 条目 | Spearman −0.35 [−0.49,−0.20]（SNR00−RECODE）；SNR10 −0.31，SNR20 −0.22 | 对话簇 bootstrap | ERI1 明确"熵中介未识别" | 新关联，不改变封版 | 否 | 否 | 若控制 A_ONLY 读对与否后消失 | `EXPLORATORY_SIGNAL`；中介 `NOT_ESTABLISHED` |
| E2 | ERI1：噪声效应在三种拓扑下同向 | 37/58/51 条 | SNR00−RECODE ΔSIDE_A −0.135/−0.112/−0.088，CI 宽且重叠 | n 小 | – | 否 | 否 | – | `NOT_ESTABLISHED`（既不显示异质也没有功效检出） |
| E3 | "可读"在重编码下不稳健（~10% 回归） | 146 条 | CLEAN 1.000（选择效应）→ RECODE 0.904 | 无 CI（计数 21/146 未读对） | ERI1 仅描述管线对照 | 新数字 | 否 | 否 | – | `EXPLORATORY_SIGNAL`（设计含义） |
| E4 | OTHER 输出对应未输入模态的标签 | Phase2 12 试次/9 簇；ERI1 22/7 | 6/12，12/22，排列 p 0.061/0.0095 | 簇极少，p 偏乐观 | – | 否 | 否 | 若扩大样本后比例回到洗牌基线 | `NOT_ESTABLISHED`（样本过薄） |
| E5 | 未输入模态的标签仍能预测二选一方向 | 523 试次/205 条 | 0.568 [0.510,0.627] | 簇 CI | 与 R2 条目级标签偏好同类 | 部分重复 R2 | 否 | – | `EXPLORATORY_SIGNAL`（与 R2 非独立） |
| F1 | ALL_DIFFERENT 组合性可用现有总体检验 | TripleReadable ALL_DIFFERENT 仅 3 条 | 不可 | – | R2 已 `NOT_ESTABLISHED` | 重复 | 需要新条目池 | – | `NOT_TESTABLE_WITH_CURRENT_DATA` |
| F2 | AV 一致样本上音频退化会降低共享标签保持率 | 225 条（历史保持率 448/450=99.6%） | 无退化臂 | – | – | 新缺口 | **是** | – | `NOT_TESTABLE_WITH_CURRENT_DATA` |
| F3 | 视频侧可靠性干预产生对称效应 | 146 条 | 无视频退化臂 | – | ERI1 S3（SIDE_V 增加）未成立 | 新缺口 | **是** | – | `NOT_TESTABLE_WITH_CURRENT_DATA` |
