---
生成时间: 2026-08-10 15:05:06
提取工具: ua
原始页面数: 228
仓库: /tmp/impl-run/ascend-ci-deployment
文档类型: quickstart
---

# ascend-ci-deployment 快速开始指南

## 概述

本仓库是一个 GitOps 部署仓库，用于在华为 Ascend NPU Kubernetes 集群上部署 GitHub Actions Runner Controller (ARC)，为开源 AI/ML 项目提供带 NPU 加速的自托管 CI Runner。

部署通过 ArgoCD 自动同步完成——你提交配置到 Git，ArgoCD 负责将其应用到目标集群。

---

## 1. 安装步骤

### 前置依赖

| 工具 | 用途 | 最低版本 |
|------|------|----------|
| kubectl | Kubernetes 集群管理 | 1.24+ |
| Helm | Chart 部署 | 3.x |
| ArgoCD | GitOps 持续部署 | 2.x |
| Git | 版本控制 | 2.x |
| Python 3 | 运行校验脚本 | 3.8+ |
| yamllint | YAML 格式检查 | - |

### 克隆仓库

```bash
git clone <repository-url> ascend-ci-deployment
cd ascend-ci-deployment
```

### 安装 Python 测试依赖（可选，用于本地校验）

```bash
pip install pyyaml pytest
```

### 确认集群连接

```bash
kubectl cluster-info
helm version
argocd version
```

---

## 2. 配置说明

### 核心配置结构

参考 `README.md`，仓库目录结构如下：

| 目录 | 作用 |
|------|------|
| `projects/` | 各开源项目的 Runner Scale Set 配置 |
| `other/` | 其他项目的 Runner 配置 |
| `argocd/controllers/` | ARC 控制器的 ArgoCD Application |
| `argocd/clusters/` | 集群基础设施组件的 ArgoCD Application |
| `manifests/` | Helm Chart 和 Kubernetes 原生清单 |
| `monitoring/` | 监控栈（Prometheus、探测 CronJob） |

### 必需的配置项

#### Runner 项目配置（以 `projects/Ascend/pytorch/linux-aarch64-a3-16/values.yaml` 为例）

关键字段：

```yaml
gha-runner-scale-set:
  githubConfigUrl: "https://github.com/<org>/<repo>"  # Runner 注册的目标仓库
  runnerScaleSetName: "linux-aarch64-a3-16"           # Runner 标签名称
  containerMode:
    type: "kubernetes"                                 # 容器运行模式
  template:
    spec:
      containers:
        - resources:
            limits:
              huawei.com/Ascend1980: "16"              # NPU 资源数量
```

#### Chart 依赖声明（`projects/<org>/<repo>/<runner>/Chart.yaml`）

```yaml
apiVersion: v2
name: <runner-name>
version: 0.1.0
dependencies:
  - name: gha-runner-scale-set
    version: "0.12.0"                                  # ARC chart 版本
    repository: "file://../../../manifests/arc-runner-scale-set"
```

### 环境变量 / Secrets

本仓库不直接使用环境变量文件。敏感信息通过以下方式管理：

- **Vault Agent Injector**：NPU Exporter 等组件通过 Pod annotation `vault.hashicorp.com/*` 注入密钥（参考 `manifests/custom-npu-exporter/aiframework-hb3/deployment.yaml`）
- **SecretDefinition CRD**：声明式从 Vault 读取凭据（参考 `monitoring/base/pushgateway-secret.yaml`、`monitoring/base/cloud-aksk-secret.yaml`）
- **ArgoCD 密钥管理**：GitHub PAT 等通过 ArgoCD 的 Secret 管理功能配置

---

## 3. 运行方法

### 方式一：GitOps 自动部署（推荐）

这是本仓库的标准工作流程。所有配置变更合入 `main` 分支后，ArgoCD 自动同步到对应集群。

#### 步骤 1：部署 ARC 控制器

将控制器 Application 应用到 ArgoCD：

```bash
kubectl apply -f argocd/controllers/arc-controller-cn12-001.yaml
kubectl apply -f argocd/controllers/arc-controller-guiyang-005.yaml
```

这会在目标集群的 `arc-systems` 命名空间部署 ARC 控制器（参考 `argocd/controllers/arc-controller-cn12-001.yaml`）。

#### 步骤 2：部署集群基础设施

```bash
kubectl apply -f argocd/clusters/openmerlin-guiyang-006/custom-npu-exporter.yaml
kubectl apply -f argocd/clusters/openmerlin-guiyang-006/argus.yaml
kubectl apply -f argocd/clusters/openmerlin-guiyang-006/buildkitd-server.yaml
```

#### 步骤 3：部署项目 Runner

```bash
kubectl apply -f argocd/clusters/openmerlin-guiyang-006/ascend-gha-runners/vllm-ascend/config.yaml
kubectl apply -f argocd/clusters/openmerlin-guiyang-006/ascend-gha-runners/vllm-ascend/linux-aarch64-a3-x.yaml
```

