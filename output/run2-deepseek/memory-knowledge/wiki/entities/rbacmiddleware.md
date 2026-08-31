---
type: entity
title: RBACMiddleware
description: ForumBot 的知识上传白名单鉴权中间件类，基于 user_id 白名单控制知识上传 API 的访问权限。
sources: ["rbac_middleware.txt"]
tags: [rbac, 中间件, 鉴权]
timestamp: 2025-06-01T00:00:00Z
---

# RBACMiddleware

- kind: module

## 定义

RBACMiddleware 是 [[ForumBot 独立 API 服务]] 中的知识上传白名单鉴权中间件类。构造时从 `config['rbac']['knowledge_upload_users']` 读取允许上传知识的 user_id 白名单，通过装饰器控制知识上传 API 的访问权限。

## 关键属性

- `config`：中间件持有的应用配置对象。
- `knowledge_upload_users`：从 `rbac.knowledge_upload_users` 配置项读取的知识上传白名单（user_id 列表）。

## 方法

- `check_upload_permission(user_id)`：检查 user_id 是否在白名单中；user_id 为空时返回 False 并记录 warning 日志。
- `require_upload_permission(f)`：Flask 视图装饰器，依赖上游认证中间件注入的 `g.current_user`：
  - `g` 上不存在 `current_user` 时返回 401 `TOKEN_MISSING`（Authorization header 缺失或格式错误）。
  - 用户不在白名单时返回 403 `ROLE_DENIED`（仅授权用户可上传知识）。
  - 校验通过后调用被装饰视图函数。

## 关系

- 日志依赖：通过 `from .logging_config import main_logger` 使用 [[logging_config]] 的日志记录器记录鉴权结果。
- 配置注入：由 [[api_main]] 读取配置文件并传入构造函数完成初始化。
- 认证衔接：上游认证中间件基于 [[OIDCClient]] 的校验结果在请求上下文注入 `g.current_user`，本中间件只消费该属性。
- 运行形态：属于 [[ForumBot 独立 API 服务]] 请求处理链中的权限控制环节。
- 部署形态：属于 [[独立 API 服务部署模型]] 下 API 服务的组成部分。
- 权限模型：是 [[知识上传白名单鉴权模型]] 的具体实现。
