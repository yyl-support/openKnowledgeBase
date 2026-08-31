---
type: concept
title: token 用量追踪模型
description: 以 topic_id 为聚合键的内存记账机制，通过 add_usage 累加四项指标、reset_usage 清零重建、get_usage 对未跟踪 topic 返回零值默认项，并以模块级全局单例暴露给调用方。
sources: ["token_tracker.txt"]
tags: [记账, 数据流, token追踪]
---

# token 用量追踪模型

## 定义

以 `topic_id` 为聚合键、在内存中按主题累计模型调用开销的记账机制。核心操作包括：`add_usage` 累加 `prompt_tokens`/`completion_tokens`/`total_tokens` 并递增 `model_calls`；`reset_usage` 将指定主题的统计清零重建；`get_usage` 对未跟踪主题返回零值默认项；`get_all_usage` 导出全量统计。该机制以模块级全局单例（[[token_tracker]]）暴露给调用方，属于"先记账、后持久化"的轻量计量层。

## 意义

- 为按主题（对话/任务）独立核算模型调用开销提供统一口径，避免调用方各自维护计数。
- 通过零值默认项与自动初始化（未知 topic 首次 `add_usage` 前先 `reset_usage`）保证幂等累加语义。
- 与 [[数据处理与持久化模型]] 配合，可将内存记账结果写入 PostgreSQL 表与 JSON/CSV 文件，实现计量数据的落盘。
- 全部统计口径由单一模块持有，便于审计与重置。

## 数据流

[[多模态模型服务]]（model1/model2/model3）调用产生 token 开销 → `add_usage(topic_id, ...)` 累加至 [[token_tracker]] 内存字典 → 经 `get_usage`/`get_all_usage` 读取 → 由 [[data_processor]] 持久化到 PostgreSQL 表与 JSON/CSV 文件。

## Schema

每主题统计记录结构：

| 字段 | 含义 |
| --- | --- |
| `prompt_tokens` | 输入 token 累计 |
| `completion_tokens` | 输出 token 累计 |
| `total_tokens` | 总 token 累计 |
| `model_calls` | 模型调用次数 |

## 相关实体

- 实现模块：[[token_tracker]]（全局单例 `token_tracker`）
- 日志来源：[[logging_config]]
- 用量产生方：[[多模态模型服务]]
- 用量接收方：[[data_processor]]、[[数据处理与持久化模型]]
- 源码依据：[[token_tracker.txt]]
