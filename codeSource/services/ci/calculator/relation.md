---
tags: [relation, calculator]
service: calculator
source: https://github.com/opensourceways/calculator-umbrella
source_repo: https://github.com/opensourceways/calculator-umbrella
updated_at: 2026-08-04
---

## connection

- 主仓通过 submodule 组织 backend 与 frontend；注册信息记录 k8s manifests 与 pod selector。

## evolution

以下记录按当前可取得的公开 commit/issue 整理；不足 10 条时不补造记录。
- 2026-05-21 [e0f06a5](https://github.com/opensourceways/calculator-umbrella/commit/e0f06a5) 演进记录：CI 参数约定调整；与通用参数约定一致。
- 2026-05-21 [dac0a45](https://github.com/opensourceways/calculator-umbrella/commit/dac0a45) 演进记录：ci: pod 步骤内联安装 kubectl；为 runner 镜像补充 kubectl。

## deploy

infra-common service.md 未核验到本服务注册主仓的直接部署记录。

## facts_insufficient

- 最近公开 commit 未达 10 条。
- infra-common service.md 未匹配 calculator-umbrella 部署记录。
- 未确认 backend/frontend 的源码 URL 和运行时连接。
- 公开 README 与目录树未提供可核验的完整组件清单。
导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
