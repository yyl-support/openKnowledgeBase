---
tags: [relation, om-datacenter]
service: om-datacenter
source: https://github.com/opensourceways/om-datacenter
updated_at: 2026-08-04
---

## connection
- om-dataarts写入PostgreSQL。
- APIMagic读取PostgreSQL并输出JSON。
- 服务注册文件提及datastat / kafka，但未取得代码仓库实现细节。

## evolution
当前来源不足，未作推断

## deploy
- environment=prod; source_repo=https://github.com/opensourceways/datastat-manage-website; archive_repo=https://github.com/opensourceways/infra-common; archive_path=common-applications/infra-hk-x86-common-environment/datastat-manage; archive_method=kustomize; note=service.md匹配到website源码仓；仅保留部署归档仓、路径和归档方式。
- environment=test; source_repo=https://github.com/opensourceways/datastat-manage-website; archive_repo=https://github.com/opensourceways/infra-common; archive_path=common-applications/test-environment/datastat-manage; archive_method=kustomize; note=service.md匹配到website源码仓；仅保留部署归档仓、路径和归档方式。

## facts_insufficient
- GitHub主仓不可访问，未取得README、目录树、Dockerfile、.gitmodules原文及子仓commit。
- 主仓最近10条commit或issue未能取得。
- service.md未找到APIMagic或om-dataarts源码仓的直接部署行；仅匹配到datastat-manage-website。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
