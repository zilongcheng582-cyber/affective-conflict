# 01 执行代码 Bug 审查（E1/E2 runner、gate、analysis）

结论：在静态审查与 24 项合成 fixture 回归测试范围内，**未发现会改变 E1 或 E2 数值结果的 CONFIRMED_BUG**。发现的问题都属于防护强度、记录方式或覆盖范围（F07、F09、F10、F14，均为 P3）。

路径简写：`E1/` = `analyses/emotiontalk_e1_video_v2/source_archive/`，`E2/` = `analyses/emotiontalk_e2_consistent_audio_v1/source_archive/`，`main:` = main 上的冻结依赖（与 `34aa1b0` 逐字节相同）。

## 逐项检查表

| 风险点 | 代码证据 | 判定 |
|---|---|---|
| trial_id 生成 | `E1/e1v2_cpu_gate.py:134-135` `E1V2|uid|condition|arm`；`E2/e1e2_media_gate.py:145` | 正确。2336/3375 唯一（独立复算） |
| 两种顺序的媒体位置 | `E1/e1e2_common.py:27-28` 使用 `core.ORDER`；`main:src/emotiontalk/phase2/core.py:79-81,275-286` | 正确。测试 `test_orders_place_media_correctly` |
| 候选标签↔选项映射 | 指令使用 UID 绑定的 `candidate_sequence`（`core.py:276`）；所有 146/225 个 item 与 main 的 `EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json` 一致 | 正确 |
| y_A/y_V 混淆 | `E1/e1v2_analysis.py:14-17` SIDE_V 取 `t['y_V']`，SIDE_A 取 `t['y_A']`；`core.classify` 中 M1=A。y_A/y_V 与 main `source_measurements.csv` 全部一致（独立复算） | 正确。测试 `test_yA_yV_swap_swaps_sides` |
| 文本证据泄漏到单模态/联合 arm | `e1e2_common.inputs` 设 `text=None`；`core.build_messages` 只在模态为 T 时加入文本 | 无泄漏。测试 `test_no_text_evidence_leak` |
| A_ONLY/V_ONLY 混入另一模态 | `main:phase1/execution.py:386-408` 只构造单一模态内容；`use_audio_in_video=False`；源视频经 ffprobe 断言无音轨（`E1/e1v2_cpu_gate.py:26`）；A_ONLY 运行时断言无视频（`E1/e1v2_runner.py:50`） | 正确。另见 F10：V_ONLY 的 `audio_input_count` 是写死的，不是测量值 |
| E1 音频随条件变化 | 每个 item 的 audio SHA 在全部条件下恒定（146/146，独立复算） | 无 |
| E2 视频随条件变化 | 每个 item 的 video SHA 在全部条件下恒定（225/225） | 无 |
| 视频同时含内部音轨与外部音频 | 原始视频和派生视频都 `probe()` 断言 0 条音频流；命令带 `-an` | 无 |
| 自动重试改变输入 | 重试复用同一 `inputs(t)`，最多 1 次（`E1/e1v2_runner.py:46-89`）。实际 0 次重试 | 无 |
| 中途重启换模型版本 | 每个 attempt 都写入 `run_fingerprint`；`check_lock` 每个 slot 重新哈希锁定文件。attempts.csv 中指纹唯一 | 无（指纹内容不公开） |
| 缓存键 / 输出覆盖 | attempt 文件名为 `sha256(trial_id).attemptN`，写入前 `assert not dest.exists()` | 无 |
| 解析失败被当作 OTHER | `E1/e1v2_analysis.py:16` 中非 `OK` 即 PARSE_FAIL；解析器严格（`main:…parser_v1.py`） | 正确。测试 `test_parse_fail_not_other`。E1/E2 实际 PARSE_FAIL 均为 0 |
| TECHNICAL_FAILURE 被错误排除 | ITT 保留全部 item，并报告 bounds（`E1/e1v2_analysis.py:39-40`；`E2/e1e2_analysis.py:34-42`）。实际技术失败为 0 | 正确 |
| scorer 失败与 generator 失败混淆 | E1 `classify` 只看 `generation_technical_failure`。scorer 失败不会删除生成结果（测试 `test_scoring_failure_does_not_delete_generation`） | 正确 |
| 取最后一次 attempt 的规则 | `sorted(...)[-1]`，并断言 attempt 编号为 `[1]` 或 `[1,2]` | 稳定。测试 `test_out_of_order_attempt_files_sorted` |
| 文件排序 / dtype 导致映射错位 | 所有 join 都按 `trial_id` 或 `(uid, condition, arm)` 键进行，不依赖行顺序 | 无 |
| CUDA/OOM 恢复改变计算契约 | 只做 `empty_cache` 后的同参数重试。实际 0 次 | 无 |
| assert 作为关键 Gate | 两个 source_archive 共 172 个 `assert`。在 `python -O` 下测试 `test_wrong_fingerprint_rejected`/`test_duplicate_attempt_rejected` 显示 gate 被绕过 | **F09 (P3, POTENTIAL_RISK_NOT_REPRODUCED)**：没有证据表明执行时用了 `-O`（流水线调用 `sys.executable -B`） |
| E2 `outcome()` 对 PARSER_EXCEPTION 的处理 | `E2/e1e2_analysis.py:14` 只把 `PARSE_FAIL`/`None` 视为解析失败 | **F14 (P3)**：在 E2 数据中不可达（0 行 PARSER_EXCEPTION） |
| 视觉帧契约 mismatch | `E1/e1v2_runner.py:52-61` 把实际消费的 4D 帧张量 SHA 与 gate 收据比对，不一致即抛异常 | 运行时防护存在。公开 replay 不检查该契约（F07） |

## 回归测试（合成数据，未触碰正式数据）

`review_tests/test_source_logic.py`：24 项测试。从 PR source_archive 用 AST 抽取函数（避免执行 AutoDL 路径副作用），并对 main 的冻结依赖直接测试。

覆盖的情形：y_A↔y_V 交换、PARSE_FAIL 与 OTHER 区分、PARSER_EXCEPTION、技术失败、scorer 失败不删除生成、E2 分类、严格解析器、两种顺序的媒体位置、无文本泄漏、单模态 arm 只含单一模态、候选顺序、全零（单类别）统计、Holm 教科书值、聚类比值估计按 item 加权、E1/E2 估计器一致、attempt ledger（错误指纹、重复 attempt、乱序文件、journal 修复幂等、pending 规则）、交互项符号。

- `logs/test_source_logic.log`：24/24 OK。
- `logs/test_source_logic_python_O.log`：24/24 OK。在 `-O` 下，测试断言的是 gate 已被绕过（错误指纹与重复 attempt 被静默接受），以此证明 F09 中“断言即 gate”的风险真实存在。

“缺失 condition”“重复 trial”“错误媒体 SHA”“单模态混入”“帧采样 mismatch”“缺失候选分数”这几类情形，在公开投影层面用 `review_scripts/adversarial_fixtures.py` 验证，见 07。
