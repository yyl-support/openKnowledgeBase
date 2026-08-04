---
tags: [relation, calculator]
service: calculator
source: https://github.com/opensourceways/calculator-umbrella
updated_at: 2026-08-04
---

## connection
- 主仓通过 submodule 组织 backend 与 frontend；注册信息记录 k8s manifests 与 pod selector。

## evolution
- 2026-05-21 `e0f06a5` fix(ci): jenkins 参数改为 --param 不公开部署细节=: 与通用参数约定一致。
- 2026-05-21 `dac0a45` ci: pod 步骤内联安装 kubectl: 为 runner 镜像补充 kubectl。

## deploy
当前来源不足，未作推断

## facts_insufficient
- 最近公开 commit 未达 10 条。
- service.md 未匹配 calculator-umbrella 部署记录。
- 未确认 backend/frontend 的源码 URL 和运行时连接。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
