# 08 安全、授权与许可审查

范围：全部 260 个新增文件（head `18b99caa`）。PR 之前的 Git 历史不在本次变更范围内（PR 没有改写历史；5 个提交全部为新增）。

| 检查 | 方法 | 结果 |
|---|---|---|
| 密钥 / token / 密码 / 私钥 | 正则：AKIA、ghp_、github_pat_、sk-、hf_、xox?-、BEGIN PRIVATE KEY、password/api_key/secret/token 赋值 | ✅ 0 命中 |
| 邮箱 | 正则 | ✅ 0 |
| 个人路径 | `C:\Users\…`、`/home/<user>`、`/Users/<user>`、OneDrive/Desktop/AppData/用户名 | ✅ 0；Windows 个人路径已被替换为 `LOCAL_REFERENCE_ARCHIVE/…` |
| 绝对路径 | `/root/autodl-tmp/...` 在 79 个文件中出现 20,843 次（锁文件、来源列、`native_audio_path`）；`D:\affective-conflict\data\MCR-Bench\…` 4 处 | ⚠️ F15 (P3)：不含个人信息，用于 provenance，PR 已说明；暴露了 AutoDL 目录结构 |
| IP / URL | 正则 | ✅ 0 |
| 受限数据集原文 / 原始生成 | 扫描所有 CSV 列与 JSON 叶节点中名字像 raw/text/answer/prompt/… 且长度>40 的字段 | ⚠️ **F06 (P3)**：`MCR_POOL_AND_DUPLICATE_AUDIO_AUDIT_V2.public_projection.json:4998,5015,5032` 保留了 3 条 `native_adversarial_source_text` 和 `controlled_text_evidence`——同类字段在兄弟文件 `MCR_1000_NATIVE_TO_909_CONTROLLED_IDENTITY_V2.public_projection.csv` 中被当作“unreviewed raw text”删除了；而 allowlist 的 transformation_rule 只列出 `/docs/*/text` 字段。**没有新增暴露**：同样的 MCR-Bench 提示模板在 main 的 `manifests/mcr/canonical_arbitration.csv` 中对全部条目公开。但这与 `MIGRATION_SAFETY_REVIEW.json` 的 PASS 描述不一致 |
| LISTEN（MUStARD）原文、CA-MER 原始输出 | 列检查 | ✅ `raw_model_output`、`raw_generated_sequence`、`raw_answer`、`source_text` 均已删除；只保留标签、选项、哈希 |
| 原始媒体 / 数据集归档 / 权重 | 扩展名与 `file` 类型检查 | ✅ 无 |
| 第三方未授权源码 | 只包含作者自己的分析脚本；runner/probe 内容被排除（3 个 UNSAFE_TO_UPLOAD 已扣留） | ✅ |
| 可执行恶意内容 | AST + 正则：无 `eval/exec/pickle/os.system`、无网络库、无 `rmtree/remove` | ✅ |
| Git LFS / 大文件 | 无 LFS；最大 3.8 MB | ✅ |
| 不安全 shell 命令 | 只有 `subprocess.run(['git', ...])` 列表形式，以及一次 `python3 replay.py --prepare-only`（`phase4_seal.py:31`，AutoDL 路径） | ✅ |
| 意外网络访问 | 无 | ✅ |
| 隐藏的推理 / GPU 路径 | 无 torch/transformers/CUDA/from_pretrained 调用（唯一命中是字符串常量 `cuda_oom` 与 source_read 中的正则） | ✅ |
| import 时副作用 | PR 声称的 6 个“安全”模块：import-safe ✅。历史归档脚本（`expanded_original/*`、`reconciliation_original/*`、`contract_focus_stream.py`、`replay_closure.py`、`phase4_replay.py`）在**模块顶层执行**：遍历 AutoDL 目录、写输出、创建目录；finalizer 会**追加修改 AutoDL 导航文档**（`phase4_finalize.py:208–209`、`finalize_expanded.py:49–52`）。在 clean checkout 中路径不存在，会立即报错 | ⚠️ F16 (P3)：建议在这些文件头或目录 README 中加上 “DO NOT EXECUTE – historical archive” |
| 修改全局环境 | `sys.path.insert` 指向 AutoDL 路径（仅在作为脚本运行时） | ✅ 可接受 |

## 授权

* `MIGRATION_PROVENANCE.authorization`：“User explicitly authorizes reviewed independent branch push and unmerged PR; raw third-party content not assumed licensed.” 222 个 payload 均为 `USER_AUTHORIZED_SCIENTIFIC_METADATA_ONLY`。
* 派生的标签/哈希投影（MCR-Bench、MUStARD/LISTEN、CA-MER 伪标签）是否符合各数据集许可：本审查无法判断，需要数据所有者确认。main 已经公开同类元数据，因此本 PR 没有引入新的类别。

## 结论

`SECURITY_AUDIT = PASS_WITH_NOTES`：没有密钥、个人信息、媒体或模型泄漏；1 处脱敏规则执行不一致（无新增暴露）；绝对路径和可执行的历史脚本是 P3 级维护项。
