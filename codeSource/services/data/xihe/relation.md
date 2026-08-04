---
tags: [relation, xihe]
service: xihe
source: https://github.com/opensourceways/xihe-all
source_repo: https://github.com/opensourceways/xihe-all
updated_at: 2026-08-04
---

## connection

- 服务间存在注册配置记录的协议连接，公开版本不展开具体组件名称。
- 持久层使用 PostgreSQL 和 Redis。

## related_deployments

| 关联仓 | 环境 | 公开域名 | 部署方式 | 来源 |
| --- | --- | --- | --- | --- |
| xihe-server | prod | 未记录 | kustomize | infra-common service.md；关联仓部署，不代表本服务主仓部署。 |
| deployment-xihe-jupyter-server | prod | 未记录 | kustomize | infra-common service.md；关联仓部署，不代表本服务主仓部署。 |

## evolution

以下记录按当前可取得的公开 commit/issue 整理；不足 10 条时不补造记录。
- 当前未取得 xihe 的足量公开提交或 issue 记录，未补造演进结论。

## deploy

infra-common service.md 未核验到本服务注册主仓的直接部署记录。

## facts_insufficient

- 允许来源未能核验完整组件清单和目录树，因此未作组件或源码结构补充。

- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- service.md 未核验到 xihe-all 主仓直接部署记录。
- 主仓最近 10 条 commit 或 issue 未能取得。
- infra-common service.md 仅匹配 xihe-server 和 deployment-xihe-jupyter-server，未匹配其他聚合子仓的直接部署源码行。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
