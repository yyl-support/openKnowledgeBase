# ascend-ci-deployment 编码规范

## 1. 命名规范

| 对象 | 规则 | 示例 |
|---|---|---|
| 活跃项目目录 | `projects/{org}/{repo}/` | `projects/vllm-project/vllm-ascend/` |
| 低活跃项目目录 | `other/{org}/{repo}/` | `other/Ascend/Ascend-CI/` |
| 单 runner 项目的 org | 直接放 `other/{org}/`，不再套 repo 层 | `other/ascend-gha-runners/` |
| 监控配置 | 永远在顶层 `monitoring/`，不进 `projects/` 或 `other/` | `monitoring/prometheus/` |
| 命名空间 | `{org-lower}-{repo-lower}` 全小写 | `alibaba/ROLL` → `alibaba-roll` |
| 命名空间（已有项目） | 保持现有命名，不重命名 | `vllm-project/vllm-ascend` → `vllm-project` |
| Runner 目录（ARC < 0.14.0） | `linux-{arch}-{npu}-{count}` | `linux-aarch64-a3-2` |
| Runner 目录（ARC >= 0.14.0） | `linux-{arch}-{npu}-{count}-{cluster_suffix}` | `linux-aarch64-a3-2-gy005` |
| config 目录 | 三种变体并存，规则是**匹配该项目已有约定**，不强制统一 | `config/`、`config-hk001/`、`config-for-guiyang-005/` |
| ARC 控制器 Application | `argocd/controllers/arc-controller-{cluster}.yaml` | `arc-controller-cn12-001.yaml` |
| Chart 依赖来源 | 官方 `oci://ghcr.io/...` 或 NJU 镜像 `oci://ghcr.nju.edu.cn/...` | — |

### ArgoCD Application 硬性要求

| 要求 | 适用对象 |
|---|---|
| `syncOptions: [CreateNamespace=true]` | Config Application |
| 显式指定 `spec.source.helm.releaseName` | Runner Application |
| `automated.prune: true` | 所有 Application |
| `source.path` 必须对应真实目录 | 所有 Application |
| 多个 runner 可合并一个文件，用 `---` 分隔 | Runner Application |

### ARC >= 0.14.0 附加要求

| 字段 | 要求 |
|---|---|
| `gha-runner-scale-set.scaleSetLabels` | 必须 2 个标签：capability label + cluster label |
| `resourceMeta.ephemeralRunnerSet.annotations` | 必须标注 `actions.github.com/job-cpu`、`job-memory`、`job-npu` |
| 控制器镜像 | 固定 `swr.cn-southwest-2.myhuaweicloud.com/modelfoundry/gha-runner-scale-set-controller:0.14.201`，通过 Application inline helm values 注入 |

### YAML 格式

`.yamllint` 基于 `extends: default`，关键调整：`line-length.max: 200`、`indentation.spaces: 2`、`indent-sequences: true`、`empty-lines.max: 1`、`document-start: disable`、`truthy.allowed-values: ['true', 'false', 'on', 'off']`。忽略 `manifests/*/templates/`、`manifests/liqo/liqo-*/`、`manifests/karmada-operator/` 等渲染目录。

## 2. 安全要求

| 项 | 规定 |
|---|---|
| 密钥存储 | 禁止明文入库。通过 `secrets-manager.tuenti.io/v1alpha1` 的 `SecretDefinition` 声明 Vault 路径，由 secret-manager 拉取（全仓 96 处） |
| 密钥引用方式 | `SecretDefinition.spec.keysMap` 指定 Vault 的 `path` 与 `key`，仓库内不出现凭据值 |
| 泄露扫描 | `.gitleaksignore` 维护扫描例外（54 行） |
| RBAC 粒度 | 优先 namespace 级 `Role`（93 处），`ClusterRole` 仅用于控制器等必需场景（22 处） |
| runner pod 权限 | 由各项目 `runner-pod-permission.yaml` 定义 ServiceAccount / Role / RoleBinding，限定为管理 ephemeral pod、读取 secret、管理 Job |
| 分支保护 | 默认分支必须经 PR 合入，禁止直接 push |
| PR 追溯 | PR body 必须含独立一行 `resolve <issue URL>` |
| 镜像来源 | 内网环境统一从华为 SWR 拉取，通过 `sync-images.yml` 每日同步 |

