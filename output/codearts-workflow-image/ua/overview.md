# codearts-workflow-image 项目总览

## 1. 职责

本项目是一个容器镜像的源码仓库，负责把工作流描述（脚本 + 环境变量 + 模板）转换成
Volcano Job CRD，并提交到 Kubernetes 集群运行、监控直至完成。

具体来说，它解决两个问题：

1. **格式转换**：把上游产出的 `shell.sh`、`env.sh`、`workflow_templatev2.yaml`
   转换成 Kubernetes 可识别的 `workflow.yaml`（Volcano Job CRD）以及可选的
   `workflow-secret.yaml`（`AGENTS.md`）。转换过程中还要完成资源规格换算
   （CPU/内存/NPU 芯片，`go/cmd/common/run_on_parser.go`、
   `go/cmd/converter/package/job_resource.go`）、敏感信息过滤
   （`go/cmd/converter/package/secret_filter.go`）、数据集 PVC 映射
   （`go/cmd/converter/package/dataset_manager.go`）、调度队列与亲和性规则生成
   （`go/cmd/converter/package/queue_manager.go`、
   `go/cmd/converter/package/affinity_manager.go`）等一系列附加处理。
2. **提交与运行监控**：把生成的 CRD 提交给集群，等待 Pod 调度、跟随日志输出，
   并在结束后上报退出状态（`go/cmd/submit/main.go`）。

容器本身以 `src/entrypoint.sh` 为入口，串联「渲染模板 → 转换 → 提交」全过程
（`Dockerfile`）。

## 2. 定位

本项目产出的是一个**执行侧容器镜像**，在更大的 CI/CD 工作流系统中处于「工作流
被调度到集群后，真正执行转换与提交动作」的一环。

- **上游**：负责生成 `shell.sh`、`env.sh`、`workflow_templatev2.yaml` 等输入文件
  的工作流编排系统。这些输入文件的具体生成逻辑不在本仓库范围内，仅是
  `AGENTS.md` 中列出的既定输入格式。
- **本项目**：以上述文件为输入，在容器内完成「转换为 Volcano Job CRD → 提交
  → 监控 → 回收制品/日志」的闭环（`src/entrypoint.sh`、`src/unit.sh`、
  `go/cmd/converter/`、`go/cmd/submit/`）。
- **下游**：真正运行工作负载的 Kubernetes 集群，调度器为 Volcano
  （`configs/queues/`、`configs/propagation-policies/`），部分场景通过 Karmada
  做多集群资源绑定与 PVC 定位（`go/cmd/common/pvccluster/pvc_cluster.go`）。
  与集群的交互通过 `kubectl`（从 `https://dl.k8s.io/release/stable.txt` 下载，
  `Dockerfile`）完成。

## 3. 边界

以下事项**不属于**本项目职责：

| 看起来相关的事 | 实际归属 |
|---|---|
| 生成 `shell.sh`/`env.sh`/`workflow_templatev2.yaml` 的编排逻辑 | 上游工作流系统，本仓库只消费这些文件（`AGENTS.md`） |
| Volcano/Karmada 调度器本身的调度算法 | 集群侧组件，本项目只提交 CRD 和读取状态，不实现调度逻辑 |
| 镜像拉取源（SWR）、kubectl 发行包 | 外部基础设施，本项目仅在 `Dockerfile` 中声明依赖来源 |
| NPU 集群选择逻辑（`go/cmd/kubeconfig/main.go`，373 行，含 `SelectCluster`/`QueryCluster`/`NPUQuerier`） | 存在于仓库中，但 `Dockerfile` 实际构建并装入镜像的 `kubeconfig` 二进制来自 `go/cmd/oldkubeconfig/main.go`（46 行，仅按文件名查找 kubeconfig.key）。前者未被构建流程引用，当前与镜像功能脱节 |
| 仓库名到命名空间的「合法字符清洗」 | `go/cmd/common/namespace/namespace.go` 的 `GetNamespaceFromRepoName` 实际只做小写化 + 关键字子串匹配，映射到 17 个硬编码命名空间常量之一，兜底为 `argo`；不做任何字符过滤或清洗 |

## 4. 核心能力

| 能力 | 承载模块 |
|---|---|
| 工作流转换入口（读取模板/脚本/环境变量并编排整个转换流程） | `go/cmd/converter/convertv2_to_yaml.go` |
| 脚本转 Volcano Job CRD 核心逻辑 | `go/cmd/converter/package/convert_script_to_volcano.go` |
| 控制面配置解析（超时、工件设置、镜像代理、共享内存等） | `go/cmd/converter/package/cp_config.go` |
| 脚本生成编排（Git clone、BCR 镜像仓库、delay-exit、制品拷贝脚本组合） | `go/cmd/converter/package/script_handler.go` |
| 敏感环境变量识别与过滤 | `go/cmd/converter/package/secret_filter.go` |
| CPU/内存/NPU 资源请求换算 | `go/cmd/converter/package/job_resource.go`、`go/cmd/common/run_on_parser.go` |
| 数据集仓库到 PVC 的映射（支持组织级/仓库级） | `go/cmd/converter/package/dataset_manager.go` |
| 转换阶段制品拷贝管理 | `go/cmd/converter/package/cp_artifact_manager.go` |
| 心跳 sidecar 管理 | `go/cmd/converter/package/heartbeat_manager.go` |
| 按 NPU 芯片需求生成 Pod 亲和性规则 | `go/cmd/converter/package/affinity_manager.go` |
| Volcano 调度队列选择 | `go/cmd/converter/package/queue_manager.go` |
| 镜像代理地址前缀应用 | `go/cmd/converter/package/image_proxy_manager.go` |
| Job 提交、等待调度、日志跟随、状态上报（CLI 主流程） | `go/cmd/submit/main.go` |
| 提交前资源可用性与集群约束校验 | `go/cmd/submit/presubmit.go` |
| 已提交 Job 的运行时补丁 | `go/cmd/submit/patch.go` |
| 带重连重试的 Pod 日志跟随 | `go/cmd/submit/logs.go` |
| 提交阶段制品拷贝协调 | `go/cmd/submit/copy_artifact_manager.go` |
| Karmada 多集群 PVC 定位与 Job 标签补丁 | `go/cmd/common/pvccluster/pvc_cluster.go` |
| 仓库名到命名空间的关键字映射 | `go/cmd/common/namespace/namespace.go` |
| kubeconfig 密钥文件查找（实际构建装入镜像的版本） | `go/cmd/oldkubeconfig/main.go` |
| 容器入口与信号转发（渲染模板、拼装提交参数、exec 提交程序） | `src/entrypoint.sh`、`Dockerfile`（`signal_forward.sh`） |
| 主工作流执行脚本（渲染模板、Argo 提交、等待主脚本 Pod、拷贝制品） | `src/unit.sh` |
