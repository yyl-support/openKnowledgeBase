---
tags: [relation, meeting-server]
service: meeting-server
source: https://github.com/opensourceways/meeting-server
updated_at: 2026-08-04
---

## connection
当前来源不足，未作推断

## evolution
当前来源不足，未作推断

## deploy
- environment=prod; source_repo=https://github.com/opensourceways/meeting-server; public_endpoint=https://meeting.osinfra.cn; method=ArgoCD

## facts_insufficient
- GitHub 仓库页面和 API 均返回 404，无法核验 README、目录树、Dockerfile、最近 10 条 commit 或 issue。
- sub_repos 名称来自本地服务注册的 separate_deploy_subs，无法由 GitHub 目录树进一步核验。
- service.md 未找到 meeting-server 的直接映射行，未将相近记录推断为本服务。
- 无法确认数据库、字幕服务或其他连接关系。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
