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

- 服务注册信息：公开入口 [id.openeuler.org](https://id.openeuler.org)；来源：受控的 backlog service YAML。
- 关联的聚合配置仓：oneid-all；来源：受控的 backlog service YAML。

## evolution

以下记录按当前可取得的公开 commit/issue 整理；不足 10 条时不补造记录。
- 2026-06-12 [419715c](https://github.com/opensourceways/oneid-all/commit/419715c) 关联 umbrella 仓 oneid-all 的记录：分支运行时处理调整。
- 2026-06-12 [a772625](https://github.com/opensourceways/oneid-all/commit/a772625) 关联 umbrella 仓 oneid-all 的记录：运行时分支处理调整；不再使用未解析的 issue 分支名称。
- 2026-06-09 [92cb9cf](https://github.com/opensourceways/oneid-all/commit/92cb9cf) 关联 umbrella 仓 oneid-all 的记录：!3 feature: 设置子模块；设置子模块。
- 2026-06-09 [0f1434f](https://github.com/opensourceways/oneid-all/commit/0f1434f) 关联 umbrella 仓 oneid-all 的记录：feature: 设置子模块；设置账号后端子模块。
- 2026-06-05 [cd5f003](https://github.com/opensourceways/oneid-all/commit/cd5f003) 关联 umbrella 仓 oneid-all 的记录：Merge pull request #2；修复 oneid-website 仓库指向并增加个人中心仓库地址。
- 2026-06-04 [db7da3b](https://github.com/opensourceways/oneid-all/commit/db7da3b) 关联 umbrella 仓 oneid-all 的记录：fix: oneid-website 仓库指向问题以及增加个人中心仓库地址；调整子仓库指向。
- 2026-05-29 [9fa194c](https://github.com/opensourceways/oneid-all/commit/9fa194c) 关联 umbrella 仓 oneid-all 的记录：主机处理逻辑调整。
- 2026-05-29 [b7edbed](https://github.com/opensourceways/oneid-all/commit/b7edbed) 关联 umbrella 仓 oneid-all 的记录：主机校验逻辑调整。
- 2026-05-28 [8f72536](https://github.com/opensourceways/oneid-all/commit/8f72536) 关联 umbrella 仓 oneid-all 的记录：全栈协作钩子骨架调整。
- 2026-05-28 [fc545c3](https://github.com/opensourceways/oneid-all/commit/fc545c3) 关联 umbrella 仓 oneid-all 的记录：协作脚本及配置骨架调整。

## deploy

infra-common service.md 未核验到本服务注册主仓的直接部署记录。

## facts_insufficient
- OneID 的组件明细尚未从现有来源确认。
导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
