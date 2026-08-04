---
tags: [relation, meeting-server]
service: meeting-server
source: https://github.com/opensourceways/meeting-server
source_repo: https://github.com/opensourceways/meeting-server
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

- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- sub_repos 名称来自本地服务注册的 separate_deploy_subs，无法由 GitHub 目录树进一步核验。
- infra-common service.md 未找到 meeting-server 的直接映射行，未将相近记录推断为本服务。
- 无法确认数据库、字幕服务或其他连接关系。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
