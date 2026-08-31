---
type: entity
title: OneID
description: 外部 OIDC 身份提供方，其 authorize、token、userinfo 端点均位于 omapi.osinfra.cn/oneid 路径下。
kind: external_system
sources: ["oidc_client.txt"]
tags: [OIDC, 身份提供方, 外部系统]
---

# OneID

- **kind**: external_system

## 定义

`OneID` 是 [[OIDCClient]] 对接的外部 OIDC 身份提供方，三个标准端点均在 `omapi.osinfra.cn/oneid` 域下：

- 授权端点（authorize）：`https://omapi.osinfra.cn/oneid/oidc/authorize`
- 令牌端点（token）：`https://omapi.osinfra.cn/oneid/oidc/token`
- 用户信息端点（userinfo）：`https://omapi.osinfra.cn/oneid/oidc/user`

## 关键属性

- 协议：OIDC / OAuth2，授权码模式 + Bearer Token（RFC 6750）错误语义。
- token 端点响应含 `access_token`、`refresh_token`、`id_token`、`expires_in`。
- `id_token` 为三段 JWT，`sub` 声明用作 `user_id`；UserInfo 响应亦返回 `sub`。

## 关系

- 被 [[OIDCClient]] 调用，承载完整 [[OIDC 授权码认证流程]]。
- UserInfo 端点在失败时返回含 `"expired"` 的 Bearer 错误描述，是 [[访问令牌校验与失效分类]] 的判定依据。
