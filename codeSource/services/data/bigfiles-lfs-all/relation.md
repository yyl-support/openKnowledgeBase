---
tags: [relation, bigfiles-lfs-all]
service: bigfiles-lfs-all
source: https://github.com/opensourceways/bigfiles-lfs-all
source_repo: https://github.com/opensourceways/bigfiles-lfs-all
updated_at: 2026-08-04
---

## connection

- 主仓通过 .gitmodules 管理两个 submodule；未确认运行时连接协议。

## related_deployments

| 关联仓 | 环境 | 公开域名 | 部署方式 | 来源 |
| --- | --- | --- | --- | --- |
| lfs-website | prod | 未记录 | kustomize | infra-common service.md；关联仓部署，不代表本服务主仓部署。 |
| openeuler-bigfiles-deployment | prod | 未记录 | kustomize | infra-common service.md；关联仓部署，不代表本服务主仓部署。 |

## evolution

以下记录按当前可取得的公开 commit/issue 整理；不足 10 条时不补造记录。
- 2026-05-31 [eb19dda](https://github.com/opensourceways/bigfiles-lfs-all/commit/eb19dda) 演进记录：chore: 接入 2 个 submodule + 初始化 CLAUDE.md；主仓接入两个 submodule。
- 2026-05-31 [36d09fa](https://github.com/opensourceways/bigfiles-lfs-all/commit/36d09fa) 演进记录：Initial commit；主仓初始化。

## deploy

infra-common service.md 未核验到本服务注册主仓的直接部署记录。

## facts_insufficient

- 未能从允许来源核验完整组件清单，因此未作补充。

- service.md 未核验到主仓直接部署记录。
- 主仓仅有 2 条 commit，未形成 10 条近期演进记录。
- infra-common service.md 未以 umbrella 仓名直接记录 BigFiles 部署行。
- 未提供后端端口、数据库或 CDN 连接细节。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
