---
type: entity
title: ForumBot 独立 API 服务
description: ForumBot 对外提供的独立部署型 API 服务，默认监听 127.0.0.1:5085。
sources:
  - api_main.txt
  - rbac_middleware.txt
tags:
  - ForumBot
  - API
  - 服务
  - api
timestamp: 2025-06-01T00:00:00Z
kind: service
---

# ForumBot 独立 API 服务

## 定义

`ForumBot 独立 API 服务` 是 [[ForumBot]] 系统对外提供 API 能力的独立运行形态，由 [[standalone_api]] 模块启动，默认监听 `127.0.0.1:5085`。它是 ForumBot 对外提供的独立部署型 API 服务。

## 关键属性

- kind: service
- 默认主机：`127.0.0.1`
- 默认端口：`5085`
- 配置文件：可通过 `--config` 指定，未指定时自动查找
- 启动链路：[[api_main]] → [[standalone_api]]，可选参数 `--host`、`--port`、`--config`

## 关系

- 由 [[standalone_api]] 模块启动
- 通过 [[api_main]] 命令行入口拉起
- 属于 [[ForumBot]] 平台的一种运行形态
- 对应 [[独立 API 服务部署模型]] 部署模型

## 请求处理链中的权限控制

- [[RBACMiddleware]] 位于请求处理链中的权限控制环节，通过 `require_upload_permission` 装饰器保护知识上传 API。
- 鉴权依赖上游认证中间件注入的 `g.current_user`，认证来源为 [[OIDCClient]] 的校验结果。
- 权限判定遵循 [[知识上传白名单鉴权模型]]。
