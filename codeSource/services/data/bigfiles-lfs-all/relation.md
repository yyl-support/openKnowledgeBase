---
tags: [relation, bigfiles-lfs-all]
service: bigfiles-lfs-all
source: https://github.com/opensourceways/bigfiles-lfs-all
updated_at: 2026-08-04
---

## connection
- 主仓通过 .gitmodules 管理两个 submodule；未确认运行时连接协议。

## evolution
- 2026-05-31 `eb19dda` chore: 接入 2 个 submodule + 初始化 CLAUDE.md: 主仓接入两个 submodule。（来源：https://github.com/opensourceways/bigfiles-lfs-all/commit/eb19dda）
- 2026-05-31 `36d09fa` Initial commit: 主仓初始化。

## deploy
- source_repo=https://github.com/opensourceways/lfs-website; environment=prod; public_endpoint=artlfs-website.openeuler.openatom.cn; method=kustomize; note=来源：service.md 部署行。
- source_repo=https://github.com/opensourceways/openeuler-bigfiles-deployment; environment=prod; public_endpoint=artlfs.openeuler.openatom.cn; method=kustomize; note=来源：service.md 部署行。

## facts_insufficient
- 主仓仅有 2 条 commit，未形成 10 条近期演进记录。
- service.md 未以 umbrella 仓名直接记录 BigFiles 部署行。
- 未提供后端端口、数据库或 CDN 连接细节。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
