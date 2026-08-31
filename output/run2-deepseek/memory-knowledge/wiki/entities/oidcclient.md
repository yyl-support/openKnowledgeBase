---
type: entity
title: OIDCClient
description: OneID OIDC 认证客户端模块，封装 config.yaml oidc 段配置读取、授权码流程与 token 刷新校验，校验结果供认证中间件使用。
sources:
  - oidc_client.txt
  - rbac_middleware.txt
tags:
  - 认证
  - oidc
timestamp: 2025-06-01T00:00:00Z
---

# OIDCClient

- kind: module

## 定义

OIDCClient 是 [[OneID]] OIDC 认证客户端模块，封装 config.yaml `oidc` 段配置读取、授权码流程与 token 刷新校验，校验结果供认证中间件使用。

## 认证与鉴权衔接

- OIDCClient 校验结果供认证中间件使用。
- 认证中间件在请求上下文注入 `g.current_user`。
- [[RBACMiddleware]] 消费 `g.current_user` 中的 `user_id` 进行知识上传白名单判定，权限模型见 [[知识上传白名单鉴权模型]]。
