# forum-reply-robot 规范与标准

## 1. 命名规范

| 对象类型 | 规则 | 示例 |
|---------|------|------|
| Python 模块文件 | snake_case，功能描述性命名 | `monitor.py`、`forum_client.py`、`ai_processor.py`、`data_processor.py` |
| Python 包目录 | PascalCase 或 snake_case | `ForumBot/`、`SchemaValidation/`、`MdbValidation/`、`update_lightrag/` |
| 配置文件 | 小写 + 下划线，版本号用点分隔 | `config.yaml`、`mdb_compliance_rules_v6.3.json`、`mdb_compliance_rules_v6.5.json`、`redfish_compliance_rules.json` |
| 数据库表名 | 小写 + 下划线，复数形式 | `forum_topics`、`processed_forum_topics`、`pre_audit_topics`、`pre_audit_processed_topics`、`consume_tokens_topic`、`forum_search_results`、`forum_retrieval_results`、`schema_debug_logs` |
| Python 类名 | PascalCase | `ForumMonitor`、`ForumClient`、`AIProcessor`、`DataProcessor`、`MdbComplianceChecker` |
| Python 函数/方法 | snake_case，内部方法加前导下划线 | `load_config()`、`delete_config_file()`、`_check_new_topics()`、`_process_new_topics()` |
| Schema 文件目录 | PascalCase，构建期从远程拉取 | `SchemaFiles/`（Redfish Schema）、`MdbRuleFiles/`（MDB 规则） |
| 日志文件 | 小写 + 下划线 + `.log` 后缀 | `logs/main.log` |
| 依赖清单 | `requirements` 前缀 + 用途后缀 | `requirements.txt`、`requirements-test.txt`、`requirements-eval.txt` |

**来源**：`CLAUDE.md`、`main.py`、`src/ForumBot/monitor.py`、`src/ForumBot/data_processor.py`、`src/ForumBot/SchemaValidation/`、`src/ForumBot/MdbValidation/`

## 2. 安全要求

| 类别 | 要求 | 实施位置 |
|------|------|----------|
| 敏感信息管理 | `config/config.yaml` 含明文 API key 与数据库口令，已被 `.gitignore` 忽略不得入库；生产启动时 `load_config()` 加载后立即调用 `delete_config_file()` 删除文件，防止敏感信息长期落盘 | `main.py`、`src/utils.py`、`CLAUDE.md` |
| SQL 注入防护 | 使用参数化查询（`%s` 占位符）而非字符串拼接，防止 SQL 注入 | `src/ForumBot/data_processor.py`（psycopg2） |
| 提示词注入防护 | 用户输入用随机字符串包裹后再喂给大模型，缓解提示词注入攻击 | `src/ForumBot/ai_processor.py` |
| 认证 | RAG API 端点通过 OIDC 认证，`require_auth` 装饰器从请求头提取 Bearer token 并委托 `OIDCClient` 校验 | `src/ForumBot/auth_middleware.py`、`src/ForumBot/oidc_client.py`、`src/ForumBot/rag_api.py` |
| 权限控制 | RBAC 中间件实施基于角色的访问控制 | `src/ForumBot/rbac_middleware.py` |
| 限流 | 用 PostgreSQL 计数器实现滑动窗口限流，用户级限流 | `src/ForumBot/rate_limiter.py` |
| 容器安全 | 以非 root 用户 `appuser` 运行；构建后删除编译器、收紧文件权限（`chmod 500 /app`、`chmod 400 /app/main.py`） | `Dockerfile` |
| 日志安全 | 不在日志或回复内容中回显 API key、数据库口令等凭据 | 全局要求（`CLAUDE.md`） |

**来源**：`CLAUDE.md`、`main.py`、`src/utils.py`、`src/ForumBot/ai_processor.py`、`src/ForumBot/data_processor.py`、`src/ForumBot/auth_middleware.py`、`src/ForumBot/oidc_client.py`、`src/ForumBot/rbac_middleware.py`、`src/ForumBot/rate_limiter.py`、`Dockerfile`

## 3. DFX 要求

| 维度 | 要求 | 实施位置 |
|------|------|----------|
| 日志 | 主日志文件 `logs/main.log`，带轮转（单文件 20MB，保留 4 份）；控制台与文件日志统一配置；`main_logger` 全项目共享 | `src/ForumBot/logging_config.py`（`setup_logger`） |
| 健康检查 | Flask 应用暴露 `/health` 与 `/health/detail` 端点，绑定 5000 端口；健康判定依赖监控线程（`MonitorThread`）是否存活，监控线程崩溃可被外部探针感知 | `main.py` |
| 监控指标 | Prometheus metrics 导出 | `src/ForumBot/prometheus_metrics.py` |
| 容错 - 单帖异常隔离 | 逐帖容错：单帖处理异常不影响其他帖（`for` 循环配合 `try/except continue`） | `src/ForumBot/monitor.py` |
| 容错 - 数据库 | 数据库连接失败时跳过当轮而非崩溃，带重试（默认 3 次）；数据库为去重权威，不可达时服务降级 | `src/utils.py`、`src/ForumBot/data_processor.py` |
| 容错 - 外部服务 | 大模型调用带重试与退避（`retrying` 库装饰器）；校验类调用失败时默认从严（判为不相关/不合格，宁可不回复） | `src/ForumBot/ai_processor.py` |
| 容错 - 知识库 | LightRAG 检索为空则用空字符串继续；若搜索也为空则跳过该帖 | `src/ForumBot/monitor.py`、`src/ForumBot/forum_client.py` |
| 容错 - 预审基础设施 | 预审链路识别基础设施异常（超时、限流、空响应）并拒绝发帖，避免把服务错误当评审意见发出 | `src/ForumBot/SchemaValidation/end_to_end_check.py`（`is_infrastructure_error_text`） |
| 数据持久化 | PostgreSQL 为权威存储；CSV 与 PostgreSQL 并行双写提供可审计旁路；token 消耗、搜索结果、检索结果、处理记录均落库 | `src/ForumBot/data_processor.py` |
| 可观测性 - Token 追踪 | 全局单例 `token_tracker` 按 `topic_id` 累计 prompt/completion/total token 用量，最终落库 `consume_tokens_topic` 表 | `src/ForumBot/token_tracker.py`、`src/ForumBot/data_processor.py` |
| 可观测性 - 调试日志 | 预审链路写独立调试表 `schema_debug_logs`（相关性/评审点/逐点校验中间数据），失败仅记日志不影响主流程 | `src/ForumBot/SchemaValidation/schema_debug_logger.py` |

