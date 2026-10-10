# Historical Evidence Reconciliation V2

日期：2026-10-10（Asia/Shanghai）。标记：RETROSPECTIVE_EVIDENCE_RECOVERY。新配对投影是历史恢复资料，未执行新的推断统计检验；后续新增科学检验应标记 POST_HOC_EXPLORATORY，不改写冻结结论。

## 结论

历史资产已经足够开展 CA-MER 单模态可读性—联合离散选择关联，以及 MCR 原生同条目四文本条件配对分析；这些不需要重新生成标签。LISTEN 已有正向 native 3C 和完整选项表，但没有恢复到反向 T_THEN_A 或单模态预测正确后才入选的完整实验。CA-MER 完整16类熵无法由现存标签或七类分布恢复。MCR native 与 controlled 虽匹配同音频，prompt/候选顺序/系统包装不同，不可混合分母。

## 范围与只读保证

优先读 expanded-v1 的执行清单、恢复报告、MCR 四条件记录，读取 AGENTS 与三份导航 docs。复核原清单54条路径、定向关联代码/checkpoint、已索引7个实验归档及 source/LISTEN.zip，共8个原归档；没有重新遍历全目录。13份已恢复 CA-MER JSONL 分别检查，不把 gates、失败尝试与正式结果按最后一行覆盖。定向哈希了 MCR 原始媒体引用；没有遍历数据集或加载任何模型、torch、transformers。没有调用原实验 runner。

原报告参照是已下载的综合 Revision V2（566e41c8f32ccf8090bc1c2ba20e366913434054），复制保留在 synthesis_reference；本轮未重新同步 GitHub。所有历史输入再次哈希一致，导航 docs 和 frozen 文件均未更新。输出全在 `/root/autodl-tmp/affective-conflict-reconciliation-v2`。

## A. LISTEN 历史执行与门控

- V1 CSV、V2 current-release CSV 是阻塞占位：各1行标记，不是1个 trial。另有 V1 native JSONL 计划及100条 pilot 选样表，均不证明执行。计划表记录数见阶段登记；MCR 的 T_THEN_A 不属于 LISTEN。
- V3 与 V4 各6条 technical gate、各1149条 full 原始结果。V3 为 superseded/diagnostic，V4 是 source-aligned native。旧 V4 empty JSONL 只是保留的未执行占位，不覆盖后续完整结果。本次登记未发现额外 partial/full LISTEN reverse 运行。
- 在54份 JSONL、已索引相关代码/checkpoint、8个原归档定向成员中，LISTEN 实际 T_THEN_A=0。LISTEN 原生说明中提到该字符串的地方明确表示不加入 MCR 的受控反向臂；不是执行证据。结论限于可访问的恢复资产，不证明历史上从未运行。
- 实际 gate 是6条工程生成/解析 PASS。full runner 只检查该 gate PASS 和 manifest 行数，然后执行全部3C；官方 ZIP 源码也直接取 experiment_type=3B 来生成3C，correct_predictions 是计数器，不参与入选。因此不能恢复出一个历史上不存在于该执行控制流的“双侧预测正确才运行 joint”门控。
- V4 3A文本正确107/387，3B音频正确139/381；V3分别108/387、136/381。V4 3C381含378源标签冲突和3同标签；242个 joint 对应音频单模态未读对，证明它不是 DualReadable 入选池。
- 每个版本381条 joint 均有唯一音频观测；244条有严格匹配文本观测，137条没有。另用 normalized source ID + 实际文本输入 SHA 验证，覆盖仍244，不能用忽略文本差异的 ID 合并扩大资格。可观察双侧正确各22条是事后诊断子组，不能替代378/381正式分母，也不能声称在推理前门控。
- V3/V4 **1149/1149 源行 ID、数据行号、音频 SHA、文本 SHA 完全对应**，但 **0/1149 候选序相同，0/1149 prompt SHA 相同**。因此只能开展版本/RNG/prompt 捆绑变化的配对诊断；不能把它解释为纯选项位置干预，更不能并入 V4 主分析。
- 原始 assistant 回答、完整 raw_generated_sequence、字母→标签映射、随机候选序列及 OTHER/PARSE_FAIL 已按版本恢复到 ANSWER_OPTION_RECOVERY CSV。必须从每行候选表解析语义标签，不能直接比较字母。该表仍使用原解析结果；没有用新的 parser 改写历史输出。V3 对 V4 标签的 outcome 仅作严格身份通过后的诊断。

