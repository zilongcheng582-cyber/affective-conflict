# 00 审查范围与 HEAD 锁定

审查对象：PR #6 "Evidence archive: EmotionTalk E1 video and E2 consistency interventions"
（https://github.com/zilongcheng582-cyber/affective-conflict/pull/6）

## 远端重新确认（2026-10-12，GitHub API + `git fetch`）

| 项 | 值 | 与任务给定值一致 |
|---|---|---|
| PR head ref | `evidence/emotiontalk-e1-e2-interventions-v1` | 是 |
| PR head SHA | `5cebd143e5c2c5e31df260383a96b45ab780efee` | 是 |
| PR base SHA (main) | `0f902da6b0910d456010d5b1640b73bb30436923` | 是 |
| 状态 | open, **draft**, mergeable_state=clean | — |
| Commits | `c837361`（科学载荷）、`5cebd14`（clean-checkout 审计记录） | — |
| 变更文件 | 78 个，全部为新增（`git diff --name-status` 全部为 `A`） | 是 |
| 修改历史文件 | 0 个 | — |
| CI check runs | 0 个（仓库没有对此 PR 运行 CI） | — |
| Reviews / 评论 | 0 / 0 | — |

## 隔离方式

- PR 源码在 scratchpad 中以 `git worktree add --detach … 5cebd14` 独立检出，**只读**。PR 分支没有任何写入。
- 审查产出只写入本分支 `claude/affective-conflict-pr6-audit-b7ohnb` 的 `reviews/pr6_independent_scientific_audit_v1/`。
- 交叉核验所用的 main 文件为只读：`manifests/emotiontalk/source_measurements.csv`、`EMOTIONTALK_PHASE2_POPULATION_PLAN_V1_2.json`、`protocols/emotiontalk/EMOTIONTALK_CANDIDATE_SEQUENCES_V1.json`、`results/eri1_scientific_closure_v1/*`，以及冻结运行时依赖 `src/emotiontalk/{phase1,phase2,reliability_v1}`、`src/common/benchmarks/emotiontalk_controlled_parser_v1.py`。
- 冻结源码提交 `34aa1b0`（E1/E2 RUN_PROTOCOL 中的 `source_code_commit`）是 main 的祖先。8 个关键运行时依赖文件在 `34aa1b0` 与 main 之间**逐字节相同**（已核对 SHA256），因此对 main 上这些文件的静态审查即是对实际执行代码的审查。

## 范围内已审查的源代码

E1：`e1e2_common.py`、`e1v2_cpu_gate.py`、`e1v2_parallel_gate.py`、`e1v2_pipeline.py`、`e1v2_runner.py`、`e1v2_analysis.py`、`e1v2_verify.py`、`e1v2_cpu_contract_test.py`、`replay.py`。
E2：`e1e2_source_gate.py`、`e1e2_media_gate.py`、`e1e2_pipeline.py`、`e1e2_full_runner.py`、`e1e2_analysis.py`、`e1e2_verify.py`、`replay.py`。
冻结依赖：`phase1/execution.py`（`build_messages`、`score_candidate_strings`、`perform_arm`）、`phase2/core.py`（`ORDER`、`build_messages`、`classify`）、`phase2/execution.py`（`execute_pairwise_record`）、解析器、`reliability_v1/audio.py`、`design.py`。
结果：两个 `results/` 目录中的全部 CSV/JSON/MD 文件，以及 `evidence/provenance/emotiontalk_e1_e2_migration_v1/*`。

## 未审查 / 无法访问（不视为 PASS）

- AutoDL 私有原件：原始媒体、派生视频/音频、原始生成文本、逐 token 评分记录、`RUN_PROTOCOL.json`/`DESIGN_SPEC_PRE_MEDIA.json` 字节、带时间戳的执行日志。本容器**没有** AutoDL 访问权限，也没有尝试访问。
- 模型权重和 GPU 推理：按要求未执行。
- 因此，凡依赖上述原件的结论，均标记为 `UNVERIFIED_DUE_TO_SOURCE_ACCESS`，或注明“仅静态审查”。
