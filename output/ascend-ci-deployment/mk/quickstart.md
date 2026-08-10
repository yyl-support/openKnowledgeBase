---
生成时间: 2026-08-10 17:52:12
提取工具: mk
原始页面数: 579
仓库: /tmp/impl-run/ascend-ci-deployment
文档类型: quickstart
---

# ascend-ci-deployment 快速开始指南

## 概述

`ascend-ci-deployment` 是一个基础设施即代码（IaC）仓库，用于在配备华为 Ascend NPU 芯片的 Kubernetes 集群上部署 GitHub Actions Runner Controller (ARC)，实现自托管 CI runner 的自动化管理。部署通过 ArgoCD GitOps 模型驱动。

---

## 1. 安装步骤

### 1.1 前置依赖

| 工具 | 版本要求 | 用途 |
|------|----------|------|
| Kubernetes 集群 | 1.16+ | 运行平台 |
| Helm | v3+ | Chart 部署 |
| kubectl | 与集群版本匹配 | 集群操作 |
| ArgoCD | — | GitOps 持续部署 |
| Python | 3.12 | CI lint 脚本 |
| Git | — | 仓库操作 |

### 1.2 克隆仓库

```bash
git clone https://github.com/opensourceways/ascend-ci-deployment.git
cd ascend-ci-deployment
```

### 1.3 安装 CI lint 依赖（开发/贡献者）

```bash
pip install pyyaml yamllint
```

---

## 2. 配置说明

### 2.1 仓库目录结构

> 参考：`wiki/sources/ascend-ci-deployment-readme.md`、`wiki/concepts/ci-project-tiering.md`

| 目录 | 职责 |
|------|------|
| `projects/{org}/{repo}/` | 活跃 CI 项目 runner 配置 |
| `other/{org}/{repo}/` | 维护期/低活跃项目 runner 配置 |
| `manifests/` | 共享基础设施（ARC controller、Vault、Prometheus 等） |
| `argocd/controllers/` | 每集群一个 ARC controller Application |
| `argocd/clusters/{cluster}/` | 每集群的 runner Application 定义 |
| `monitoring/` | 集群监控栈配置 |

### 2.2 ARC 版本选择

> 参考：`wiki/concepts/arc-版本分界规范.md`

| ARC 版本 | Controller 目录 | Chart 来源 |
|----------|----------------|------------|
| < 0.14.0（0.12.x/0.13.x） | `manifests/arc-controller-0.13.1/` | `oci://ghcr.nju.edu.cn/actions/actions-runner-controller-charts` |
| ≥ 0.14.0 | `manifests/arc-controller-0.14.2/` | `oci://ghcr.io/actions/actions-runner-controller-charts` |

### 2.3 存储类分配

> 参考：`wiki/concepts/存储类分配规范.md`

| 存储类 | 适用集群 |
|--------|----------|
| `csi-sfsturbo` | gy-003、gy-004、gy-005、hb-003 等 |
| `sfsturbo-subpath-sc` | gy-006、cn12-001、hk-ci |

### 2.4 命名空间命名规范

> 参考：`wiki/concepts/命名空间命名规范.md`

- 新项目：`{org-lower}-{repo-lower}`（如 `alibaba-roll`）
- 已有项目：保持现有命名不变

### 2.5 必需的 Secret 配置

GitHub App 凭据需通过 Vault 同步到 Kubernetes Secret：

> 参考：`wiki/concepts/secret-synchronization-flow.md`

```yaml
# SecretDefinition 示例（projects/volcengine/verl-omni/config-for-guiyang-001/github-app-secret.yaml）
apiVersion: secrets-manager.tuenti.io/v1alpha1
kind: SecretDefinition
metadata:
  name: github-app-secret
  namespace: <your-namespace>
spec:
  name: <your-secret-name>
  keysMap:
    github_app_id:
      path: secrets/data/ascend/ci
      key: github_app_id
    github_app_installation_id:
      path: secrets/data/ascend/ci
      key: <your_installation_id_key>
    github_app_private_key:
      path: secrets/data/ascend/ci
      key: github_app_private_key
```

运维团队需在 Vault 中配置对应路径的凭据。

---

## 3. 运行方法

### 3.1 部署 ARC Controller（GitOps 方式）

ARC controller 通过 ArgoCD Application 自动部署。每个集群对应一个 Application 文件：

> 参考：`wiki/concepts/argocd-application-per-controller-deployment-pattern.md`

