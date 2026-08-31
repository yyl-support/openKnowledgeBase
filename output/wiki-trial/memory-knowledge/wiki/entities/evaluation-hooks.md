---
type: entity
title: evaluation_hooks
description: 提供检索指标采集装饰器的评估辅助模块
sources: ["forum_client.txt"]
tags: [评估, 检索, 装饰器]
kind: module
---

# 定义

`evaluation_hooks` 是提供 `capture_retrieval_metrics` 装饰器的模块，用于在检索调用发生时采集评估指标。在 [[ForumClient]] 中，该装饰器被应用于 `_get_response_data` 方法，实现了 [[检索指标采集机制]]。

# 关键属性

- 提供装饰器：`capture_retrieval_metrics`
- 应用位置：装饰 [[ForumClient]] 的 `_get_response_data` 方法（该方法实际调用 [[Retrieval Service]]）

# 关系

- 被 [[ForumClient]] 依赖，用于装饰检索方法
- 是 [[检索指标采集机制]] 的实现载体

# 待补充

后续如摄入 `evaluation_hooks.py` 源码，应回来更新本页，补充装饰器内部实现与采集的具体指标字段。

# Citations

- forum_client.txt（导入语句及 `@capture_retrieval_metrics` 装饰器使用）
