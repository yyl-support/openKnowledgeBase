---
type: entity
title: OpenUBMC 论坛
description: discuss.openubmc.cn 技术论坛，ForumBot 处理帖子的内容来源，也是图片相对路径的默认基准 URL。
kind: external_system
sources: ["image_processor.txt"]
tags: [论坛, 外部系统]
---

# OpenUBMC 论坛

## 定义

运行于 discuss.openubmc.cn 的技术论坛。[[ForumBot]] 所处理的帖子文本来自该论坛，其中以 `[img: (...)]` 标签嵌入图片引用。

## 关键属性

- 域名：`discuss.openubmc.cn`
- 角色：论坛帖子文本是图片标签的载体；同时作为 [[ImageProcessor]] 解析图片相对路径的默认基准 URL（`config['image_processing']['base_url']` 缺省值）。

## 关系

- 为 [[ImageProcessor]] 提供图片 URL 解析基准。
- 承载 [[图片标签提取与增强机制]] 所处理的原始论坛文本。
- 来源：[[image_processor.txt]]
