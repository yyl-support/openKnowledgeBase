# 仓库扫描清单：forum-reply-robot

- 仓库路径：/tmp/forum-reply-robot
- 文件总数：138
- 目录数：19

## 目录统计（按文件数降序，前 60）

| 目录 | 文件数 | 字节数 |
|---|---|---|
| tests | 37 | 441204 |
| src/ForumBot | 18 | 169621 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents | 12 | 1390094 |
| src/update_lightrag | 11 | 78635 |
| . | 10 | 48113 |
| src/ForumBot/SchemaValidation | 9 | 255049 |
| tests/schema_validation | 9 | 94023 |
| backups | 5 | 114325 |
| src/evaluation | 4 | 15363 |
| tests/mdb_validation | 4 | 51093 |
| .ai-flow/deploy | 3 | 15283 |
| .ai-flow/deploy/test-sync | 3 | 16830 |
| src | 3 | 13594 |
| src/ForumBot/MdbValidation | 3 | 55346 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/tool-results | 2 | 127219 |
| src/ForumBot/MdbValidation/MdbRuleFiles | 2 | 107754 |
| config | 1 | 175 |
| projects/-private-tmp-forum-reply-robot | 1 | 410286 |
| src/ForumBot/SchemaValidation/SchemaFiles | 1 | 37567 |

## 规则候选文件

- CLAUDE.md
- Dockerfile
- requirements.txt

## CLAUDE.md 全文

### CLAUDE.md

```markdown
# CLAUDE.md

本文件为 Claude Code 及其他 AI 助手在本仓库工作时提供指引。内容描述的是代码当前的实际行为，修改代码时请同步更新本文件。

## 服务定位与核心功能

forum-reply-robot 是一个**自动监控论坛新帖并智能回复的机器人服务**。它常驻运行，周期性轮询论坛，对新帖调用大模型生成回答并自动发布，同时维护一套基于 LightRAG 的知识库用于检索增强。

服务承担两条相互独立的处理链路：

1. **常规问答回复链路**（`ForumMonitor._check_new_topics` → `_process_new_topics`）
   监控带指定标签/类别的新帖，对每个新帖依次执行：提示词注入检测 → 问题摘要 → 论坛站内搜索 + LightRAG 文档检索 → 调用大模型生成回答 → 答案相关性/质量双重校验 → 生成"AI 生成"提示语并折叠详细解答 → 调用论坛 API 发帖回复。全过程的 token 消耗、搜索结果、检索结果、处理记录均落库（PostgreSQL）并写 CSV。

2. **AI 预审回复链路**（`ForumMonitor._check_pre_audit_topics` → `_process_pre_audit_topic`）
   针对"预审"标签/类别的帖子，先解析帖子 HTML 判断作者是否已标记"准备好 AI 预审"（`parse_pre_audit_readiness`），就绪后**不做搜索/检索**，直接走结构化合规校验流程（Redfish Schema 校验 + MDB 规则校验），把校验报告作为评审意见回复。校验过程中的基础设施/服务异常（超时、限流、空响应等）会被识别并**拒绝发帖**，避免把服务错误当成评审意见发出去。

3. **知识库（LightRAG）维护链路**（`src/update_lightrag/`）
   启动时做一次全量初始化（`FullDataUpdate`），随后由定时器（`UpdateLightRAGTimer`，默认每天 18:00 UTC≈东八区凌晨 02:00）做增量更新。数据来源包括论坛帖子和 GitCode 仓库文档，处理后灌入 LightRAG 服务。

核心约束与设计取舍：

- **回复内容一律带"由 AI 生成，仅供参考"提示语**，常规回答会把"总结/结论"章节摘出来放在折叠块外，完整解答放进 `[details]` 折叠块。
- **去重以数据库为权威**：`forum_topics` / `pre_audit_topics` 表记录已见过的 topic_id，每轮只处理新 ID。数据库连接失败时跳过当轮而非崩溃。
- **失败容错**：单帖处理异常不影响其他帖子（逐帖 try/except continue）；大模型调用带重试与退避；注入检测/相关性/质量校验出错时**默认从严**（判为注入/不相关/不合格，宁可不回复）。
- **安全优先**：用户输入用随机字符串包裹后再喂给大模型以缓解提示词注入；config.yaml 加载后立即删除以防敏感信息落盘（见 `main.py` 的 `delete_config_file()`）。

## 技术栈与架构概览

**语言/运行时**：Python 3.10（Docker 基础镜像 `python:3.10-slim`）。

**关键库**（见 `requirements.txt`）：

- AI/大模型：`openai`（OpenAI 兼容接口，实际指向 SiliconFlow 等）、`langchain-openai` / `langchain-core`、`httpx`
- HTTP：`requests`
- HTML/数据解析：`beautifulsoup4`、`markdownify`（HTML→Markdown）、`pandas`
- Web 服务：`flask` + `werkzeug`（仅用于健康检查接口）
- 数据库：`psycopg[binary]`（PostgreSQL）
- 配置/日志：`PyYAML`、`python-json-logger`、`python-dotenv`
- 调度/重试：`schedule`、`retrying`
- 其他：`pytz`、`gitpython`、`netifaces`

**进程结构**（`main.py` 为唯一生产入口）：

主进程是一个 Flask 应用，仅对外暴露健康检查接口（`/health`、`/health/detail`），绑定到自动探测出的内网私有 IP（优先 `10.` 段，其次 `192.168.`）的 5000 端口。真正的业务逻辑跑在两个守护线程里：

```
main()
 ├─ 启动前检查 SchemaFiles / MdbRuleFiles 目录是否就绪（SchemaFiles 缺失则退出）
 ├─ load_config() → 随即 delete_config_file() 删除配置文件
 ├─ lightrag_data_init()        # 同步全量初始化知识库，失败则退出
 ├─ initialize_service()        # 起 MonitorThread（守护线程）跑 ForumMonitor.start() 轮询循环
 ├─ lightrag_data_update_timer()# 起 scheduler 守护线程跑 LightRAG 增量更新定时任务
 └─ app.run()                   # 主线程跑 Flask，提供健康检查
