---
type: entity
title: Search Service
description: 内部关键词搜索服务，用于检索相关论坛主题
sources: ["forum_client.txt"]
tags: [搜索, 外部系统]
kind: external_system
---

# 定义

Search Service 是内部关键词搜索服务，[[ForumClient]] 通过其接口检索相关主题。返回结果中的标题与正文可能带有 HTML 标签，需经过清洗，参见 [[相关主题搜索与内容清洗]]。

# 关键属性

- 端点：`{base_url}{endpoint}`（POST），由 `config['search']['base_url']` 与 `config['search']['endpoint']` 拼接
- 请求头：
  - `source`：来自 `config['search']['source']`
  - `referer`：来自 `config['search']['referer']`（可选，默认空字符串）
- 请求体（JSON）：
  - `keyword`：搜索关键词（超过 `config['search']['max_keyword_length']` 会被截断）
  - `lang`：固定为 `"zh"`
  - `type`：空字符串
  - `filter`：`[{}]`
  - `pageSize`：结果数量，默认取 `config['search']['default_page_size']`
- SSL 验证：`config['search']['verify_ssl']`（默认 `True`）
- 超时设置：30 秒
- 响应结构：`result['obj']['records']`，每条记录含 `title`、`textContent` 字段（含 HTML 标签，需清洗）

# 关系

- 被 [[ForumClient]] 的 `search_related_topics` 方法调用
- 其返回结果由 [[相关主题搜索与内容清洗]] 流程处理

# Citations

- forum_client.txt（`search_related_topics` 方法）
