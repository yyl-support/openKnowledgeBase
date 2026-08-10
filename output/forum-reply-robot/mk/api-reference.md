---
生成时间: 2026-08-10 17:47:48
提取工具: mk
原始页面数: 35
仓库: forum-reply-robot (wiki=wiki-iw1oe7f2)
文档类型: api-reference
---

# ForumBot API 参考文档

## 1. API 概览

ForumBot 提供一个独立部署的 REST API 服务，默认监听 `127.0.0.1:5085`。该服务作为 ForumBot 系统平台的对外能力入口，支持知识上传等操作，并通过 OIDC 认证 + 白名单鉴权保护受限接口。

| 属性 | 说明 |
|------|------|
| 类型 | REST API（Flask） |
| 默认地址 | `127.0.0.1:5085` |
| 启动方式 | 命令行脚本 `api_main.py` 或直接调用 `standalone_api.run_standalone_api()` |
| 协议 | HTTP |
| 数据格式 | JSON |

> 来源：`wiki/entities/forumbot-独立-api-服务.md`、`wiki/concepts/独立-api-服务部署模型.md`

---

## 2. 认证方式

### 2.1 认证协议

系统使用 **OneID OIDC（OpenID Connect）授权码模式** 进行身份认证。

| 端点 | URL |
|------|-----|
| 授权端点 | `https://omapi.osinfra.cn/oneid/oidc/authorize` |
| 令牌端点 | `https://omapi.osinfra.cn/oneid/oidc/token` |
| 用户信息端点 | `https://omapi.osinfra.cn/oneid/oidc/user` |

### 2.2 认证流程

1. 客户端通过授权端点获取授权码（含 CSRF state 校验）
2. 使用授权码换取 `access_token`、`refresh_token`、`id_token`
3. `id_token` 为三段 JWT，`sub` 声明作为 `user_id`
4. 后续请求携带 `access_token` 在 Authorization header 中

### 2.3 Token 管理

| 操作 | 说明 |
|------|------|
| 获取 Token | 授权码换 token，响应含 `access_token`、`refresh_token`、`id_token`、`expires_in` |
| 刷新 Token | 使用 `refresh_token` 以 `grant_type=refresh_token` 换取新 token |
| 校验 Token | 调用 UserInfo 端点验证有效性，按 RFC 6750 Bearer 错误语义分类失败原因 |

### 2.4 鉴权模型

受保护的接口（如知识上传）采用 **白名单鉴权模型**：

- 配置项：`config['rbac']['knowledge_upload_users']`（user_id 列表）
- 认证中间件将 OIDC 校验结果注入 `g.current_user`
- `RBACMiddleware` 消费 `g.current_user` 中的 `user_id` 进行白名单判定

> 来源：`wiki/entities/oidcclient.md`、`wiki/entities/oneid.md`、`wiki/concepts/知识上传白名单鉴权模型.md`、`wiki/entities/rbacmiddleware.md`

---

## 3. 服务启动

### 3.1 命令行参数

```bash
python api_main.py [--host HOST] [--port PORT] [--config CONFIG]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--host` | `127.0.0.1` | 服务监听地址 |
| `--port` | `5085` | 服务监听端口 |
| `--config` | `None`（自动查找） | 配置文件路径 |

### 3.2 启动流程

1. 路径注入：脚本目录与 `src` 目录加入 `sys.path`
2. 参数解析：读取 CLI 参数
3. 日志初始化：导入 `logging_config.main_logger`
4. 委托启动：调用 `run_standalone_api(host, port, config_file)`

> 来源：`wiki/sources/api-main-txt.md`、`wiki/concepts/命令行入口启动流程.md`

---

## 4. 接口列表

### 4.1 知识上传接口

知识上传 API 受 `RBACMiddleware.require_upload_permission` 装饰器保护。

| 属性 | 说明 |
|------|------|
| 鉴权 | 需要有效 access_token + user_id 在白名单中 |
| 请求头 | `Authorization: Bearer <access_token>` |

**权限校验逻辑：**

1. 检查 `g.current_user` 是否存在（由上游认证中间件注入）
2. 不存在 → 返回 `401 TOKEN_MISSING`
3. 存在但 `user_id` 不在白名单 → 返回 `403 ROLE_DENIED`
4. 校验通过 → 执行业务逻辑

> 来源：`wiki/entities/rbacmiddleware.md`

---

### 4.2 内部模块接口（Python SDK）

