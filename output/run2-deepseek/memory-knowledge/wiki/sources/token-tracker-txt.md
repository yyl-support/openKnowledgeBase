---
type: source
source_type: other
title: token_tracker.txt
description: src.token_tracker 模块（TokenTracker 类）的源码摘要，覆盖按 topic_id 累计 token 用量与模型调用次数的内存记账实现。
sources: ["token_tracker.txt"]
tags: [源码摘要, token追踪, 记账]
---

# token_tracker.txt

`src/token_tracker.py` 的源码摘要，对应 ForumBot 中负责模型调用 token 开销记账的 [[token_tracker]] 模块。

## 摘要

- 定义 `TokenTracker` 类：以 `topic_id` 为键，在内存字典 `token_usage` 中按主题累计 `prompt_tokens`、`completion_tokens`、`total_tokens` 与 `model_calls` 四项统计。
- 对外接口：`reset_usage(topic_id)`、`add_usage(topic_id, ...)`、`get_usage(topic_id)`、`get_all_usage()`。
- 模块末尾创建全局单例 `token_tracker = TokenTracker()`，供系统其他部分直接引用。
- 日志统一通过 `logging_config.main_logger` 输出，见 [[logging_config]]。

## 接口约定

| 方法 | 语义 |
| --- | --- |
| `reset_usage(topic_id)` | 将指定 topic 的四项统计清零重建，并输出重置日志 |
| `add_usage(topic_id, prompt_tokens, completion_tokens, total_tokens)` | 累加三项 token 指标并递增 `model_calls`；未跟踪的 topic 自动先重置 |
| `get_usage(topic_id)` | 返回指定 topic 的统计；未跟踪的 topic 返回零值默认项 |
| `get_all_usage()` | 返回所有 topic 的统计字典 |

## 关联

- 实现模块：[[token_tracker]]
- 记账机制抽象：[[token 用量追踪模型]]
- 日志来源：[[logging_config]]
- 用量产生方：[[多模态模型服务]]
- 用量持久化：[[data_processor]]、[[数据处理与持久化模型]]
