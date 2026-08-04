---
tags: [identity, oneid-all]
service: oneid-all
source: https://github.com/opensourceways/oneid-all
updated_at: 2026-08-04
---

## summary
openEuler OneID 统一身份认证 umbrella 仓，聚合后端 API、前端 UI 和工作台前端；README 说明其用于统一账号/SSO/CLA 登录等身份中心能力。

## infrastructure
- 本地 service 注册：生产入口为 https://id.openeuler.org。
- 本地 YAML 记录预览集群、命名空间和预览域名，但按要求不写入公开部署字段。
- 源码仓 README/CLAUDE.md 中包含预览工作流与子模块驱动信息。

## components

| name | role |
| --- | --- |
| oneid-server | 后端 API |
| oneid-website | 前端 UI |
| oneid-workbench-website | 工作台前端 |

## 源码

- source_repo: https://github.com/opensourceways/oneid-all
- sub_repos:
  - name=oneid-server; repo=https://github.com/opensourceways/om-webserver; branch=master; role=后端 API
  - name=oneid-website; repo=https://github.com/opensourceways/oneid-website; branch=release; role=前端 UI
  - name=oneid-workbench-website; repo=https://github.com/opensourceways/oneid-workbench-website; branch=release; role=工作台前端

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
