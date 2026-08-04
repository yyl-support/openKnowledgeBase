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

- 未记录可公开的 registry YAML 入口。
- 关联仓部署记录：mailman-web 和 dovecot；来源：infra-common service.md。该记录不作为主仓直接部署结论。

## evolution

- 2026-07-17 [4228c59](https://github.com/opensourceways/mailman/commit/4228c59) 演进记录：!131 supplement OpenAPI annotations for APIG registry compliance；补充 OpenAPI 注解。。
- 2026-07-17 [022c3bc](https://github.com/opensourceways/mailman/commit/022c3bc) 演进记录：补充 OpenAPI annotations；对应 API 文档变更。。

## deploy

- service.md 未核验到主仓直接部署记录。

## facts_insufficient

- 未能从允许来源核验组件清单，因此未列入 components 表。
- service.md 未核验到主仓直接部署记录；已核验部署属于关联仓。
- 最近公开 commit 未达 10 条。
- 未确认 mailman-core 和 mailman-exim 独立部署。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
