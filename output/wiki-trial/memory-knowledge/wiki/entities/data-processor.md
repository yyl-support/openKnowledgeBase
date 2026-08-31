---
type: entity
title: data_processor
description: 提供论坛主题拉取相关函数与默认配置键的依赖模块
sources: ["forum_client.txt"]
tags: [论坛, 数据处理]
kind: module
---

# 定义

`data_processor` 是被 [[ForumClient]] 依赖的外部模块，提供论坛主题数据的拉取能力。目前仅通过其在 `forum_client.txt` 中的导入接口可见，具体实现细节待摄入 `data_processor.py` 源码后补充。

# 关键属性

- 提供函数：
  - `fetch_all_forum_topics(config, tag_key, cutoff_date_key, category_path_key)` — 获取所有论坛主题
  - `fetch_topic_details(topic_id, config)` — 获取单个主题详情
- 提供默认配置键常量：
  - `DEFAULT_CATEGORY_PATH_KEY` — 默认分类路径键
  - `DEFAULT_REQUIRED_TAG_KEY` — 默认必需标签键
  - `DEFAULT_TOPIC_CUTOFF_DATE_KEY` — 默认主题截止日期键

# 关系

- 被 [[ForumClient]] 依赖，用于拉取主题列表与主题详情

# 待补充

后续如摄入 `data_processor.py` 源码，应回来更新本页，补充函数内部实现、数据结构与过滤逻辑，而非重复创建新页。

# Citations

- forum_client.txt（导入语句及方法委托调用）
