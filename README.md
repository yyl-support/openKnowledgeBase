# openKnowledgeBase

这是一个公开仓库，也是 AI 时代团队外网知识库总仓。

## 定位

`codeSource/` 用于沉淀可公开发布的组织概览、服务地图和相关代码事实。内容采用渐进式披露原则：先提供稳定、可验证的概览，再逐步补充经过审核的细节。

事实来源铁律：任何事实必须能够追溯到明确来源，生成内容不得替代来源，不确定内容必须标注为待确认或待生成。

## 敏感信息边界

本仓库只收录适合公开发布的信息。不收录凭据、密钥、令牌、内网地址、内部部署路径、集群或 namespace 信息、内部镜像地址、内部拓扑、数据库连接细节、个人敏感信息、未公开业务数据或其他受限内容。本地分析草稿放在 `.drafts/`，不进入仓库发布范围。

## 目录

- [`codeSource/`](codeSource/)：公开代码事实和服务知识
- [`codeSource/org-overview.md`](codeSource/org-overview.md)：组织概览占位文档
- [`codeSource/service-map.md`](codeSource/service-map.md)：服务地图占位文档
- [`codeSource/source-registry.md`](codeSource/source-registry.md)：本次服务注册项范围快照
- [`codeSource/services/`](codeSource/services/)：服务级文档预留目录

当前覆盖范围为 24 个服务注册项。每个服务注册项由 backlog 仓库外部输入 `.ai-flow/services/<id>.yaml` 定义。其中 `label: project:<id>` 是 GitHub issue 路由标签，不是另一组服务数量，二者不代表两个数量。具体服务清单以 [`codeSource/source-registry.md`](codeSource/source-registry.md) 为准。

backlog 外部来源：<https://github.com/opensourceways/backlog>，访问需要组织权限，公开读者可能收到 404，不能将其描述为公开可验证来源。本公开仓库不复制 backlog 配置。

`.drafts/` 仅用于本地分析草稿，不入库，不发布。