```yaml
# argocd/controllers/arc-controller-guiyang-005.yaml 示例
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: arc-controller-guiyang-005
  namespace: argocd
spec:
  destination:
    namespace: arc-systems
    name: openmerlin-guiyang-005-cluster
  project: openmerlin-guiyang-005-cluster
  source:
    helm:
      releaseName: arc
    path: manifests/arc-controller-0.14.2
    repoURL: https://github.com/opensourceways/ascend-ci-deployment.git
    targetRevision: HEAD
  syncPolicy:
    automated:
      prune: true
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
```

### 3.2 手动部署 Runner Scale Set（命令式方式）

> 参考：`wiki/concepts/arc-runner-scale-set-手动部署流程.md`、`wiki/sources/script-sh.md`

```bash
# 1. 设置参数
ORGANIZATION="your-org"
REPOSITORY="your-repo"
INSTALLATION_NAME="linux-aarch64-a2-4"
NAMESPACE="${ORGANIZATION}"

# 2. 创建命名空间
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# 3. 安装配置 chart（PVC、ConfigMap 等）
helm upgrade --install "${INSTALLATION_NAME}-config" \
  ./${ORGANIZATION}/${REPOSITORY}/${INSTALLATION_NAME}/arc-config \
  -f ./${ORGANIZATION}/${REPOSITORY}/${INSTALLATION_NAME}/values.yaml \
  -n "${NAMESPACE}"

# 4. 生成 runner-scale-set values
helm template "${INSTALLATION_NAME}" \
  ./${ORGANIZATION}/${REPOSITORY}/${INSTALLATION_NAME}/arc \
  --show-only templates/runner-scale-set-values.yaml.gotemp \
  > ./runner-scale-set-values.yaml

# 5. 安装 runner scale set
helm upgrade --install "${INSTALLATION_NAME}" \
  oci://ghcr.nju.edu.cn/actions/actions-runner-controller-charts/gha-runner-scale-set \
  --version=0.13.1 \
  -f ./runner-scale-set-values.yaml \
  -n "${NAMESPACE}"
```

### 3.3 使用 arc-deploy Skill 自动生成配置

> 参考：`wiki/entities/arc-deploy-skill.md`、`wiki/concepts/arc-deploy-json-配置-schema.md`

准备 JSON 配置文件：

```json
{
  "project": {
    "name": "my-org-my-project",
    "github_config_url": "https://github.com/my-org/my-project",
    "github_config_secret": "my-org-my-project-secret",
    "namespace": "my-org-my-project",
    "config_dir": "config"
  },
  "cluster": {
    "name": "cn12-001",
    "region": "cn-north-12",
    "scheduler": "volcano"
  },
  "runner": {
    "label": "linux-aarch64-a3-8",
    "arch": "aarch64",
    "npu_model": "ascend-1980",
    "npu_count": "8",
    "cpu": "128",
    "memory": "512Gi",
    "min_runners": 0,
    "max_runners": 3
  },
  "storage": {
    "type": "sfsturbo",
    "pvc_name": "my-org-my-project-cn12-001",
    "storage_size": "100Gi",
    "storage_class": "csi-sfsturbo",
    "sfsturbo_share_id": "<your-share-id>"
  },
  "image": {
    "runner": "swr.cn-southwest-2.myhuaweicloud.com/modelfoundry/runner-containers-hooks:release-no_volumes-9c3ea5"
  },
  "advanced": {
    "container_mode": "kubernetes-novolume",
    "prepare_job_timeout": "43200",
    "work_storage_size": "64Gi",
    "work_storage_class": "sfsturbo-subpath-sc"
  }
}
```

生成的文件将输出到 `{project.name}/{project.config_dir}/` 目录。

### 3.4 更新 Helm 依赖

部署前确保 chart 依赖已更新：

```bash
cd projects/<org>/<repo>/<variant>/
helm dependency update
```

---

## 4. 验证方法

### 4.1 验证 ARC Controller 运行状态

```bash
# 检查 controller pod
kubectl get pods -n arc-systems -l app.kubernetes.io/name=gha-rs-controller

# 检查 controller 日志
kubectl logs -n arc-systems -l app.kubernetes.io/name=gha-rs-controller --tail=50
```

### 4.2 验证 Runner Scale Set

```bash
# 检查 runner pods
kubectl get pods -n <namespace> -l app.kubernetes.io/part-of=gha-runner-scale-set

# 检查 AutoscalingRunnerSet CR
kubectl get autoscalingrunnersets -n <namespace>

# 检查 EphemeralRunner 状态
kubectl get ephemeralrunners -n <namespace>
```

### 4.3 验证 ArgoCD 同步状态

```bash
# 检查 Application 同步状态
kubectl get applications -n argocd | grep arc-controller

# 查看同步详情
kubectl get application <app-name> -n argocd -o jsonpath='{.status.sync.status}'
```

