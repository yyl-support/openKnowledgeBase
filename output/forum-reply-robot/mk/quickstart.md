---
生成时间: 2026-08-10 17:46:20
提取工具: mk
原始页面数: 35
仓库: forum-reply-robot (wiki=wiki-iw1oe7f2)
文档类型: quickstart
---

# ForumBot 快速开始指南

## 1. 安装步骤

### 1.1 克隆项目

```bash
git clone <your-repo-url>
cd forumbot
```

### 1.2 安装 Python 依赖

项目基于 Python，核心依赖包括：

```bash
pip install flask psycopg2-binary openai requests argparse
```

> 具体依赖版本请以项目根目录的 `requirements.txt` 或 `setup.py` 为准。如果存在该文件，直接执行：

```bash
pip install -r requirements.txt
```

### 1.3 数据库准备

系统使用 PostgreSQL 进行数据持久化（参考 `wiki/concepts/数据处理与持久化模型.md`）。确保本地或远程有可用的 PostgreSQL 实例：

```bash
# 创建数据库（示例）
createdb forumbot
```

## 2. 配置说明

### 2.1 配置文件

系统通过 YAML 配置文件驱动，启动时可通过 `--config` 参数指定路径，未指定时自动查找（参考 `wiki/entities/api-main.md`）。

配置文件核心段落：

```yaml
# 数据库连接
database:
  host: localhost
  port: 5432
  dbname: forumbot
  user: your_user
  password: your_password

# 多模态模型服务（OpenAI 兼容协议）
api:
  base_url: https://your-model-service/v1
  api_key: your_api_key

# 图像处理模型列表（故障转移顺序）
image_processing:
  model1: model-name-1
  model2: model-name-2
  model3: model-name-3
  base_url: https://discuss.openubmc.cn  # 图片相对路径基准 URL

# 论坛服务配置
posts:
  base_url: https://discuss.openubmc.cn
  api_key: your_forum_api_key
  api_username: your_bot_username
  verify_ssl: true

search:
  base_url: https://your-search-service
  verify_ssl: true

retrieval:
  base_url: https://your-retrieval-service
  verify_ssl: true

# OIDC 认证（参考 wiki/sources/oidc-client-txt.md）
oidc:
  client_id: your_client_id
  client_secret: your_client_secret
  redirect_uri: https://your-domain/api/v1/rag/auth/callback
  authorize_url: https://omapi.osinfra.cn/oneid/oidc/authorize   # 默认值
  token_url: https://omapi.osinfra.cn/oneid/oidc/token            # 默认值
  userinfo_url: https://omapi.osinfra.cn/oneid/oidc/user          # 默认值

# 知识上传白名单（参考 wiki/concepts/知识上传白名单鉴权模型.md）
rbac:
  knowledge_upload_users:
    - user_id_1
    - user_id_2

# 监控间隔
monitor:
  check_interval: 60

# 文件路径
paths:
  csv_file: data/forum_data.csv
  forum_data_dir: data/forum_data
```

### 2.2 必需配置项

| 配置项 | 说明 | 来源文档 |
|--------|------|----------|
| `api.base_url` / `api.api_key` | 多模态模型服务地址与密钥 | `wiki/entities/多模态模型服务.md` |
| `database.*` | PostgreSQL 连接信息 | `wiki/concepts/数据处理与持久化模型.md` |
| `posts.base_url` / `posts.api_key` | 论坛 API 地址与凭据 | `wiki/entities/forumclient.md` |
| `oidc.client_id` / `oidc.client_secret` | OIDC 认证凭据 | `wiki/sources/oidc-client-txt.md` |
| `rbac.knowledge_upload_users` | 知识上传白名单用户列表 | `wiki/entities/rbacmiddleware.md` |

### 2.3 环境变量

| 变量 | 说明 |
|------|------|
| `PREVIEW_ENV=true` | 启用预览环境，OIDC 使用测试配置（参考 `wiki/sources/oidc-client-txt.md`） |

## 3. 运行方法

### 3.1 启动独立 API 服务

这是 ForumBot 对外提供 API 能力的主要运行形态（参考 `wiki/concepts/独立-api-服务部署模型.md`）：

