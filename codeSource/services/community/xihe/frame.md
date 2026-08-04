---
tags: [community, xihe]
service: xihe
source: https://github.com/opensourceways/xihe-all
updated_at: 2026-08-04
---

## summary
AI模型训练推理协作微服务平台，包含API、Notebook、消息、内部服务、gRPC协议库、SDK和Kubernetes Operator。

## infrastructure
- 服务注册文件统一service id为xihe，源码umbrella仓为opensourceways/xihe-all。
- 注册文件将xihe-all描述为git submodule聚合umbrella仓，列出7个dev子仓。
- 有镜像的服务包括xihe-server、xihe-jupyter-server、xihe-message-server和xihe-internal-server；SDK和协议库无镜像，Operator部署方式不同。

## components

| name | role |
| --- | --- |
| xihe-server | 主服务API |
| xihe-jupyter-server | Notebook服务 |
| xihe-message-server | 消息服务 |
| xihe-internal-server | 内部服务 |
| xihe-sdk | SDK库 |
| xihe-grpc-protocol | gRPC协议定义 |
| code-server-operator | Kubernetes Operator |

## 源码

- source_repo: https://github.com/opensourceways/xihe-all
- sub_repos:
  - name=xihe-server
  - name=xihe-jupyter-server
  - name=xihe-message-server
  - name=xihe-internal-server
  - name=xihe-sdk
  - name=xihe-grpc-protocol
  - name=code-server-operator

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
