# 09 可重复性与测试报告

环境：Claude Code 云容器，Linux 6.18.44 x86_64，Python 3.13.16，numpy 2.5.3，pandas 3.0.5，scipy 1.18.1，pytest 9.0.3（审查 venv），**无 torch**，无 GPU，**无 AutoDL 私有资产**。所有命令都从 `/root/autodl-tmp/affective-conflict-pr4-review-v1/` 运行；`checkout/` 固定在 `18b99caa`。

| # | 测试 | 命令 | 结果 | 日志 | 是否依赖 AutoDL |
|---|---|---|---|---|---|
| 1 | Git diff 静态检查 | `git diff --name-status/--numstat/--binary 544ca0e 18b99ca` | ✅ 260 A，0 M/D；diff sha `8c17b390…` | 00/01 | 否 |
| 2 | Python 静态解析 | AST 解析 4 个新增分析目录下全部 `.py`（38 个） | ✅ 38/38 | 02 | 否 |
| 3 | import 安全 | AST 顶层语句扫描 + 在空 sandbox 中 `-B` import | ✅ 6/6 个声称安全的模块 import 无副作用；历史脚本顶层会执行（F16） | 02 | 否 |
| 4a | 现有 36 个测试 | `venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=../pytest_tmp/36 tests/test_post_audit_closure.py tests/test_evidence_anchors.py` | ✅ **36 passed** | 终端输出 | 否 |
| 4b | 完整测试套件（参考） | `pytest -q tests` | 71 passed / 4 failed / 1 skipped；**base main 544ca0e 上完全相同**（torch 缺失 ×2；`test_release_contracts` 的 AST 哈希对 Python 3.13 敏感 ×2）→ 环境问题，不是 PR 引起的 | 终端输出 | 否 |
| 5 | 新增边界测试 | `PR4_CHECKOUT=$PWD/checkout venv/bin/python -m pytest -q review_tests` | ✅ **29/29 passed**（其中 6 个把缺陷固定为可复现行为） | `logs/review_tests.txt`、`logs/review_tests_detail.txt` | 否 |
| 6 | 科学投影行数 | r03/r04/r05 | ✅ MCR 4000 / 1000 / 909；CA-MER 6000 / 5825 / 1500；LISTEN 1149×2 / 381 / 378 / 167 | `logs/r03_mcr.json`、`r04_listen.json`、`r05_camer.json` | 否 |
| 7 | SHA256 证据核验 | r01 | ✅ 259 + 52 + 67 + 31 条，0 失败；allowlist 222/222 | `logs_r01.json` | 否 |
| 8 | 18 组冻结 Transfer 指标复算 | `python3 -I review_scripts/r06_transfer_replay.py checkout logs/r06_transfer_replay.json` | ✅ 18/18，相对 main 冻结表和 PR 表的误差都是 0.0；特征从 corrected B3 重新推导（误差 0） | `logs/r06_*` | 否 |
| 8b | PR 自带验证器 | `python3 -I checkout/analyses/transfer_failure_integration_v1/validate_migration.py --report logs/validate_migration_report.json` | ✅ PASS（259 / 18 / 2.22e-16）——但见 F04、F09 | `logs/validate_migration.stdout` | 否 |
| 9 | 主要分析表内部一致性 | r07（116 个子组）、r08（分解文档中的数字） | ✅ 115/116 精确（剩 1 行审查方无法重建），r08 全部一致 | `logs/r07_*`、`logs/r08_*` | 否 |
| 10 | 随机种子 / 重复运行稳定性 | 在独立 clone 中完整重跑 `python -m analyses.four_regime_synthesis_v1.run_all` | ✅ 61/61 个科学输出与已提交版本逐字节一致（只有 provenance/manifest 元数据不同） | `logs/four_regime_replay.stdout` | 否 |
| 11 | Linux 独立 checkout | 全部以上 | ✅ | — | 否 |
| 12 | Windows/Linux 字节敏感性 | `core.autocrlf=true` 模拟 clone + r01 + 验证器 | ⚠️ 222 个 payload 不受影响；`.gitattributes` 与 `docs/RECOVERED_EVIDENCE_MIGRATION_V1.md` 被转换 → 验证器失败（F03） | `logs/crlf_sim_integrity.json` | 否 |

## 复算范围声明

* `GITHUB_CLEAN_CHECKOUT_REPLAY_PASS`：文件身份；18 组指标点估计 + 分母 + 身份；Phase4 子组点估计；MCR/CA-MER/LISTEN 投影计数与分组；四区制综合完整重跑。
* **未复现**（需要 AutoDL 或本次未执行）：`recovered_evidence_scientific_analysis_v1` 与 Phase4 脚本对原始 JSONL 的完整执行；全部 bootstrap / sign-flip CI 与 p 值（冻结 seed 20261008，Phase4 seed 20261010+tag）；原始媒体身份；177 条科学清单重哈希；6 个 AutoDL replay 哈希；CA-MER 科学等价性决定。
* 因此：`AUTODL_RESTRICTED_SOURCE_REPLAY_PASS` = **NOT VERIFIED**。本审查不扩大 PR 的可重复性声明，并确认 PR 自己也没有声称 `GITHUB_CLEAN_CHECKOUT_FULLY_REPRODUCIBLE`。
