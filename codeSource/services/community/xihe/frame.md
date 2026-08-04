---
tags: [community, xihe]
service: xihe
source: https://github.com/opensourceways/xihe-all
updated_at: 2026-08-04
---

## summary
AI 模型训练推理协作微服务平台，包含 API、Notebook、消息、注册配置中的内部组件、gRPC 协议库、SDK 和 Kubernetes Operator。

## infrastructure
- 服务注册文件统一 service id 为 xihe，源码 umbrella 仓为 opensourceways/xihe-all。
- 注册文件将 xihe-all 描述为 Git submodule 聚合 umbrella 仓，列出 7 个 dev 子仓。
- 注册配置记录部分组件存在镜像，但公开版本不展示未公开部署细节。

## components

| name | role |
| --- | --- |
| xihe-server | 主服务API |
| xihe-jupyter-server | Notebook服务 |
| xihe-message-server | 消息服务 |
| 注册配置中的内部组件（名称不公开） | 未公开组件 |
| xihe-sdk | SDK库 |
| xihe-grpc-protocol | gRPC协议定义 |
| code-server-operator | Kubernetes Operator |

## 源码

- source_repo: https://github.com/opensourceways/xihe-all
- sub_repos:
  - 已核验源码仓：xihe-server（https://github.com/opensourceways/xihe-server）
  - 已核验源码仓：xihe-jupyter-server（https://github.com/opensourceways/xihe-jupyter-server）
  - 已核验源码仓：xihe-message-server（https://github.com/opensourceways/xihe-message-server）
  - 注册配置中的内部组件（名称不公开）
  - 注册配置名称，未核验独立源码仓：xihe-sdk
  - 注册配置名称，未核验独立源码仓：xihe-grpc-protocol
  - 注册配置名称，未核验独立源码仓：code-server-operator


导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
