# forum-reply-robot 项目总览

## 1. 职责

forum-reply-robot 是一个自动监控论坛新帖并智能回复的机器人服务。

它常驻运行，周期性轮询论坛，对新帖调用大模型生成回答并自动发布，同时维护一套基于 LightRAG 的知识库用于检索增强（`CLAUDE.md`）。服务承担两条相互独立的处理链路：一是常规问答回复（对新帖做搜索/检索后生成回答并发帖），二是 AI 预审回复（对"预审"标签帖子做 Redfish/MDB 结构化合规校验，把校验报告作为评审意见回复）。它解决的问题是把论坛上人工答疑、以及 Redfish/MDB 接口合规评审这两类重复性工作自动化，同时通过知识库检索增强保证回答有据可查。

## 2. 定位

- **上游**：论坛平台（Discourse 风格 API，`posts` 配置段），提供新帖列表、帖子详情、发帖能力；GitCode 远程仓库，提供 Redfish/MDB Schema 规则文件（构建期拉取）和知识源文档。
- **本体**：作为独立服务运行，`main.py` 是唯一生产入口，内部由 Flask 主线程（仅对外暴露健康检查）+ 两个守护线程（`ForumMonitor` 轮询、LightRAG 定时增量更新）构成（`CLAUDE.md`）。
- **下游**：
  - 大模型 API（OpenAI 兼容接口，如 SiliconFlow），承担摘要、注入检测、答案生成与校验、Redfish/MDB 合规校验。
  - LightRAG 服务，承担文档检索与知识库灌入。
  - PostgreSQL，作为去重与处理记录的权威存储。
  - 论坛平台 API，作为最终发帖出口。

## 3. 边界

- **不负责**论坛平台本身的帖子存储、用户体系、权限管理——这些由外部的 Discourse 风格论坛系统承担，本服务只是它的 API 调用方。
- **不负责**知识库的语义索引/图谱构建算法——LightRAG 服务本身负责检索与图谱能力，本服务只做数据抓取、过滤后灌入。
- **不负责**Redfish/MDB Schema 规则集的维护——规则文件在构建期从 GitCode 远程仓库拉取（`Dockerfile`），不在本仓库版本管理范围内。
- `src/ForumBot/api_main.py` / `standalone_api.py` 等独立调试 API（默认监听 `127.0.0.1:5085`）不是生产主链路，仅用于按需触发单项能力做调试，不承担常驻监控职责。
- `src/evaluation/` 下的评估数据集构建与基线运行是离线评估工具，不参与线上回复流程。

## 4. 核心能力

| 能力 | 承载模块 |
| --- | --- |
| 论坛新帖监控与轮询编排 | `src/ForumBot/monitor.py`（`ForumMonitor`） |
| 常规问答回复（搜索+检索+生成+校验+发帖） | `monitor.py` → `forum_client.py` / `ai_processor.py` / `data_processor.py` |
| AI 预审回复（Redfish/MDB 合规校验并发布评审报告） | `src/ForumBot/SchemaValidation/end_to_end_check.py`（`run_schema_check`）+ `src/ForumBot/MdbValidation/` |
| 论坛 HTTP 交互（拉帖列表/详情、发帖、站内搜索、LightRAG 检索） | `src/ForumBot/forum_client.py`（`ForumClient`） |
| 大模型调用（摘要、注入检测、答案相关性/质量校验、生成回答） | `src/ForumBot/ai_processor.py`（`AIProcessor`） |
| 数据持久化与解析（PostgreSQL 建表读写、CSV、HTML 解析） | `src/ForumBot/data_processor.py`（`DataProcessor`） |
| Token 用量统计 | `src/ForumBot/token_tracker.py` |
| 服务健康检查 | `main.py`（Flask `/health`、`/health/detail`） |
| 知识库全量初始化 | `src/update_lightrag/full_data_init.py`（`FullDataUpdate`） |
| 知识库定时增量更新（论坛帖子 + GitCode 文档） | `src/update_lightrag/increment_date_update_timer.py`（`UpdateIncrementData` / `UpdateLightRAGTimer`）+ `forum_data_Fetcher.py` / `gitcode_client.py` / `gitode_full_fetcher.py` / `gitcode_api_increment_fetcher.py` |
