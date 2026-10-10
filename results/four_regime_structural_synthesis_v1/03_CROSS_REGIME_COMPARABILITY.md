# 03a 跨数据集可比性判断

两条主线：**A–T**＝EmotionTalk(AT)、MCR、LISTEN(3C)；**A–V**＝EmotionTalk(AV)、CA-MER。
等级：`DIRECTLY_COMPARABLE` / `CONDITIONALLY_COMPARABLE` / `DESCRIPTIVE_ONLY` / `NOT_COMPARABLE`。
判断依据是下面的 8 项检查，**只在判定过的共同科学量上做了横向分析**（`03_CROSS_REGIME_STRUCTURE_REPORT.md`）。

## 1. 八项检查

| 检查 | EmotionTalk | MCR | LISTEN | CA-MER |
|---|---|---|---|---|
| 模态身份 | A=原始语音（含词汇内容）；T=转写；V=静音视频 | A=原始语音；T=**描述性断言**"This audio expresses X emotion" | A=原始语音；T=转写 | A=抽取音频（16 kHz 单声道）；V=静音视频 |
| 证据性质 | 自然感知 | 音频自然、文本**命题型**（人工合成断言） | 音频自然、文本自然语句（来自 MUStARD/MELD 类语料） | 自然感知 |
| 标签语义与候选空间 | 7 类，人工逐模态标注 | 7 类；音频侧标签=benchmark GT（非独立标注） | 音频 5 类、文本 8 类；**选择题字母**（原生选项+8 增补，逐条随机序） | 16 类并集，**模型伪标签**（官方明确"非 ground truth"） |
| 单模态读取成功 | Phase1 `Readable`（读对源标签），用于门控 | 文本≈100%（命题即标签）；音频 B3 40.8% | 3A/3B 本身；source-label prob 全未定义 | B3 近似（7 类）；受控 16 类单模态**无输出** |
| joint response 的 SIDE/OTHER 定义 | 解析标签==某侧标签 / 都不是=OTHER | 同左（7 类） | 所选字母对应标签==某侧；否则 OTHER（**不含标签名**） | 所选 16 类标签==某侧；否则 OTHER（含标签名） |
| 顺序与提示 | 两序（Phase2 受控提示；ERI1 同） | 两序，结构化内容、候选序旋转 | **仅 A_THEN_T**；原生指令随条件变 | 两序，JSON 输出、16 类候选旋转 |
| "conflict" 指的对象 | 同一话语上，不同模态各自标注的情感标签不同 | 音频的 GT 标签 vs 文本**断言**的另一标签（后者是实验者写的） | 隐含情感类别 vs 显式情感类别（构念差异） | 官方两个模态伪标签不同 |
| 重复/簇 | 对话簇，条目内两序配对 | 3 组字节相同音频（7 条，1 组 GT 冲突）；推断对话簇 | base 条目跨条件匹配 | 样本即簇 |

## 2. 可比性矩阵（按科学量）

| 科学量 | ET-AT vs MCR | ET-AT vs LISTEN-3C | MCR vs LISTEN-3C | ET-AV vs CA-MER |
|---|---|---|---|---|
| Q1 完整 SIDE/OTHER/PARSE_FAIL 分布 | CONDITIONALLY（同 7 类、同类定义；但文本是断言，"冲突"对象不同） | DESCRIPTIVE_ONLY（字母选择题 vs 生成） | DESCRIPTIVE_ONLY | CONDITIONALLY（同模态对；标签空间 7 vs 16） |
| Q2 两侧标签可解析覆盖（二选一覆盖率） | CONDITIONALLY | DESCRIPTIVE_ONLY | DESCRIPTIVE_ONLY | CONDITIONALLY |
| Q3 条件二元选择 P(音频\|二选一) | DESCRIPTIVE_ONLY（选择机制不同，且被选择性覆盖率调制） | DESCRIPTIVE_ONLY | DESCRIPTIVE_ONLY | DESCRIPTIVE_ONLY |
| Q4 配对顺序敏感性（音频先 − 音频后，条目配对） | CONDITIONALLY | **NOT_COMPARABLE**（LISTEN 单序） | NOT_COMPARABLE | CONDITIONALLY |
| Q5 单模态熵差→选择（未拟合低熵规则 AUROC） | CONDITIONALLY（共享 7 类 B3 测量空间） | NOT_COMPARABLE（LISTEN 标签在 7 类外，source-prob 未定义） | NOT_COMPARABLE | CONDITIONALLY **仅限两源标签都在 7 类内的子集**；全集 MEASUREMENT_INCOMPATIBLE |
| Q6 冻结 source→target 迁移（已完成） | 仅引用；各目标集流行率/覆盖率不同，**不构成排名** | 同 | 同 | 同 |
| Q7 OTHER 条目持久性 | DESCRIPTIVE_ONLY | DESCRIPTIVE_ONLY | DESCRIPTIVE_ONLY | CONDITIONALLY |
| Q8 单模态"可读" | NOT_COMPARABLE（定义不同） | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE（CA-MER 缺 16 类单模态） |

**没有任何一个跨数据集科学量达到 `DIRECTLY_COMPARABLE`。** 这本身是结论：四个数据集在冲突对象、标签接口、响应格式、顺序设计上都至少差一项，共同点只有"模型输出是否落在两个源标签上"这一粗粒度读数。

## 3. 内部可直接比较的情形（不跨数据集，仅作 sanity）
- ET Phase2 AV 冲突 vs ERI1 CLEAN：`DIRECTLY_COMPARABLE`，实测 292/292 试次结果相同。
- LISTEN 3A/3B/3C 的 base 条目匹配：已核实标签完全一致；但提示/GT 定义/选项随机序不同，只是 `CONDITIONALLY_COMPARABLE` 的条件对比。

## 4. 对横向分析的约束
1. 不得把 CA-MER 16 类伪标签冲突与 ET 的 7 类人工标注冲突合并成"自然冲突"一个总体。
2. 不得把 MCR 的"文本断言"当作与 ET 文本同类的"文本模态"。
3. LISTEN 的 OTHER 率不得与 ET/MCR 的 OTHER 率直接比大小（选项表含 8+个增补标签，字母位置随机）。
4. 凡涉及 B3 熵特征的比较，都要写明它们是在 EmotionTalk 的 7 类候选空间里测得的，对 LISTEN/CA-MER 属"近似"。
5. 数据集层面的 AUROC/log loss 排序不能解读为"机制强弱"（已有文档同样结论）。
