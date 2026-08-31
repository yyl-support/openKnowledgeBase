---
type: entity
title: token_tracker
description: ForumBot 的 token 用量追踪模块，提供 add_usage(topic_id, ...) 接口，按主题累计模型调用的
  prompt/completion/total token 与调用次数，并导出全局单例供系统其他部分直接引用。
sources:
  - image_processor.txt
  - token_tracker.txt
tags:
  - token追踪
  - 成本统计
  - 模块
  - 记账
kind: module
---

# token_tracker

## 定义

[[ForumBot]] 中 `src` 包内的 token 用量追踪模块（`src/token_tracker.py`），基于 `TokenTracker` 类以内存字典按主题（`topic_id`）累计模型调用的 token 开销，为成本统计提供数据。模块末尾实例化全局单例 `token_tracker`，供系统其他部分直接引用。

## 关键属性

- 以 `topic_id` 为聚合键，存储于 `token_usage` 字典。
- 每主题累计四项统计：`prompt_tokens`、`completion_tokens`、`total_tokens`、`model_calls`。
- 对未跟踪的 `topic_id`，`get_usage` 返回全部为零的默认统计项。
- `add_usage` 遇到未跟踪 topic 时自动先调用 `reset_usage` 初始化。

## 关键接口

| 方法 | 行为 |
| --- | --- |
| `reset_usage(topic_id)` | 清零重建指定 topic 的四项统计，经 [[logging_config]] 的 main_logger 输出重置日志 |
| `add_usage(topic_id, prompt_tokens=0, completion_tokens=0, total_tokens=0)` | 把一次模型调用的 token 用量记入指定主题；累加三项 token 指标并将 `model_calls` 递增 1，输出更新日志 |
| `get_usage(topic_id)` | 返回指定 topic 统计；未跟踪 topic 返回零值默认项 |
| `get_all_usage()` | 返回全部 topic 的统计字典 |

## 说明

- 早期源码（`src/image_processor.py`）只展示了 `add_usage` 的调用方式，未包含实现细节；`src/token_tracker.txt` 提供了类实现与接口语义。
- [[ImageProcessor]] 仅在多模态模型调用成功且响应含 `usage` 时记录；token 字段缺失时按 0 记账，兼容不同模型响应。

## 关系

- 被 [[ImageProcessor]] 依赖：在 `_call_multimodal_model` 中按 `topic_id` 记录 token。
- 服务于 [[ForumBot]] 主题处理流程：按主题记账，支撑成本统计与用量分析。
- 日志：通过 `from .logging_config import main_logger as logger` 复用 [[logging_config]] 的 main_logger。
- 持久化：追踪得到的 token 用量由 [[data_processor]] 落库/落盘，见 [[数据处理与持久化模型]]。
- 用量来源：记录的是对 [[多模态模型服务]]（model1/model2/model3）调用所产生的 token 开销。
- 记账机制抽象：见 [[token 用量追踪模型]]。
- 源码摘要：见 [[image_processor.txt]] 与 [[token_tracker.txt]]。
