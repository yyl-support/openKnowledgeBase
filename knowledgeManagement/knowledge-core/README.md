# Knowledge Core CLI

第一条可运行的团队知识流水线骨架。当前版本只处理本地 Git 仓库，以文件系统、SQLite 和独立 Git Wiki 验证：

```text
Git revision
  → immutable Source snapshot
  → NormalizedDocument
  → Claim candidates
  → Wiki candidate
  → human approval
  → approved Wiki Git commit
  → approved-only query
```

## 运行要求

- Python 3.9+
- Git
- 当前不依赖第三方 Python 包

## 快速开始

从 `knowledge-core/` 目录执行：

```bash
export PYTHONPATH="$PWD/src"
WORKSPACE="$PWD/.knowledge"
OUTPUT_DIR="../../output"

python3 -m knowledge_core.cli --workspace "$WORKSPACE" --output-dir "$OUTPUT_DIR" init

python3 -m knowledge_core.cli --workspace "$WORKSPACE" \
  source add-git \
  --repo /path/to/public/repository \
  --ref HEAD \
  --canonical-url https://github.com/owner/repository \
  --include report/ \
  --title "Project Name"
```

命令会返回 JSON，其中包含后续命令所需的 ID：

```bash
python3 -m knowledge_core.cli --workspace "$WORKSPACE" \
  normalize --source <source-id>

python3 -m knowledge_core.cli --workspace "$WORKSPACE" \
  claims extract --normalized <normalized-id> --model deterministic

python3 -m knowledge_core.cli --workspace "$WORKSPACE" \
  wiki build --source <source-id> --model deterministic

python3 -m knowledge_core.cli --workspace "$WORKSPACE" \
  review approve \
  --candidate <candidate-id> \
  --reviewer human-<id>

python3 -m knowledge_core.cli --workspace "$WORKSPACE" \
  query "project topic"
```

批准前，候选 Wiki 不会出现在查询结果中。批准成功后，页面写入 `--output-dir` 指定的独立 Git 目录；在本仓库中统一使用根级 `output/`。从仓库根目录运行时默认值就是 `output`，从 `knowledgeManagement/knowledge-core/` 运行时应显式传入 `--output-dir ../../output`。

## 当前模型 Adapter

`deterministic` 是用于开发流水线和自动测试的确定性 Adapter。它按文件提取可重复的候选 Claim，不代表真实 LLM 的理解能力，也不应被用于生产知识生成。

真实模型接入应实现相同的 Claim 与 Wiki 输出契约，不能将具体 SDK 写入领域逻辑。

### DeepSeek V4 Flash

项目包含不含密钥的 Profile：`config/models.json`。

```bash
python3 -m knowledge_core.cli \
  --workspace "$WORKSPACE" \
  --model-config config/models.json \
  claims extract \
  --normalized <normalized-id> \
  --model deepseek-v4-flash

python3 -m knowledge_core.cli \
  --workspace "$WORKSPACE" \
  --model-config config/models.json \
  wiki build \
  --source <source-id> \
  --model deepseek-v4-flash
```

`--include` 可以重复使用，用于将 Source 冻结到明确的仓库子目录。范围会进入 Source identity、manifest、哈希和来源定位；同一 revision 的全仓 Source 与子目录 Source 是不同实体。

`--canonical-url` 应用于本地 clone 的公开仓库，使 Source identity 和人类可读来源基于稳定的远端 URL，而不是机器临时路径。

当前本地实验 Profile 从 OpenCode 的认证存储中读取 `deepseek` Provider 的 Key，不会复制到项目或 CLI 输出。正式部署应改用 Profile 的 `api_key_env`，由部署环境注入密钥：

```json
{
  "api_key_env": "KNOWLEDGE_MODEL_API_KEY"
}
```

OpenAI-compatible Adapter 要求模型返回严格 JSON，并校验 Claim 引用的文件路径和块 ID。规整层把每个文件切成带稳定 ID 的语义块，模型只返回 `block_id`，程序把块映射回精确行范围并提取 `evidence_quote`——定位不依赖模型记忆行号。同时执行词项重叠校验：statement 与块内容无任何重叠词时整批拒绝。模型 Claim 在人工审核前保持 `evidence_status: unverified`。无效来源、缺失 Wiki 章节或 API/JSON 错误都会阻断候选产物生成。

Wiki 候选采用“可读文档与机器溯源分离”：构建信息位于最后，概览章节名为“整体概述”，正文不逐条堆叠块 ID 和行号；详细证据仍完整保存在 Claim JSON。数据罗列与方案比较使用 Markdown 表格，代码流程、架构和系统关系在证据充分时使用 Mermaid。`wiki build` 会自动执行生成后校验，也可独立校验人工渲染文件：

```bash
python3 -m knowledge_core.cli --workspace "$WORKSPACE" \
  wiki validate --file /path/to/candidate.md
```

DeepSeek Profile 对结构化抽取关闭 thinking 模式，避免推理内容耗尽最终 JSON 的输出预算。该参数属于 Profile，可按任务调整。

调试公开资料的模型格式错误时，可以显式设置 `KNOWLEDGE_MODEL_DEBUG_DIR` 保存模型响应正文。该目录不保存 Key、请求头或认证文件，仍不应在内部知识场景启用或提交到 Git。

## 当前边界

- 只支持本地 Git 仓库和固定 revision。
- 只规整常见 UTF-8 文本文件。
- 只实现批准流程，尚未实现驳回、纠正标注和重新生成指令。
- 查询是 approved Wiki 的简单全文匹配，不是 RAG 或语义搜索。
- 身份和 RBAC 尚未实现，`--reviewer` 只是审计字段。
- 尚未接入 GitHub Issue、PR、Review、内部 PDF 或真实模型。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

测试 seam 是 CLI 用户行为，覆盖完整纵向链路、Source 幂等登记和快照完整性阻断。
