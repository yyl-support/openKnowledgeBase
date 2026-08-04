---
tags: [security, certification-all]
service: certification-all
source: https://github.com/opensourceways/certification-all
updated_at: 2026-08-04
---

## summary
认证/证书 umbrella 仓，聚合 openEuler 兼容性认证服务端和认证网站，服务说明为证书签发与验证。

## infrastructure
- 本地 service 注册的生产入口为 https://certification.openeuler.openatom.cn。
- 仓库目录包含 .gitmodules、CLAUDE.md、认证服务端和认证网站子仓目录。

## components

| name | role |
| --- | --- |
| certification-server | 认证服务端 |
| certification-website | 认证网站 |

## 源码

- source_repo: https://github.com/opensourceways/certification-all
- sub_repos:
  - name=certification-server; repo=https://github.com/opensourceways/certification-server; role=认证服务端
  - name=certification-website; repo=https://github.com/opensourceways/certification-website; role=认证网站

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
