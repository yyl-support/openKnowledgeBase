---
tags: [relation, hotopic-all]
service: hotopic-all
source: https://github.com/opensourceways/hotopic-all
source_repo: https://github.com/opensourceways/hotopic-all
updated_at: 2026-08-04
---

## connection

- .ai-flow/deploy/init 包含 SQL 与 MongoDB 初始化脚本，test-sync 包含同步脚本。

## evolution

以下记录按当前可取得的公开 commit/issue 整理；不足 10 条时不补造记录。
- 2026-07-15 [eb3d1f1](https://github.com/opensourceways/hotopic-all/commit/eb3d1f1) 演进记录：!25 更新 CLAUDE.md 模型指导；更新协作指导。
- 2026-07-14 [f204581](https://github.com/opensourceways/hotopic-all/commit/f204581) 演进记录：chore: 更新测试分支参数；调整部署测试参数。
- 2026-06-16 [73b91c2](https://github.com/opensourceways/hotopic-all/commit/73b91c2) 演进记录：Merge pull request #22；合并分支变更。
- 2026-06-16 [d2caf31](https://github.com/opensourceways/hotopic-all/commit/d2caf31) 演进记录：fix(deploy): is_changed base 修复；修复浅克隆变更基线。
- 2026-06-15 [04be991](https://github.com/opensourceways/hotopic-all/commit/04be991) 演进记录：修复部署相关问题；调整部署行为。
- 2026-06-15 [2be3df8](https://github.com/opensourceways/hotopic-all/commit/2be3df8) 演进记录：fix: Go 脚本 CERT_SRC 转义；修复 heredoc 变量展开。
- 2026-06-15 [ec4f4da](https://github.com/opensourceways/hotopic-all/commit/ec4f4da) 演进记录：fix: mining source_url 转义；修复 API_URL 展开。
- 2026-06-15 [1c57cb2](https://github.com/opensourceways/hotopic-all/commit/1c57cb2) 演进记录：fix: PG Deployment YAML 结构；修复 env 结构。
- 2026-06-15 [e20203d](https://github.com/opensourceways/hotopic-all/commit/e20203d) 演进记录：修复 CA 证书写入处理；修复证书处理。
- 2026-06-15 [8e010b7](https://github.com/opensourceways/hotopic-all/commit/8e010b7) 演进记录：!19 fix: MongoDB TLS；修复 MongoDB TLS 配置。

## deploy

infra-common service.md 未核验到本服务注册主仓的直接部署记录。

## facts_insufficient

- 未能从允许来源核验完整组件清单，因此未作补充。

- 未确认可公开保留的 infra-common service.md 部署行。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
