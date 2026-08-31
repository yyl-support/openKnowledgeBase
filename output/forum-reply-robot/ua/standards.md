# forum-reply-robot 规范与风险

## 1. 命名规范

| 对象类型 | 规则 | 示例 |
|---------|------|------|
| Python 模块文件 | 小写字母 + 下划线分隔 | `data_processor.py`、`forum_client.py`、`ai_processor.py` |
| Python 包目录 | 小写字母 + 下划线分隔，含 `__init__.py` | `src/ForumBot/`、`src/update_lightrag/`、`src/ForumBot/SchemaValidation/` |
| Python 类名 | 大驼峰（PascalCase） | `ForumMonitor`、`DataProcessor`、`AIProcessor`、`MonitorThread` |
| Python 函数名 | 小写字母 + 下划线分隔 | `load_config`、`delete_config_file`、`parse_pre_audit_readiness`、`fetch_topic_details` |
| 数据库表名 | 小写字母 + 下划线分隔 | `forum_topics`、`processed_forum_topics`、`pre_audit_topics`、`consume_tokens_topic`、`schema_debug_logs` |
| 配置文件 | 小写字母 + 点分隔 | `config.yaml`、`requirements.txt`、`pytest.ini` |
| 日志文件 | 小写字母 + 点分隔 | `logs/main.log` |
| 测试文件 | `test_` 前缀 + 小写字母 + 下划线分隔 | `test_data_processor_pre_audit.py`、`test_monitor_pre_audit.py`、`test_flask_secret_key.py` |
| 环境变量 | 大写字母 + 下划线分隔 | `PYTHONDONTWRITEBYTECODE`、`PYTHONUNBUFFERED`、`PYTHONPATH` |
| Docker 容器用户 | 小写字母 | `appuser` |
| Docker 工作目录 | 绝对路径 | `/app` |

## 2. 安全要求

| 类别 | 要求 | 依据 |
|------|------|------|
| 配置文件保护 | `config/config.yaml` 已被 `.gitignore` 忽略，不入库；`main.py` 加载配置后立即调用 `delete_config_file()` 删除配置文件，防止含明文密钥的配置文件长期落盘 | `CLAUDE.md`、`main.py`、`src/utils.py` |
| 提示词注入防护 | 用户输入用随机字符串包裹后再喂给大模型以缓解提示词注入；注入检测失败时默认从严（判为注入，宁可不回复） | `CLAUDE.md`、`src/ForumBot/ai_processor.py` 的 `check_prompt_injection` |
| 容器运行用户 | 镜像以非 root 用户 `appuser`（uid 1000、gid 1000）运行，shell 设为 `/sbin/nologin` | `Dockerfile` |
| 容器文件权限 | `/app` 目录权限 `750`，`/app/config` 目录权限 `700`，`config.yaml` 文件权限 `600` | `Dockerfile` |
| 容器加固 | 构建后删除 `dpkg`、`gcc` 等编译器与包管理工具，关闭 shell history（`unset HISTFILE`） | `Dockerfile` |
| Flask secret_key | 优先使用配置值，缺失时记录错误；调试模式有默认值 | `main.py`、`tests/test_flask_secret_key.py` |
| 数据库连接 | 支持 `sslmode` 配置，生产环境可启用 SSL 加密连接 | `config/config.yaml`、数据库配置段 |
| 凭据管理 | 所有外部服务凭据（API key、数据库口令）集中在 `config/config.yaml`，仓库内版本为脱敏占位（key 被 `****` 掩码） | `CLAUDE.md`、`config/config.yaml` |

## 3. DFX 要求

