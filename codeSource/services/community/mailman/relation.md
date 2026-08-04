---
tags: [relation, mailman]
service: mailman
source: https://github.com/opensourceways/mailman
source_repo: https://github.com/opensourceways/mailman
updated_at: 2026-08-04
---

## connection

- 三个组件职责来自本地注册信息；未确认组件连接协议。

## related_deployments

| 关联仓 | 环境 | 公开域名 | 部署方式 | 来源 |
| --- | --- | --- | --- | --- |
| mailman-web | prod | 未记录 | kustomize | infra-common service.md；关联仓部署，不代表本服务主仓部署。 |
| dovecot | prod | 未记录 | kustomize | infra-common service.md；关联仓部署，不代表本服务主仓部署。 |

## evolution

以下记录按当前可取得的公开 commit/issue 整理；不足 10 条时不补造记录。
- 2026-07-17 [4228c59](https://github.com/opensourceways/mailman/commit/4228c59) 演进记录：!131 supplement OpenAPI annotations for APIG registry compliance；补充 OpenAPI 注解。
- 2026-07-17 [022c3bc](https://github.com/opensourceways/mailman/commit/022c3bc) 演进记录：补充 OpenAPI annotations；对应 API 文档变更。

## deploy

infra-common service.md 未核验到本服务注册主仓的直接部署记录。

## facts_insufficient

- 最近公开 commit 未达 10 条。
- 未确认 mailman-core 和 mailman-exim 独立部署。
- 当前公开来源未能为 Mailman 服务 核验完整组件清单。
导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
