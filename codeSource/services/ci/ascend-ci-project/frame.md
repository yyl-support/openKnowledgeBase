---
tags: [ci, ascend-ci-project]
service: ascend-ci-project
source: https://github.com/opensourceways/ascend-ci-project
source_repo: https://github.com/opensourceways/ascend-ci-project
updated_at: 2026-08-04
---

## summary
昇腾CI资源池的ArgoCD/kustomize配置仓库，服务注册说明将其定义为纯配置类仓库，代码合入后由ArgoCD自动同步。

## infrastructure
- 实现仓库为opensourceways/ascend-ci-project，引用 main 分支。
- 注册文件声明无需上线测试，纯配置仓库代码合入即完成。

## components

## 源码

- 服务注册 tools_repo：[ascend-ci-project](https://github.com/opensourceways/ascend-ci-project)

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
