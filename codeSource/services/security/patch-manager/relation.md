---
tags: [relation, patch-manager]
service: patch-manager
source: https://github.com/opensourceways/patch-manager
source_repo: https://github.com/opensourceways/patch-manager
updated_at: 2026-08-04
---

## connection

- 未能从允许来源核验连接关系。

## registry_info

- 未记录可公开的 registry YAML 入口。

## evolution

- GitHub API 未能核验演进记录，因此未推断演进方向。

## deploy

- service.md 未核验到主仓直接部署记录。

## facts_insufficient

- 未能从允许来源核验组件清单，因此未列入 components 表。
- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- infra-common service.md 未找到 patch-manager 的直接服务映射行。
- 无法确认系统组件清单和演进记录。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
