---
生成时间: 2026-08-10 17:44:39
提取工具: ua
原始页面数: 237
仓库: /tmp/ua-trial/forum-reply-robot
文档类型: api-reference
---

# forum-reply-robot API 参考文档

## 1. API 概览

forum-reply-robot 是一个自动监控论坛新帖并调用大模型智能回复的机器人服务。对外提供以下类型的接口：

| 接口类型 | 说明 |
|---------|------|
| REST API | 基于 Flask 的 HTTP 接口，包括健康检查、Prometheus 指标、RAG 检索与问答 |
| 内部服务 | 后台守护线程驱动的论坛监控、LightRAG 数据管道（无外部 HTTP 接口） |

服务默认暴露两个端口：
- **5000**：主服务（健康检查、Prometheus 指标、RAG API）
- **5001**：附属 API 服务（独立问答接口）

来源：`Dockerfile`、`main.py`

---

## 2. 认证方式

### 2.1 OIDC Bearer Token 认证

RAG API 路由受 `AuthMiddleware` 保护，采用 OIDC（OpenID Connect）协议进行身份认证。

**认证流程：**

1. 客户端通过 OIDC 授权码流程获取 Access Token
2. 请求时在 HTTP Header 中携带 Bearer Token：
   ```
   Authorization: Bearer <access_token>
   ```
3. 服务端通过 OIDC userinfo 端点校验 Token 有效性
4. Token 失效时区分「过期」与「无效」两种错误语义，支持 Token 刷新

**Token 生命周期管理：**

| 操作 | 说明 |
|------|------|
| 获取 Token | 通过 OIDC 授权码流程（code → token 交换） |
| 刷新 Token | 使用 refresh_token 调用刷新端点 |
| 校验 Token | 服务端通过 userinfo 端点验证 |
| State 防护 | 授权请求携带随机 state 参数防 CSRF |

来源：`src/ForumBot/auth_middleware.py`、`src/ForumBot/oidc_client.py`

### 2.2 RBAC 权限控制

在认证基础上，部分接口（如知识库上传）叠加基于 user_id 白名单的 RBAC 校验。

```
认证通过 → RBAC 白名单检查 → 限流检查 → 业务处理
```

来源：`src/ForumBot/rbac_middleware.py`

### 2.3 限流机制

基于 PostgreSQL 计数器的用户级滑动窗口限流，超出配额时返回 429 状态码。

来源：`src/ForumBot/rate_limiter.py`

---

## 3. 接口列表

### 3.1 健康检查接口

#### GET /health

基础健康检查，返回服务存活状态。

**认证：** 无需认证

**请求参数：** 无

**响应示例：**
```json
{
  "status": "ok"
}
```

**状态码：**
| 状态码 | 含义 |
|--------|------|
| 200 | 服务正常运行 |

来源：`main.py` — `health_check` 函数

---

#### GET /startup

启动自检接口，返回服务初始化状态与关键依赖就绪情况。

**认证：** 无需认证

**请求参数：** 无

**响应示例：**
```json
{
  "status": "ready",
  "dependencies": {
    "database": true,
    "config": true,
    "schema_files": true
  }
}
```

来源：`main.py` — `startup_check` 函数

---

#### GET /health/detailed

详细健康检查接口，逐项汇总监控线程、配置文件与规则文件的检查结果。

**认证：** 无需认证

**请求参数：** 无

**响应示例：**
```json
{
  "status": "healthy",
  "checks": {
    "monitor_thread": "running",
    "config_file": "ok",
    "schema_files": "ok",
    "mdb_rule_files": "ok"
  }
}
```

来源：`main.py` — `detailed_health_check` 函数

---

### 3.2 Prometheus 指标接口

#### GET /metrics

暴露 Prometheus 格式的运行指标供抓取。

**认证：** 无需认证

**请求参数：** 无

**响应格式：** `text/plain`（Prometheus exposition format）

**指标列表：**

| 指标名 | 类型 | 说明 |
|--------|------|------|
| 检索延迟 | Histogram | 知识检索耗时 |
| 生成延迟 | Histogram | 大模型生成耗时 |
| 端到端延迟 | Histogram | 完整处理链路耗时 |
| 空回复率 | Gauge | 未能生成有效回复的比例 |
| 处理量 | Counter | 已处理帖子总数 |

来源：`main.py` — `metrics_endpoint` 函数、`src/ForumBot/prometheus_metrics.py`

---

### 3.3 RAG API（知识检索接口）

所有 RAG API 路由注册在 Flask Blueprint 下，叠加认证与限流装饰器。

