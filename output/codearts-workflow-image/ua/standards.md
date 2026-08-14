# codearts-workflow-image 项目规范

## 1. 命名规范

| 对象 | 规则 | 示例 | 来源 |
|------|------|------|------|
| Kubernetes namespace | 通过 `GetNamespaceFromRepoName` 将仓库名转小写后匹配关键字，映射到 17 个预定义常量之一，无匹配时默认 `argo` | `ascend-op-plugin` → `OpPluginNamespace`<br>`ascend-recsdk` → `RecsdkNamespace`<br>其他 → `argo` | `go/cmd/common/namespace/namespace.go` |
| 测试用例目录 | 每个测试用例必须包含 4 个文件：`env.sh`, `expected.yaml`, `shell.sh`, `workflow_templatev2.yaml` | `go/cmd/converter/case/newtest/*/` | `AGENTS.md` |
| 单元测试文件 | 每个新函数必须在同一 package 下有对应 `*_test.go` | `convert_script_to_volcano.go` → `convert_script_to_volcano_test.go` | `AGENTS.md` |
| Go module | `github.com/opensourceways/codearts-workflow-image-go` | - | `go/go.mod` |
| Docker 构建产物 | `convert_to_yaml`, `kubeconfig`, `submit` 三个二进制文件 | `RUN CGO_ENABLED=0 go build -o convert_to_yaml ./cmd/converter` | `Dockerfile` |

## 2. 安全要求

| 类别 | 要求 | 来源 |
|------|------|------|
| 构建安全 | 禁用 CGO (`CGO_ENABLED=0`)，避免引入 C 依赖的安全风险 | `Dockerfile` 第 7 行 |
| 密钥管理 | 环境变量过滤函数 `isConfigEnv()`, `isSystemEnv()` 用于识别敏感配置 | `AGENTS.md` |
| 输出隔离 | 敏感信息通过 `workflow-secret.yaml` 单独生成，不混入主 workflow.yaml | `AGENTS.md` |
| 运行时权限 | Alpine 基础镜像 (3.18) 最小化攻击面 | `Dockerfile` 第 11 行 |

## 3. DFX 要求

### 可靠性

| 项目 | 要求 | 来源 |
|------|------|------|
| 信号处理 | `BASH_ENV=/usr/local/bin/signal_forward.sh` 启用信号转发，容器收到 SIGTERM 时通过 `pkill -P 1` 优雅终止子进程 | `Dockerfile` 第 38、41 行 |
| 构建隔离 | 多阶段构建，编译阶段 (`golang:1.24-alpine`) 与运行时阶段 (`alpine:3.18`) 分离 | `Dockerfile` 第 1、11 行 |

### 可维护性

| 项目 | 要求 | 来源 |
|------|------|------|
| 测试覆盖率 | 路径覆盖率必须 > 90% | `AGENTS.md` |
| 单元测试命令 | `cd go/cmd/converter && go test -cover ./...` | `AGENTS.md` |
| E2E 测试命令 | `cd go/cmd/converter && go test -v -run Test_main` | `AGENTS.md` |
| Volcano Job 测试 | `skill submit-test -k <kubeconfig> -t all` | `AGENTS.md` |
| Lint 工具 | golangci-lint，超时 5 分钟，启用 12 个 linter（errcheck, gosimple, govet, ineffassign, staticcheck, unused, gofmt, goimports, misspell, unconvert, unparam, gocyclo, gocritic） | `.golangci.yml` |
| 圈复杂度限制 | gocyclo.min-complexity: 20 | `.golangci.yml` |
| CI 检查脚本 | `.ci/typos.sh`, `.ci/golangci-lint.sh` | `AGENTS.md` |
| 错误检查 | errcheck.check-type-assertions: true<br>errcheck.check-blank: true | `.golangci.yml` |
| 测试文件豁免 | `*_test.go` 文件豁免 errcheck, gocyclo, gosec 检查 | `.golangci.yml` |

### 可观测性

| 项目 | 要求 | 来源 |
|------|------|------|
| 错误日志 | 未见相关规定 | - |
| 监控指标 | 未见相关规定 | - |
| 链路追踪 | 未见相关规定 | - |

## 4. 当前风险点

1. **构建目标与实际部署不一致**（`Dockerfile` 第 8 行，`go/cmd/oldkubeconfig/main.go` vs `go/cmd/kubeconfig/main.go`）
   - 现状：Dockerfile 编译的 `kubeconfig` 二进制来自 `./cmd/oldkubeconfig`（46 行，仅查找 kubeconfig.key 文件），但仓库中存在功能更完整的 `go/cmd/kubeconfig/main.go`（373 行，包含 NPU 集群选择逻辑 SelectCluster/QueryCluster/NPUQuerier），后者未被构建或调用
   - 影响：若有代码变更错误修改了 `go/cmd/kubeconfig/main.go`，实际运行的容器不会体现这些修改；NPU 集群选择功能处于休眠状态

2. **命名空间映射函数的实现与描述不符**（`go/cmd/common/namespace/namespace.go` 第 36-99 行）
   - 现状：`GetNamespaceFromRepoName` 仅执行小写转换和关键字匹配，无字符净化或正则替换逻辑，但函数文档或历史注释可能暗示存在 k8s 命名规则清洗
   - 影响：开发者依据函数名或注释预期会进行字符过滤（如 `_`、`.`、`/` 等非法字符），但实际不会，若仓库名包含 k8s 不兼容字符且未命中 17 个关键字，将直接使用默认 namespace `argo`，可能导致资源冲突或分配错误

3. **Go 版本依赖**（`go/go.mod` 第 3 行）
   - 现状：要求 Go 1.24.2，该版本为未来版本（当前最新稳定版为 1.23.x 系列）
   - 影响：构建环境必须使用特定的 Go 1.24.2 或向后兼容版本，否则编译失败；若 Go 1.24.2 包含破坏性变更，现有代码可能需要适配

4. **Lint 配置对测试文件的豁免**（`.golangci.yml` 第 47-51 行）
   - 现状：`*_test.go` 文件豁免 errcheck, gocyclo, gosec 三个关键 linter
   - 影响：测试代码中的未处理错误、高圈复杂度、安全问题不会被自动检测，可能掩盖测试质量问题或引入测试环境的安全风险

5. **缺少可观测性规范**
   - 现状：输入中未找到关于错误日志格式、监控指标导出、链路追踪的明确规定
   - 影响：服务运行时问题排查依赖人工日志查看，缺乏统一的指标和追踪体系，故障定位困难
