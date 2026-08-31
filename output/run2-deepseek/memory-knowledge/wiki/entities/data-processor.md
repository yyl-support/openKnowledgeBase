---
type: entity
title: data_processor
description: ForumBot 的数据处理模块，负责搜索结果、检索结果、token 用量与评估样本的数据库持久化，以及帖子数据提取与 CSV/JSON 导出。
sources: ["data_processor.txt"]
tags: [模块, 数据处理, 持久化]
---

# data_processor

- kind: module

## 定义

`src.data_processor` 是 [[forumbot]] 平台内的数据处理模块，负责将 ForumBot 运行过程中产生的搜索结果、检索结果、token 用量与评估样本持久化到 PostgreSQL 与 JSON/CSV 文件，同时承担从 Discourse 帖子数据中提取用户问题、最佳答案与回复的职责。

## 关键属性

- 所属包：`src.ForumBot`（见 [[forumbot]]）
- 语言：Python
- 持久化方式：PostgreSQL 数据库 + JSON/CSV 文件双写
- 数据库表：forum_search_results、forum_retrieval_results、consume_tokens_topic、evaluation_samples、forum_topics、pre_audit_topics

## 主要方法

| 方法 | 职责 |
|---|---|
| `save_search_results_to_db` | 将搜索结果限量 10 条写入 forum_search_results 表（result_1..result_10 列） |
| `save_retrieval_results_to_db` | 将每个 topic_id 的 related_docs 写入 forum_retrieval_results 表 |
| `save_token_usage_to_db` | 按 topic_id 对 consume_tokens_topic 表做 upsert（ON CONFLICT DO UPDATE） |
| `save_evaluation_sample` | 写入评估样本记录，供 [[评估样本采集]] 使用 |
| `load_existing_data` / `load_pre_audit_existing_data` | 加载 forum_topics / pre_audit_topics 已有 ID，实现增量去重 |
| `extract_topic_data` | 提取帖子 id、标题、标签、用户问题、最佳答案与回复 |
| `append_to_csv` / `append_to_answer_csv` | 将提取数据追加写入 CSV 文件 |
| `process_search_results` / `process_retrieval_results` | 结果同时入库并落盘 JSON 文件 |
| `format_search_results_for_prompt` | 组装检索上下文并填充 PROMPT_TEMPLATE（见 [[检索上下文与提示词组装]]） |

## 关系

- 属于 [[forumbot]] 平台 src 包的组成模块。
- 调用 [[image_processor]] 为用户问题与最佳答案补充图像描述。
- 相关概念：[[数据处理与持久化模型]]、[[检索上下文与提示词组装]]、[[帖子数据提取与图像增强]]、[[评估样本采集]]。
- 源文档：[[data_processor.txt]]。
