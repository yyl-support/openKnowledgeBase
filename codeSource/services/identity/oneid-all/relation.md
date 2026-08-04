---
tags: [relation, oneid-all]
service: oneid-all
source: https://github.com/opensourceways/oneid-all
updated_at: 2026-08-04
---

## connection
- oneid-all 通过 Git submodule 聚合三个子仓。
- oneid-website 与 oneid-server 共同组成 OneID 前后端；oneid-workbench-website 为独立工作台前端。

## evolution
- 2026-06-12 `419715c` Merge pull request #4: fix/preview-clone-resolve-from-branch: 预览 runtime-clone 按前缀解析真实分支。
- 2026-06-12 `a772625` fix(preview): runtime-clone 按前缀解析真实分支 issue-N-from-<base>: 不再裸 clone issue-N。
- 2026-06-09 `92cb9cf` !3 feature: 设置子模块: 设置子模块。
- 2026-06-09 `0f1434f` feature: 设置子模块: 设置账号后端子模块。
- 2026-06-05 `cd5f003` Merge pull request #2: 修复 oneid-website 仓库指向并增加个人中心仓库地址。
- 2026-06-04 `db7da3b` fix: oneid-website 仓库指向问题以及增加个人中心仓库地址: 调整子仓库指向。
- 2026-05-29 `9fa194c` Merge pull request #2: fix/preview-endgroup-guard: 修复预览 host 异常值导致假 URL。
- 2026-05-29 `b7edbed` fix(preview): 防御 ingress host 取到 ::endgroup::: 非法 host 时不生成预览 URL。
- 2026-05-28 `8f72536` Merge pull request #1: feat/add-preview-hook: 加入全栈预览 hook 骨架。
- 2026-05-28 `fc545c3` feat(preview): 加 .ai-flow/deploy 全栈预览 hook 骨架: 生成预览脚本及配置骨架。

## deploy
- environment=prod; source_repo=https://github.com/opensourceways/oneid-server; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_method=kustomize; note=service.md 匹配的是 oneid-server 源码仓；生产入口 id.openeuler.org 仅来自本地 service YAML，因此未写入本部署记录。

## facts_insufficient
当前来源不足，未作推断

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
