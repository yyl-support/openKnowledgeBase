---
tags: [relation, software-package-all]
service: software-package-all
source: https://github.com/opensourceways/software-package-all
source_repo: https://github.com/opensourceways/software-package-all
updated_at: 2026-08-04
---

## connection

- 服务注册信息记录了：prod_url 为 https://software-pkg.openeuler.org；实现分支为 main。

## registry_info

- 服务注册信息：公开入口 [software-pkg.openeuler.org](https://software-pkg.openeuler.org)；来源：backlog service yaml。

## evolution

- GitHub API 未能核验演进记录，因此未推断演进方向。

## deploy

- service.md 未核验到主仓直接部署记录。

## facts_insufficient

- 未能从允许来源核验完整组件清单，因此未作补充。

- GitHub API 无法核验 README、目录树和最近提交，因此未推断组件与演进方向。
- infra-common service.md 未找到软件包平台主仓本身的匹配行；deploy 仅采用能够按源码仓直接匹配的 EasySoftware 子仓记录。
- service 注册中记录 EasySoftware-autorepair 构建脚本路径为空，且 easysoftware-autoupgrade、software-package-gateway、software-package-github-server、software-package-server、software-package-website 未自动填充测试部署目标。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
