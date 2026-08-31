---
type: entity
title: ForumMonitor
description: ForumBot 的论坛监控模块，驱动新帖与预审帖的周期检查及全流程处理。
sources: ["monitor.txt"]
tags: [ForumBot, 监控, 流水线]
---

# ForumMonitor

## Schema

- **kind**: module
- **所属系统**: [[ForumBot]]
- **依赖模块**: [[ForumClient]]、[[AIProcessor]]、[[DataProcessor]]、[[token_tracker]]、[[evaluation_hooks]]、[[prometheus_metrics]]、[[SchemaValidation]]、[[logging_config]]
- **外部系统**: [[大模型服务]]（经由 AIProcessor）、[[Prometheus]]（经由 prometheus_metrics）

## 定义

ForumMonitor 是 ForumBot 的论坛监控模块，负责周期性检查新帖与预审帖，并驱动从发现、AI 处理到落库评估的完整[[论坛监控流水线]]。它以 `while True` 主循环运行，按配置的 `check_interval` 间隔执行检查。

## 关键属性

| 常量 | 值 | 含义 |
| --- | --- | --- |
| `KG_VOTE_THRESHOLD` | 5 | 知识图谱链接的票数阈值 |
| `KG_HIGH_VOTE_MIN_COUNT` | 4 | 达到票阈值链接的保留数量 |
| `KG_TOP_COUNT_IF_LOW_VOTE` | 3 | 票数不足时保留的 KG 链接数量 |
| `MAX_LINKS` | 5 | 回复中最大链接数量 |
| `MAX_SEARCH_RESULTS` | 5 | 最大搜索结果数量 |

模块级辅助函数：

- `_get_non_replyable_review_reason(answer)` — 判断不可回复答案的原因：空（`empty`）、基础设施错误（`infrastructure_error`，经 `is_infrastructure_error_text`）、处理失败（`processing_failure`，前缀 `处理失败:` 或 `未知错误:`）。

## 主要方法

- `start()` — 监控主循环：加载配置、建立数据库表，反复执行新帖检查与预审检查。
- `_check_new_topics(csv_file)` — 对比已存在 CSV 数据与论坛全部主题，识别新帖；获取详情、提取数据、追加 CSV、写入 `forum_topics` 表，再进入 `_process_new_topics`。
- `_process_new_topics(new_topics)` — 逐帖执行注入检测 → 摘要 → 相关主题搜索 → 文档检索 → 大模型回答 → 相关性/质量检查 → 回复 → 落库 → 评估采样 → Prometheus 指标上报。
- `_generate_related_links(search_results, retrieval_data)` — 实现[[#相关链接生成策略]]。
- `_check_pre_audit_topics()` — 按 `pre_audit_tag` / `pre_audit_category_path` 拉取预审帖子，按标题关键字过滤，写入 `pre_audit_topics` 表后进入 `_process_pre_audit_topic`。
- `_process_pre_audit_topic(topic)` — 执行[[预审处理流程]]：注入检测 → `run_schema_check` 验证 → 预审模型作答。

## 相关链接生成策略

1. 从检索结果的 `chunks` 中提取 `file_path`，正则 `_(\d+)(?:_topic)?\.json$` 解析 topic_id（跳过 `< 10` 的），生成 `{forum_base_url}/t/topic/{topic_id}` 知识图谱链接，最多保留 4 条。
2. 处理搜索结果链接：过滤含 `news` 的路径；`/t/topic` 路径按 topic_id 与 KG 链接去重；`http` 开头不拼接 base_url；其余拼接 `docs_base_url` 并做空格转义。
3. 组合顺序：KG 链接优先 → 搜索链接补充 → 重复补充搜索链接 → 重复补充 KG 链接；最终 `all_links[:MAX_LINKS]` 最多 5 条。
4. 输出格式为「相关链接：\n1. …\n2. …」。

## 关系

- 调用 [[ForumClient]]：`fetch_all_forum_topics`、`fetch_topic_details`、`search_related_topics`、`retrieve_documents_for_topic`、`reply_to_topic`。
- 调用 [[AIProcessor]]：`check_prompt_injection`、`summarize_text`、`call_large_model`、`check_answer_relevance`、`check_answer_quality`、`summarize_answer`。
- 调用 [[DataProcessor]]：建表、CSV 读写、`forum_topics` / `processed_forum_topics` / `pre_audit_topics` / `pre_audit_processed_topics` / `consume_tokens_topic` 写入、评估样本保存。
- 读取 [[token_tracker]] 的 `get_usage(topic_id)` 获取 token 用量。
- 使用 [[evaluation_hooks]] 的 `get_evaluation_context()` 与 `classify_question()`。
- 调用 [[prometheus_metrics]] 的 `update_prometheus_metrics(evaluation_data)`。
- 预审流程调用 [[SchemaValidation]] 的 `run_schema_check`。
- 日志经由 [[logging_config]] 的 `main_logger` 输出。

## 实现的概念

- 实现 [[论坛监控流水线]]
- 实现 [[预审处理流程]]
- 参与 [[评估与指标采集机制]]