**来源**：`CLAUDE.md`、`main.py`、`src/utils.py`、`src/ForumBot/logging_config.py`、`src/ForumBot/monitor.py`、`src/ForumBot/ai_processor.py`、`src/ForumBot/data_processor.py`、`src/ForumBot/token_tracker.py`、`src/ForumBot/prometheus_metrics.py`、`src/ForumBot/SchemaValidation/end_to_end_check.py`、`src/ForumBot/SchemaValidation/schema_debug_logger.py`

## 4. 当前风险点

1. **配置文件泄露风险**  
   `config/config.yaml` 含明文敏感信息（API key、数据库口令），虽已被 `.gitignore` 忽略，但仍存在误提交风险。  
   **可能后果**：敏感凭据泄露至版本库，导致未授权访问外部服务或数据库。  
   **来源**：`CLAUDE.md` - "config/config.yaml（已被.gitignore忽略，不入库）"、"`main.py` 加载配置后立即删除以防敏感信息落盘"

2. **Schema 文件缺失导致服务启动失败**  
   `main.py` 启动时检查 `SchemaFiles` 目录是否就绪，缺失则直接退出。`SchemaFiles/` 与 `MdbRuleFiles/` 在构建期从 GitCode 远程仓库 `git clone` 拉取，不在本仓库。  
   **可能后果**：本地开发或非 Docker 部署时，缺少这些目录会导致服务无法启动；预审链路失效。  
   **来源**：`CLAUDE.md` - "SchemaFiles目录缺失则退出"、`Dockerfile` - "构建期从GitCode远程仓库git clone拉取Schema文件"

3. **校验失败默认从严可能导致漏回复**  
   提示词注入检测、答案相关性校验、答案质量校验失败时，`ai_processor.py` 默认从严判定为注入/不相关/不合格，直接跳过回复。  
   **可能后果**：外部服务（大模型 API）偶发异常时，合法帖子被误判拒绝回复；用户得不到应有的答案。  
   **来源**：`src/ForumBot/ai_processor.py`、`CLAUDE.md` - "校验失败时默认从严不回复"

4. **预审链路基础设施异常识别不完备**  
   `end_to_end_check.py` 通过 `is_infrastructure_error_text()` 识别超时、限流、空响应等基础设施异常以拒绝发帖，但识别规则可能无法覆盖所有异常模式（如新增的错误码、变化的错误文本）。  
   **可能后果**：未被识别的服务错误被当成评审结论发布到论坛，误导用户。  
   **来源**：`src/ForumBot/SchemaValidation/end_to_end_check.py`、`CLAUDE.md` - "校验过程中的基础设施/服务异常会被识别并拒绝发帖"

5. **数据库不可达时去重失效**  
   去重依赖 `forum_topics` / `pre_audit_topics` 表记录已见 `topic_id`，数据库连接失败时跳过当轮。若数据库长时间不可达，重启后可能对同一帖子重复处理。  
   **可能后果**：论坛上同一问题收到多条相同回复；token 消耗重复计费；用户体验下降。  
   **来源**：`src/ForumBot/data_processor.py`、`CLAUDE.md` - "数据库连接失败时跳过当轮而非崩溃"

6. **知识库更新失败静默降级**  
   `increment_date_update_timer.py` 每天 18:00 UTC 执行增量更新，失败仅记日志不告警。若 GitCode 仓库不可达或 LightRAG 服务异常，知识库会逐渐过时。  
   **可能后果**：回复依赖的 RAG 检索返回陈旧文档，答案不准确；新增知识无法被利用。  
   **来源**：`src/update_lightrag/increment_date_update_timer.py`、`CLAUDE.md` - "知识库更新失败记日志"

7. **MDB 校验子包可选导致评审覆盖不全**  
   `MdbValidation/` 子包缺失时，主流程降级跳过 MDB 校验不致命。预审链路对 MDB 相关帖子的评审会缺失该维度。  
   **可能后果**：MDB 接口合规问题未被发现即通过预审；后续集成时暴露规范冲突。  
   **来源**：`CLAUDE.md` - "该子包可选：缺失时主流程降级跳过 MDB 校验，不致命"

8. **守护线程崩溃后健康检查失效前的空窗期**  
   `MonitorThread` 是守护线程，崩溃后健康检查 `/health` 会返回失败，但在探针下次轮询之前（轮询间隔内），服务实际已停止工作但外部无感知。  
   **可能后果**：监控告警延迟，新帖无人回复的时长取决于探针间隔。  
   **来源**：`main.py`、`CLAUDE.md` - "监控线程崩溃可被外部探针感知"
