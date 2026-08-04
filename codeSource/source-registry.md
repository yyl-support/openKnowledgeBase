# 服务注册项来源清单

文档导航：[`README.md`](../README.md) · [`org-overview.md`](org-overview.md) · [`service-map.md`](service-map.md) · [`source-registry.md`](source-registry.md)。

## 快照说明

以下 24 个服务注册项来自 2026-08-04 通过已认证 GitHub API 读取的 `opensourceways/backlog` 仓库 `.ai-flow/services/*.yaml`。

backlog 是组织访问受控的外部来源。公开读者访问其 URL 时可能收到 404，因此不能将该 URL 描述为公开可验证来源。外部来源入口为 <https://github.com/opensourceways/backlog>，访问需要组织权限。本文件是本次公开知识库的范围快照，不复制 YAML 全文。

每行依次为 `service_id`、`project_label`、`tools_repo` 和来源文件名。`project_label` 是 GitHub issue 路由标签，不是另一组服务数量。

来源记录如下：读取日期为 `2026-08-04`，API 请求路径模板为 `GET /repos/opensourceways/backlog/contents/.ai-flow/services/<filename>`，REST API 地址为 <https://api.github.com>。表格中的逐项来源路径是受控来源定位信息，公开读者可能无法访问；当前未记录 backlog commit SHA。

表格字段为 `service_id`、`project_label`、`tools_repo` 和 `source_file`。原始清单中的斜杠分隔字段依次表示这四列：服务标识、GitHub issue 路由标签、实现仓库和 backlog 配置文件名。`project_label` 不是另一组服务数量。

## 注册项

| service_id | project_label | tools_repo | source_file |
| --- | --- | --- | --- |
| ascend-ci-project | project:ascend-ci-project | opensourceways/ascend-ci-project | ascend-ci-project.yaml |
| bigfiles-lfs-all | project:bigfiles-lfs-all | opensourceways/bigfiles-lfs-all | bigfiles-lfs-all.yaml |
| calculator | project:calculator-umbrella | opensourceways/calculator-umbrella | calculator.yaml |
| certification-all | project:certification-all | opensourceways/certification-all | certification-all.yaml |
| ci-all | project:ci-all | opensourceways/ci-all | ci-all.yaml |
| cla-all | project:cla-all | opensourceways/cla-all | cla-all.yaml |
| etherpad-lite | project:etherpad-lite | opensourceways/etherpad-lite | etherpad-lite.yaml |
| eur-build-all | project:eur-build-all | opensourceways/eur-build-all | eur-build-all.yaml |
| forum-reply-robot | project:forum-reply-robot | opensourceways/forum-reply-robot | forum-reply-robot.yaml |
| hotopic-all | project:hotopic-all | opensourceways/hotopic-all | hotopic-all.yaml |
| mailman | project:mailman | opensourceways/mailman | mailman.yaml |
| meeting-server | project:meeting-server | opensourceways/meeting-server | meeting-server.yaml |
| message-bus-all | project:message-bus-all | opensourceways/message-bus-all | message-bus-all.yaml |
| om-datacenter | project:om-datacenter | opensourceways/om-datacenter | om-datacenter.yaml |
| om-webserver | project:om-webserver | opensourceways/om-webserver | om-webserver.yaml |
| oneid-all | project:oneid-all | opensourceways/oneid-all | oneid-all.yaml |
| oss-map | project:oss-map | opensourceways/oss-map | oss-map.yaml |
| patch-manager | project:patch-manager | opensourceways/patch-manager | patch-manager.yaml |
| pod-exporter-monitoring | project:pod_exporter_monitoring | opensourceways/pod_exporter_monitoring | pod-exporter-monitoring.yaml |
| robot | project:community-robots | opensourceways/community-robots | robot.yaml |
| search-all | project:search-all | opensourceways/search-all | search-all.yaml |
| security-cve-all | project:security-cve-all | opensourceways/security-cve-all | security-cve-all.yaml |
| software-package-all | project:software-package-all | opensourceways/software-package-all | software-package-all.yaml |
| xihe | project:xihe-all | opensourceways/xihe-all | xihe-all.yaml |
