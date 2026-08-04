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

- 未记录可公开的服务注册入口。

## evolution

- 当前来源不足，未推断演进方向。

## deploy

- 环境为 prod；源码仓为 [datastat-manage-website](https://github.com/opensourceways/datastat-manage-website)；部署方式为 kustomize；来源：infra-common service.md。
- 环境为 test；源码仓为 [datastat-manage-website](https://github.com/opensourceways/datastat-manage-website)；部署方式为 kustomize；来源：infra-common service.md。

## facts_insufficient

- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- 主仓最近10条commit或issue未能取得。
- service.md未找到APIMagic或om-dataarts源码仓的直接部署行；仅匹配到datastat-manage-website。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
