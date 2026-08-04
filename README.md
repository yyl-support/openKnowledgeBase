# openKnowledgeBase

这是一个公开仓库，也是 AI 时代团队外网知识库总仓。

文档导航：[`README.md`](README.md) · [`org-overview.md`](codeSource/org-overview.md) · [`org-repos-snapshot.json`](codeSource/org-repos-snapshot.json) · [`service-map.md`](codeSource/service-map.md) · [`source-registry.md`](codeSource/source-registry.md)。

## 定位

`codeSource/` 用于沉淀可公开发布的组织概览、服务地图和相关代码事实。内容采用渐进式披露原则：先提供稳定、可验证的概览，再逐步补充经过审核的细节。

事实来源铁律：任何事实必须能够追溯到明确来源，生成内容不得替代来源，不确定内容必须标注为待确认或待生成。

## 敏感信息边界

本仓库只收录适合公开发布的信息。不收录凭据、密钥、令牌、内网地址、内部部署路径、集群与网络细节、内部镜像地址、内部拓扑、数据库连接细节、个人敏感信息、未公开业务数据或其他受限内容。本地分析草稿放在 `.drafts/`，不进入仓库发布范围。

## 目录

- [`codeSource/`](codeSource/)：公开代码事实和服务知识
- [`codeSource/org-overview.md`](codeSource/org-overview.md)：组织仓库画像与代码来源全景
- [`codeSource/org-repos-snapshot.json`](codeSource/org-repos-snapshot.json)：不含仓库清单的组织仓库聚合统计快照
- [`codeSource/service-map.md`](codeSource/service-map.md)：24 个服务的分类与文档入口
- [`codeSource/source-registry.md`](codeSource/source-registry.md)：本次服务注册项范围快照
- [`codeSource/services/`](codeSource/services/)：已生成的 24 个服务级文档

当前已完成 `codeSource` 文档，覆盖 24 个服务注册项、48 个服务级 Markdown 文件（每个服务一份 `frame.md` 和一份 `relation.md`），详见 [`codeSource/services/`](codeSource/services/)。组织概览、组织仓库聚合快照、服务地图和本次来源快照分别见 [`codeSource/org-overview.md`](codeSource/org-overview.md)、[`codeSource/org-repos-snapshot.json`](codeSource/org-repos-snapshot.json)、[`codeSource/service-map.md`](codeSource/service-map.md) 和 [`codeSource/source-registry.md`](codeSource/source-registry.md)。聚合快照仅保存统计，不保存仓库名称、私有仓库元数据或源码；原始授权 API 的仓库级数据未复制。每个服务注册项由 backlog 仓库外部输入 `.ai-flow/services/<id>.yaml` 定义。其中 `label: project:<id>` 是 GitHub issue 路由标签，不是另一组服务数量，二者不代表两个数量。

公开安全边界：服务成品仅发布经过审核的公开事实，不发布凭据、密钥、令牌、内部部署路径、集群与网络细节等受限内容；私有/归档统计仅来自授权元数据，不发布私有源码细节。

backlog 外部来源：<https://github.com/opensourceways/backlog>，访问需要组织权限，公开读者可能收到 404，不能将其描述为公开可验证来源。本公开仓库不复制 backlog 配置。

`.drafts/` 仅用于本地分析草稿，不入库，不发布。