来源：`src/ForumBot/rag_api.py`

#### GET /rag/query

执行知识库检索查询。

**认证：** 需要 Bearer Token + 限流

**请求参数：**

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| q | query | string | 是 | 检索查询文本 |

**响应示例：**
```json
{
  "results": [
    {
      "content": "检索到的文档片段...",
      "score": 0.85,
      "source": "document_name.md"
    }
  ]
}
```

**状态码：**
| 状态码 | 含义 |
|--------|------|
| 200 | 检索成功 |
| 401 | 未认证或 Token 无效 |
| 429 | 请求超出限流配额 |

---

#### GET /rag/documents/status

查询知识库文档状态。

**认证：** 需要 Bearer Token + 限流

**请求参数：** 无

**响应示例：**
```json
{
  "total_documents": 256,
  "last_update": "2024-01-15T08:30:00Z",
  "pipeline_status": "idle"
}
```

---

#### GET /rag/oauth/callback

OIDC 授权码回调端点，用于完成 OAuth 授权流程。

**认证：** 无需（授权流程中间步骤）

**请求参数：**

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| code | query | string | 是 | 授权码 |
| state | query | string | 是 | 防 CSRF 状态参数 |

来源：`src/ForumBot/rag_api.py` — `RAGAPIController`

---

### 3.4 独立问答接口

通过 `standalone_api.py` 提供的独立 Flask 服务，默认运行在端口 5001。

来源：`src/ForumBot/standalone_api.py`、`src/ForumBot/api_main.py`

#### GET /health

独立 API 服务健康检查。

**认证：** 无需认证

**响应示例：**
```json
{
  "status": "ok"
}
```

---

#### POST /process_question

提交问题并获取大模型生成的回答。内部复用论坛检索与大模型生成链路。

> ⚠️ **安全警告**：此接口当前无鉴权保护，直接对外暴露会导致大模型调用被滥用，建议补充认证或限流。

**认证：** 无（存在安全风险）

**请求体：**
```json
{
  "question": "用户提问内容",
  "title": "可选的主题标题"
}
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 用户问题 |
| title | string | 否 | 问题标题，用于检索增强 |

**响应示例：**
```json
{
  "answer": "基于知识库检索生成的回答内容...",
  "sources": ["相关文档1.md", "相关文档2.md"]
}
```

**状态码：**
| 状态码 | 含义 |
|--------|------|
| 200 | 处理成功 |
| 400 | 请求参数缺失 |
| 500 | 内部处理错误 |

来源：`src/ForumBot/standalone_api.py` — `create_standalone_api` 函数

---

### 3.5 启动命令行参数

独立 API 服务通过 `api_main.py` 启动，支持以下命令行参数：

```bash
python src/ForumBot/api_main.py --host 0.0.0.0 --port 5001 --config config/config.yaml
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --host | 0.0.0.0 | 监听地址 |
| --port | 5001 | 监听端口 |
| --config | 自动查找 | 配置文件路径 |

来源：`src/ForumBot/api_main.py`

---

## 4. 配置文件

### config/config.yaml

项目唯一的运行时配置文件，定义大模型 API 凭据：

```yaml
base_url: "https://api.siliconflow.cn/v1"
api_key: "sk-xxxxxxxxxxxxx"
model_name: "Qwen/Qwen3-235B-A22B"
```

| 字段 | 说明 |
|------|------|
| base_url | 大模型 API 基础地址（OpenAI 兼容格式） |
| api_key | API 密钥（⚠️ 建议改用环境变量注入） |
| model_name | 使用的模型标识 |

由 `src/utils.py` 的 `load_config()` 函数读取并注入到所有调用点。

来源：`config/config.yaml`、`src/utils.py`

---

## 5. 错误码与处理

### 5.1 HTTP 状态码

| 状态码 | 含义 | 处理建议 |
|--------|------|----------|
| 200 | 请求成功 | — |
| 400 | 请求参数缺失或格式错误 | 检查请求体必填字段 |
| 401 | 未认证或 Token 无效/过期 | 重新获取或刷新 Token |
| 403 | 权限不足（RBAC 拒绝） | 确认 user_id 已加入白名单 |
| 429 | 超出限流配额 | 等待窗口重置后重试 |
| 500 | 服务内部错误 | 查看服务日志排查 |

### 5.2 认证错误分类

Token 校验失败时，服务端区分两种语义（来源：`src/ForumBot/oidc_client.py` — `_classify_token_failure`）：

