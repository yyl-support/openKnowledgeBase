---
type: entity
title: ForumBot
description: ForumBot 整体系统平台，对应 src.ForumBot 包，独立 API 服务是其对外提供能力的一种运行形态。
sources: ["api_main.txt"]
kind: platform
tags: ["ForumBot"]
---

# ForumBot

## 定义

`ForumBot` 是整体系统平台，对应 `src.ForumBot` 包。[[ForumBot 独立 API 服务]] 是其对外提供能力的一种运行形态。

## 关键属性

- 包结构：`src.ForumBot`，包含 [[logging_config]] 等模块
- 运行形态：可提供独立 API 服务（默认 `127.0.0.1:5085`）
- 入口组件：[[api_main]] 命令行启动流程

## 关系

- 包含 [[logging_config]] 日志配置模块
- 通过 [[api_main]] 与 [[standalone_api]] 提供 [[ForumBot 独立 API 服务]]
- 运行形态由 [[独立 API 服务部署模型]] 描述
