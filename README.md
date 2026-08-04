# openKnowledgeBase

这是一个公开仓库, 也是 AI 时代团队外网知识库总仓.

## 定位

`codeSource/` 用于沉淀可公开发布的组织概览, 服务地图和相关代码事实. 内容采用渐进式披露原则: 先提供稳定, 可验证的概览, 再逐步补充经过审核的细节.

事实来源铁律: 任何事实必须能够追溯到明确来源, 生成内容不得替代来源, 不确定内容必须标注为待确认或待生成.

## 敏感信息边界

本仓库只收录适合公开发布的信息. 不收录凭据, 密钥, 令牌, 内网地址, 内部部署路径, 集群或 namespace 信息, 内部镜像地址, 内部拓扑, 数据库连接细节, 个人敏感信息, 未公开业务数据或其他受限内容. 本地分析草稿放在 `.drafts/`, 不进入仓库发布范围.

## 目录

- [`codeSource/`](codeSource/): 公开代码事实和服务知识
- [`codeSource/org-overview.md`](codeSource/org-overview.md): 组织概览占位文档
- [`codeSource/service-map.md`](codeSource/service-map.md): 服务地图占位文档
- [`codeSource/services/`](codeSource/services/): 服务级文档目录

当前覆盖范围计划为 24 个服务注册项. 每个服务注册项由 backlog 仓库外部输入 `.ai-flow/services/<id>.yaml` 定义. 其中 `label: project:<id>` 是 GitHub issue 路由标签, 不是另一组服务数量, 二者不代表两个数量.

backlog 外部来源: <https://github.com/opensourceways/backlog/tree/main/.ai-flow/services>. 本公开仓库不复制 backlog 配置, 具体服务明细仍以外部输入的生成和审核结果为准, 不在骨架阶段预先编造.

`.drafts/` 仅用于本地分析草稿, 不入库, 不发布.
