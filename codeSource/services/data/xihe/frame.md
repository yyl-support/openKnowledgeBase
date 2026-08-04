---
tags: [data, xihe]
service: xihe
source: https://github.com/opensourceways/xihe-all
source_repo: https://github.com/opensourceways/xihe-all
updated_at: 2026-08-04
---

## summary
AI 模型训练推理协作微服务平台，包含 API、Notebook、消息服务、协议库、SDK 和 Kubernetes Operator。

## infrastructure
- 服务注册文件统一 service id 为 xihe，源码 umbrella 仓为 opensourceways/xihe-all。
- 注册文件将 xihe-all 描述为 Git submodule 聚合 umbrella 仓，列出 7 个 dev 子仓。

## components

| name | role |
| --- | --- |
| xihe-server | 主服务 API |
| xihe-jupyter-server | Notebook 服务 |
| xihe-message-server | 消息服务 |

## 源码

- 服务注册 tools_repo：[xihe-all](https://github.com/opensourceways/xihe-all)
- umbrella/聚合仓：[xihe-all](https://github.com/opensourceways/xihe-all)
- 已核验子仓：[xihe-server](https://github.com/opensourceways/xihe-server)
- 已核验子仓：[xihe-jupyter-server](https://github.com/opensourceways/xihe-jupyter-server)
- 已核验子仓：[xihe-message-server](https://github.com/opensourceways/xihe-message-server)

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