| 维度 | 要求 | 依据 |
|------|------|------|
| **可靠性 - 容错** | 单帖处理异常不影响其他帖子（逐帖 `try/except continue`）；大模型调用带重试与退避；数据库连接失败时跳过当轮而非崩溃 | `CLAUDE.md` |
| **可靠性 - 从严默认** | 注入检测/相关性/质量校验出错时默认从严（判为注入/不相关/不合格，宁可不回复） | `CLAUDE.md` |
| **可靠性 - 降级** | MDB 校验为可选能力：`MdbRuleFiles` 目录缺失时仅记录 warning 而不阻断启动，主流程降级跳过 MDB 校验 | `CLAUDE.md`、`main.py` 的 `check_mdb_rule_files` |
| **可靠性 - 启动检查** | 启动前检查 `SchemaFiles` 目录与 Redfish Schema 定义文件是否就绪，目录缺失或文件为空时退出 | `CLAUDE.md`、`main.py` 的 `check_schema_files` |
| **可观测性 - 日志** | 主日志 `logs/main.log` 带轮转（单文件 20MB，保留 4 份）；`logging_config.py` 统一配置控制台与文件输出 | `CLAUDE.md`、`src/ForumBot/logging_config.py` |
| **可观测性 - 健康检查** | Flask 提供 `/health` 与 `/health/detail` 接口，健康判定依赖 `MonitorThread` 是否存活，监控线程崩溃可被外部探针感知 | `CLAUDE.md`、`main.py` |
| **可观测性 - 指标** | Prometheus 指标导出能力（`src/ForumBot/prometheus_metrics.py`） | `src/ForumBot/prometheus_metrics.py` |
| **可观测性 - Token 追踪** | 全局单例 `token_tracker` 按 topic_id 累计 prompt/completion/total token 用量，最终由 `DataProcessor.save_token_usage_to_db` 落库到 `consume_tokens_topic` 表 | `CLAUDE.md`、`src/ForumBot/token_tracker.py` |
| **可观测性 - 调试日志** | Schema 校验过程写入 `schema_debug_logs` 表 | `CLAUDE.md` |
| **可维护性 - 数据持久化** | PostgreSQL 是权威存储，`DataProcessor.create_tables()` 启动时建表；CSV 文件与数据库并行写出 | `CLAUDE.md`、`src/ForumBot/data_processor.py` |
| **可维护性 - 去重** | 去重以数据库为权威：`forum_topics` / `pre_audit_topics` 表记录已见过的 topic_id，每轮只处理新 ID | `CLAUDE.md` |
| **可维护性 - 测试** | pytest 测试覆盖核心模块，`conftest.py` 提供 mock | `CLAUDE.md`、`tests/` 目录 |
| **容量 - 并发模型** | 主进程是 Flask 应用，业务逻辑跑在两个守护线程：`MonitorThread`（轮询监控）+ scheduler 守护线程（LightRAG 增量更新定时器） | `CLAUDE.md`、`main.py` |
| **容量 - 端口** | Flask 绑定到内网私有 IP（优先 `10.` 段，其次 `192.168.`）的 5000 端口；Docker 暴露 5000 与 5001 端口 | `CLAUDE.md`、`Dockerfile` |

## 4. 当前风险点

1. **数据库依赖包名文档错误**  
   `CLAUDE.md` 第 37 行将数据库依赖包名写为 `psycopg[binary]`，但 `requirements.txt` 实际使用的是 `psycopg2-binary >= 2.9`。包名错误可能误导新开发者安装错误的依赖包。  
   依据：`verify.json` corrections_for_refiner、`requirements.txt:24`、`CLAUDE.md:37`

2. **Schema 文件运行时依赖外部仓库**  
   `SchemaFiles/` 与 `MdbRuleFiles/` 目录在构建期从 GitCode 远程仓库拉取（`https://gitcode.com/Richardli25/Redfish_SchemaFiles.git` 和 `https://gitcode.com/Richardli25/MDB_SchemaFiles.git`），这些文件不在本仓库中。若远程仓库不可达或内容变更，构建将失败或产生不一致的镜像。  
   依据：`CLAUDE.md`、`Dockerfile`

3. **配置文件生产环境缺失风险**  
   `config/config.yaml` 已被 `.gitignore` 忽略且 `main.py` 加载后立即删除，生产部署时必须通过外部方式（ConfigMap、Secret、环境变量注入等）提供配置，否则服务无法启动。  
   依据：`CLAUDE.md`、`main.py`、`.gitignore`

4. **数据库连接失败时静默跳过**  
   数据库连接失败时跳过当轮处理而非崩溃，这可能导致帖子未被处理但服务看似正常运行，外部监控无法感知数据处理停滞。  
   依据：`CLAUDE.md` "数据库连接失败时跳过当轮而非崩溃"

5. **预审链路基础设施错误可能发帖**  
   虽然 `is_infrastructure_error_text` 识别基础设施/服务异常（超时、限流、空响应）会拒绝发帖，但若校验服务返回的错误格式未被识别，可能把服务错误当成评审意见回复到论坛。  
   依据：`CLAUDE.md` "校验过程中的基础设施/服务异常会被识别并拒绝发帖"，`src/ForumBot/SchemaValidation/end_to_end_check.py`

6. **MDB 校验能力降级无明确告警**  
   `MdbRuleFiles` 目录缺失时仅记录 warning 日志，预审链路会跳过 MDB 校验继续执行，但外部系统（监控/告警）可能无法感知该能力已降级，导致预审结果不完整。  
   依据：`CLAUDE.md`、`main.py` 的 `check_mdb_rule_files`

7. **Flask secret_key 生产环境配置遗漏**  
   Flask `secret_key` 优先使用配置值，缺失时仅记录错误日志，会话管理可能不安全。生产环境必须在 `config.yaml` 中显式配置 `secret_key`。  
   依据：`main.py`、`tests/test_flask_secret_key.py`

8. **Docker 缓存失效机制依赖远程 git refs**  
   Dockerfile 通过 `ADD https://gitcode.com/.../info/refs?service=git-upload-pack` 让缓存随上游 Schema 仓库 HEAD 变化失效。若该 URL 不可达或返回格式变化，缓存失效机制失效，可能拉到过期的规则文件。  
   依据：`Dockerfile`、`CLAUDE.md`