可开展：V4 正向选择和OTHER分类、22条可观察双侧正确子组描述、按语义标签的 V3/V4 版本敏感性。不能开展：同协议 LISTEN forward-versus-reverse 效应或完整正确性门控总体结论。若这些问题必须回答，才需要新冻结的 GPU 测量；不把本轮恢复当成新实验授权。

## B. CA-MER 6000键结果

| arm | 计划键/记录 | 生成成功/原始回答 | 可解析科学可用 | OOM | PARSE_FAIL |
|---|---:|---:|---:|---:|---:|
| A_ONLY | 1500 | 1500 | 1499 | 0 | 1 |
| V_ONLY | 1500 | 1442 | 1442 | 58 | 0 |
| A_THEN_V | 1500 | 1442 | 1442 | 58 | 0 |
| V_THEN_A | 1500 | 1442 | 1442 | 58 | 0 |

6000唯一(sample_id,arm)，5825科学可用+174 OOM+1 parser-unscorable。科学索引逐行映射到 immutable resource sweep 的原始行号和 SHA；非空媒体 SHA、候选序、标签映射均无不一致。原始 run_type=TECHNICAL_RESOURCE_SWEEP、scientific_result=false **保持不变**；科学可用性来自既有 D-016 equivalence 投影，不把技术运行重新标成正式 full。另一个正式 full 仅58记录（57成功+1 OOM）不能当作6000完整科学运行或与 sweep 按最后记录合并。

A_ONLY 匹配源侧标签702/1500；V_ONLY639/1500（639/1442成功可解析），交集316个条目。它们是源伪标签匹配，不是独立人类真值验证。联合两序的116 OOM来自同58个样本；V_ONLY也是这58条，而A_ONLY均已有回答。需要保留所有计划键与技术缺失，不静默删掉失败行。316双侧匹配条目可做选定子组的关联描述，不是 causal 识别或已门控实验。

生成归档只有离散标签/原始文本；processor token计数、tensor shapes 等不是 token logits，也不是候选评分。13份恢复 CA-MER JSONL 和8个定向原归档均未找到完整16候选数值向量。独立 corrected B3 确有 A/V各1500条七候选 log scores 与归一化概率；本轮重算 `-sum(p*log(p))/log(7)` 与已存 entropy 一致，概率归一化和媒体 SHA 均通过。它们来自不同测量prompt/candidate体系，不是原16类生成调用的 logits。

**CPU 可恢复七类 entropy，不能恢复16类 entropy。** 一个生成标签不能确定概率分布；七类 softmax 不含其余九类的总质量，改除以log(16)或补零均无效。现在不建议重跑3000条单模态生成。若以后明确需要完整16类 uncertainty，才需新候选评分协议/冻结和新的 GPU 评分；这不是补跑已有标签臂。是否需要该测量取决于科学目标，现存数据不要求自动新增它。

## C. MCR 四文本条件与受控身份

4000/4000 native 生成成功并保存原始回答。同1000 released source_index 的 neutral/faithful/adversarial/irrelevant 各1000。前三条件 parse OK各1000；irrelevant parse OK995、PARSE_FAIL_NO_LABEL5，不能静默剔除。原生 neutral 表示无额外描述的分类指令，不表示音频标签全为neutral。

909 controlled 条目全部与 native 按 source_index、音频相对路径、字节 SHA、音频标签匹配；controlled 3636条是909×A_ONLY/T_ONLY/A_THEN_T/T_THEN_A，不是四种文本关系。native adversarial 的 Description 行与909个 controlled text_evidence 逐条一致，**整个 source_text 0/909一致**：native还包含可靠性提示、Description包装及完整固定候选指令。

| 项 | Native | Controlled V3 | 可比性 |
|---|---|---|---|
| 文本关系 | 无额外描述、faithful、adversarial、irrelevant | 仅提取adversarial情感声明；四模态顺序臂 | 非同一干预 |
| 系统包装 | You are a careful emotion classification assistant. | build_conversation无显式system消息 | prompt改变 |
| 用户内容顺序 | audio后source_text | 按arm拼音频/声明，最后共同instruction | 不能识别纯文本效应 |
| 候选 | source_text固定七类顺序 | 14种C/R候选序，按item冻结 | 不能直接pool |
| 输出接口 | greedy16 tokens，trim后自由标签文本，项目parser | greedy16 tokens，trim后自由标签文本，同parser | 离散输出可对照；非评分向量 |
| 模型身份 | 同Qwen2.5-Omni-7B路径、类、processor、auto dtype | 同路径/类/processor，执行配置声明decoding held constant | 支持配置层一致；无可独立核验的两次运行权重字节快照，不能仅凭路径证明历史权重完全相同 |

