---
tags: [identity, cla-all]
service: cla-all
source: https://github.com/opensourceways/cla-all
updated_at: 2026-08-04
---

## summary
CLA umbrella 仓，聚合 CLA 签署后端、统计服务和 WebUI。

## infrastructure
- 本地 service 注册的生产入口为 https://clasign.osinfra.cn。
- 仓库目录包含 .gitmodules、CLAUDE.md、三个 CLA 子仓目录。

## components

| name | role |
| --- | --- |
| app-cla-server | 后端服务 |
| app-cla-stat | 统计服务 |
| app-cla-webui | Web UI |

## 源码

- source_repo: https://github.com/opensourceways/cla-all
- sub_repos:
  - name=app-cla-server; repo=https://github.com/opensourceways/app-cla-server; role=CLA 后端
  - name=app-cla-stat; repo=https://github.com/opensourceways/app-cla-stat; role=CLA 统计
  - name=app-cla-webui; repo=https://github.com/opensourceways/app-cla-webui; role=CLA WebUI

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
