# Service Map

## 文档目的

本文件用于展示公开知识库中的服务全景, 帮助读者理解服务之间的分类, 归属, 依赖和公开文档入口. 它是索引和导航文档, 不是未经审核的数据源.

## 字段说明

正式服务记录计划包含以下字段:

- `service_id`: 对应 yaml 中的 `service.id`
- `project_label`: 对应 yaml 中的 `service.label`, 其值形如 `project:<id>` 并用于 GitHub issue 路由
- `service`: 服务名称或公开显示名称
- `category`: 服务分类
- `owner`: 维护归属或责任边界
- `status`: 当前生命周期或生成状态
- `source_repo`: 对应 yaml 中的 `implement.tools_repo`
- `source`: 事实来源引用
- `links`: 公开文档或代码链接

字段只有在存在明确来源时才能填写. 每条服务文档中的事实字段都必须附原始仓库 URL, 或 GitHub API / 文件路径引用. 缺失或未确认的字段应保留为空或标注待确认, 不得推测.

## 当前覆盖范围

目标覆盖范围为 24 个服务注册项. 每个服务注册项由 backlog 仓库外部输入 `.ai-flow/services/<id>.yaml` 定义; 当前骨架只建立文档入口和服务目录, 尚未生成任何服务明细.

分类将基于外部 backlog 的 `.ai-flow/services/*.yaml` 中的服务数据生成. 外部来源为 <https://github.com/opensourceways/backlog/tree/main/.ai-flow/services>, 本公开仓库不复制 backlog 配置. `label: project:<id>` 是 GitHub issue 路由标签, 与 24 个服务注册项不是两个数量.

## 生成状态

当前处于生成阶段. 服务地图尚未形成正式数据快照, 不代表已经完成 24 个服务注册项的清单, 分类或统计. 后续生成结果必须保留来源引用并经过公开发布边界审核.
