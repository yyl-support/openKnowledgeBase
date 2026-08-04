---
tags: [identity, oneid-all]
service: oneid-all
source: https://github.com/opensourceways/oneid-server
source_repo: https://github.com/opensourceways/oneid-server
updated_at: 2026-08-04
---

## summary
openEuler OneID 统一身份认证 umbrella 仓，聚合后端 API、前端 UI 和工作台前端；README 说明其用于统一账号/SSO/CLA 登录等身份中心能力。

## infrastructure
- 本地 service 注册：生产入口为 https://id.openeuler.org。
- 本地 YAML 含不公开部署细节，按要求不写入公开部署字段。
- 源码仓 README/CLAUDE.md 中包含未公开部署工作流与子模块驱动信息。

## components

| name | role |
| --- | --- |
| oneid-server | 后端 API |
| oneid-website | 前端 UI |
| oneid-workbench-website | 工作台前端 |

## 源码

- 服务注册 tools_repo：[oneid-server](https://github.com/opensourceways/oneid-server)
- umbrella/聚合仓：oneid-all（配置聚合角色，来源：受限来源：backlog service yaml（公开读者可能无法访问））。
- 已核验子仓：[oneid-website](https://github.com/opensourceways/oneid-website)
- 已核验子仓：[oneid-workbench-website](https://github.com/opensourceways/oneid-workbench-website)

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
