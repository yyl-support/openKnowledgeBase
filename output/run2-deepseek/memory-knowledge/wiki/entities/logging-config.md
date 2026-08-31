---
type: entity
title: logging_config
description: ForumBot 的日志配置模块，导出 main_logger 供入口脚本与系统其他部分使用。
sources:
  - api_main.txt
  - api-main.txt
  - image_processor.txt
  - rbac_middleware.txt
tags:
  - ForumBot
  - 日志
  - 模块
  - 配置
timestamp: 2025-06-01T00:00:00Z
kind: module
---

# logging_config

## 定义

`logging_config` 是 [[ForumBot]] 的日志配置模块（新来源标注路径为 `src/logging_config.py`），导出 `main_logger`，供 [[api_main]] 等入口组件记录启动、停止与失败日志，也供系统其他部分使用。

## 关键属性

- 导出符号：`main_logger`（统一的日志器，供系统各模块记录运行日志）
- 使用方式（旧来源）：`from src.ForumBot.logging_config import main_logger as logger`
- 模块路径（新来源）：`src/logging_config.py`

## 关系

- 被 [[api_main]] 使用，记录“正在启动”、“已停止”、“启动失败”等日志；也被 [[api_main]] 等入口脚本引用，用于日志初始化。
- 被 [[ImageProcessor]] 引用（`from .logging_config import main_logger`），记录图片处理错误、模型调用失败与模型切换信息。
- 被 [[RBACMiddleware]] 引用（`from .logging_config import main_logger`），记录知识上传白名单鉴权结果（如用户是否在白名单中）。
- 属于 [[ForumBot]] 系统平台 / 平台内部的日志基础设施。

## 来源

- 旧来源：[[api_main.txt]]
- 新来源：[[api_main.txt]]、[[image_processor.txt]]、[[rbac_middleware.txt]]
- 来源文件名存在不一致：旧页与部分正文使用 `api_main.txt`，新页 frontmatter 使用 `api-main.txt`；本页保留两种写法并标注冲突，二者可能指向同一文件。

## 说明

旧说明：本页内容目前仅来源于 [[api_main.txt]]，信息较薄；若后续来源无更多信息，可降级为 [[ForumBot]] 页面的子条目。现来源已增加 [[image_processor.txt]]，包含 [[ImageProcessor]] 的使用信息，页面内容已不再单薄。另新增来源 [[rbac_middleware.txt]]，补充 [[RBACMiddleware]] 对 `main_logger` 的使用信息。