以下为 ForumBot 内部模块暴露的编程接口，供集成和扩展使用。

#### 4.2.1 token_tracker — Token 用量追踪

模块路径：`src/token_tracker.py`

全局单例：`token_tracker`

| 方法 | 签名 | 说明 |
|------|------|------|
| `reset_usage` | `reset_usage(topic_id)` | 清零指定 topic 的四项统计 |
| `add_usage` | `add_usage(topic_id, prompt_tokens=0, completion_tokens=0, total_tokens=0)` | 累加 token 指标并递增 `model_calls`；未跟踪 topic 自动初始化 |
| `get_usage` | `get_usage(topic_id)` | 返回指定 topic 的统计；未跟踪返回零值 |
| `get_all_usage` | `get_all_usage()` | 返回所有 topic 的统计字典 |

**返回结构（每主题）：**

```json
{
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0,
  "model_calls": 0
}
```

> 来源：`wiki/entities/token-tracker.md`、`wiki/sources/token-tracker-txt.md`

---

#### 4.2.2 data_processor — 数据处理与持久化

模块路径：`src/data_processor.py`

| 方法 | 说明 |
|------|------|
| `save_search_results_to_db(topic_id, search_results)` | 搜索结果限量 10 条写入 `forum_search_results` 表 |
| `save_retrieval_results_to_db(topic_id, related_docs)` | 检索结果写入 `forum_retrieval_results` 表 |
| `save_token_usage_to_db(topic_id, usage)` | token 用量 upsert 到 `consume_tokens_topic` 表 |
| `save_evaluation_sample(...)` | 评估样本写入 `evaluation_samples` 表 |
| `load_existing_data()` | 加载 `forum_topics` 已有 ID 集合（增量去重） |
| `load_pre_audit_existing_data()` | 加载 `pre_audit_topics` 已有 ID 集合 |
| `extract_topic_data(topic_details)` | 从 Discourse 话题详情提取结构化数据 |
| `append_to_csv(data)` | 追加写入 CSV 文件 |
| `process_search_results(topic_id, results)` | 搜索结果入库并落盘 JSON |
| `process_retrieval_results(topic_id, results)` | 检索结果入库并落盘 JSON |
| `format_search_results_for_prompt(retrieval_result, search_results)` | 组装检索上下文并填充 PROMPT_TEMPLATE |

**`extract_topic_data` 返回结构：**

```json
{
  "id": "topic_id",
  "title": "帖子标题",
  "tags": "tag1,tag2",
  "created_at": "2025-01-01T00:00:00Z",
  "user_question": "用户问题内容（含图像增强）",
  "best_answer": "最佳答案内容（含图像增强）",
  "replies": ["回复1", "回复2"],
  "llm_answer": "",
  "summary_question": ""
}
```

> 来源：`wiki/entities/data-processor.md`、`wiki/concepts/数据处理与持久化模型.md`

---

#### 4.2.3 ForumClient — 论坛客户端

模块路径：`src/forum_client.py`

| 方法 | 说明 | 外部依赖 |
|------|------|----------|
| `fetch_all_forum_topics()` | 获取所有论坛主题，支持 tag/cutoff_date/category_path 配置 | data_processor |
| `fetch_topic_details(topic_id)` | 获取单个帖子详情 | data_processor |
| `reply_to_topic(topic_id, raw)` | 回复指定主题 | 外部论坛 posts API |
| `search_related_topics(keywords)` | 按关键字搜索相关主题 | 外部搜索 API |
| `retrieve_documents_for_topic(title, question)` | 以"标题+问题"检索相关文档 | 外部检索 API |

**配置段结构：**

```yaml
posts:
  base_url: "..."
  api_key: "..."
  api_username: "..."
  verify_ssl: true

search:
  base_url: "..."
  verify_ssl: true

retrieval:
  base_url: "..."
  verify_ssl: true
```

**`reply_to_topic` 请求：**

```
POST {posts.base_url}/posts.json
Headers:
  Api-Key: {posts.api_key}
  Api-Username: {posts.api_username}
Body:
  {"topic_id": 123, "raw": "回复内容"}
```

> 来源：`wiki/entities/forumclient.md`、`wiki/sources/forum-client-txt.md`

---

#### 4.2.4 image_processor — 图像处理

模块路径：`src/image_processor.py`

