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

- 未记录可公开的服务注册入口。

## evolution

- 当前来源不足，未推断演进方向。

## deploy

- 环境为 prod；源码仓为 [xihe-server](https://github.com/opensourceways/xihe-server)；部署方式为 kustomize；来源：infra-common service.md。
- 环境为 prod；源码仓为 [deployment-xihe-jupyter-server](https://github.com/opensourceways/deployment-xihe-jupyter-server)；部署方式为 kustomize；来源：infra-common service.md。

## facts_insufficient

- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- 主仓最近10条commit或issue未能取得。
- service.md仅匹配xihe-server和deployment-xihe-jupyter-server，未匹配其他umbrella子仓的直接部署源码行。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