native四条件可开展同条目的新的配对离散选择/准确率分析，不需GPU；faithful/adversarial各1000描述声明与gt同/不同均已核实。neutral对比其它条件还捆绑“额外描述包装是否存在”；不可称为仅改变情感声明。

**统计单位重要勘误：** native1000条目有947个路径、943个字节SHA。受控909条目有909个路径、**905个不同SHA**。冻结pool表里存的音频SHA与当前字节1000/1000、909/909、924/924全部吻合，差异不是本轮媒体改写造成。原pool规则排除76个同路径GT冲突记录，并移除15个同GT重复路径代表；但不同路径仍可字节相同。受控池中存在**1个字节相同却GT不一致的组，共3条目**。因此既有“909 unique physical paths”不能改写为“909独立且无歧义音频字节”。

新分析要保留1000 native released-item分母、909 controlled分母的区别，声明重复音频相关性、对源标签冲突做预先写明的探索性敏感性；不要默默去重/删除3条来改冻结结果。配对投影已经保存音频SHA，可支持按音频组处理相关性。标签含糊不能靠再跑模型解决。native与controlled的跨协议差异只能作探索性、受prompt/选项/包装混杂的对照，不能称为同协议四条件效果。

## D. 科学综合勘误与 GPU 优先级

综合报告07/08的“未取得CA-MER A_ONLY/V_ONLY”是当时本机无归档的证据状态，现应改为**已执行、有原始标签，但未纳入发布的联合科学投影/待CPU分析**。其“已有生成runner不保存16类评分”的结构判断仍成立。归档访问阻塞已经解除，但这不表示原综合报告全部新关联统计已执行完毕：本轮完成证据对账、投影和七类entropy验证，没有运行新的配对假设检验或重拟合。

MCR的“四种文本关系未运行”若指native则应撤回：native4000已完整；若指受控共同prompt/候选下的四文本关系，仍未运行。LISTEN T_THEN_A和真实正确性门控full依然没有执行证据，不把MCR反向臂移植为LISTEN证据。LISTEN其它native计划条件也不能由计划文件证明执行。

修订建议：
1. **先CPU、不追加Qwen GPU**：CA-MER可读性与联合离散结果对账分析；MCR原生四文本条件配对分析；LISTEN语义标签/OTHER与版本诊断。所有新增检验单独记录为探索性。
2. 若核心问题是跨模态顺序/可读性门控，三数据集中真实缺口优先是**LISTEN同协议reverse与匹配单模态资格**；新协议冻结后才可GPU，不复用V3来补V4。
3. **CA-MER16类评分是条件性、新测量缺口**，优先级低于先用已有标签完成CPU解释。既有3000个A/V生成不需要重复；若真的需要16类熵，新增GPU教师强制评分仍不可由CPU替代。
4. **MCR原生四文本关系不进入补跑队列**。只有科学目标明确要求共同controlled prompt/候选序下的faithful/irrelevant等反事实时，才另设计冻结新的实验；这不是历史恢复。

原08对ERI1一致样本降质控制(C)、视频反向干预(B)的因果识别讨论不会因为恢复MCR/CA-MER离散标签而被自动推翻；这两项在本轮三数据集历史对账之外。其新干预数据不能从现有标签恢复。没有“一次最终Qwen GPU实验必需”的新结论；维持原限定主张可以停止新增Qwen实验。

## 关键原资产路径、实际计数与SHA256