| 方法 | 签名 | 说明 |
|------|------|------|
| `enhance_text_with_image_descriptions` | `(text, field_name, topic_id)` | 提取文本中 `[img: (...)]` 标签，调用多模态模型生成描述，替换为 `[图片: 描述]` |
| `extract_image_info_from_text` | `(text)` | 正则提取图片标签列表 |
| `process_image_content` | `(image_url, context, topic_id)` | 处理单张图片，头像返回 `USER_AVATAR` |

**上下文提示词策略：**

| context 值 | 描述生成侧重 |
|------------|------------|
| `user_question` | 逐字提取截图中的文字信息 |
| `best_answer` | 总结关键技术信息 |
| 默认 | 描述图片内容，关注技术信息 |

> 来源：`wiki/entities/image-processor.md`、`wiki/other/image-processor.md`

---

#### 4.2.5 OIDCClient — OIDC 认证客户端

模块路径：`src/oidc_client.py`

| 方法 | 说明 |
|------|------|
| `generate_state()` | 生成防 CSRF 的 state 值 |
| `validate_state(state)` | 校验 state 值 |
| `get_authorization_url()` | 构造授权 URL |
| `exchange_code_for_token(code)` | 授权码换 token，返回 `access_token`/`refresh_token`/`id_token`/`user_id` |
| `refresh_access_token(refresh_token)` | 刷新 token，返回新 token 及 `expires_at` |
| `validate_token(access_token)` | 校验 token 有效性，返回 `{valid, reason, user_info}` |

**配置（config.yaml `oidc` 段）：**

```yaml
oidc:
  client_id: "必填"
  client_secret: "必填"
  redirect_uri: "必填"
  authorize_url: "https://omapi.osinfra.cn/oneid/oidc/authorize"  # 可选，有默认值
  token_url: "https://omapi.osinfra.cn/oneid/oidc/token"          # 可选，有默认值
  userinfo_url: "https://omapi.osinfra.cn/oneid/oidc/user"        # 可选，有默认值
  scope: "openid"                                                   # 可选，有默认值
```

**预览环境降级：** 当 `PREVIEW_ENV=true` 或配置值为 `${...}` 占位符时，使用测试配置，不抛异常。

> 来源：`wiki/entities/oidcclient.md`、`wiki/sources/oidc-client-txt.md`

---

## 5. 错误码

### 5.1 认证与鉴权错误

| HTTP 状态码 | 错误码 | 场景 | 处理建议 |
|-------------|--------|------|----------|
| 401 | `TOKEN_MISSING` | Authorization header 缺失或格式错误，`g.current_user` 不存在 | 检查请求是否携带有效的 Bearer token |
| 401 | `TOKEN_EXPIRED` | access_token 已过期（UserInfo 端点返回 expired） | 使用 refresh_token 刷新后重试 |
| 401 | `TOKEN_INVALID` | access_token 无效 | 重新进行授权码流程获取新 token |
| 403 | `ROLE_DENIED` | 用户已认证但不在知识上传白名单中 | 联系管理员将 user_id 加入 `rbac.knowledge_upload_users` 配置 |

### 5.2 Token 校验失效分类

`OIDCClient.validate_token()` 返回结构：

```json
{
  "valid": false,
  "reason": "TOKEN_EXPIRED | TOKEN_INVALID",
  "user_info": null
}
```

失效分类依据 RFC 6750 Bearer 错误语义：
- UserInfo 端点返回含 `"expired"` 描述 → `TOKEN_EXPIRED`
- 其他失败 → `TOKEN_INVALID`

> 来源：`wiki/concepts/知识上传白名单鉴权模型.md`、`wiki/entities/rbacmiddleware.md`、`wiki/sources/oidc-client-txt.md`

---

## 6. 数据库 Schema

### 6.1 表结构

| 表名 | 用途 | 写入方式 |
|------|------|----------|
| `forum_search_results` | 搜索关键字与结果（result_1..result_10 列，JSONB） | INSERT |
| `forum_retrieval_results` | 检索结果（related_docs，JSONB） | INSERT |
| `consume_tokens_topic` | token 用量统计 | UPSERT（ON CONFLICT topic_id DO UPDATE） |
| `evaluation_samples` | 评估样本（输入、上下文、输出、延迟、token） | INSERT |
| `forum_topics` | 已抓取帖子 ID（增量去重） | 只读 SELECT |
| `pre_audit_topics` | 预审帖子 ID（增量去重） | 只读 SELECT |

### 6.2 文件输出