| 错误类型 | 含义 | 客户端处理 |
|----------|------|------------|
| token_expired | Token 已过期 | 使用 refresh_token 刷新 |
| token_invalid | Token 无效（签名错误、被吊销等） | 重新走授权码流程 |

### 5.3 大模型调用错误

`ai_processor.py` 内置多模型轮询与重试机制，对上游不稳定做自动降级：

| 错误类型 | 处理策略 |
|----------|----------|
| APIError | 切换到候选模型列表中的下一个模型重试 |
| APITimeoutError | 切换模型重试 |
| 所有模型均失败 | 返回空结果，不自动回帖 |

来源：`src/ForumBot/ai_processor.py`

### 5.4 限流错误响应

超出配额时返回：
```json
{
  "error": "rate_limit_exceeded",
  "message": "请求频率超出限制，请稍后重试",
  "retry_after": 60
}
```

来源：`src/ForumBot/rate_limiter.py`

---

## 6. 内部模块 API 参考

以下为项目关键模块的编程接口，供二次开发或集成参考。

### 6.1 工具层（src/utils.py）

```python
from src.utils import (
    load_config,
    init_db_connection_pool,
    get_db_connection_from_pool,
    release_db_connection_to_pool,
    close_db_connection_pool,
    ensure_database_exists,
    clear_directory,
    delete_directory,
    delete_config_file,
)
```

| 函数 | 说明 |
|------|------|
| `load_config()` | 加载并解析 config/config.yaml，返回配置字典 |
| `init_db_connection_pool()` | 初始化全局 PostgreSQL 线程连接池 |
| `get_db_connection_from_pool()` | 从池中借出连接，池未就绪时返回 None |
| `release_db_connection_to_pool(conn)` | 归还连接到池中 |
| `close_db_connection_pool()` | 关闭连接池并释放所有连接 |
| `ensure_database_exists()` | 检查目标数据库是否存在，不存在则创建 |
| `clear_directory(path, ignore_files)` | 清空目录内容，可指定保留文件 |
| `delete_directory(path)` | 递归删除目录 |
| `delete_config_file(path)` | 删除配置文件（用后清理敏感信息） |

来源：`src/utils.py`

### 6.2 日志模块（src/ForumBot/logging_config.py）

```python
from src.ForumBot.logging_config import setup_logger, main_logger

# 使用全局 logger
main_logger.info("消息")

# 创建自定义 logger
logger = setup_logger("my_module", "logs/my_module.log")
```

| 接口 | 说明 |
|------|------|
| `setup_logger(name, log_file)` | 创建带文件轮转与控制台输出的 logger |
| `main_logger` | 全局共享 logger 实例（模块级单例） |

来源：`src/ForumBot/logging_config.py`

### 6.3 论坛客户端（src/ForumBot/forum_client.py）

```python
from src.ForumBot.forum_client import ForumClient

client = ForumClient(config)
```

| 方法 | 说明 |
|------|------|
| 拉取主题详情 | 获取指定主题的完整内容 |
| 发布回复 | 向指定主题发送回复内容 |
| 检索相关主题 | 按关键词搜索论坛相关帖子 |
| LightRAG 文档召回 | 从知识库检索相关文档片段 |

来源：`src/ForumBot/forum_client.py`

### 6.4 AI 处理器（src/ForumBot/ai_processor.py）

```python
from src.ForumBot.ai_processor import AIProcessor

processor = AIProcessor(config)
```

| 能力 | 说明 |
|------|------|
| 文本摘要 | 对长文本生成摘要 |
| 提示注入检测 | 检测用户输入是否包含提示注入攻击 |
| 答案相关性校验 | 校验生成答案与原始问题的相关度 |
| 答案质量校验 | 评估回答质量是否达标 |
| 多模型轮询 | 候选模型列表按序尝试，自动降级 |

安全机制（三层把关）：
1. 提示注入检测
2. 答案相关性校验
3. 质量校验

校验失败时默认不回复。

来源：`src/ForumBot/ai_processor.py`

### 6.5 合规校验接口

#### Redfish Schema 校验

```python
from src.ForumBot.SchemaValidation.end_to_end_check import run_schema_check

result = run_schema_check(title="帖子标题", content="帖子正文内容")
```

| 函数 | 说明 |
|------|------|
| `run_schema_check(title, content)` | 对外主入口，执行完整 Schema 合规检测并返回回复文本 |
| `is_post_relevant(title, content)` | 判断帖子是否需要进入检测流程 |
| `extract_review_points(content)` | 从正文中切分评审点列表 |
| `classify_review_point(point)` | 判定评审点归属（Redfish / MDB / 无关） |

