# Service Map

文档导航：[`README.md`](../README.md) · [`org-overview.md`](org-overview.md) · [`service-map.md`](service-map.md) · [`source-registry.md`](source-registry.md)。

## 文档目的

本文件用于展示公开知识库中的服务全景，帮助读者理解服务之间的分类、归属、依赖和公开文档入口。它是索引和导航文档，不是未经审核的数据源。

相关入口：[`org-overview.md`](org-overview.md)；具体服务注册项清单：[`source-registry.md`](source-registry.md)。

## 字段说明

正式服务记录计划包含以下字段：

- `service_id`：对应 yaml 中的 `service.id`
- `project_label`：对应 yaml 中的 `service.label`，其值形如 `project:<id>`，并用于 GitHub issue 路由
- `service`：服务名称或公开显示名称
- `category`：服务分类
- `owner`：维护归属或责任边界
- `status`：当前生命周期或生成状态
- `source_repo`：对应 yaml 中的 `implement.tools_repo`
- `source`：事实来源引用
- `links`：公开文档或代码链接

字段只有在存在明确来源时才能填写。每条服务文档中的事实字段都必须附原始仓库 URL，或 GitHub API / 文件路径引用。缺失或未确认的字段应保留为空或标注待确认，不得推测。

## 当前覆盖范围

目标覆盖范围为 24 个服务注册项。每个服务注册项由 backlog 仓库外部输入 `.ai-flow/services/<id>.yaml` 定义；24 个服务文档已生成，详见 [`services/`](services/)。具体清单以 [`source-registry.md`](source-registry.md) 为准。

分类将基于外部 backlog 的 `.ai-flow/services/*.yaml` 中的服务数据生成。外部来源为 <https://github.com/opensourceways/backlog>，访问需要组织权限，公开读者可能收到 404，不能将其描述为公开可验证来源。本公开仓库不复制 backlog 配置。`label: project:<id>` 是 GitHub issue 路由标签，与 24 个服务注册项不是两个数量。

`codeSource/services/` 包含 24 个已生成的服务级文档。

## 服务分类表

| category | service_id | project_label | tools_repo | source_file |
| --- | --- | --- | --- | --- |
| ci | ascend-ci-project | project:ascend-ci-project | https://github.com/opensourceways/ascend-ci-project | ascend-ci-project.yaml |
| data | bigfiles-lfs-all | project:bigfiles-lfs-all | https://github.com/opensourceways/bigfiles-lfs-all | bigfiles-lfs-all.yaml |
| ci | calculator | project:calculator-umbrella | https://github.com/opensourceways/calculator-umbrella | calculator.yaml |
| security | certification-all | project:certification-all | https://github.com/opensourceways/certification-all | certification-all.yaml |
| ci | ci-all | project:ci-all | https://github.com/opensourceways/ci-all | ci-all.yaml |
| identity | cla-all | project:cla-all | https://github.com/opensourceways/cla-all | cla-all.yaml |
| community | etherpad-lite | project:etherpad-lite | https://github.com/opensourceways/etherpad-lite | etherpad-lite.yaml |
| package | eur-build-all | project:eur-build-all | https://github.com/opensourceways/eur-build-all | eur-build-all.yaml |
| robots | forum-reply-robot | project:forum-reply-robot | https://github.com/opensourceways/forum-reply-robot | forum-reply-robot.yaml |
| community | hotopic-all | project:hotopic-all | https://github.com/opensourceways/hotopic-all | hotopic-all.yaml |
| community | mailman | project:mailman | https://github.com/opensourceways/mailman | mailman.yaml |
| community | meeting-server | project:meeting-server | https://github.com/opensourceways/meeting-server | meeting-server.yaml |
| community | message-bus-all | project:message-bus-all | https://github.com/opensourceways/message-bus-all | message-bus-all.yaml |
| data | om-datacenter | project:om-datacenter | https://github.com/opensourceways/om-datacenter | om-datacenter.yaml |
| identity | om-webserver | project:om-webserver | https://github.com/opensourceways/om-webserver | om-webserver.yaml |
| identity | oneid-all | project:oneid-all | https://github.com/opensourceways/oneid-server | oneid-all.yaml |
| data | oss-map | project:oss-map | https://github.com/opensourceways/oss-map | oss-map.yaml |
| security | patch-manager | project:patch-manager | https://github.com/opensourceways/patch-manager | patch-manager.yaml |
| community | pod-exporter-monitoring | project:pod_exporter_monitoring | https://github.com/opensourceways/pod_exporter_monitoring | pod-exporter-monitoring.yaml |
| robots | robot | project:community-robots | https://github.com/opensourceways/community-robots | robot.yaml |
| community | search-all | project:search-all | https://github.com/opensourceways/search-all | search-all.yaml |
| security | security-cve-all | project:security-cve-all | https://github.com/opensourceways/security-cve-all | security-cve-all.yaml |
| package | software-package-all | project:software-package-all | https://github.com/opensourceways/software-package-all | software-package-all.yaml |
| data | xihe | project:xihe-all | https://github.com/opensourceways/xihe-all | xihe-all.yaml |

## 生成状态

服务地图已形成 24 个服务注册项的文档入口；后续补充内容必须保留来源引用并经过公开发布边界审核。
