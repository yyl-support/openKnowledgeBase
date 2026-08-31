# Index

## Sources

* [api_main.txt](/sources/api-main-txt.md) - ForumBot 独立 API 服务命令行入口脚本 api_main.py 的源码摘要。
* [data_processor.txt](/sources/data-processor-txt.md) - ForumBot 的 src.data_processor 模块源码摘要（第 2/2 块），覆盖数据持久化、帖子提取与提示词组装的完整流程。
* [forum_client.txt](/sources/forum-client-txt.md) - ForumClient 论坛客户端类的源码摘要，涵盖主题抓取、主题详情、帖子回复、相关主题搜索与文档检索能力。
* [monitor.txt](/sources/monitor-txt.md) - ForumBot 论坛监控模块（ForumMonitor）源码摘要（第 1/2 块），覆盖监控主循环、新帖处理与预审处理流程。
* [oidc_client.txt](/sources/oidc-client-txt.md) - OIDCClient 类的源码摘要，覆盖 OneID OIDC 认证客户端的配置读取、预览环境降级、授权码换 token、token 刷新与校验。
* [token_tracker.txt](/sources/token-tracker-txt.md) - src.token_tracker 模块（TokenTracker 类）的源码摘要，覆盖按 topic_id 累计 token 用量与模型调用次数的内存记账实现。

## Entities

* [多模态模型服务](/entities/多模态模型服务.md) - 由 config['api'] 配置的 OpenAI 兼容外部模型服务，承载 model1/model2/model3 三个多模态模型，用于生成图片内容描述。
* [api_main](/entities/api-main.md) - ForumBot 独立 API 服务的命令行启动入口脚本，负责路径注入、参数解析、日志初始化与服务委托启动。
* [data_processor](/entities/data-processor.md) - ForumBot 的数据处理模块，负责搜索结果、检索结果、token 用量与评估样本的数据库持久化，以及帖子数据提取与 CSV/JSON 导出。
* [ForumBot](/entities/forumbot.md) - ForumBot 整体系统平台，对应 src.ForumBot 包，独立 API 服务是其对外提供能力的一种运行形态。
* [ForumBot 独立 API 服务](/entities/forumbot-独立-api-服务.md) - ForumBot 对外提供的独立部署型 API 服务，默认监听 127.0.0.1:5085。
* [ForumClient](/entities/forumclient.md) - ForumBot 的论坛客户端模块，封装论坛主题抓取、主题详情、帖子回复、相关主题搜索与文档检索能力。
* [ForumMonitor](/entities/forummonitor.md) - ForumBot 的论坛监控模块，驱动新帖与预审帖的周期检查及全流程处理。
* [image_processor](/entities/image-processor.md) - ForumBot 的图像处理模块，通过 enhance_text_with_image_descriptions 为文本中的图像链接补充图像描述，供帖子数据提取流程使用。
* [logging_config](/entities/logging-config.md) - ForumBot 的日志配置模块，导出 main_logger 供入口脚本与系统其他部分使用。
* [OIDCClient](/entities/oidcclient.md) - OneID OIDC 认证客户端模块，封装 config.yaml oidc 段配置读取、授权码流程与 token 刷新校验，校验结果供认证中间件使用。
* [OneID](/entities/oneid.md) - 外部 OIDC 身份提供方，其 authorize、token、userinfo 端点均位于 omapi.osinfra.cn/oneid 路径下。
* [OpenUBMC 论坛](/entities/openubmc-论坛.md) - discuss.openubmc.cn 技术论坛，ForumBot 处理帖子的内容来源，也是图片相对路径的默认基准 URL。
* [RBACMiddleware](/entities/rbacmiddleware.md) - ForumBot 的知识上传白名单鉴权中间件类，基于 user_id 白名单控制知识上传 API 的访问权限。
* [standalone_api](/entities/standalone-api.md) - 提供 run_standalone_api() 的模块，负责实际拉起 ForumBot 独立 API 服务。
* [token_tracker](/entities/token-tracker.md) - ForumBot 的 token 用量追踪模块，提供 add_usage(topic_id, ...) 接口，按主题累计模型调用的 prompt/completion/total token 与调用次数，并导出全局单例供系统其他部分直接引用。

## Concepts

* [独立 API 服务部署模型](/concepts/独立-api-服务部署模型.md) - 将 ForumBot 的 API 能力作为独立进程部署的运行模型，通过命令行参数配置主机、端口与配置文件。
* [检索上下文与提示词组装](/concepts/检索上下文与提示词组装.md) - 将知识图谱（Entities/Relationships）与文档块（Document Chunks）等检索上下文与搜索结果合并，格式化后填充进 PROMPT_TEMPLATE 的提示词组装方式。
* [命令行入口启动流程](/concepts/命令行入口启动流程.md) - api_main 定义的从参数解析、路径注入、日志初始化到服务委托启动的标准启动流水线。
* [数据处理与持久化模型](/concepts/数据处理与持久化模型.md) - data_processor 将搜索结果、检索结果、token 用量与评估样本同时写入 PostgreSQL 表和 JSON/CSV 文件的 DB+文件双写持久化模型。
* [帖子数据提取与图像增强](/concepts/帖子数据提取与图像增强.md) - 从 Discourse 帖子流中提取用户问题、最佳答案与回复，并利用 image_processor 为文本中的图像补充描述的数据预处理流程。
* [知识上传白名单鉴权模型](/concepts/知识上传白名单鉴权模型.md) - 基于 user_id 白名单的简化权限模型，仅允许配置的白名单用户执行知识上传操作，搭配 401 与 403 两级错误契约。
* [token 用量追踪模型](/concepts/token-用量追踪模型.md) - 以 topic_id 为聚合键的内存记账机制，通过 add_usage 累加四项指标、reset_usage 清零重建、get_usage 对未跟踪 topic 返回零值默认项，并以模块级全局单例暴露给调用方。

## Other

* [图片标签提取与增强机制](/other/图片标签提取与增强机制.md)
* [image-processor](/other/image-processor.md)
