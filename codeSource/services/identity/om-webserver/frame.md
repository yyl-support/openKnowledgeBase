---
tags: [identity, om-webserver]
service: om-webserver
source: https://github.com/opensourceways/om-webserver
source_repo: https://github.com/opensourceways/om-webserver
updated_at: 2026-08-04
---

## summary
OM-Webserver 是提供账号管理能力的独立服务，README 记录 Spring Boot、Redis 和 OBS 技术栈，支持 Maven 构建运行或 Docker 构建运行。

## infrastructure
- 仓库目录包含 src、pom.xml、Dockerfile、.mvn 和 Maven/Java 工程配置。
- 本地 service 注册标明源码分支为 master；其 release 段明确是模板占位且未在 service.md 注册。

## components

| name | role |
| --- | --- |
| om-webserver | 账号管理后端 |
| Redis | 缓存或数据依赖 |
| OBS | 对象存储依赖 |

## 源码

- 注册主仓：[om-webserver](https://github.com/opensourceways/om-webserver)
- 无已核验子仓记录。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
