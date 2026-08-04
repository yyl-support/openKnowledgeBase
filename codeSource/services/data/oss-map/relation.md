---
tags: [relation, oss-map]
service: oss-map
source: https://github.com/opensourceways/oss-map
updated_at: 2026-08-04
---

## connection
- backend 为 FastAPI（端口 8000），frontend 为 Vue 3 + Nginx（端口 7070），data-collector 为 CLI runner；backend 依赖 PostgreSQL。

## evolution
- 2026-08-04 `a2c271f` Merge pull request #312: 私密邮箱关联 GitHub login: 修复人员关联与事务提交。（来源：https://github.com/opensourceways/oss-map/commit/a2c271f）
- 2026-08-04 `1dce8f0` 支持私密邮箱关联 github login: 修复人员合并。（来源：https://github.com/opensourceways/oss-map/commit/1dce8f0）
- 2026-08-03 `7cd9849` Merge pull request #311: 合并变更。（来源：https://github.com/opensourceways/oss-map/commit/7cd9849）
- 2026-08-03 `603f1bd` 修复采集 repo 问题: 修复仓库采集。（来源：https://github.com/opensourceways/oss-map/commit/603f1bd）
- 2026-08-03 `fe05659` fix(maintainers): 组织成员 Option B: primary 场景取唯一活跃关系。（来源：https://github.com/opensourceways/oss-map/commit/fe05659）

## deploy
- source_repo=https://github.com/opensourceways/oss-map; environment=test; public_endpoint=oss-map不公开部署细节; method=ArgoCD; note=service.md 与本地注册信息确认的测试部署。

## facts_insufficient
- 最近公开 commit 未达 10 条。
- 未确认生产部署记录。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