```

健康检查的"健康"判定依赖 `MonitorThread` 是否存活，因此监控线程崩溃可被外部探针感知。

**数据存储**：

- **PostgreSQL** 是权威存储，`DataProcessor.create_tables()` 启动时建表。主要表：`forum_topics`（已发现帖）、`processed_forum_topics`（已处理回复帖）、`forum_search_results`、`forum_retrieval_results`、`consume_tokens_topic`（token 消耗）、`pre_audit_topics` / `pre_audit_processed_topics`（预审链路）、`schema_debug_logs`（预审调试日志）。
- **CSV 文件**：与数据库并行写出，路径由 config 的 `paths` 段指定。
- **日志**：`logging_config.setup_logger` 配置，主日志 `logs/main.log` 带轮转（单文件 20MB，保留 4 份）。

**配置**：

所有运行参数集中在 `config/config.yaml`（已被 `.gitignore` 忽略，不入库）。`src/utils.load_config()` 负责加载。关键配置段：`api`（大模型）、`posts`（论坛发帖 API）、`search`（站内搜索）、`retrieval`（LightRAG 检索）、`database`、`paths`、`monitor`（轮询间隔、各类标签/类别/截止日期、预审字段）、`links`（拼链接用的 base url）、`schema_validation`（Redfish/MDB 校验的模型配置）、`pre_audit`、`timer`、`lightrag_paths`、`git`。大模型支持主备双模型（`model_name` + `model2_name`），部分校验调用失败时按列表顺序回退。

**外部部署**：`Dockerfile` 在构建期从 GitCode 远程仓库 `git clone` 拉取 Schema 文件（`Redfish_SchemaFiles`、`MDB_SchemaFiles`），这些文件不在本仓库中；用 `ADD .../info/refs` 让缓存随上游 HEAD 失效。镜像以非 root 用户 `appuser` 运行，并做了大量加固（删除编译器、收紧权限、关闭 history）。

## 子模块职责划分

```
forum-reply-robot/
├── main.py                       # 生产入口：装配线程、健康检查、目录/Schema 校验
├── config/config.yaml            # 运行配置（不入库）
├── Dockerfile                    # 构建期拉取 Schema，非 root 加固运行
├── src/
│   ├── utils.py                  # load_config / delete_config_file 等通用工具
│   ├── ForumBot/                 # 【核心业务包】问答与预审两条回复链路
│   └── update_lightrag/          # 【知识库维护包】全量初始化 + 定时增量更新
└── tests/                        # pytest 测试，含 mdb_validation / schema_validation 子目录
```

### `src/ForumBot/` — 核心业务包

| 模块 | 职责 |
| --- | --- |
| `monitor.py` | **编排核心**。`ForumMonitor` 跑轮询主循环，串起两条链路；负责相关链接拼接（`_generate_related_links`，融合 LightRAG 知识图谱链接与搜索结果链接，去重、限 5 条）、回复内容组装、落库/写 CSV。 |
| `forum_client.py` | **论坛 HTTP 客户端**。`ForumClient` 封装拉帖列表、拉单帖详情、发帖回复（`/posts.json`）、站内搜索、LightRAG 文档检索。底层拉帖逻辑委托给 `data_processor` 的模块级函数。 |
| `ai_processor.py` | **大模型调用层**。`AIProcessor` 封装所有 LLM 调用：问题摘要、提示词注入检测、答案相关性校验、答案质量校验、生成正式回答（带重试退避）、提取答案总结章节。用随机字符串包裹用户输入防注入；主备模型回退。 |
| `data_processor.py` | **数据与解析层**（最大模块，~1150 行）。`DataProcessor` 管理 PostgreSQL 连接/建表/读写、CSV 读写、token 落库；模块级函数处理拉帖、HTML→Markdown 转换、HTML 表格转换、JSON 块提取、预审就绪状态解析（`parse_pre_audit_readiness`）等。 |
| `image_processor.py` | 帖子图片相关处理。 |
| `token_tracker.py` | 全局单例 `token_tracker`，按 topic_id 累计 prompt/completion/total token 用量。 |
| `logging_config.py` | 日志器配置，导出 `main_logger`，支持文件轮转。 |
| `api_main.py` / `standalone_api.py` | **独立调试用 API 服务**（非生产主链路）。`standalone_api` 提供按需触发摘要/检索/回复等能力的 Flask 接口，`api_main` 是其命令行入口（默认 127.0.0.1:5085）。 |

#### `src/ForumBot/SchemaValidation/` — Redfish 结构化校验子包

预审链路的 Redfish 评审引擎。`end_to_end_check.py` 是对外入口（`run_schema_check`、`process_post`、`is_infrastructure_error_text`）：判断帖子是否与 Redfish/MDB 相关 → 提取评审点 → 三路分类（mdb/redfish/other）→ 逐点生成 URI 示例、做 JSON Schema 静态校验、做规则合规校验 → 汇总成 Markdown 评审报告。其余模块分工：`extract_reviews.py`（评审点提取与相关性判断）、`redfish_schema_validator.py`（JSON Schema 校验）、`redfish_uri_generator.py`（URI 返回体示例生成）、`redfish_review_workflow.py`（规则合规检查 + 规则集 `REDFISH_COMPLIANCE_RULES`）、`redfish_common.py`（`Config` 配置类与工具）、`schema_debug_logger.py`（调试记录）。Schema 定义文件在 `SchemaFiles/`（构建期拉取，不入库）。

#### `src/ForumBot/MdbValidation/` — MDB 合规校验子包

`mdb_classifier.py` 判断评审点是否与 MDB 资源协作接口相关；`mdb_checker.py` 的 `MdbComplianceChecker` 调用大模型按规则集校验单个评审点，支持同级评审点上下文以降低误报。规则集 JSON 在 `MdbRuleFiles/`（构建期从远程拉取）。该子包为可选：缺失时主流程降级跳过 MDB 校验，不致命。

### `src/update_lightrag/` — 知识库维护包

| 模块 | 职责 |
| --- | --- |
| `full_data_init.py` | `FullDataUpdate`：启动时全量初始化 LightRAG 知识库。 |
| `increment_date_update_timer.py` | `UpdateIncrementData`（执行一次增量更新）+ `UpdateLightRAGTimer`（用 `schedule` 每天 18:00 UTC 触发增量任务）。 |
| `lightrag_client.py` | `LightRAGClient`：与 LightRAG 服务交互（灌库/删除等）。 |
| `forum_data_Fetcher.py` | `ForumDataFetcher`：抓取论坛帖子数据作为知识源。 |
| `gitcode_client.py` | `GitCodeClient`：GitCode API 客户端。 |
| `gitode_full_fetcher.py` / `gitcode_api_increment_fetcher.py` | 分别做 GitCode 仓库文档的全量 / 增量抓取。 |
| `image_processor.py` | 知识源中的图片处理。 |
| `filter.py` | `Filter`：数据灌库前的过滤。 |
| `update_time.py` | 增量更新的"上次更新时间"读写（`get/save_last_update_time`）与幂等初始化（`init_last_update_time`：仅在「启动全量初始化」时调用一次，作为尽早落库的 best-effort）。读路径 `get` 自愈：表空时幂等补种水位（`config['last_update_time']` 或 `now()`）再回读，保证 DB 可达必返回有效水位；DB 不可达则抛 `UpdateTimeUnavailableError` 让定时任务跳过本轮。 |

## 关键依赖与外部接口

本服务是一个高度依赖外部系统的"胶水"服务，所有外部端点/凭据均来自 `config/config.yaml`。

### 外部服务依赖

| 依赖 | 用途 | 配置段 | 失败行为 |
| --- | --- | --- | --- |
| **大模型 API**（OpenAI 兼容，如 SiliconFlow） | 摘要、注入检测、答案生成与校验 | `api`（含主备 `model_name`/`model2_name`） | 重试退避；校验类调用失败时从严默认（不回复） |
| **校验用大模型** | Redfish/MDB 规则合规校验 | `schema_validation`（`MODELSCOPE_*`） | 识别为基础设施错误则拒绝发帖，重试 `MAX_RETRY` 次 |
| **论坛平台 API**（Discourse 风格） | 拉帖列表、拉帖详情、发帖回复（`POST /posts.json`） | `posts`（`base_url`/`api_key`/`api_username`） | 发帖失败记日志，不阻塞其他帖 |
| **站内搜索服务** | 按摘要搜相关主题 | `search`（`base_url`/`endpoint`/`source`） | 返回空列表，降级继续 |
| **LightRAG 服务** | 文档检索（RAG）+ 知识库灌入 | `retrieval`、`lightrag_paths` | 检索为空则用空字符串继续；若搜索也为空则跳过该帖 |
| **GitCode** | 知识源仓库文档抓取；构建期拉取 Schema/MDB 规则 | `git` / Dockerfile | 知识库更新失败记日志 |
| **PostgreSQL** | 权威数据存储与去重 | `database`（含 `sslmode`） | 连接失败跳过当轮，带重试（默认 3 次） |

### 关键内部接口（模块间约定）

- `ForumMonitor` → `ForumClient` / `AIProcessor` / `DataProcessor`：编排层依赖三大能力层，构造时注入同一份 config。
- 预审链路 → `SchemaValidation.end_to_end_check.run_schema_check(title, user_question, topic_id, config)`：返回 Markdown 评审报告字符串；`is_infrastructure_error_text(text)` 用于判断返回内容是否为不可发帖的服务异常。
- `parse_pre_audit_readiness(html_content, config)`：解析帖子 HTML 判断是否就绪做 AI 预审，返回 `True`/`False`/`None`（`None` 表示无法判定，跳过）。
- `token_tracker`（全局单例）：跨模块按 topic_id 累计 token，最终由 `DataProcessor.save_token_usage_to_db` 落库。

### 凭据与敏感信息处理

- `config/config.yaml` 含明文 API key / 数据库口令，**已被 `.gitignore` 忽略，切勿提交**。仓库内的版本是脱敏占位（key 被 `****` 掩码）。
- 生产启动时 `main.py` 加载配置后立即调用 `delete_config_file()` 删除配置文件，防止敏感信息长期落盘。
- 涉及凭据的改动需谨慎：不要在日志或回复内容中回显 key/口令。

## 开发与测试

- **运行**：`python main.py`（需先准备好 `config/config.yaml`、PostgreSQL、SchemaFiles 目录）。
- **测试**：`tests/` 下为 pytest 测试，`conftest.py` 提供 mock。运行 `pytest`（或 `python -m pytest tests/`）。新增功能/修 bug 时请补对应测试。
- **依赖锁定**：`requirements.txt` 多数依赖已固定精确版本，新增依赖请同样固定版本。
- 修改业务链路时注意保持**逐帖容错**与**从严默认**两条既有约定，不要让单点失败拖垮整轮或把服务错误当评审结论发出去。



```


