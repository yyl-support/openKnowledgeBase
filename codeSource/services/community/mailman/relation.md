---
tags: [relation, mailman]
service: mailman
source: https://github.com/opensourceways/mailman
updated_at: 2026-08-04
---

## connection
- 三个组件职责来自本地注册信息；未确认组件连接协议。

## evolution
- 2026-07-17 `4228c59` !131 supplement OpenAPI annotations for APIG registry compliance: 补充 OpenAPI 注解。（来源：https://github.com/opensourceways/mailman/commit/4228c59）
- 2026-07-17 `022c3bc` 补充 OpenAPI annotations: 对应 API 文档变更。（来源：https://github.com/opensourceways/mailman/commit/022c3bc）

## deploy
- source_repo=https://github.com/opensourceways/mailman-web; environment=prod; public_endpoint=mailweb.osinfra.cn; method=kustomize; note=service.md 记录部署行，已移除敏感字段。
- source_repo=https://github.com/opensourceways/dovecot; environment=prod; public_endpoint=mailweb.osinfra.cn; method=kustomize; note=service.md 记录部署行，已移除敏感字段。

## facts_insufficient
- 最近公开 commit 未达 10 条。
- 未确认 mailman-core 和 mailman-exim 独立部署。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
