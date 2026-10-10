# 00 PR #4 审查范围与提交身份

审查类型：独立、只读的合并前审查（READ-ONLY REVIEW）。未修改 PR 分支、未推送 main、未合并、未使用 GPU、未加载模型、未重新拟合。

## 绑定身份（已从 GitHub 重新核实）

| 项 | 值 | 核实方式 |
|---|---|---|
| PR | https://github.com/zilongcheng582-cyber/affective-conflict/pull/4 | GitHub API `pull_request_read get` |
| 状态 | open，未合并，非 draft，`mergeable_state=clean` | GitHub API |
| 源分支 | `evidence/recovered-science-transfer-phase4-v1` | GitHub API + `git ls-remote` |
| head SHA | `18b99caa5c11c3719e67ccbd3a0c71a0d70a77d7` | API、`refs/pull/4/head`、分支 ref 三者一致 |
| base SHA | `544ca0efae158df369a7b25dd110dc4254f67a7d`（= 当前 `main`） | API + `git ls-remote` |
| merge-base(head, base) | `544ca0efae158df369a7b25dd110dc4254f67a7d` | `git merge-base` |
| 二进制 diff SHA256（`git diff --binary base head`） | `8c17b3901439f5ba9ae04d9756e41dd58b5773fd65ffd3150f88d21793f10e2e` | 本地计算 |
| 变更文件 | 260，全部为 `A`（新增），0 个 M/D/R | `git diff --name-status` |
| 新增字节 | 17,189,976（与 PR 描述一致） | `git cat-file -s` 求和 |
| 行数 | +83,778 / −0 | `git diff --stat` |
| CI 检查 / commit status | 0 个 check run，combined status `pending`、0 statuses（仓库未配置 CI） | GitHub API |
| Reviews | 0 | GitHub API |
| 合并冲突 | 无（`mergeable_state=clean`，纯新增） | GitHub API |

审查结束时（2026-10-10T12:30Z）再次核对：head 仍为 `18b99ca…`，base/main 仍为 `544ca0e…`。**本审查结论只对 head `18b99caa` 有效**；若 head 变化，结论自动失效。

## 提交清单（base..head）

| # | SHA | 作者 | 内容 | 文件变化 |
|---|---|---|---|---|
| 1 | `8679809a184408423f346f3d24d22c7f652ff09a` | Claude（session 019q…） | Four-regime synthesis V1 | 70 A |
| 2 | `566e41c8f32ccf8090bc1c2ba20e366913434054` | Claude | Four-regime Revision V2（errata） | 17 A + 6 M（仅修改本 PR 内第 1 个提交新增的文件） |
| 3 | `be83e5125903a7e6365a2124cfd5bd41e8666247` | zilongcheng582-cyber | 恢复证据、Transfer Phase4 归档 | 168 A |
| 4 | `41f2681c3e8fe36771237e407546fef149376104` | zilongcheng582-cyber | clean checkout 验证与证据身份 | 2 A + 8 M（仅迁移元数据） |
| 5 | `18b99caa5c11c3719e67ccbd3a0c71a0d70a77d7` | zilongcheng582-cyber | 包级 SHA256 清单与安全复核 | 3 A + 3 M（仅迁移元数据） |

70+17+168+2+3 = 260 ✓。`claude/funny-brahmagupta-i7mdam` 分支 head 仍为 `566e41c`，确认第 1–2 个提交按原历史复用。

## 审查环境

| 项 | 值 |
|---|---|
| 主机 | Claude Code 云容器（Linux 6.18.44 x86_64），**不是 AutoDL**；无 GPU；无 AutoDL 私有资产 |
| 审查目录 | `/root/autodl-tmp/affective-conflict-pr4-review-v1/`（新建；`checkout/` 为独立 clone，HEAD 固定在 `18b99caa`） |
| Python | 3.13.16 |
| 依赖 | numpy 2.5.3、pandas 3.0.5（系统）；在审查 venv 中安装 scipy 1.18.1、pytest 9.0.3；**未安装** torch / transformers / sklearn |
| 审查时间 | 2026-10-10 UTC |
| 工作树状态 | 审查 checkout 的已跟踪文件始终干净（`git status` 仅有被忽略的 `__pycache__`） |

## 范围限制（如实说明）

* AutoDL 受限源（原始 JSONL、媒体、原文、导航备份）**不可访问**，因此所有需要这些资产的项目最多只能做到 `GITHUB_CLEAN_CHECKOUT_REPLAY_PASS`，不能给出 `AUTODL_RESTRICTED_SOURCE_REPLAY_PASS`。
* `recovered_evidence_scientific_analysis_v1` 与 `transfer_failure_integration_v1` 的原始脚本硬编码 `/root/autodl-tmp/...` 路径，在 clean checkout 中无法执行；对它们做的是静态审查 + 基于公开投影的独立重算。
