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

## registry_info

- 未记录可公开的 registry YAML 入口。

## evolution

- GitHub API 未能核验演进记录，因此未推断演进方向。

## deploy

- service.md 未核验到 xihe-all 主仓直接部署记录。

## facts_insufficient

- 未能从允许来源核验完整组件清单，因此未作补充。

- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- 关联仓匹配到 xihe-server 和 deployment-xihe-jupyter-server；这是关联仓信息，不作为本服务主仓部署结论。
- service.md 未核验到 xihe-all 主仓直接部署记录。
- 主仓最近 10 条 commit 或 issue 未能取得。
- infra-common service.md 仅匹配 xihe-server 和 deployment-xihe-jupyter-server，未匹配其他 umbrella 子仓的直接部署源码行。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
