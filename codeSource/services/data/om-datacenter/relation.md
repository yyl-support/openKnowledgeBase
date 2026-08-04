---
tags: [relation, om-datacenter]
service: om-datacenter
source: https://github.com/opensourceways/om-datacenter
source_repo: https://github.com/opensourceways/om-datacenter
updated_at: 2026-08-04
---

## connection

- om-dataarts 写入 PostgreSQL。
- APIMagic 读取 PostgreSQL 并输出 JSON。
- 服务注册文件提及 datastat / Kafka，但未取得代码仓库实现细节。

## related_deployments

| 关联仓 | 环境 | 公开域名 | 部署方式 | 来源 |
| --- | --- | --- | --- | --- |
| datastat-manage-website | prod/test | 未记录 | kustomize | infra-common service.md；关联仓部署，不代表本服务主仓部署。 |

## evolution

以下记录按当前可取得的公开 commit/issue 整理；不足 10 条时不补造记录。
- GitHub API 未能核验演进记录，因此未推断演进方向。

## deploy

infra-common service.md 未核验到本服务注册主仓的直接部署记录。

## facts_insufficient

- 未能从允许来源核验完整组件清单，因此未作补充。

- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- 主仓最近 10 条 commit 或 issue 未能取得。
- infra-common service.md 未找到APIMagic或om-dataarts源码仓的直接部署行；仅匹配到datastat-manage-website。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
