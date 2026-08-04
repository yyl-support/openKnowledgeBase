---
tags: [package, eur-build-all]
service: eur-build-all
source: https://github.com/opensourceways/eur-build-all
source_repo: https://github.com/opensourceways/eur-build-all
updated_at: 2026-08-04
---

## summary
openEuler User Repository（EUR）软件包构建、补丁和缺陷管理服务。

## infrastructure
- 生产入口为 https://eur.openeuler.openatom.cn（服务注册 YAML）。
- 注册配置声明预览环境使用专属服务标识和 ArgoCD 发布流程。

## components

| name | role |
| --- | --- |
| EUR 软件包构建 | 注册配置组件，职责未核验 |
| 补丁 | 注册配置组件，职责未核验 |
| 缺陷管理 | 注册配置组件，职责未核验 |

## 源码

- 注册主仓：[eur-build-all](https://github.com/opensourceways/eur-build-all)
- 无已核验子仓记录。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
