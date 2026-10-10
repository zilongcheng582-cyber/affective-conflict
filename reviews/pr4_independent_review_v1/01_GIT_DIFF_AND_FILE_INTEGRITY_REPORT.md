# 01 Git diff 与文件完整性报告

脚本：`review_scripts/r01_integrity.py`（日志 `logs_r01.json`），`review_scripts` 下其他脚本见 09。

## 1. 文件级检查

| 检查 | 结果 |
|---|---|
| 只有新增？ | ✅ 260 个文件全部为 `A`；0 个修改/删除/重命名 |
| 已冻结文件被改？ | ✅ 否。base 树中全部文件逐字节与 head 一致（PR 验证器 + 本审查 `git diff` 双重确认） |
| 86 个 main 冻结资产哈希一致 | ✅ 独立核实 86/86：`GITHUB_GAP_ANALYSIS.csv` 中 `main_status=ALREADY_PRESENT_IDENTICAL` 的每一行，`git show 544ca0e:<path>` 的 SHA256 = 记录的 source/target SHA |
| 空文件 | 1 个：`analyses/four_regime_synthesis_v1/__init__.py`（0 字节，合法包标记） |
| `.gitignore` 绕过 | ✅ `git check-ignore --no-index` 对 260 个路径均无命中；无 `.wav/.mp4/.npz/.parquet/.zip/.safetensors/.bin` |
| 大文件 / LFS | 最大文件 3,827,448 B（`CAMER_6000_KEY_RECONCILIATION_V2.public_projection.csv`）；无 LFS 指针 |
| 二进制文件 | 无；`MCR_NATIVE_FOUR_CONDITION_PAIRED_PROJECTION_V2.public_projection.csv` 被 `file` 识别为 `data`，原因是 `source_record_key` 中含 `\x1f` 分隔符（P3 便携性备注） |

### 同内容不同路径（冗余）

| 内容 | 路径数 | 说明 |
|---|---|---|
| 通用 README（2,894 B，sha `ff2e24c9…`） | 16 | 每个目录的 README 都是同一份迁移总说明，不描述各自目录 → **F08 (P3)** |
| `MIGRATION_ALLOWLIST.csv` = `MIGRATION_FILE_SHA256.csv` = `MIGRATION_LINEAGE_MAP.csv`（121,141 B） | 3 | 声称角色不同的三份机器清单逐字节相同 → **F08 (P3)** |
| `INPUTS_USED_a02_{camer,listen,mcr}.json`；`a04`=`a05`；`a02_et`=`a02_et_extras` | 3+2+2 | 运行时登记的自然重复，无害 |
| `AUTODL_PHASE4_REPLAY_CHECK.json` = `phase4_replay_same_seed/PHASE4_REPLAY_CHECK.json` | 2 | 有意的副本（已登记为 renamed copy） |

未发现重复的科学结果被当作两份独立证据。

## 2. SHA256 / 清单核验

| 清单 | 条目 | 结果 |
|---|---|---|
| `evidence/provenance/recovered_evidence_migration_v1/SHA256SUMS.txt` | 259（= 260 − 自身） | ✅ 0 失败 |
| `results/historical_evidence_reconciliation_v2/SHA256SUMS.txt` | 52 | ✅ 0 缺失 / 0 不符 |
| `results/recovered_evidence_scientific_analysis_v1/SHA256SUMS.txt` | 67 | ✅ |
| `results/transfer_failure_integration_v1/SHA256SUMS.txt` | 31 | ✅ |
| `MIGRATION_ALLOWLIST.csv` | 222 行 / 222 唯一 target | ✅ target SHA 全部吻合；`bytes` 列与实际大小全部吻合；`byte_identical` 标志与 source==target 一致；全部 target 都在 PR diff 中 |
| 字节一致 / 脱敏派生 | 209 / 13 | ✅ 与声明一致 |
| 13 个脱敏派生的 source SHA | — | 11/13 被原始 AutoDL 清单（`AUTODL_ORIGINAL_OUTPUT_SHA256SUMS_V2.txt`、`AUTODL_ORIGINAL_SHA256SUMS.txt`）独立佐证；2 个（expanded 包的 `MCR_NATIVE_FOUR_CONDITION_RECOVERY`、`OWN_CODE_AND_CHECKPOINT_SUPPLEMENT`）只由 allowlist 自身记录 → **F17 (P3)** |
| 脱敏 CSV 行数保持 | — | MCR 1000 / 4000、CA-MER 6000、LISTEN 381 / 1149 / 1149 与原始记录数一致（`OUTPUT_RECORD_COUNTS_V2.json`） |