```bash
python api_main.py --host 127.0.0.1 --port 5085 --config config.yaml
```

参数说明：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--host` | `127.0.0.1` | 监听地址 |
| `--port` | `5085` | 监听端口 |
| `--config` | `None`（自动查找） | 配置文件路径 |

启动流程（参考 `wiki/concepts/命令行入口启动流程.md`）：
1. 路径注入：脚本目录和 `src` 子目录加入 `sys.path`
2. 参数解析：解析 CLI 参数
3. 日志初始化：加载 `logging_config.main_logger`
4. 委托启动：调用 `standalone_api.run_standalone_api()`

### 3.2 启动论坛监控服务

ForumMonitor 以主循环方式运行，按配置的 `check_interval` 周期轮询新帖（参考 `wiki/entities/forummonitor.md`）：

```bash
python -m src.ForumBot.monitor
```

## 4. 验证方法

### 4.1 API 服务验证

```bash
# 检查服务是否存活
curl http://127.0.0.1:5085/

# 查看日志输出
# 成功启动会看到类似日志：
# "正在启动 API 服务，地址：127.0.0.1:5085"
```

### 4.2 数据库连接验证

```bash
# 确认表已创建
psql -d forumbot -c "\dt"

# 应能看到以下表：
# forum_search_results, forum_retrieval_results, consume_tokens_topic,
# evaluation_samples, forum_topics, pre_audit_topics
```

### 4.3 日志确认

系统使用统一的 `main_logger`（参考 `wiki/entities/logging-config.md`）。正常启动后日志中应出现：

- API 服务：启动地址和端口信息
- Monitor 服务：开始周期检查的日志

### 4.4 Token 追踪验证

处理帖子后，通过 `token_tracker.get_all_usage()` 可查看各主题的 token 消耗统计（参考 `wiki/entities/token-tracker.md`）。数据库 `consume_tokens_topic` 表中也会有对应记录。

## 5. 常见问题

### Q1: 启动报 ModuleNotFoundError

**原因**：`sys.path` 未正确注入，或未从项目根目录启动。

**解决**：确保从项目根目录执行命令，`api_main.py` 会自动将脚本目录和 `src` 目录加入路径（参考 `wiki/sources/api-main-txt.md`）。

```bash
cd /path/to/forumbot
python api_main.py
```

### Q2: 数据库连接失败

**原因**：PostgreSQL 未启动或配置项错误。

**解决**：
1. 确认 PostgreSQL 服务运行中：`pg_isready`
2. 检查配置文件中 `database` 段的 host/port/dbname/user/password
3. 确认数据库已创建且用户有权限

### Q3: OIDC 认证报错 ValueError

**原因**：`oidc` 配置段缺少必填项（`client_id`、`client_secret`、`redirect_uri`）。

**解决**：补全配置项。如果是开发/预览环境，可设置环境变量跳过严格校验（参考 `wiki/sources/oidc-client-txt.md`）：

```bash
export PREVIEW_ENV=true
python api_main.py
```

### Q4: 图像处理失败，日志显示模型调用错误

**原因**：多模态模型服务不可达或 API key 无效。

**解决**：
1. 确认 `api.base_url` 可访问
2. 确认 `api.api_key` 有效
3. 系统会按 model1 → model2 → model3 故障转移（参考 `wiki/other/图片标签提取与增强机制.md`），三个模型全部失败才会返回兜底文案

### Q5: 知识上传 API 返回 401 或 403

**原因**：
- 401 `TOKEN_MISSING`：请求缺少 Authorization header 或格式错误
- 403 `ROLE_DENIED`：用户不在白名单中

**解决**（参考 `wiki/concepts/知识上传白名单鉴权模型.md`）：
1. 确保请求携带有效的 Bearer token
2. 将用户 ID 添加到配置文件 `rbac.knowledge_upload_users` 列表中

### Q6: 论坛帖子抓取无新数据

**原因**：增量去重机制生效，`forum_topics` 表中已有对应帖子 ID。

**解决**：这是正常行为。系统通过 `load_existing_data` 加载已入库 ID 实现增量抓取（参考 `wiki/concepts/数据处理与持久化模型.md`）。如需重新处理，需清理对应表记录。