### 方式二：手动 Helm 部署（调试用）

参考 `script.sh`：

```bash
# 设置变量
ORG="Ascend"
REPO="pytorch"
INSTALL_NAME="linux-aarch64-a3-16"

# 创建命名空间
kubectl create namespace "${ORG}-${REPO}" --dry-run=client -o yaml | kubectl apply -f -

# 部署 runner scale set
helm upgrade --install "${INSTALL_NAME}" \
  ./projects/${ORG}/${REPO}/${INSTALL_NAME} \
  --namespace "${ORG}-${REPO}" \
  --create-namespace
```

### 新增一个项目 Runner

参考 `README.md` 中的部署步骤和 `CLAUDE.md` 中的命名规范：

1. 创建项目目录：

```bash
mkdir -p projects/<org>/<repo>/<runner-label>
```

2. 创建 `Chart.yaml`：

```yaml
apiVersion: v2
name: <runner-label>
version: 0.1.0
dependencies:
  - name: gha-runner-scale-set
    version: "0.12.0"
    repository: "file://../../../../manifests/arc-runner-scale-set"
```

3. 创建 `values.yaml`（按需调整 NPU 数量、镜像等）

4. 创建对应的 ArgoCD Application YAML 放入 `argocd/clusters/<cluster>/`

5. 提交 PR，CI 通过后合入 `main`

---

## 4. 验证方法

### 验证 ARC 控制器运行状态

```bash
kubectl get pods -n arc-systems
kubectl get deployment -n arc-systems
```

### 验证 Runner Scale Set 注册

```bash
kubectl get ephemeralrunners -A
kubectl get autoscalingrunnersets -A
```

### 验证 ArgoCD 同步状态

```bash
argocd app list | grep arc-controller
argocd app get <app-name>
```

期望状态为 `Synced` 和 `Healthy`。

### 验证 GitHub 端 Runner 注册

在目标 GitHub 仓库的 `Settings > Actions > Runners` 页面确认 runner 出现。

### 运行本地 CI 校验

```bash
# YAML 格式检查
yamllint -c .yamllint .

# ArgoCD Application 规范校验
bash scripts/argocd-app-lint.sh

# 项目覆盖率检查
python scripts/check-projects-coverage.py

# 单元测试
pytest tests/
```

### 验证监控组件

```bash
kubectl get pods -n monitoring
kubectl get cronjobs -n monitoring
```

---

## 5. 常见问题

### Q: Helm dependency 报错找不到 chart

确保 `Chart.yaml` 中 `repository` 字段的相对路径正确指向 `manifests/` 下对应的 chart 目录。路径深度取决于项目目录层级。

```bash
# 更新依赖
helm dependency update projects/<org>/<repo>/<runner>/
```

### Q: ArgoCD Application 一直显示 OutOfSync

检查：
- `spec.source.path` 是否与实际目录路径一致（参考 `scripts/argocd-app-lint.sh` 中的 r4/r5 规则）
- `spec.destination.namespace` 是否存在
- syncPolicy 是否开启了 `automated`

### Q: Runner Pod 无法调度（Pending）

NPU 资源不足或调度器未就绪：

```bash
kubectl describe pod <runner-pod> -n <namespace>
# 检查 Events 中的调度失败原因

# 确认 NPU 资源可用
kubectl get nodes -o custom-columns=NAME:.metadata.name,NPU:.status.allocatable."huawei\.com/Ascend1980"
```

### Q: CI Lint 检查失败

参考 `docs/ci-checks.md`：
- **yamllint 失败**：按照 `.yamllint` 配置修正格式（行长 200、缩进 2 空格）
- **argocd-app-lint 失败**：确认 Application 名称与 source path 对应关系一致
- **projects-coverage 失败**：新增的 `projects/` 目录需要有对应的 ArgoCD Application 引用

### Q: 镜像拉取失败

本仓库使用内部镜像仓库。镜像同步由 `.github/workflows/sync-images.yml` 定时执行。如果新版本镜像未同步：

```bash
# 手动触发镜像同步 workflow
gh workflow run sync-images.yml
```

### Q: 如何确认命名规范

参考 `CLAUDE.md`：
- 命名空间：`<org>-<repo>`（小写，连字符分隔）
- Runner 目录：`linux-<arch>-<accelerator>-<count>`
- ArgoCD Application 名称需与 source path 末端目录对应

### Q: 多集群部署如何选择目标集群

每个集群在 ArgoCD 中注册为 destination，通过 Application 的 `spec.destination.name` 指定：

```yaml
spec:
  destination:
    name: openmerlin-guiyang-006-cluster  # 集群注册名
    namespace: arc-systems
```

可用集群参考 `argocd/controllers/` 下已有的 Application 文件名。