## 3. 已知数值差异（重点）

| 数字 | 出处 | 实际含义 |
|---|---|---|
| **16,358,604** | PR 描述；最终 `MIGRATION_PROVENANCE.json` `payload_bytes`；allowlist `bytes` 列求和；**本审查实测 222 个 payload 文件字节和** | ✅ 正确的最终值 |
| 16,372,023 | 提交 `be83e51` 中的 `MIGRATION_PROVENANCE.json` | 早期快照：当时 allowlist 记录的是 Windows CRLF 转换后的工作区字节（该快照只有 123/222 个文件被判为 byte-identical）。与最终值差 13,419 B，即 CRLF 换行转换带来的膨胀 |
| **16,372,203** | 最终 `MIGRATION_VALIDATION_REPORT.md:7` | **任何快照都不存在这个值**：它是过时的 16,372,023 再加上 023→203 的数字错位。与最终值差 13,599 B |

结论：这个差异**不是**文件范围不同，也**不是**新 manifest 被算进去（payload 统计不含迁移文档），而是：(a) 验证报告沿用了 Windows 换行转换之前的快照；(b) 同时又抄错了数字。`41f2681` 中修正了 `MIGRATION_PROVENANCE.json`，但没有修正报告正文。→ **F01 (P2，证据身份文档)**

文件计数：

| 数字 | 出处 | 含义 |
|---|---|---|
| 245 | `LOCAL_FIXED_METRIC_REPLAY_CHECK.json` `sha256_files` | AutoDL 本地复算时的清单大小（早于 be83e51 定稿） |
| 254 | `be83e51` 的 SHA256SUMS；`CLEAN_CHECKOUT_VALIDATION_V1.json`；验证报告“254 then-current” | be83e51 状态下的 clean checkout |
| 256 | `41f2681` 的 SHA256SUMS | 新增 CLEAN_CHECKOUT_VALIDATION、STAGED_REVIEW 之后 |
| 259 | 最终 `18b99ca` 的 SHA256SUMS | 新增 3 个包级 SHA256SUMS 之后 |

仓库内**没有任何已提交的回执**覆盖最终 head（259 条）；PR 描述里说的“259 entries pass”目前只在 PR 正文中出现。本审查在 `18b99ca` 上独立运行验证器：259/259 PASS（日志 `logs/validate_migration.stdout`）。→ 并入 **F01**。

## 4. `.gitattributes`、换行与跨平台

* `.gitattributes` 只对 9 个新增目录设置 `-text`，不覆盖任何已有的 main 路径 → 不改变已有文件的 checkout 行为 ✅。
* 新增的科学 payload 保留 CRLF/EOF 原始字节；Git blob 与 SHA256 一致 ✅。
* **跨平台模拟**（`core.autocrlf=true`，即 Windows Git 默认值，在 Linux 上模拟）：222 个 payload 文件全部保持字节不变 ✅；但 `.gitattributes` 与 `docs/RECOVERED_EVIDENCE_MIGRATION_V1.md` 没有 `-text` 属性，被转换成 CRLF，导致迁移 SHA256 校验失败，验证器在 `.gitattributes` 处抛 `AssertionError`。另外 main 的已有文件（如 `README.md`）在该模式下也会被转换，所以验证器“main 文件逐字节不变”这一项在 Windows 默认配置下同样会失败。而 README 明确给出了 Windows 用法。→ **F03 (P2)**（日志 `logs/crlf_sim_integrity.json`）

## 5. Provenance 映射

* source path → target path：222/222 唯一，无冲突。16 个文件改名（`.public_projection`、`AUTODL_ORIGINAL_*`），映射只记录在 allowlist 里；仍有约 30 个报告/锁文件引用改名前的文件名 → **F12 (P3)**。
* 原始 Git commit：`MIGRATION_PROVENANCE.source_code_commit = 34aa1b03…`（ERI1 冻结发布），在 main 历史中 ✅。
* `MIGRATION_EXCLUSIONS.csv`（58 行）的 `status` 列与 `reason`/gap 状态不一致：42 个 SUPERSEDED 被标为 `HELD_BACK_FOR_REVIEW`；6 行被标为 `CANDIDATE`（其中 3 行是 `UNSAFE_TO_UPLOAD`）→ **F05 (P2)**。
* 无法从公开 checkout 确认的项（单独登记）：177 条 AutoDL 科学清单重哈希；6 个 AutoDL 复跑输出 SHA 匹配；58 个被排除资产的 SHA；2 个 expanded 脱敏派生的原始 SHA。