| 内容 | 路径模式 |
|------|----------|
| 搜索结果 | `forum_data_dir/search_results_topic_{topic_id}_{timestamp}.json` |
| 检索结果 | `forum_data_dir/retrieval_results_{timestamp}.json` |
| 帖子数据 | `paths.csv_file` 配置指定的 CSV 文件（追加写入） |

> 来源：`wiki/concepts/数据处理与持久化模型.md`

---

## 7. SDK 使用示例

### 7.1 Token 用量追踪

```python
from src.token_tracker import token_tracker

# 记录一次模型调用的 token 用量
token_tracker.add_usage(
    topic_id="12345",
    prompt_tokens=150,
    completion_tokens=80,
    total_tokens=230
)

# 查询指定 topic 的用量
usage = token_tracker.get_usage("12345")
print(usage)
# {'prompt_tokens': 150, 'completion_tokens': 80, 'total_tokens': 230, 'model_calls': 1}

# 获取全量统计
all_usage = token_tracker.get_all_usage()

# 重置指定 topic
token_tracker.reset_usage("12345")
```

### 7.2 图像增强处理

```python
from src.image_processor import ImageProcessor

processor = ImageProcessor(config)

# 为包含图片标签的文本补充描述
enhanced_text = processor.enhance_text_with_image_descriptions(
    text="问题描述 [img: (screenshot.png)] 如上所示",
    context="user_question",
    topic_id="12345"
)
# 输出: "问题描述 [图片: 截图中显示了错误日志...] 如上所示"
```

### 7.3 ForumClient 使用

```python
from src.forum_client import ForumClient

client = ForumClient(config)

# 获取所有主题
topics = client.fetch_all_forum_topics()

# 获取主题详情
details = client.fetch_topic_details(topic_id=12345)

# 搜索相关主题
results = client.search_related_topics("安装报错")

# 检索相关文档
docs = client.retrieve_documents_for_topic(
    title="BMC 安装失败",
    question="安装过程中报 permission denied 错误"
)

# 回复帖子
client.reply_to_topic(topic_id=12345, raw="建议检查文件权限...")
```

### 7.4 服务启动

```bash
# 使用默认配置启动
python api_main.py

# 指定主机和端口
python api_main.py --host 0.0.0.0 --port 8080

# 指定配置文件
python api_main.py --config /path/to/config.yaml
```

### 7.5 编程方式启动

```python
from standalone_api import run_standalone_api

run_standalone_api(
    host="127.0.0.1",
    port=5085,
    config_file="/path/to/config.yaml"
)
```

---

## 8. 配置文件结构

```yaml
# OIDC 认证配置
oidc:
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  redirect_uri: "https://your-domain/callback"

# RBAC 权限配置
rbac:
  knowledge_upload_users:
    - "user_id_1"
    - "user_id_2"

# 外部模型服务
api:
  base_url: "https://model-service-url"
  api_key: "your-api-key"

# 图像处理
image_processing:
  base_url: "https://discuss.openubmc.cn"  # 可选，默认论坛地址
  model1: "model-name-1"
  model2: "model-name-2"
  model3: "model-name-3"

# 论坛 API 配置
posts:
  base_url: "https://discuss.openubmc.cn"
  api_key: "forum-api-key"
  api_username: "bot-username"
  verify_ssl: true

search:
  base_url: "https://search-service-url"
  verify_ssl: true

retrieval:
  base_url: "https://retrieval-service-url"
  verify_ssl: true

# 文件路径
paths:
  csv_file: "/path/to/output.csv"
  forum_data_dir: "/path/to/data/"
```

> 来源：`wiki/sources/oidc-client-txt.md`、`wiki/entities/forumclient.md`、`wiki/other/image-processor.md`

---

## 9. 架构概览

```
┌─────────────────────────────────────────────────────┐
│                   客户端请求                          │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  ForumBot 独立 API 服务 (127.0.0.1:5085)             │
│  ┌─────────────────────────────────────────────────┐ │
│  │  OIDC 认证中间件 (OIDCClient → g.current_user) │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │  RBACMiddleware (白名单鉴权)                     │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────┐ │
│  │  业务处理层                                      │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
         │                    │                │
         ▼                    ▼                ▼
   ┌──────────┐      ┌──────────────┐   ┌──────────┐
   │ OneID    │      │ PostgreSQL   │   │ 文件系统  │
   │ (OIDC)  │      │ (持久化)      │   │ JSON/CSV │
   └──────────┘      └──────────────┘   └──────────┘
```

> 来源：`wiki/overview.md`、`wiki/concepts/独立-api-服务部署模型.md`