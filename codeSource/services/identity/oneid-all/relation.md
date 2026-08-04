---
tags: [relation, oneid-all]
service: oneid-all
source: https://github.com/opensourceways/oneid-server
source_repo: https://github.com/opensourceways/oneid-server
updated_at: 2026-08-04
---

## connection

- oneid-all 通过 Git submodule 聚合三个子仓。
- oneid-website 与 oneid-server 共同组成 OneID 前后端；oneid-workbench-website 为独立工作台前端。

## registry_info

- 服务注册信息：公开入口 [id.openeuler.org](https://id.openeuler.org)；来源：受限的 backlog service YAML（公开读者可能无法访问）。
- 关联配置仓：oneid-all；来源：受限的 backlog service YAML（公开读者可能无法访问）。

## evolution

- 2026-06-12 [419715c](https://github.com/opensourceways/oneid-all/commit/419715c) 关联 umbrella 仓 oneid-all 的记录：分支运行时处理调整。
- 2026-06-12 [a772625](https://github.com/opensourceways/oneid-all/commit/a772625) 关联 umbrella 仓 oneid-all 的记录：fix(preview): runtime-clone 按前缀解析真实分支 issue-N-from-<base>；不再裸 clone issue-N。
- 2026-06-09 [92cb9cf](https://github.com/opensourceways/oneid-all/commit/92cb9cf) 关联 umbrella 仓 oneid-all 的记录：!3 feature: 设置子模块；设置子模块。
- 2026-06-09 [0f1434f](https://github.com/opensourceways/oneid-all/commit/0f1434f) 关联 umbrella 仓 oneid-all 的记录：feature: 设置子模块；设置账号后端子模块。
- 2026-06-05 [cd5f003](https://github.com/opensourceways/oneid-all/commit/cd5f003) 关联 umbrella 仓 oneid-all 的记录：Merge pull request #2；修复 oneid-website 仓库指向并增加个人中心仓库地址。
- 2026-06-04 [db7da3b](https://github.com/opensourceways/oneid-all/commit/db7da3b) 关联 umbrella 仓 oneid-all 的记录：fix: oneid-website 仓库指向问题以及增加个人中心仓库地址；调整子仓库指向。
- 2026-05-29 [9fa194c](https://github.com/opensourceways/oneid-all/commit/9fa194c) 关联 umbrella 仓 oneid-all 的记录：主机处理逻辑调整。
- 2026-05-29 [b7edbed](https://github.com/opensourceways/oneid-all/commit/b7edbed) 关联 umbrella 仓 oneid-all 的记录：主机校验逻辑调整。
- 2026-05-28 [8f72536](https://github.com/opensourceways/oneid-all/commit/8f72536) 关联 umbrella 仓 oneid-all 的记录：全栈协作钩子骨架调整。
- 2026-05-28 [fc545c3](https://github.com/opensourceways/oneid-all/commit/fc545c3) 关联 umbrella 仓 oneid-all 的记录：协作脚本及配置骨架调整。

## deploy

| 环境 | 公开域名 | 镜像/源码仓 | 部署方式 | 来源 |
| --- | --- | --- | --- | --- |
| prod | 未记录 | [oneid-server](https://github.com/opensourceways/oneid-server) | kustomize | infra-common service.md |

## facts_insufficient

- 未能从允许来源核验完整组件清单，因此未作补充。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
