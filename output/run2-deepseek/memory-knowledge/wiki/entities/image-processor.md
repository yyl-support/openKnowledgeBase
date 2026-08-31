---
type: entity
title: image_processor
description: ForumBot 的图像处理模块，通过 enhance_text_with_image_descriptions 为文本中的图像链接补充图像描述，供帖子数据提取流程使用。
sources: ["data_processor.txt"]
tags: [模块, 图像处理]
---

# image_processor

- kind: module

## 定义

`image_processor` 是 [[forumbot]] 平台内的图像处理模块，对外提供 `enhance_text_with_image_descriptions(text, field_name, topic_id)` 方法，用于为文本内容中的图像链接生成并注入图像描述。

## 关键属性

- 提供方法：`enhance_text_with_image_descriptions(text, field_name, topic_id)`
- 调用方：[[data_processor]]

## 调用场景

在 [[帖子数据提取与图像增强]] 流程中，被用于增强两类文本：

1. 用户问题（user_question）
2. 最佳答案（best_answer）

## 关系

- 被 [[data_processor]] 通过 `self.image_processor.enhance_text_with_image_descriptions(...)` 调用。
- 相关概念：[[帖子数据提取与图像增强]]。
