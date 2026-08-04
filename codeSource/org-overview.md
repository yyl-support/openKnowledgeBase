# Organization Overview

文档导航：[`README.md`](../README.md) · [`org-overview.md`](org-overview.md) · [`service-map.md`](service-map.md) · [`source-registry.md`](source-registry.md)。

## 文档目的

本文件是 `codeSource` 的组织级入口，提供 opensourceways 组织仓库元数据画像、已注册服务范围和公开发布边界。内容遵循渐进式披露原则，只呈现有明确来源、已核验且适合公开的信息。

本次数据快照日期为 **2026-08-04**。组织仓库统计来源为公开仓库中的[聚合快照](org-repos-snapshot.json)，不包含仓库清单。快照只保留组织级聚合数量（包括私有仓库数量），不保存仓库名称、逐仓私有属性和仓库级私有元数据。服务注册项的逐项范围见 [`source-registry.md`](source-registry.md)，分类与服务入口见 [`service-map.md`](service-map.md)。

## 组织仓库画像

根据[聚合快照](org-repos-snapshot.json)，GitHub API 元数据统计包含 **450** 个组织仓库，其中 fork **42** 个、归档 **246** 个、私有 **397** 个。私有和归档数量来自授权 API 元数据统计，不表示本公开仓库发布了相应仓库的源码或内部细节。

### 语言分布 Top 10

以下结果由[聚合快照](org-repos-snapshot.json)记录；空语言值统一记为 `Unknown`，未手填推断。

| 排名 | 语言 | 仓库数 |
| --- | --- | ---: |
| 1 | Go | 160 |
| 2 | Unknown | 87 |
| 3 | Python | 75 |
| 4 | Java | 23 |
| 5 | Shell | 19 |
| 6 | Vue | 16 |
| 7 | JavaScript | 13 |
| 8 | HTML | 10 |
| 9 | Dockerfile | 8 |
| 10 | CSS | 7 |

### 推送活跃度

以 2026-08-04 为基准，按 `pushed_at` 划分为最近 6 个月（2026-02-04 及以后）、6-24 个月（2024-08-04 至 2026-02-03）和超过 24 个月（早于 2024-08-04）；具体聚合结果见[快照](org-repos-snapshot.json)。

| 区间 | 仓库数 |
| --- | ---: |
| 6 个月内 | 222 |
| 6-24 个月 | 135 |
| 超过 24 个月 | 93 |

三档合计 450 个仓库；统计字段缺失时不补造，本次快照没有缺失的 `pushed_at` 值。

## 治理事实

- backlog 是受控的外部来源，公开读者访问其 URL 可能收到 404；本文件不声称公开读者可以访问 backlog。
- 本次通过授权读取 `.ai-flow/services/*.yaml`，得到 24 个服务注册项。`source-registry.md` 是本次快照的范围清单，不复制 YAML 全文。
- 每个服务的 `label: project:<id>` 是 GitHub issue 路由标签，不是另一组服务数量。

## 代码来源全景

以下七个分类与 [`service-map.md`](service-map.md) 保持一致，服务 ID 为该文件中的注册项：

| 分类 | 服务 ID |
| --- | --- |
| identity | `cla-all`, `om-webserver`, `oneid-all` |
| robots | `forum-reply-robot`, `robot` |
| ci | `ascend-ci-project`, `calculator`, `ci-all` |
| data | `bigfiles-lfs-all`, `om-datacenter`, `oss-map`, `xihe` |
| package | `eur-build-all`, `software-package-all` |
| security | `certification-all`, `patch-manager`, `security-cve-all` |
| community | `etherpad-lite`, `hotopic-all`, `mailman`, `meeting-server`, `message-bus-all`, `pod-exporter-monitoring`, `search-all` |

共 24 个服务注册项；服务地图提供分类、项目标签、实现仓库和服务文档入口。

## 部署知识来源

`infra-common/service.md` 是部署映射的事实来源。已生成服务文档中的 `deploy`/`related_deployments` 内容按公开边界过滤，只保留适合公开发布的部署事实；本组织概览不复制内部部署配置、敏感配置路径、集群与网络细节或其他受限配置细节。

## 覆盖边界

本轮仅覆盖 24 个注册服务，并生成 48 个服务级 Markdown 文件（每个服务一份 `frame.md` 和一份 `relation.md`）。其他组织仓库未生成服务文档。组织仓库总量及其中私有、归档仓库的统计来自授权元数据；本公开仓库不发布私有源码细节。

## 数据来源与限制

- [组织仓库聚合快照](org-repos-snapshot.json)：公开仓库中的组织仓库数量、fork、归档、私有、语言和 `pushed_at` 统计。
- 受控 backlog 的 `.ai-flow/services/*.yaml`：服务注册项及其路由标签、实现仓库范围。
- 各源码仓的 README、目录树、commit 和 issue：服务级公开代码事实。
- `infra-common/service.md`：部署映射事实来源，按公开边界过滤后用于服务文档。

原始授权 GitHub API 返回的仓库级数据未复制到本公开仓库；公开读者可复核组织级聚合结果，但不能从本仓恢复仓库清单或逐仓属性。源码 URL 可能指向需要组织权限的私有或受控仓库；URL 是原始来源定位，不代表公开读者一定可访问。以上来源无法核验的部分不补造；受控 backlog 的内容也不因出现在来源清单中而被描述为公开可访问。

---

导航：[`README.md`](../README.md) · [`service-map.md`](service-map.md) · [`source-registry.md`](source-registry.md)
