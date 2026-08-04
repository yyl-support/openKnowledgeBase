---
tags: [relation, om-webserver]
service: om-webserver
source: https://github.com/opensourceways/om-webserver
source_repo: https://github.com/opensourceways/om-webserver
updated_at: 2026-08-04
---

## connection

- README 明确服务使用 Redis 和 OBS；未在允许来源中确认更细的接口或数据流连接。

## registry_info

- 未记录可公开的 registry YAML 入口。

## evolution

- 2026-07-29 [67ea4fd](https://github.com/opensourceways/om-webserver/commit/67ea4fd) 演进记录：!239 fix(om-webserver): 启用 fastjson/fastjson2 safeMode 修复 CVE 安全漏洞；启用 fastjson/fastjson2 safeMode。。
- 2026-07-29 [216f115](https://github.com/opensourceways/om-webserver/commit/216f115) 演进记录：fix(om-webserver): 启用 fastjson/fastjson2 safeMode 修复 CVE 安全漏洞；在 Dockerfile CMD 增加 JVM safeMode 参数。。
- 2026-07-22 [2461649](https://github.com/opensourceways/om-webserver/commit/2461649) 演进记录：!238 fix(om-webserver): 升级 fastjson2 至 2.0.62 修复 CVE 安全告警；升级 fastjson2。。
- 2026-07-22 [87ab240](https://github.com/opensourceways/om-webserver/commit/87ab240) 演进记录：fix(om-webserver): 升级 fastjson2 至 2.0.62 修复 CVE 安全告警；fastjson2 由 2.0.49 升级至 2.0.62。。
- 2026-07-08 [c474408](https://github.com/opensourceways/om-webserver/commit/c474408) 演进记录：!223 oidc 登录记录登录日志开发实现；OIDC 登录入口增加登录日志需求实现。。
- 2026-07-08 [c89975b](https://github.com/opensourceways/om-webserver/commit/c89975b) 演进记录：fix(om-webserver): 升级 jackson 至 2.18.9 修复 Trivy 安全门禁；统一升级 Jackson BOM。。
- 2026-07-07 [6ec4684](https://github.com/opensourceways/om-webserver/commit/6ec4684) 演进记录：feat(om-webserver): 在 /oidc/auth 登录入口补记登录审计日志；复用 LogUtil.createLoginLogs 记录审计日志。。
- 2026-06-24 [6f65d8e](https://github.com/opensourceways/om-webserver/commit/6f65d8e) 演进记录：!221 IP 频率限制增加白名单需求实现；通过配置文件为 IP 频率限制增加白名单。。
- 2026-06-24 [1e9b832](https://github.com/opensourceways/om-webserver/commit/1e9b832) 演进记录：fix(om-webserver): 修正注释中日期错误；修正注释日期。。
- 2026-06-24 [e1a3221](https://github.com/opensourceways/om-webserver/commit/e1a3221) 演进记录：docs(om-webserver): 补充 trusted.proxy 示例配置；补充 whitelist.yml.example 配置示例。。

## deploy

| 环境 | 公开域名 | 镜像/源码仓 | 部署方式 | 来源 |
| --- | --- | --- | --- | --- |
| test | 未记录 | [om-webserver](https://github.com/opensourceways/om-webserver) | kustomize | infra-common service.md |
| prod | 未记录 | [om-webserver](https://github.com/opensourceways/om-webserver) | helm | infra-common service.md |

## facts_insufficient

- 当前来源未提供具体事实缺口。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
