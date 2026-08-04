---
tags: [relation, om-datacenter]
service: om-datacenter
source: https://github.com/opensourceways/om-datacenter
source_repo: https://github.com/opensourceways/om-datacenter
updated_at: 2026-08-04
---

## connection

- om-dataarts写入PostgreSQL。
- APIMagic读取PostgreSQL并输出JSON。
- 服务注册文件提及datastat / kafka，但未取得代码仓库实现细节。

## registry_info

- 未记录可公开的 registry YAML 入口。
- 关联仓部署记录：datastat-manage-website；来源：infra-common service.md。该记录不作为主仓直接部署结论。

## evolution

- GitHub API 未能核验演进记录，因此未推断演进方向。

## deploy

- service.md 未核验到主仓直接部署记录。

## facts_insufficient

- 未能从允许来源核验组件清单，因此未列入 components 表。
- service.md 未核验到主仓直接部署记录；已核验部署属于关联仓。
- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- 主仓最近10条commit或issue未能取得。
- infra-common service.md未找到APIMagic或om-dataarts源码仓的直接部署行；仅匹配到datastat-manage-website。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
