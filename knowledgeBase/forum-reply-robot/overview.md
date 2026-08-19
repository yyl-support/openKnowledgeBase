# forum-reply-robot 项目总览

## 1. 职责

**一句话**：自动监控论坛新帖并提供智能回复的机器人服务。

**解决的问题**：论坛新帖需要及时响应，但人工响应效率低且质量不稳定。本服务通过大模型结合知识库检索自动生成回答，对带特定标签的新帖提供常规问答，对带"预审"标签的帖子提供 Redfish/MDB 协议的结构化合规性评审。同时维护一套基于 LightRAG 的知识库，持续从论坛帖子和 GitCode 仓库文档中提取知识用于检索增强。服务常驻运行，周期性轮询论坛，全流程包含提示词注入检测、答案相关性与质量校验、token 消耗追踪，确保回复内容安全可靠。

## 2. 定位

本服务是论坛平台与 AI 能力之间的自动化桥梁，串联多个外部系统完成智能问答与合规评审。

**上游依赖**（数据与能力来源）：
- 论坛平台（Discourse 风格）：拉取新帖列表与详情，发布回复
- 大模型 API（OpenAI 兼容接口，实际指向 SiliconFlow 等）：生成问题摘要、答案、执行注入检测与质量校验
- LightRAG 服务：文档检索（RAG）与知识库灌入
- GitCode 仓库：作为知识源，提供 Schema 定义文件（Redfish_SchemaFiles、MDB_SchemaFiles）与文档数据
- PostgreSQL 数据库：权威数据存储，去重依据

**下游消费**（输出与接口）：
- 论坛用户：接收服务自动发布的回复（带"由 AI 生成，仅供参考"提示语）
- 外部监控系统：通过 Flask 健康检查接口（`/health`、`/health/detail`，5000 端口）感知服务状态

**在系统中的角色**：不参与论坛内容治理或用户管理，专注于"新帖触发 → 知识检索 → AI 生成 → 自动回复"的自动化流水线。

## 3. 边界

本服务**不负责**以下职责：

- **论坛平台管理**：用户注册/登录、帖子审核、权限控制、标签管理等由论坛平台自身承担
- **大模型训练或部署**：仅通过 API 调用外部大模型服务，不涉及模型的训练、微调或托管
- **知识库存储实现**：依赖外部 LightRAG 服务，本服务仅负责数据抓取、过滤与灌库调用
- **Schema 定义文件维护**：Redfish/MDB 的 Schema 文件由 GitCode 远程仓库维护，服务在构建期拉取，运行期只读使用
- **数据库运维**：PostgreSQL 的部署、备份、高可用由外部基础设施负责，服务仅作为客户端读写

**典型误区**：虽然服务会对帖子做提示词注入检测与内容质量校验，但这不等同于论坛的内容审核能力（如违规内容识别、人工复审流程），服务的校验仅用于决策"是否自动回复"，不影响帖子本身的可见性或状态。

## 4. 核心能力

| 能力 | 承载模块 | 说明 |
|------|----------|------|
| **常规问答回复** | `src/ForumBot/monitor.py`（编排）<br>`src/ForumBot/forum_client.py`（论坛交互）<br>`src/ForumBot/ai_processor.py`（大模型调用）<br>`src/ForumBot/data_processor.py`（数据处理与存储） | 监控带指定标签/类别的新帖，依次执行提示词注入检测 → 问题摘要 → 论坛站内搜索 + LightRAG 文档检索 → 大模型生成回答 → 答案相关性/质量双重校验 → 生成"AI 生成"提示语并折叠详细解答 → 调用论坛 API 发帖回复。全流程 token 消耗、搜索结果、检索结果、处理记录均落库（PostgreSQL）并写 CSV |
| **AI 预审回复** | `src/ForumBot/monitor.py`（编排）<br>`src/ForumBot/SchemaValidation/end_to_end_check.py`（Redfish 评审引擎入口）<br>`src/ForumBot/MdbValidation/mdb_checker.py`（MDB 合规校验）<br>`src/ForumBot/data_processor.py`（解析与存储） | 针对"预审"标签/类别的帖子，先解析帖子 HTML 判断作者是否已标记"准备好 AI 预审"，就绪后走结构化合规校验流程（Redfish Schema 校验 + MDB 规则校验），把校验报告作为评审意见回复。**不做搜索/检索**。基础设施/服务异常（超时、限流、空响应等）会被识别并拒绝发帖，避免把服务错误当成评审意见 |
| **知识库维护** | `src/update_lightrag/full_data_init.py`（全量初始化）<br>`src/update_lightrag/increment_date_update_timer.py`（增量更新定时器）<br>`src/update_lightrag/lightrag_client.py`（LightRAG 交互）<br>`src/update_lightrag/forum_data_Fetcher.py`（论坛数据抓取）<br>`src/update_lightrag/gitcode_client.py`（GitCode 数据抓取） | 启动时做一次全量初始化，随后由定时器（默认每天 18:00 UTC≈东八区凌晨 02:00）做增量更新。数据来源包括论坛帖子和 GitCode 仓库文档，处理后灌入 LightRAG 服务 |
| **服务健康检查** | `main.py`（Flask 应用） | 对外暴露 `/health` 和 `/health/detail` 两个接口，绑定到自动探测出的内网私有 IP（优先 `10.` 段，其次 `192.168.`）的 5000 端口。健康判定依赖监控线程是否存活，监控线程崩溃可被外部探针感知 |
| **数据持久化与去重** | `src/ForumBot/data_processor.py` | PostgreSQL 为权威存储，`forum_topics` / `pre_audit_topics` 表记录已见过的 topic_id，每轮只处理新 ID。数据库连接失败时跳过当轮而非崩溃。同时维护 CSV 文件作为并行输出 |
| **Token 消耗追踪** | `src/ForumBot/token_tracker.py`（全局单例）<br>`src/ForumBot/data_processor.py`（落库） | 跨模块按 topic_id 累计 prompt/completion/total token 用量，最终写入 `consume_tokens_topic` 表与 CSV |
| **安全防护** | `src/ForumBot/ai_processor.py`（提示词注入检测）<br>`src/utils.py`（配置文件删除） | 用户输入用随机字符串包裹后再喂给大模型以缓解提示词注入；`config/config.yaml` 加载后立即删除（`main.py` 的 `delete_config_file()`）以防敏感信息落盘 |

**说明**：
- 回复内容一律带"由 AI 生成，仅供参考"提示语，常规回答会把"总结/结论"章节摘出来放在折叠块外，完整解答放进 `[details]` 折叠块
- 去重以数据库为权威，数据库连接失败时跳过当轮而非崩溃
- 失败容错：单帖处理异常不影响其他帖子（逐帖 try/except continue）；大模型调用带重试与退避；注入检测/相关性/质量校验出错时默认从严（判为注入/不相关/不合格，宁可不回复）
