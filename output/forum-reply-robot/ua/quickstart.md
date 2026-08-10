---
生成时间: 2026-08-10 17:43:00
提取工具: ua
原始页面数: 237
仓库: /tmp/ua-trial/forum-reply-robot
文档类型: quickstart
---

# forum-reply-robot 快速开始指南

## 1. 环境要求

- Python 3.9+
- PostgreSQL 数据库实例
- Docker（可选，用于容器化部署）
- Git
- 可访问的大模型 API（默认使用 SiliconFlow Qwen3-235B）
- LightRAG 服务实例
- 论坛账号与 API 访问凭据

---

## 2. 安装步骤

### 2.1 克隆仓库

```bash
git clone <仓库地址>
cd forum-reply-robot
```

### 2.2 安装 Python 依赖

```bash
pip install -r requirements.txt
```

如需运行测试：

```bash
pip install -r requirements-test.txt
```

> 依赖清单路径：`requirements.txt`、`requirements-test.txt`、`requirements-eval.txt`

### 2.3 拉取 Schema 文件

服务启动时会校验 Redfish Schema 与 MDB 规则文件是否存在。需要将对应的 Schema 仓库克隆到项目目录下（Dockerfile 中有此步骤的参考）：

```bash
# 根据 Dockerfile 中的构建逻辑，拉取 Redfish/MDB Schema 文件仓库
# 具体仓库地址请参考 Dockerfile 中的 git clone 命令
```

> 相关路径：`Dockerfile`、`src/ForumBot/SchemaValidation/SchemaFiles/`、`src/ForumBot/MdbValidation/MdbRuleFiles/`

---

## 3. 配置说明

### 3.1 核心配置文件

编辑 `config/config.yaml`，这是项目唯一的运行时配置文件：

```yaml
# 大模型 API 配置（必填）
base_url: "https://api.siliconflow.cn/v1"   # 大模型 API 地址
api_key: "your-api-key-here"                  # API 密钥
model_name: "Qwen/Qwen3-235B-A22B"          # 模型名称
```

> 配置路径：`config/config.yaml`
> 加载逻辑：`src/utils.py` 中的 `load_config()` 函数

**安全建议**：当前 api_key 以明文存放在 YAML 中，生产环境建议改用环境变量或密钥管理服务注入。

### 3.2 其他需要配置的外部服务

根据项目架构，还需要配置以下服务的连接信息（在 `config/config.yaml` 中）：

| 配置项 | 说明 |
|--------|------|
| PostgreSQL 连接信息 | 数据库地址、端口、用户名、密码、库名 |
| 论坛 API 凭据 | 论坛访问地址、API Token |
| LightRAG 服务地址 | 知识库服务的 URL |
| GitCode API Token | 用于拉取代码仓库数据（可选） |
| OIDC 配置 | 如启用认证中间件，需配置 OIDC 提供商信息 |

### 3.3 PostgreSQL 数据库准备

服务启动时会自动检查并创建目标数据库（`src/utils.py` 中的 `ensure_database_exists()`），但需要确保：

```bash
# PostgreSQL 服务已启动且可连接
# 配置中的数据库用户有创建数据库的权限
```

---

## 4. 运行方法

### 4.1 直接运行

```bash
python main.py
```

服务启动后的进程模型：

1. `main()` → 加载配置、校验 Schema 文件
2. 注册 RAG API Blueprint、创建限流表
3. 启动后台初始化线程（`initialization_worker`）：
   - 创建 `ForumMonitor` 实例并启动监控守护线程
   - 触发 LightRAG 全量初始化
   - 启动增量更新定时器
4. 主线程运行 Flask 服务（默认端口 5000）

> 入口文件：`main.py`

### 4.2 Docker 容器运行

```bash
# 构建镜像
docker build -t forum-reply-robot .

# 运行容器
docker run -d \
  -p 5000:5000 \
  -p 5001:5001 \
  -v $(pwd)/config:/app/config \
  forum-reply-robot
```

容器暴露两个端口：
- `5000`：主服务（健康检查、Prometheus 指标、RAG API）
- `5001`：附属 API 进程

> 相关文件：`Dockerfile`

### 4.3 独立 API 服务（调试用）

```bash
python -m src.ForumBot.api_main --host 0.0.0.0 --port 5001 --config config/config.yaml
```

> 相关文件：`src/ForumBot/api_main.py`、`src/ForumBot/standalone_api.py`

