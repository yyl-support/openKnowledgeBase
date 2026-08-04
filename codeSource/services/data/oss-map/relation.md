---
tags: [relation, oss-map]
service: oss-map
source: https://github.com/opensourceways/oss-map
source_repo: https://github.com/opensourceways/oss-map
updated_at: 2026-08-04
---

## connection

- backend 为 FastAPI（端口 8000），frontend 为 Vue 3 + Nginx（端口 7070），data-collector 为 CLI runner；backend 依赖 PostgreSQL。

## evolution

以下记录按当前可取得的公开 commit/issue 整理；不足 10 条时不补造记录。
- 2026-08-04 [a2c271f](https://github.com/opensourceways/oss-map/commit/a2c271f) 演进记录：Merge pull request #312: 私密邮箱关联 GitHub login；修复人员关联与事务提交。
- 2026-08-04 [1dce8f0](https://github.com/opensourceways/oss-map/commit/1dce8f0) 演进记录：支持私密邮箱关联 github login；修复人员合并。
- 2026-08-03 [7cd9849](https://github.com/opensourceways/oss-map/commit/7cd9849) 演进记录：Merge pull request #311；合并变更。
- 2026-08-03 [603f1bd](https://github.com/opensourceways/oss-map/commit/603f1bd) 演进记录：修复采集 repo 问题；修复仓库采集。
- 2026-08-03 [fe05659](https://github.com/opensourceways/oss-map/commit/fe05659) 演进记录：fix(maintainers): 组织成员 Option B；primary 场景取唯一活跃关系。

## deploy

| 部署范围 | 环境 | 公开域名 | 镜像/源码仓 | 归档方式 | 来源 |
| --- | --- | --- | --- | --- | --- |
| 主仓 | test | 未记录 | [oss-map](https://github.com/opensourceways/oss-map) | 未记录 | infra-common service.md |

## facts_insufficient

- 最近公开 commit 未达 10 条。
- 未确认生产部署记录。
- 公开 README 与目录树未提供可核验的完整组件清单。
导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
