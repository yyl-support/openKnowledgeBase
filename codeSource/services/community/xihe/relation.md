---
tags: [relation, xihe]
service: xihe
source: https://github.com/opensourceways/xihe-all
updated_at: 2026-08-04
---

## connection
- 服务间使用xihe-grpc-protocol定义的gRPC。
- 持久层使用PostgreSQL和Redis。

## evolution
当前来源不足，未作推断

## deploy
- environment=prod; source_repo=https://github.com/opensourceways/xihe-server; archive_repo=https://github.com/opensourceways/infra-mindspore; archive_path=applications/xihe-new; archive_method=kustomize; note=service.md匹配到xihe-server源码仓；仅保留部署归档仓、路径和归档方式。
- environment=prod; source_repo=https://github.com/opensourceways/deployment-xihe-jupyter-server; archive_repo=https://github.com/opensourceways/infra-mindspore; archive_path=applications/xihe-new; archive_method=kustomize; note=service.md匹配到Notebook部署源码仓；仅保留部署归档仓、路径和归档方式。

## facts_insufficient
- GitHub主仓不可访问，未取得README、目录树、Dockerfile、.gitmodules原文及子仓commit。
- 主仓最近10条commit或issue未能取得。
- service.md仅匹配xihe-server和deployment-xihe-jupyter-server，未匹配其他umbrella子仓的直接部署源码行。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
