---
tags: [relation, xihe]
service: xihe
source: https://github.com/opensourceways/xihe-all
source_repo: https://github.com/opensourceways/xihe-all
updated_at: 2026-08-04
---

## connection

- 服务间存在注册配置记录的协议连接，公开版本不展开具体组件名称。
- 持久层使用PostgreSQL和Redis。

## registry_info

- 未记录可公开的 registry YAML 入口。
- 关联仓部署记录：xihe-server 和 deployment-xihe-jupyter-server；来源：infra-common service.md。该记录不作为 xihe-all 主仓直接部署结论。

## evolution

- GitHub API 未能核验演进记录，因此未推断演进方向。

## deploy

- service.md 未核验到 xihe-all 主仓直接部署记录。

## facts_insufficient

- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- service.md 未核验到 xihe-all 主仓直接部署记录；已核验部署属于关联仓。
- 主仓最近10条commit或issue未能取得。
- infra-common service.md仅匹配xihe-server和deployment-xihe-jupyter-server，未匹配其他umbrella子仓的直接部署源码行。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