| 资产 | 准确路径 | SHA256 | 实际记录数 |
|---|---|---|---:|
| LISTEN/V1 all-native manifest | `/root/autodl-tmp/affective-conflict/audit/QWEN25_LISTEN_NATIVE_V1/listen_native_qwen25_manifest_v1.jsonl` | `3503029c16e219327b6f8dff9660e684fa789d3d96365869d3f9d621e5b2bdfc` | 21899 |
| LISTEN/V3 technical gate | `/root/autodl-tmp/affective-conflict/audit/QWEN25_LISTEN_NATIVE_V3/technical_gate_outputs_local_v3.jsonl` | `b388962c39e4de0871124b314922d1eeb623f2688774465177a112e8c89b94e4` | 6 |
| LISTEN/V3 full native | `/root/autodl-tmp/affective-conflict/audit/QWEN25_LISTEN_NATIVE_V3/listen_native_raw_outputs_local_v3.jsonl` | `effdf7f070d99e38d127a3d9a9ecc2909dbe388d8985289ed4e6621cbc3f2993` | 1149 |
| LISTEN/V4 full native | `/root/autodl-tmp/affective-conflict/results/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/listen_native_raw_outputs_source_aligned_v4.jsonl` | `efb604ffcdd4f746cda961da0fa17f8fae995e34aa02779bf2334917c19e74ea` | 1149 |
| LISTEN/V4 canonical identity join | `/root/autodl-tmp/affective-conflict/audit/QWEN25_LISTEN_NATIVE_V4_SOURCE_ALIGNED/LISTEN_V4_CANONICAL_AT_JOIN_V1.csv` | `f11685ced0edcc9eb40700da3492eff7e6b43ec58569c3ab7fe8662722d610d6` | 1149 |
| CA-MER/immutable resource sweep four arms | `/root/autodl-tmp/affective-conflict/audit/QWEN25_CAMER_CONTROLLED_V1/resource_sweep_v1/qwen25_camer_controlled_resource_sweep_v1.jsonl` | `28194bdc880c375809228808e91a18c509573ff22acfaeaa416165446d4b905e` | 6000 |
| CA-MER/6000-key scientific availability index | `/root/autodl-tmp/affective-conflict/audit/QWEN25_CAMER_CONTROLLED_V1/scientific_equivalence_v1/CAMER_CONTROLLED_AVAILABLE_SCIENTIFIC_OUTCOMES_V1.csv` | `1bbde3b79d09b7ccd265ae63931420a3e73738ed227e570bec5f2c16b52c67d8` | 6000 |
| CA-MER/corrected B3 seven-class scores | `/root/autodl-tmp/affective-conflict_execution/B3_CORRECTED_TARGET_GPU_EXECUTION_V1/amendment_001/outputs/B3_MEASUREMENTS_V1.jsonl` | `0ad7785530a52923dabdf3ec6b3c5afe27e68d87be61e1b5f4465fde79fad450` | 6354 |
| MCR/native four text conditions | `/root/autodl-tmp/affective-conflict/audit/QWEN25_MCR_NATIVE_V1/full_run/qwen25_mcr_native_full_v1.jsonl` | `e20ede77e563d4bb5ae29c4b6f57308bd06c736dd4344e318e7acf560b0c6b77` | 4000 |
| MCR/controlled four arms | `/root/autodl-tmp/affective-conflict/audit/QWEN25_MCR_CONTROLLED_V3/full_run/qwen25_mcr_controlled_full_v2.jsonl` | `2772bd2d536caa4e55f1305300b4e9a523a5315afd37992c098d6724e4c25775` | 3636 |

每项对应runner与manifest路径/哈希见 THREE_DATASET_HISTORICAL_EVIDENCE_MATRIX_V2.csv；完整输入（包括原音频引用、代码、pool、归档）见 INPUT_SHA256_RECORD_COUNTS_V2.json。B3表的6354是全部数据集记录，CA-MER部分为3000，不混分母。code/manifest缺少独立完整producer证明的地方仍注明，不把对应源码文件存在当作运行证明。

## 恢复输出

- LISTEN_V3_V4_STRICT_IDENTITY_JOIN_V2.csv：1149严格源身份对账及科学pool禁令。
- LISTEN_V3/V4_ANSWER_OPTION_RECOVERY_V2.csv：各1149原始回答、候选字母映射、随机序与OTHER。
- LISTEN_UNIMODAL_CORRECTNESS_JOIN_V2.csv：两版本共762 joint，单模态匹配/未知资格保留。
- CAMER_6000_KEY_RECONCILIATION_V2.csv：6000计划键，原始来源行、失败和离散标签。
- CAMER_UNIMODAL_READABILITY_JOIN_V2.csv：1500条目资格诊断。
- CAMER_B3_SEVEN_CLASS_CPU_VERIFICATION_V2.csv：3000七类entropy复核。
- MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.csv：1000条目与909成员、媒体字节与文本来源。
- MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.csv：4000原始文本条件/回答/解析状态，不合并controlled。
- MCR_POOL_AND_DUPLICATE_AUDIO_AUDIT_V2.json：原pool规则、路径/字节差异、1组三条GT冲突。
- INDEXED_ARCHIVE_RECONCILIATION_V2.json：8原归档逐个路径SHA、定向member SHA和实际记录计数；零读取错误。

历史文件修改=NO；冻结协议修改=NO；GPU/模型重跑=NO；GitHub合并=NO；完成后STOP。