来源：`src/ForumBot/SchemaValidation/end_to_end_check.py`

#### MDB 合规校验

```python
from src.ForumBot.MdbValidation import is_mdb_related, MdbComplianceChecker

# 相关性判断
related = is_mdb_related(title, content)

# 执行校验
checker = MdbComplianceChecker(config)
results = checker.check(review_points)
```

来源：`src/ForumBot/MdbValidation/__init__.py`、`src/ForumBot/MdbValidation/mdb_checker.py`

### 6.6 LightRAG 客户端（src/update_lightrag/lightrag_client.py）

```python
from src.update_lightrag.lightrag_client import LightRAGClient

client = LightRAGClient(config)
```

| 方法 | 说明 |
|------|------|
| 文档上传 | 将文档写入 LightRAG 知识库 |
| 文档删除 | 从知识库移除指定文档 |
| 文件名-ID 映射维护 | 管理文件名到文档 ID 的对应关系 |
| pipeline 状态轮询 | 阻塞式等待 pipeline 空闲，避免并发写入冲突 |

来源：`src/update_lightrag/lightrag_client.py`

### 6.7 Token 用量追踪

```python
from src.ForumBot.token_tracker import TokenTracker

tracker = TokenTracker()
tracker.add(model="qwen3-235b", prompt_tokens=100, completion_tokens=50)
usage = tracker.get_usage()
tracker.reset()
```

来源：`src/ForumBot/token_tracker.py`、`src/ForumBot/llm_token_usage.py`

---

## 7. 合规规则文件

### 7.1 Redfish 合规规则

文件：`src/ForumBot/SchemaValidation/SchemaFiles/redfish_compliance_rules.json`

共 17 条规则（编号 RULE-001 ~ RULE-017），覆盖：
- PascalCase 命名规范
- URI 路径层级限制（前 3 层）
- 属性定义合规性
- 类型一致性

### 7.2 MDB 合规规则

| 版本 | 文件 | 规则数 |
|------|------|--------|
| v6.3 | `src/ForumBot/MdbValidation/MdbRuleFiles/mdb_compliance_rules_v6.3.json` | 45 条 |
| v6.5 | `src/ForumBot/MdbValidation/MdbRuleFiles/mdb_compliance_rules_v6.5.json` | 26 条 |

规则结构：
```json
{
  "id": "MDB-REVIEW-001",
  "category": "分类",
  "severity": "must|should",
  "rule": "规则描述",
  "check": "判定口径（直接拼入 LLM prompt）",
  "rationale": "误报分析说明"
}
```

来源：相应 JSON 规则文件

---

## 8. 部署与运行

### 容器化启动

```bash
docker build -t forum-reply-robot .
docker run -p 5000:5000 -p 5001:5001 \
  -v $(pwd)/config:/app/config \
  forum-reply-robot
```

容器以非 root 用户 `appuser` 运行，权限收敛至 750。

### 本地开发启动

```bash
# 安装依赖
pip install -r requirements.txt

# 准备配置
cp config/config.yaml.example config/config.yaml
# 编辑填入 API Key

# 启动主服务
python main.py

# 或启动独立 API
python src/ForumBot/api_main.py --port 5001
```

### 健康检查验证

```bash
curl http://localhost:5000/health
# {"status": "ok"}

curl http://localhost:5000/health/detailed
# 返回各组件详细状态
```

来源：`Dockerfile`、`README.md`、`main.py`

---

## 9. 依赖与环境要求

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.9 | 运行时 |
| Flask | 固定版本 | Web 框架 |
| LangChain (openai/core) | 固定版本 | LLM 调用框架 |
| OpenAI | 固定版本 | 模型 API 客户端 |
| psycopg2-binary | >=2.9 | PostgreSQL 连接 |
| prometheus-client | 固定版本 | 指标暴露 |
| Authlib | 固定版本 | OIDC 认证 |
| BeautifulSoup4 | 固定版本 | HTML 解析 |
| pandas | 固定版本 | 数据处理 |
| schedule | 固定版本 | 定时任务 |
| PyYAML | 固定版本 | 配置解析 |

外部服务依赖：
- PostgreSQL 数据库
- LightRAG 知识库服务
- 论坛 API（被监控的目标论坛）
- GitCode 代码仓库
- 大模型 API（OpenAI 兼容接口）
- OIDC Identity Provider

来源：`requirements.txt`、`requirements-test.txt`、`CLAUDE.md`