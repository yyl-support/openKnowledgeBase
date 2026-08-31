# Index

## Sources

* [forum_client.txt](/sources/forum-client-txt.md) - ForumClient 类源码，封装论坛主题拉取、回复、搜索与文档检索四大能力，本次更新新增了一个位置异常的实验性方法 brand_new_capability。

## Entities

* [data_processor](/entities/data-processor.md) - 提供论坛主题拉取相关函数与默认配置键的依赖模块
* [evaluation_hooks](/entities/evaluation-hooks.md) - 提供检索指标采集装饰器的评估辅助模块
* [Forum Posts API](/entities/forum-posts-api.md) - 类 Discourse 风格的论坛后端，接收带鉴权的回复请求
* [ForumClient](/entities/forumclient.md)
* [Retrieval Service](/entities/retrieval-service.md) - RAG 风格的文档检索后端，为论坛主题提供相关文档检索能力
* [Search Service](/entities/search-service.md) - 内部关键词搜索服务，用于检索相关论坛主题

## Concepts

* [检索指标采集机制](/concepts/检索指标采集机制.md) - 通过装饰器对检索函数进行包装以采集评估指标的设计模式
* [论坛自动问答/检索处理链路](/concepts/论坛自动问答-检索处理链路.md) - 从主题拉取、查询构造、文档检索到自动回复的端到端数据流。
* [相关主题搜索与内容清洗](/concepts/相关主题搜索与内容清洗.md) - 关键词长度截断加 HTML 标签去除的搜索后处理模式
* [主题文档检索流程](/concepts/主题文档检索流程.md) - 将主题标题与用户问题拼接为查询，调用检索服务同时获取 response 与 data 两类结果的数据流模式
