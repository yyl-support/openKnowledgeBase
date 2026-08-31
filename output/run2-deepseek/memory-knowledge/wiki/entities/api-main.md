---
type: entity
title: api_main
description: ForumBot 独立 API 服务的命令行启动入口脚本，负责路径注入、参数解析、日志初始化与服务委托启动。
sources:
  - api_main.txt
  - rbac_middleware.txt
tags:
  - 入口
  - 命令行
timestamp: 2025-06-01T00:00:00Z
---

# api_main

- kind: module

## 定义

api_main 是 [[ForumBot 独立 API 服务]] 的命令行启动入口脚本，负责路径注入、参数解析、日志初始化与服务委托启动。

## 配置流转

- 读取配置文件后，将 config 传入 [[RBACMiddleware]] 构造函数，中间件据此初始化知识上传白名单。
- 白名单配置项为 `rbac.knowledge_upload_users`，权限判定遵循 [[知识上传白名单鉴权模型]]。
- 相关部署形态见 [[独立 API 服务部署模型]]。
