---
type: entity
kind: module
title: ForumClient
description: ForumBot 的论坛客户端模块，封装论坛主题抓取、主题详情、帖子回复、相关主题搜索与文档检索能力。
sources: ["forum_client.txt"]
tags: [ForumBot, 论坛客户端, 模块]
---

# ForumClient

## 定义

ForumClient 是 [[ForumBot]] 平台下的论坛客户端模块（`forum_client.py`），对外提供论坛主题抓取、主题详情获取、帖子回复、相关主题搜索与文档检索五类能力。所有外部服务地址与参数均从 `self.config` 的 `posts`、`search`、`retrieval` 三段配置读取，各段均支持 `verify_ssl` 开关。

## 关键属性

- **配置驱动**：构造函数接收 `config`，各外部服务的 `base_url`、密钥与参数均在对应配置段（`posts` / `search` / `retrieval`）下声明。
- **SSL 开关**：三段配置均支持 `verify_ssl`（默认 `True`），控制是否校验外部服务 TLS 证书。
- **日志**：通过 [[logging_config]] 导出的 `main_logger` 记录请求、成功与错误日志。
- **指标采集**：检索方法 `_get_response_data` 应用 `@capture_retrieval_metrics` 装饰器。

## 方法清单

| 方法 | 职责 | 外部依赖 |
|---|---|---|
| `fetch_all_forum_topics` | 获取所有论坛主题，支持 tag / cutoff_date / category_path 可配置键 | [[data_processor]] |
| `fetch_topic_details` | 根据 `topic_id` 获取单个帖子详情 | [[data_processor]] |
| `reply_to_topic` | 回复指定主题，使用 `Api-Key` / `Api-Username` 请求头，payload 为 `topic_id` + `raw` | [[外部论坛服务（posts API）]] |
| `search_related_topics` | 按关键字搜索相关主题，清洗记录中的 HTML 标签并过滤当前帖子 | [[相关主题搜索服务（search API）]] |
| `retrieve_documents_for_topic` | 以"标题 + 用户问题"构造查询，为单个帖子检索相关文档 | [[文档检索服务（retrieval API）]] |
| `_get_response_data` | 发送查询请求并返回响应数据，应用 `@capture_retrieval_metrics` 装饰器 | [[文档检索服务（retrieval API）]]、[[evaluation_hooks]] |
| `_remove_html_tags` | 去除 HTML 标签的工具方法 | — |

## 关系

- 委托 [[data_processor]] 完成主题抓取与详情获取。
- 调用 [[外部论坛服务（posts API）]] 发布帖子回复。
- 调用 [[相关主题搜索服务（search API）]] 查找相关主题。
- 调用 [[文档检索服务（retrieval API）]] 为自动回复检索上下文。
- 通过 `@capture_retrieval_metrics` 装饰器与 [[evaluation_hooks]] 关联，参与 [[检索指标采集机制]]。
- 属于 [[ForumBot]] 系统平台下的论坛客户端模块。
- 使用 [[logging_config]] 的 `main_logger` 记录日志。

## 参见

- [[论坛文档检索数据流]]
- [[检索指标采集机制]]
