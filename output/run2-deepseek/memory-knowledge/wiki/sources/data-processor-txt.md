---
type: source
title: data_processor.txt
description: ForumBot 的 src.data_processor 模块源码摘要（第 2/2 块），覆盖数据持久化、帖子提取与提示词组装的完整流程。
sources: ["data_processor.txt"]
tags: [源码摘要, 数据处理, 持久化]
---

# data_processor.txt

> 源码摘要页面，对应 `data_processor.txt` 第 2/2 块的内容。

## 源文档摘要

本文档为 `src.data_processor` 模块（类）的源码片段，展示了 [[data_processor]] 将帖子数据持久化的完整流程：

- 将搜索结果、检索结果、token 用量和评估样本写入 PostgreSQL（forum_search_results、forum_retrieval_results、consume_tokens_topic、evaluation_samples 等表）。
- 同时将结果以 JSON/CSV 文件形式落盘（DB + 文件双写）。
- 从 Discourse 话题数据中提取用户问题、最佳答案和回复的逻辑，并通过 [[image_processor]] 增强图像描述。
- 把知识图谱（Entities/Relationships）与文档块（Document Chunks）组装进 PROMPT_TEMPLATE 的提示词格式化方法。

## 主要内容

| 主题 | 关联页面 |
|---|---|
| 数据库 + 文件双写持久化 | [[数据处理与持久化模型]] |
| 检索上下文与提示词组装 | [[检索上下文与提示词组装]] |
| 帖子数据提取与图像增强 | [[帖子数据提取与图像增强]] |
| 评估样本采集 | [[评估样本采集]] |

## 涉及实体

- [[data_processor]] — 模块主体
- [[image_processor]] — 被调用的图像描述增强模块

## 涉及数据库表

forum_search_results、forum_retrieval_results、consume_tokens_topic、evaluation_samples、forum_topics、pre_audit_topics

## Citations

- 源码文件：`data_processor.txt`（第 2/2 块）
