---
tags: [relation, mailman]
service: mailman
source: https://github.com/opensourceways/mailman
source_repo: https://github.com/opensourceways/mailman
updated_at: 2026-08-04
---

## connection

- 三个组件职责来自本地注册信息；未确认组件连接协议。

## registry_info

- 未记录可公开的服务注册入口。

## evolution

- 2026-07-17 [4228c59](https://github.com/opensourceways/mailman/commit/4228c59) !131 supplement OpenAPI annotations for APIG registry compliance：补充 OpenAPI 注解。
- 2026-07-17 [022c3bc](https://github.com/opensourceways/mailman/commit/022c3bc) 补充 OpenAPI annotations：对应 API 文档变更。

## deploy

- 环境为 prod；源码仓为 [mailman-web](https://github.com/opensourceways/mailman-web)；部署方式为 kustomize；来源：infra-common service.md。
- 环境为 prod；源码仓为 [dovecot](https://github.com/opensourceways/dovecot)；部署方式为 kustomize；来源：infra-common service.md。

## facts_insufficient

- 最近公开 commit 未达 10 条。
- 未确认 mailman-core 和 mailman-exim 独立部署。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