## 全量文件清单

| 路径 | 字节数 | 二进制 |
|---|---|---|
| .gitignore | 710 | 否 |
| .last-cleanup | 24 | 否 |
| CLAUDE.md | 14505 | 否 |
| Dockerfile | 4075 | 否 |
| README.md | 12042 | 否 |
| main.py | 15324 | 否 |
| pytest.ini | 442 | 否 |
| requirements-eval.txt | 207 | 否 |
| requirements-test.txt | 101 | 否 |
| requirements.txt | 683 | 否 |
| .ai-flow/deploy/README.md | 3243 | 否 |
| .ai-flow/deploy/preview.sh | 10544 | 否 |
| .ai-flow/deploy/services.yaml | 1496 | 否 |
| .ai-flow/deploy/test-sync/README.md | 1557 | 否 |
| .ai-flow/deploy/test-sync/routes.sh | 3556 | 否 |
| .ai-flow/deploy/test-sync/sync.sh | 11717 | 否 |
| backups/.claude.json.backup.1787130310096 | 22865 | 否 |
| backups/.claude.json.backup.1787130402959 | 22865 | 否 |
| backups/.claude.json.backup.1787130494511 | 22865 | 否 |
| backups/.claude.json.backup.1787130686493 | 22865 | 否 |
| backups/.claude.json.backup.1787130795617 | 22865 | 否 |
| config/config.yaml | 175 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5.jsonl | 410286 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-a57d67455cbccf1aa.jsonl | 319611 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-a57d67455cbccf1aa.meta.json | 128 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-a99bba02beac1164c.jsonl | 157222 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-a99bba02beac1164c.meta.json | 128 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-aa661d3e2827e82df.jsonl | 338470 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-aa661d3e2827e82df.meta.json | 128 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-abe8dd5ea6320dd01.jsonl | 274760 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-abe8dd5ea6320dd01.meta.json | 128 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-ac0fcc432e99b6bba.jsonl | 250221 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-ac0fcc432e99b6bba.meta.json | 128 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-ac15dc068dcdd3731.jsonl | 49035 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/subagents/agent-ac15dc068dcdd3731.meta.json | 135 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/tool-results/b80ga5gf7.txt | 40885 | 否 |
| projects/-private-tmp-forum-reply-robot/96ecd3be-9f35-418f-9c32-c59647df2ad5/tool-results/bow7x26f0.txt | 86334 | 否 |
| src/__init__.py | 38 | 否 |
| src/external_api_app.py | 4843 | 否 |
| src/utils.py | 8713 | 否 |
| src/ForumBot/__init__.py | 38 | 否 |
| src/ForumBot/ai_processor.py | 19291 | 否 |
| src/ForumBot/api_main.py | 1206 | 否 |
| src/ForumBot/auth_middleware.py | 3082 | 否 |
| src/ForumBot/data_processor.py | 48235 | 否 |
| src/ForumBot/evaluation_hooks.py | 2209 | 否 |
| src/ForumBot/forum_client.py | 7394 | 否 |
| src/ForumBot/image_processor.py | 5846 | 否 |
| src/ForumBot/llm_token_usage.py | 3158 | 否 |
| src/ForumBot/logging_config.py | 2259 | 否 |
| src/ForumBot/monitor.py | 35028 | 否 |
| src/ForumBot/oidc_client.py | 12563 | 否 |
| src/ForumBot/prometheus_metrics.py | 2739 | 否 |
| src/ForumBot/rag_api.py | 10787 | 否 |
| src/ForumBot/rate_limiter.py | 7053 | 否 |
| src/ForumBot/rbac_middleware.py | 1756 | 否 |
| src/ForumBot/standalone_api.py | 5093 | 否 |
| src/ForumBot/token_tracker.py | 1884 | 否 |
| src/ForumBot/MdbValidation/__init__.py | 205 | 否 |
| src/ForumBot/MdbValidation/mdb_checker.py | 45274 | 否 |
| src/ForumBot/MdbValidation/mdb_classifier.py | 9867 | 否 |
| src/ForumBot/MdbValidation/MdbRuleFiles/mdb_compliance_rules_v6.3.json | 65996 | 否 |
| src/ForumBot/MdbValidation/MdbRuleFiles/mdb_compliance_rules_v6.5.json | 41758 | 否 |
| src/ForumBot/SchemaValidation/__init__.py | 0 | 否 |
| src/ForumBot/SchemaValidation/end_to_end_check.py | 52501 | 否 |
| src/ForumBot/SchemaValidation/extract_reviews.py | 18631 | 否 |
| src/ForumBot/SchemaValidation/redfish_checker.py | 106725 | 否 |
| src/ForumBot/SchemaValidation/redfish_common.py | 9738 | 否 |
| src/ForumBot/SchemaValidation/redfish_review_workflow.py | 1749 | 否 |
| src/ForumBot/SchemaValidation/redfish_schema_validator.py | 47519 | 否 |
| src/ForumBot/SchemaValidation/redfish_uri_generator.py | 9743 | 否 |
| src/ForumBot/SchemaValidation/schema_debug_logger.py | 8443 | 否 |
| src/ForumBot/SchemaValidation/SchemaFiles/redfish_compliance_rules.json | 37567 | 否 |
| src/evaluation/__init__.py | 0 | 否 |
| src/evaluation/build_dataset.py | 4904 | 否 |
| src/evaluation/run_baseline.py | 9318 | 否 |
| src/evaluation/templates.py | 1141 | 否 |
| src/update_lightrag/__init__.py | 31 | 否 |
| src/update_lightrag/filter.py | 1579 | 否 |
| src/update_lightrag/forum_data_Fetcher.py | 7009 | 否 |
| src/update_lightrag/full_data_init.py | 5854 | 否 |
| src/update_lightrag/gitcode_api_increment_fetcher.py | 8781 | 否 |
| src/update_lightrag/gitcode_client.py | 7179 | 否 |
| src/update_lightrag/gitode_full_fetcher.py | 7061 | 否 |
| src/update_lightrag/image_processor.py | 5614 | 否 |
| src/update_lightrag/increment_date_update_timer.py | 10633 | 否 |
| src/update_lightrag/lightrag_client.py | 14191 | 否 |
| src/update_lightrag/update_time.py | 10703 | 否 |
| tests/conftest.py | 8481 | 否 |
| tests/test_auth_middleware.py | 9772 | 否 |
| tests/test_coverage_boost.py | 28920 | 否 |
| tests/test_data_processor.py | 4259 | 否 |
| tests/test_data_processor_pre_audit.py | 20935 | 否 |
| tests/test_evaluation_build_dataset.py | 6707 | 否 |
| tests/test_evaluation_data_processor.py | 23740 | 否 |
| tests/test_evaluation_hooks.py | 5191 | 否 |
| tests/test_evaluation_run_baseline.py | 15673 | 否 |
| tests/test_external_api_app.py | 10617 | 否 |
| tests/test_flask_secret_key.py | 1973 | 否 |
| tests/test_forum_client.py | 7273 | 否 |
| tests/test_forum_client_pre_audit.py | 1139 | 否 |
| tests/test_full_data_init.py | 4043 | 否 |
| tests/test_gitcode_api_increment_fetcher.py | 17221 | 否 |
| tests/test_gitcode_client.py | 17169 | 否 |
| tests/test_gitode_full_fetcher.py | 13461 | 否 |
| tests/test_health_check.py | 9673 | 否 |
| tests/test_image_processor.py | 8444 | 否 |
| tests/test_increment_update_timer.py | 14930 | 否 |
| tests/test_jsonb_registration.py | 12775 | 否 |
| tests/test_lightrag_client.py | 13596 | 否 |
| tests/test_llm_token_usage.py | 914 | 否 |
| tests/test_logging_config.py | 2277 | 否 |
| tests/test_main_initialization.py | 6442 | 否 |
| tests/test_main_schema_files.py | 2144 | 否 |
| tests/test_monitor_pre_audit.py | 10795 | 否 |
| tests/test_oidc_client.py | 10409 | 否 |
| tests/test_prometheus_metrics.py | 17952 | 否 |
| tests/test_rag_api.py | 45126 | 否 |
| tests/test_rate_limiter.py | 8126 | 否 |
| tests/test_rbac_middleware.py | 4674 | 否 |
| tests/test_request_size_limit.py | 7181 | 否 |
| tests/test_token_tracker.py | 3218 | 否 |
| tests/test_update_lightrag_image_processor.py | 12272 | 否 |
| tests/test_update_time.py | 40194 | 否 |
| tests/test_utils.py | 13488 | 否 |
| tests/mdb_validation/__init__.py | 23 | 否 |
| tests/mdb_validation/test_mdb_checker.py | 25808 | 否 |
| tests/mdb_validation/test_mdb_classifier.py | 13075 | 否 |
| tests/mdb_validation/test_mdb_integration.py | 12187 | 否 |
| tests/schema_validation/test_end_to_end_check.py | 30745 | 否 |
| tests/schema_validation/test_extract_reviews.py | 2159 | 否 |
| tests/schema_validation/test_extract_reviews_numbered_summary.py | 18019 | 否 |
| tests/schema_validation/test_redfish_checker.py | 12590 | 否 |
| tests/schema_validation/test_redfish_common.py | 2655 | 否 |
| tests/schema_validation/test_redfish_review_workflow.py | 1696 | 否 |
| tests/schema_validation/test_redfish_schema_validator.py | 16171 | 否 |
| tests/schema_validation/test_redfish_uri_generator.py | 5718 | 否 |
| tests/schema_validation/test_schema_debug_logger.py | 4270 | 否 |