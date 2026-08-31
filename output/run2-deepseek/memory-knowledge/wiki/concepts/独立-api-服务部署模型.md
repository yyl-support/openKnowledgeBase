---
type: concept
title: 独立 API 服务部署模型
description: 将 ForumBot 的 API 能力作为独立进程部署的运行模型，通过命令行参数配置主机、端口与配置文件。
sources:
  - api_main.txt
  - rbac_middleware.txt
tags:
  - 部署模型
  - ForumBot
timestamp: 2025-06-01T00:00:00Z
---

# 独立 API 服务部署模型

## 定义

`独立 API 服务部署模型` 描述将 [[ForumBot]] 的 API 能力作为独立进程部署的形态：通过 [[api_main]] 的命令行参数配置主机、端口与配置文件，未指定配置时自动查找，与主应用解耦。

## 意义

- 提供独立于主应用的服务进程，便于单独部署、监控与运维
- 通过 CLI 参数（`--host`、`--port`、`--config`）灵活指定监听地址与配置来源
- 默认配置开箱即用：`127.0.0.1:5085`

## 权限控制组件

- 该部署形态下，[[RBACMiddleware]] 由命令行入口注入的 config 初始化，构成 API 服务的组成部分。
- 中间件的知识上传白名单来自 `config['rbac']['knowledge_upload_users']`，权限判定模型为 [[知识上传白名单鉴权模型]]。

## 启动流程（机制）

该部署模型的启动遵循 [[命令行入口启动流程]]：

1. 路径注入：脚本目录与 `src` 目录加入 `sys.path`
2. 参数解析：读取 `--host` / `--port` / `--config`
3. 日志初始化：使用 [[logging_config]] 的 `main_logger`
4. 委托启动：[[api_main]] 调用 [[standalone_api]] 的 `run_standalone_api()`，拉起 [[ForumBot 独立 API 服务]]

## 相关实体

- [[api_main]] — 命令行入口，负责解析参数、读取配置并注入 [[RBACMiddleware]]
- [[standalone_api]] — 服务启动器
- [[ForumBot 独立 API 服务]] — 部署模型对应的服务实例
- [[RBACMiddleware]] — 权限控制中间件
- [[ForumBot]] — 被部署的系统平台

## 共同主题

- 部署模型（deployment model）
- 数据流 / 模块边界（启动调用链）
- 权限控制 / 中间件
