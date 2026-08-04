---
tags: [community, search-all]
service: search-all
source: https://github.com/opensourceways/search-all
source_repo: https://github.com/opensourceways/search-all
updated_at: 2026-08-04
---

## summary
EasySearch 索引、文档搜索、文档输入和 RM-CHECK 服务。

## infrastructure
- 生产入口为 https://doc-search.openeuler.org（服务注册 YAML）。
- 注册配置声明预览环境使用专属服务标识和 ArgoCD 发布流程。

## components

| name | role |
| --- | --- |
| EasySearch 索引 | 注册配置组件，职责未核验 |
| 文档搜索 | 注册配置组件，职责未核验 |
| 文档输入 | 注册配置组件，职责未核验 |
| RM-CHECK | 注册配置组件，职责未核验 |

## 源码

- 注册主仓：[search-all](https://github.com/opensourceways/search-all)
- 无已核验子仓记录。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
