---
type: entity
title: Retrieval Service
description: RAG 风格的文档检索后端，为论坛主题提供相关文档检索能力
sources: ["forum_client.txt"]
tags: [检索, RAG, 外部系统]
kind: external_system
---

# 定义

Retrieval Service 是 RAG（Retrieval-Augmented Generation）风格的文档检索后端，[[ForumClient]] 通过其 `query_endpoint` 及对应的 `/data` 子路径检索与查询相关的文档，是 [[主题文档检索流程]] 的核心依赖。

# 关键属性

- 主端点：`{base_url}{query_endpoint}`（POST），返回 `response` 字段
- 数据端点：`{base_url}{query_endpoint}/data`（POST），返回完整数据 `result_data`
- 请求体（JSON payload）：
  - `query`：拼接后的查询字符串（主题标题 + 用户问题）
  - `only_need_prompt`：是否只需 prompt，默认 `False`
  - `only_need_context`：是否只需上下文，默认 `True`
  - `top_k`：检索文档数量上限
  - `chunk_top_k`：检索文档片段数量上限
  - `enable_rerank`：是否启用重排序
- SSL 验证：`config['retrieval']['verify_ssl']`（默认 `True`）
- 超时设置：600 秒（远高于其他两个外部系统，反映检索/重排序耗时较长）
- 错误处理：`requests.RequestException` 与 `ValueError`（JSON 解析错误）均被捕获并记录日志

# 关系

- 被 [[ForumClient]] 的 `_get_response_data` 方法调用（该方法由 [[evaluation_hooks]] 的装饰器包装）
- 是 [[主题文档检索流程]] 的实现载体
- 检索调用被 [[检索指标采集机制]] 监控

# Citations

- forum_client.txt（`_get_response_data` 方法）
