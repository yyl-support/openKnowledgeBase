---
tags: [relation, om-webserver]
service: om-webserver
source: https://github.com/opensourceways/om-webserver
updated_at: 2026-08-04
---

## connection
- README 明确服务使用 Redis 和 OBS；未在允许来源中确认更细的接口或数据流连接。

## evolution
- 2026-07-29 `67ea4fd` !239 fix(om-webserver): 启用 fastjson/fastjson2 safeMode 修复 CVE 安全漏洞: 启用 fastjson/fastjson2 safeMode。（来源：https://github.com/opensourceways/om-webserver/commit/67ea4fd）
- 2026-07-29 `216f115` fix(om-webserver): 启用 fastjson/fastjson2 safeMode 修复 CVE 安全漏洞: 在 Dockerfile CMD 增加 JVM safeMode 参数。（来源：https://github.com/opensourceways/om-webserver/commit/216f115）
- 2026-07-22 `2461649` !238 fix(om-webserver): 升级 fastjson2 至 2.0.62 修复 CVE 安全告警: 升级 fastjson2。（来源：https://github.com/opensourceways/om-webserver/commit/2461649）
- 2026-07-22 `87ab240` fix(om-webserver): 升级 fastjson2 至 2.0.62 修复 CVE 安全告警: fastjson2 由 2.0.49 升级至 2.0.62。（来源：https://github.com/opensourceways/om-webserver/commit/87ab240）
- 2026-07-08 `c474408` !223 oidc 登录记录登录日志开发实现: OIDC 登录入口增加登录日志需求实现。（来源：https://github.com/opensourceways/om-webserver/commit/c474408）
- 2026-07-08 `c89975b` fix(om-webserver): 升级 jackson 至 2.18.9 修复 Trivy 安全门禁: 统一升级 Jackson BOM。（来源：https://github.com/opensourceways/om-webserver/commit/c89975b）
- 2026-07-07 `6ec4684` feat(om-webserver): 在 /oidc/auth 登录入口补记登录审计日志: 复用 LogUtil.createLoginLogs 记录审计日志。（来源：https://github.com/opensourceways/om-webserver/commit/6ec4684）
- 2026-06-24 `6f65d8e` !221 IP 频率限制增加白名单需求实现: 通过配置文件为 IP 频率限制增加白名单。（来源：https://github.com/opensourceways/om-webserver/commit/6f65d8e）
- 2026-06-24 `1e9b832` fix(om-webserver): 修正注释中日期错误: 修正注释日期。（来源：https://github.com/opensourceways/om-webserver/commit/1e9b832）
- 2026-06-24 `e1a3221` docs(om-webserver): 补充 trusted.proxy 示例配置: 补充 whitelist.yml.example 配置示例。（来源：https://github.com/opensourceways/om-webserver/commit/e1a3221）

## deploy
- environment=test; source_repo=https://github.com/opensourceways/om-webserver; note=service.md 有该源码仓映射；已移除测试域名、内部路径、集群、不公开部署细节、不公开部署细节、镜像地址等字段。
- environment=prod; source_repo=https://github.com/opensourceways/om-webserver; note=service.md 有该源码仓映射；已移除敏感及内部部署字段。

## facts_insufficient
当前来源不足，未作推断

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