---

## 5. 验证方法

### 5.1 健康检查

```bash
# 基础存活检查
curl http://localhost:5000/health

# 详细健康检查（含监控线程、配置文件与规则文件状态）
curl http://localhost:5000/health/detailed

# 启动自检（依赖就绪情况）
curl http://localhost:5000/startup
```

> 接口定义：`main.py` 中的 `health_check()`、`detailed_health_check()`、`startup_check()`

### 5.2 Prometheus 指标

```bash
curl http://localhost:5000/metrics
```

> 指标定义：`src/ForumBot/prometheus_metrics.py`

### 5.3 运行测试

```bash
pytest
```

> 测试配置：`pytest.ini`（已禁用 pytest-asyncio 插件以避免版本冲突）

---

## 6. 常见问题

### Q1: 启动报错 `Schema files not found`

**原因**：Redfish Schema 定义文件或 MDB 规则文件未正确放置。

**解决**：确认以下路径下存在对应文件：
- `src/ForumBot/SchemaValidation/SchemaFiles/redfish_compliance_rules.json`
- `src/ForumBot/MdbValidation/MdbRuleFiles/mdb_compliance_rules_v6.5.json`

参考 `main.py` 中的 `check_schema_files()` 和 `check_mdb_rule_files()` 了解具体校验逻辑。

### Q2: 数据库连接失败

**原因**：PostgreSQL 未启动或连接信息配置错误。

**解决**：
1. 确认 PostgreSQL 服务运行中
2. 检查 `config/config.yaml` 中数据库连接参数
3. 确保配置的用户有 CREATE DATABASE 权限（首次运行需要自动建库）

> 连接池逻辑：`src/utils.py` 中的 `init_db_connection_pool()`

### Q3: 大模型调用超时或报错

**原因**：API 地址不可达、密钥无效或模型不可用。

**解决**：
1. 验证 `config/config.yaml` 中的 `base_url` 可访问
2. 确认 `api_key` 有效
3. 服务内置多模型轮询与重试机制，检查日志中具体的错误信息

> 重试逻辑：`src/ForumBot/ai_processor.py`

### Q4: pytest 启动崩溃，报 `FixtureDef` 相关错误

**原因**：pytest-asyncio 插件版本与 pytest 7.4.4 不兼容。

**解决**：项目已通过 `pytest.ini` 中的 `-p no:asyncio` 禁用该插件。如仍有问题，确认使用的是 `requirements-test.txt` 中钉定的 pytest 版本：

```bash
pip install pytest==7.4.4 pytest-cov==4.1.0 pytest-mock==3.12.0
```

> 配置文件：`pytest.ini`

### Q5: LightRAG 知识库初始化时间过长

**原因**：全量初始化需要抓取论坛和 GitCode 的全部数据并上传。

**解决**：
- 全量初始化在后台线程执行，不阻塞主服务启动
- 可通过 `/startup` 接口查看初始化进度
- LightRAG 客户端会轮询 pipeline 状态避免并发写入冲突

> 相关文件：`src/update_lightrag/full_data_init.py`、`src/update_lightrag/lightrag_client.py`

### Q6: 日志文件在哪里？

日志基于 `RotatingFileHandler` 自动轮转，查看 `src/ForumBot/logging_config.py` 中配置的日志目录。所有模块共享 `main_logger` 全局实例。

---

## 7. 项目目录结构概览

```
forum-reply-robot/
├── main.py                          # 服务主入口
├── config/
│   └── config.yaml                  # 运行时配置
├── src/
│   ├── utils.py                     # 配置加载、数据库连接池
│   ├── external_api_app.py          # 独立调试 API 工厂
│   ├── ForumBot/
│   │   ├── monitor.py              # 论坛监控主循环
│   │   ├── ai_processor.py         # 大模型调用封装
│   │   ├── forum_client.py         # 论坛 HTTP 客户端
│   │   ├── data_processor.py       # 数据清洗与持久化
│   │   ├── logging_config.py       # 日志配置
│   │   ├── SchemaValidation/       # Redfish 合规校验
│   │   └── MdbValidation/          # MDB 合规校验
│   ├── update_lightrag/            # RAG 数据管道
│   └── evaluation/                 # 离线评测工具
├── Dockerfile
├── requirements.txt
├── requirements-test.txt
└── pytest.ini
```