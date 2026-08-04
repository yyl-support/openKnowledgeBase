---
tags: [relation, software-package-all]
service: software-package-all
source: https://github.com/opensourceways/software-package-all
updated_at: 2026-08-04
---

## connection
- {'prod_url': 'https://software-pkg.openeuler.org', 'implement_ref': 'main'}

## evolution
当前来源不足，未作推断

## deploy
- source_repo=https://github.com/opensourceways/autoupgrade; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/autoupgrade-conda; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/easysoftware-server-deployment; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/easysoftware-website-deployment; environment=prod; domain=easysoftware.openeuler.org; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/easysoftware-website-openatom-deployment; environment=prod; domain=easysoftware.openeuler.org; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/input; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/input-archnum; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware-cn4; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/input-epkg; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware-cn4; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/input-externalos; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/input-field-domain; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware-cn4; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/input-oepkg; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware-cn4; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/input-rpm; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware-cn4; archive_mode=kustomize
- source_repo=https://github.com/opensourceways/input-srcrepo; environment=prod; archive_repo=https://github.com/opensourceways/infra-openeuler; archive_path=applications/easysoftware; archive_mode=kustomize

## facts_insufficient
- GitHub 主源码仓当前返回 404，未取得 README、目录树、Dockerfile 或主仓最近 10 条 commit/issue。
- service.md 未找到软件包平台主仓本身的匹配行；deploy 仅采用能够按源码仓直接匹配的 EasySoftware 子仓记录。
- service 注册中记录 EasySoftware-autorepair 构建脚本路径为空，且 easysoftware-autoupgrade、software-package-gateway、software-package-github-server、software-package-server、software-package-website 未自动填充测试部署目标。

导航：[`README`](../../../../README.md) · [`org-overview`](../../../org-overview.md) · [`service-map`](../../../service-map.md) · [`source-registry`](../../../source-registry.md)
