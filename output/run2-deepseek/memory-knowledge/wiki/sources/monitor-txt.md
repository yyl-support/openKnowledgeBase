---
type: source
title: monitor.txt
description: ForumBot 论坛监控模块（ForumMonitor）源码摘要（第 1/2 块），覆盖监控主循环、新帖处理与预审处理流程。
sources: ["monitor.txt"]
source_type: other
---

# monitor.txt

`monitor.txt` 是 [[ForumBot]] 论坛监控模块（[[ForumMonitor]]）的源码片段，本页为第 1/2 块。第 2 块可能包含文件入口（main）及剩余方法，待两块合并后补充本摘要。

## 内容摘要

- **模块定位**：`ForumMonitor` 是 ForumBot 的论坛监控模块，驱动新帖与预审帖的周期检查及全流程处理。
- **常量**：`KG_VOTE_THRESHOLD = 5`、`KG_HIGH_VOTE_MIN_COUNT = 4`、`KG_TOP_COUNT_IF_LOW_VOTE = 3`、`MAX_LINKS = 5`、`MAX_SEARCH_RESULTS = 5`。
- **监控主循环**：`start()` 按 `check_interval` 周期执行 `_check_new_topics` 与 `_check_pre_audit_topics`。
- **新帖处理链路**：`_check_new_topics` → `_process_new_topics`，体现「发现新帖 → 提示词注入检测 → 摘要 → 相关主题搜索 → 文档检索 → 大模型回答 → 相关性/质量把关 → 回复 → 落库 → 评估采样 → Prometheus 指标上报」的[[论坛监控流水线]]。
- **预审旁路流程**：`_check_pre_audit_topics` → `_process_pre_audit_topic`，即[[预审处理流程]]，Schema 验证后由预审模型作答。
- **相关链接生成**：`_generate_related_links` 实现知识图谱链接优先、搜索结果补充、按 topic_id 去重、过滤 news 路径、最多保留 5 条的策略。

## 关键调用关系

- [[ForumMonitor]] 调用 [[ForumClient]]（主题抓取/详情/搜索/检索/回复）、[[AIProcessor]]（注入检测/摘要/回答/质检）、[[DataProcessor]]（建表/落库/格式化）。
- [[token_tracker]] 提供 token 用量；[[evaluation_hooks]] 提供评估上下文与问题分类；[[prometheus_metrics]] 上报指标到 [[Prometheus]]。
- 预审流程使用 [[SchemaValidation]] 的 `run_schema_check` 与 `is_infrastructure_error_text`。

## 待第 2/2 块补充

- `main` 入口及启动方式（是否接入[[命令行入口启动流程]] / [[独立 API 服务部署模型]]）。
- 剩余方法实现（含 `_process_pre_audit_topic` 的后续逻辑）。
