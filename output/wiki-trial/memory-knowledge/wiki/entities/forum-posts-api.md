---
type: entity
title: Forum Posts API
description: 类 Discourse 风格的论坛后端，接收带鉴权的回复请求
sources: ["forum_client.txt"]
tags: [论坛, 外部系统, API]
kind: external_system
---

# 定义

Forum Posts API 是论坛系统的后端接口，[[ForumClient]] 通过其 `posts.json` 接口向指定主题发起回复。接口风格类似 Discourse。

# 关键属性

- 鉴权方式：请求头包含 `Api-Key` 与 `Api-Username`，值来自配置 `config['posts']['api_key']`、`config['posts']['api_username']`
- 端点：`{base_url}/posts.json`（POST）
- 请求体：`{"topic_id": ..., "raw": ...}`（JSON）
- 支持配置项：
  - `verify_ssl`（SSL 验证开关，默认 `True`）
  - `base_url`
- 超时设置：30 秒
- 成功响应：HTTP 200，返回 JSON 数据
- 失败处理：非 200 状态码或请求异常均记录错误日志并返回结构化失败结果（`success: False`）

# 关系

- 被 [[ForumClient]] 的 `reply_to_topic` 方法调用

# Citations

- forum_client.txt（`reply_to_topic` 方法）
