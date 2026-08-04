---
tags: [data, om-datacenter]
service: om-datacenter
source: https://github.com/opensourceways/om-datacenter
source_repo: https://github.com/opensourceways/om-datacenter
updated_at: 2026-08-04
---

## summary
跨社区数据采集、治理和看板平台，涉及D1/D2开发者度量、贡献统计、datastat和kafka。umbrella仓聚合4个dev子仓。

## infrastructure
- 服务注册文件说明om-datacenter是git submodule聚合umbrella仓。
- om-dataarts写PostgreSQL，APIMagic只读PostgreSQL，前端为datastat-manage-website，配置由om-deployment提供。
- 服务注册文件记录APIMagic的.ms变更可执行数据库替换和reload；该行为仅作为注册配置事实记录。

## components

## 源码

- 服务注册 tools_repo：[om-datacenter](https://github.com/opensourceways/om-datacenter)

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
