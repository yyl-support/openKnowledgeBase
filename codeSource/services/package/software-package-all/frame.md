---
tags: [package, software-package-all]
service: software-package-all
source: https://github.com/opensourceways/software-package-all
updated_at: 2026-08-04
---

## summary
软件包平台，注册描述包含网关、server、website、自动修复和自动升级。

## infrastructure
- 生产入口为 https://software-pkg.openeuler.org（服务注册 YAML）。
- 发布方式登记为 ArgoCD；注册配置还记录了 EasySoftware 自动修复构建脚本字段为空，以及多个子仓未配置测试部署目标。

## components

| name | role |
| --- | --- |
| 网关 | 当前来源不足，未作推断 |
| server | 当前来源不足，未作推断 |
| website | 当前来源不足，未作推断 |
| 自动修复 | 当前来源不足，未作推断 |
| 自动升级 | 当前来源不足，未作推断 |

## 源码

- source_repo: https://github.com/opensourceways/software-package-all
- sub_repos:
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/autoupgrade（https://github.com/opensourceways/autoupgrade）（https://github.com/opensourceways/autoupgrade（https://github.com/opensourceways/autoupgrade）（https://github.com/opensourceways/autoupgrade（https://github.com/opensourceways/autoupgrade）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/autoupgrade-conda（https://github.com/opensourceways/autoupgrade-conda）（https://github.com/opensourceways/autoupgrade-conda（https://github.com/opensourceways/autoupgrade-conda）（https://github.com/opensourceways/autoupgrade-conda（https://github.com/opensourceways/autoupgrade-conda）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/easysoftware-server-deployment（https://github.com/opensourceways/easysoftware-server-deployment）（https://github.com/opensourceways/easysoftware-server-deployment（https://github.com/opensourceways/easysoftware-server-deployment）（https://github.com/opensourceways/easysoftware-server-deployment（https://github.com/opensourceways/easysoftware-server-deployment）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/easysoftware-website-deployment（https://github.com/opensourceways/easysoftware-website-deployment）（https://github.com/opensourceways/easysoftware-website-deployment（https://github.com/opensourceways/easysoftware-website-deployment）（https://github.com/opensourceways/easysoftware-website-deployment（https://github.com/opensourceways/easysoftware-website-deployment）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/easysoftware-website-openatom-deployment（https://github.com/opensourceways/easysoftware-website-openatom-deployment）（https://github.com/opensourceways/easysoftware-website-openatom-deployment（https://github.com/opensourceways/easysoftware-website-openatom-deployment）（https://github.com/opensourceways/easysoftware-website-openatom-deployment（https://github.com/opensourceways/easysoftware-website-openatom-deployment）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/input（https://github.com/opensourceways/input）（https://github.com/opensourceways/input（https://github.com/opensourceways/input）（https://github.com/opensourceways/input（https://github.com/opensourceways/input）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/input-archnum（https://github.com/opensourceways/input-archnum）（https://github.com/opensourceways/input-archnum（https://github.com/opensourceways/input-archnum）（https://github.com/opensourceways/input-archnum（https://github.com/opensourceways/input-archnum）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/input-epkg（https://github.com/opensourceways/input-epkg）（https://github.com/opensourceways/input-epkg（https://github.com/opensourceways/input-epkg）（https://github.com/opensourceways/input-epkg（https://github.com/opensourceways/input-epkg）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/input-externalos（https://github.com/opensourceways/input-externalos）（https://github.com/opensourceways/input-externalos（https://github.com/opensourceways/input-externalos）（https://github.com/opensourceways/input-externalos（https://github.com/opensourceways/input-externalos）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/input-field-domain（https://github.com/opensourceways/input-field-domain）（https://github.com/opensourceways/input-field-domain（https://github.com/opensourceways/input-field-domain）（https://github.com/opensourceways/input-field-domain（https://github.com/opensourceways/input-field-domain）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/input-oepkg（https://github.com/opensourceways/input-oepkg）（https://github.com/opensourceways/input-oepkg（https://github.com/opensourceways/input-oepkg）（https://github.com/opensourceways/input-oepkg（https://github.com/opensourceways/input-oepkg）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/input-rpm（https://github.com/opensourceways/input-rpm）（https://github.com/opensourceways/input-rpm（https://github.com/opensourceways/input-rpm）（https://github.com/opensourceways/input-rpm（https://github.com/opensourceways/input-rpm）
  - 已核验源码仓：已核验源码仓：已核验源码仓：https://github.com/opensourceways/input-srcrepo（https://github.com/opensourceways/input-srcrepo）（https://github.com/opensourceways/input-srcrepo（https://github.com/opensourceways/input-srcrepo）（https://github.com/opensourceways/input-srcrepo（https://github.com/opensourceways/input-srcrepo）

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