## 3. DFX 要求

| 维度 | 规定 |
|---|---|
| 可观测性 | `monitoring/` 提供 Prometheus + Alertmanager + kube-state-metrics + node-exporter + pushgateway；Prometheus 用基于文件的服务发现跨集群抓取，关闭本地集群监控组件 |
| 告警 | Alertmanager 已部署，具体告警规则见各集群 `monitoring/config-for-{cluster}/prometheus-rules.yaml` |
| 配置一致性 | 四道 CI 门禁：`yamllint`（格式）、`argocd-app-lint.sh`（Application 结构）、`check-projects-coverage.py`（新项目是否有对应 Application 与文档条目）、`check-scale-set-labels`（标签变更提醒） |
| 变更可追溯 | GitOps 模式，所有变更经 PR；`automated.prune: true` 保证集群状态与仓库一致 |
| 文档同步 | `projects/` 或 `argocd/` 变更时自动触发文档仓刷新 |
| 高可用 | **未见相关规定**。Prometheus 与 Alertmanager 当前为单副本，见风险点 2 |
| 资源限制 | **未见相关规定**。ARC 控制器 chart 未配置 limits/requests，见风险点 1 |
| 容量规划 | **未见相关规定** |
| 日志采集 | **未见相关规定** |

## 4. 当前风险点

1. **ARC 控制器无资源限制。** `manifests/arc-controller-0.13.0/`、`0.13.1/`、`0.14.2/`、`for-cpu-node/` 四个版本的 `values.yaml` 全部是 `resources: {}`，limits/requests 整块被注释。控制器异常时可能无上限占用节点资源，或在节点压力下被优先驱逐，影响该集群全部 runner 的调度。

2. **监控自身无高可用。** `monitoring/prometheus/values.yaml` 中 Prometheus 与 Alertmanager 的 `replicas` 均为 1，跨节点反亲和性配置被注释，注释写明「正式上线时恢复 replicas: 2」。承载监控的节点故障即失去全部可观测性与告警能力。

3. **103 个 runner chart 的 `name` 与所在目录名不一致。** 占 329 个 runner chart 的 31%。其中 14 个是 `arrch64` 拼写错误（如 `projects/vllm-project/vllm-ascend/linux-aarch64-a3-2/Chart.yaml` 写 `name: linux-arrch64-a3-2`），其余是型号错配（如 `projects/Ascend/sglang/linux-aarch64-a2b3-1/Chart.yaml` 写 `name: linux-aarch64-a2-1`）。因 Application 显式指定 `releaseName`，**不影响实际部署**，但按 chart name 检索会找错目录，复制目录时会继承错误的 name。

4. **CLAUDE.md 的存储类描述与实际相反。** 文档称 `csi-sfsturbo` 为大多数集群使用、`sfsturbo-subpath-sc` 仅用于 gy-006 / cn12-001 / hk-ci。实际 `sfsturbo-subpath-sc` 被 304 个文件引用、覆盖 gy-001 / gy-004 / gy-005 / gy-006 / hk-001 / hk-ci / cn12-001 等集群，是使用最广泛的存储类；`csi-sfsturbo` 仅 99 个文件引用。按文档选存储类会选错。

5. **`argocd-app-lint.sh` 规则编号不连续。** 脚本定义 `r1_check`、`r2_check`、`r4_check`、`r5_check`、`r6_check`、`r7_check` 六个函数，不存在 `r3_check`。新增规则时若按「下一个编号」推断会与 `docs/ci-checks.md` 的规则对应关系错位。

6. **config 目录三种命名变体并存。** `config/`、`config-{cluster}/`、`config-for-{cluster}/` 同时存在，规范明确接受这种不一致（要求「匹配已有约定」）。新增集群配置时必须先查看该项目现有目录才能确定用哪种，无法从规范直接推断。

7. **根目录 `script.sh` 为孤立脚本。** 未被任何 CI 工作流引用，`README.md` 全文未提及。用途与是否仍需保留无从判断。
