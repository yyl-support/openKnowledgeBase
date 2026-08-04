---
tags: [community, message-bus-all]
service: message-bus-all
source: https://github.com/opensourceways/message-bus-all
source_repo: https://github.com/opensourceways/message-bus-all
updated_at: 2026-08-04
---

## summary
消息总线服务，包含 GitHub 钩子和事件分发能力，注册描述列出 collect、manager、push、transfer。

## infrastructure
- 生产入口为 https://message-center.openeuler.openatom.cn（服务注册 YAML）。
- 注册配置声明预览环境使用专属服务标识和 ArgoCD 发布流程。

## components

| name | role |
| --- | --- |
| collect | 注册配置组件，职责未核验 |
| manager | 注册配置组件，职责未核验 |
| push | 注册配置组件，职责未核验 |
| transfer | 注册配置组件，职责未核验 |
| GitHub 钩子 | 注册配置组件，职责未核验 |
| 事件分发 | 注册配置组件，职责未核验 |

## 源码

- 注册主仓：[message-bus-all](https://github.com/opensourceways/message-bus-all)
- 无已核验子仓记录。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