### 4.4 验证 NPU 设备就绪

```bash
# 检查节点 NPU 资源
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.allocatable.huawei\.com/ascend-1980}{"\n"}{end}'

# 检查 runner pod 的 NPU 探针日志
kubectl logs <runner-pod> -n <namespace> -c <container> | grep -i npu
```

### 4.5 运行 CI Lint 校验（本地开发）

```bash
# YAML 格式校验
yamllint -c .yamllint <your-changed-files>

# ArgoCD Application lint
bash scripts/argocd-app-lint.sh

# 项目覆盖率检查（需设置环境变量）
export BASE_SHA=<merge-base>
export HEAD_SHA=<head>
export GITHUB_TOKEN=<token>
python3 scripts/check-projects-coverage.py
```

### 4.6 运行测试套件

```bash
# ArgoCD lint 测试
bash tests/test-argocd-app-lint.sh

# Python 脚本单元测试
pip install pytest pyyaml
pytest tests/
```

---

## 5. 常见问题

### Q1: Runner pod 启动后 NPU 检查超时

**症状**：Runner pod 的 postStart hook 报错 `NPU check timed out after 300 seconds`

**原因**：Ascend NPU 驱动未初始化完成，或设备文件 `/dev/davinci_manager` 不存在。

**解决方案**：
- 确认节点上 Ascend 驱动已安装且运行正常：`npu-smi info`
- 检查 device plugin 是否正常注册 NPU 资源：`kubectl describe node <node> | grep ascend`
- 如节点无 NPU 硬件，确认 ConfigMap 中使用了 `davinci_manager` 字符设备守卫变体（`if [ -c "/dev/davinci_manager" ]`），CPU 节点会自动跳过检查

> 参考：`wiki/concepts/npu-readiness-poststart-probe-pattern.md`

### Q2: Helm dependency update 失败

**症状**：`helm dependency update` 无法拉取 OCI chart

**解决方案**：
```bash
# 对于 NJU 镜像站
helm registry login ghcr.nju.edu.cn

# 对于上游 ghcr.io
helm registry login ghcr.io
```

确认网络可达性。如使用 NJU 镜像站（`oci://ghcr.nju.edu.cn/...`），确认 DNS 解析正常。

### Q3: ArgoCD Application 同步失败，报 path 不存在

**症状**：ArgoCD 报 `source.path` 指向的目录不存在

**原因**：项目目录已迁移（如从 `projects/` 迁移到 `other/`），但 ArgoCD Application 的 `source.path` 未更新。

**解决方案**：
- 更新对应 Application YAML 中的 `spec.source.path`
- 确保 PR 通过 `argocd-app-lint` 检查（规则 R1 校验路径存在性）

> 参考：`wiki/concepts/argocd-application-删除与退役流程.md`

### Q4: PVC 无法绑定（Pending 状态）

**原因**：使用了错误的存储类。

**解决方案**：查看目标集群应使用的存储类：
- gy-006、cn12-001、hk-ci 集群：使用 `sfsturbo-subpath-sc`
- 其他集群：使用 `csi-sfsturbo`

> 参考：`wiki/concepts/存储类分配规范.md`

### Q5: Job 准备阶段超时

**症状**：Job 在准备阶段失败，容器镜像拉取或 NPU 初始化未完成。

**解决方案**：增大 `ACTIONS_RUNNER_PREPARE_JOB_TIMEOUT_SECONDS` 环境变量值。观察范围为 21600（6h）至 43200（12h）。

```yaml
env:
  - name: ACTIONS_RUNNER_PREPARE_JOB_TIMEOUT_SECONDS
    value: "43200"
```

> 参考：`wiki/concepts/actions-runner-prepare-job-timeout-seconds.md`

### Q6: PR lint 检查失败

**常见规则失败及修复**：

| 规则 | 失败原因 | 修复 |
|------|----------|------|
| R1 | `source.path` 目录不存在 | 创建目录或修正路径 |
| R2 | path 前缀不合法 | 使用 `projects/`、`other/`、`monitoring/`、`manifests/` 之一 |
| R5 | 缺少 `automated.prune: true` | 添加 syncPolicy 配置 |
| RA | 新目录无对应 ArgoCD Application | 创建 Application YAML |
| RC | Runner 目录名未登记文档 | 联系维护者更新 docs 仓库 |

> 参考：`wiki/concepts/ci-检查规则.md`、`wiki/entities/argocd-app-lint-sh.md`

### Q7: 如何跳过 CI 检查

在 PR 标题中包含 `[skip ci]` 即可跳过所有 lint job。

> 参考：`wiki/sources/github-workflows-ci-lint-yml.md`