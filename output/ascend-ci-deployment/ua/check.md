# 校验记录：ascend-ci-deployment

生成时间：2026-08-11　三方件：raw.json（tool=ua，pages 数 2154）　校验条目数：45　冲突数：6

本记录分两轮：第一轮为规则冲突核验（rule_facts vs raw.json content，K01）；
第二轮为 core 层 19 个文件的结构性核验（源文件实际结构 vs raw.json 对应 page 的
content/metadata.relations，K02-K06）。

## 第一轮：规则冲突核验范围说明

以 preprocess.json 的 rule_facts（来源：CLAUDE.md、AGENTS.md、.yamllint、
.github/workflows/{ci-lint,notify-docs-refresh,notify-superproject,sync-images}.yml、
manifests/arc-controller-0.14.2/Chart.yaml、manifests/liqo/liqo-1.2.0/Chart.yaml，
共 13 条 path 分组的 assertions）逐条与 raw.json 中对应 page 的 content 字段核对，
冲突项在 /tmp/pipeline-val/ascend-ci-deployment 实际执行 Grep/Bash grep/Read 检索验证。

## 校验通过项（无冲突，不逐条展开）

- `.github/workflows/ci-lint.yml`：4 个 job（yamllint、argocd-app-lint、check-projects-coverage、
  check-scale-set-labels），均 `runs-on: linux-amd64-cpu-1`、`container: image: python:3.12`，触发条件
  `pull_request: branches: [main]` 及路径过滤、`if: !contains(title, '[skip ci]')`。经 Read 实际文件
  `/tmp/pipeline-val/ascend-ci-deployment/.github/workflows/ci-lint.yml` 逐字核对一致。
- `.yamllint`：extends default、line-length max 200、indentation spaces 2/indent-sequences true、
  truthy.allowed-values 等，经 Read 实际文件核对一致。
- `manifests/arc-controller-0.14.2/Chart.yaml`：apiVersion v2、name arc、version 0.14.2、依赖
  gha-runner-scale-set-controller 0.14.2（oci://ghcr.io/actions/actions-runner-controller-charts）——
  经 Read 实际文件逐字一致。
- `manifests/liqo/liqo-1.2.0/Chart.yaml`：name liqo、type application、version 0.1.0、
  appVersion v1.2.0、依赖 liqo-crds 0.1.0（file://./charts/liqo-crds）—— 经 Read 实际文件逐字一致。
- ARC >= 0.14.0 的 `scaleSetLabels`（恰好 2 个：capability label + cluster label）与
  `resourceMeta.ephemeralRunnerSet.annotations`（job-cpu/job-memory/job-npu）模式：抽样
  `projects/vllm-project/vllm-ascend/linux-aarch64-a3-2/values.yaml` 验证
  `scaleSetLabels: ["linux-aarch64-a3-2", "gy-005"]`，与规则一致。
- 定制镜像 `swr.cn-southwest-2.myhuaweicloud.com/modelfoundry/gha-runner-scale-set-controller:0.14.201`：
  在多个 ARC>=0.14.0 controller Application 与 runner values.yaml 中一致出现，无冲突。
- NPU 资源键名：实际检索到仓库内 `ascend-1980`（连字符、小写）在 463 个文件中出现 1244 次，
  `Ascend1980`（历史事故模式：无连字符、首字母大写）0 次出现。raw.json 中出现的 13 处
  "Ascend 1980"（带空格）均为描述型行文（指代 NPU 型号名称），涉及具体资源键名处 raw.json 与仓库
  一致使用 `ascend-1980`，不构成冲突，也不重现历史事故模式。
- ArgoCD 集群目录 ↔ ARC 版本对应表中列出的 12 个集群（gy-003/004/005/006、hk-001、hk-ci、cn12-001、
  hb-003、hb-003-verl、hidevlab-k8s、verl-suzhou、karmada-test）逐一比对
  `argocd/controllers/arc-controller-*.yaml` 及对应 Application 的目标集群名，版本号一致，无冲突。
  （注：该表未列出 sh-001、sh-002、ascend-infra-guiyang-cluster-001/gy-001，但 rule_facts 未声称
  该表是穷尽列表，raw.json 亦未就这三个集群与 rule_facts 产生矛盾断言，故不计入冲突条目，仅记录为
  覆盖缺口，属 description_vague，不升级处理。）

## 冲突明细

### K01 存储类作用域断言与仓库实际检索结果冲突

- **三方件断言**：`argocd/clusters/gy-004/git-cdn.yaml` 对应 page 的 content 写明：
  "Uses inline `valuesObject` instead of an external values file, and `sfsturbo-subpath-sc`
  storage class specific to gy-004."（即 sfsturbo-subpath-sc 用在 gy-004）；同时匿名 path 的
  "Shared Cluster Resources" 汇总节点将 `config:storage:sfsturbo-subpath-sc` 列为跨项目共享资源，
  且多个 gy006 buildkit/cpu 资源节点标注 `storage_class=sfsturbo-subpath-sc`。
- **来源**：raw.json，path=`argocd/clusters/gy-004/git-cdn.yaml`（title: git-cdn.yaml）；
  以及匿名 path 的 "Shared Cluster Resources" 汇总节点。
- **规则依据**：preprocess.json rule_facts，path=CLAUDE.md，assertion：
  "存储类：csi-sfsturbo（ReadWriteMany，大多数集群使用）；sfsturbo-subpath-sc 仅用于
  gy-006、cn12-001、hk-ci"。
- **实际核验**：
  ```
  grep -rl "storageClassName:.*csi-sfsturbo" --include="*.yaml" .
  # 99 个文件

  grep -rl "storageClassName:.*sfsturbo-subpath-sc" --include="*.yaml" .
  # 303 个文件

  grep -rl "sfsturbo-subpath-sc" --include="*.yaml" .
  # 304 个文件（含非 storageClassName 字段引用）

  grep -rl "sfsturbo-subpath-sc" argocd/clusters/*/*.yaml | sed -E 's#argocd/clusters/([^/]+)/.*#\1#' | sort -u
  # → ascend-infra-guiyang-cluster-001, cn12-001, gy-004, gy-005, hk-001, openmerlin-guiyang-006

  cat other/opensourceways/config/local-storage-pvc.yaml
  # opensourceways-hk-ci PVC，storageClassName: sfsturbo-subpath-sc
  # （argocd/clusters/hk-ci/opensourceways-hk-ci-config.yaml 的 source.path 指向该目录）
  ```
- **核验结果**：`sfsturbo-subpath-sc` 是仓库内出现次数最多（304 个文件）的存储类，
  远超 `csi-sfsturbo`（99 个文件）。除 rule_facts 声称的 gy-006、cn12-001、hk-ci 外，该存储类还被
  gy-004（`git-cdn.yaml` 明确写明 "specific to gy-004"）、gy-005（`vllm-project/vllm-ascend/
  linux-aarch64-a3-2` 等 runner ephemeral 存储、`smart-git-proxy.yaml`）、hk-001（`git-cdn.yaml`、
  `smart-git-proxy.yaml`）、ascend-infra-guiyang-cluster-001（即 gy-001，`git-cdn.yaml`）广泛使用；
  此外几乎所有 `projects/` 与 `other/` 下的 runner `values.yaml`（triton-lang、fla-org、
  sgl-project、Ascend/pytorch、Ascend/sglang、volcengine、alibaba/ROLL 等数十个项目）以及
  `manifests/grafana/pvc.yaml`、`manifests/nginx-pypi-cache-{new,test}/pvc.yaml` 均使用
  `sfsturbo-subpath-sc` 作为 ephemeral/共享存储的默认选择。而 `csi-sfsturbo` 主要出现在各项目
  `config/local-storage-pvc.yaml`（基础 Kustomize overlay 的持久化存储）中，并非
  "大多数集群使用" 的 ephemeral 存储类；两者的实际角色与 rule_facts 描述相反。
- **裁定**：规则依据错（rule_basis_wrong）。CLAUDE.md 中的存储类作用域描述已过时或本就不准确，
  raw.json 中关于 gy-004 使用 sfsturbo-subpath-sc 的具体断言与仓库实际情况一致，反而是 raw.json
  的断言揭示了 rule_facts 的错误。
- **修正后事实**：`sfsturbo-subpath-sc` 是仓库中使用最广泛的存储类（304 个文件引用），
  用于绝大多数项目 runner 的 ephemeral 工作卷及部分共享组件（grafana、nginx-pypi-cache）的持久化
  存储，实际使用集群包括但不限于 gy-004、gy-005、gy-006、hk-001、hk-ci、cn12-001、
  ascend-infra-guiyang-cluster-001（gy-001），而非仅限 gy-006、cn12-001、hk-ci 三个集群；
  `csi-sfsturbo`（99 个文件引用）主要用于各项目 `config/local-storage-pvc.yaml` 的基础持久化存储，
  并非 "大多数集群使用" 的 ephemeral 存储类。
- **严重度**：fact_conflict

## 第二轮：结构性核验

对 core 层清单的 19 个文件逐一 Read 源文件，与 raw.json 中对应 page 的 content 字段
逐条对照位置（键在哪一层级）、量纲（数字指代什么）、主体（断言的属性属于谁）、
存在性（断言提到的字段是否真的存在）。19 个文件全部核对完毕，其中 13 个无结构性
问题（见下方「结构性核验通过项」），5 个发现结构性错误（K02-K06）。

### K02 linux-aarch64-a3-2/values.yaml：NPU 标签位置与规模量纲双误

- **三方件断言**：raw.json page（path=`projects/vllm-project/vllm-ascend/linux-aarch64-a3-2/values.yaml`）
  content：「using scaleSetLabels [linux-aarch64-a3-2, gy-005] and an **ascend-1980 NPU node
  selector** for a **2-way runner pool**」
- **来源**：raw.json，path=`projects/vllm-project/vllm-ascend/linux-aarch64-a3-2/values.yaml`
- **规则依据**：源文件自身实际结构（结构性核验，非 CLAUDE.md 条目）
- **实际核验**：
  ```
  grep -n "ascend-1980\|nodeSelector\|minRunners\|maxRunners\|replicas\|npu-resource-model\|required-npu-count" \
    projects/vllm-project/vllm-ascend/linux-aarch64-a3-2/values.yaml
  ```
- **核验结果**：
  ```
  16:      nodeSelector:
  25:        ascend-ci.com/required-npu-count: "2"
  27:        ascend-ci.com/npu-resource-model: "ascend-1980"
  ```
  `ascend-1980` 在第 27 行，位于 `gha-runner-scale-set.template.metadata.labels` 下，是
  **pod 标签**，不是 nodeSelector。该文件唯一的 `nodeSelector`（16-17 行）位于
  `listenerTemplate.spec` 下，值为 `beta.kubernetes.io/arch: amd64`，与 NPU 无关。
  另外 `grep -c "minRunners\|maxRunners\|replicas"` 结果为 0——全文件不存在这三个字段。
  第 25 行的 `"2"` 来自 `ascend-ci.com/required-npu-count`，表示**单个 runner pod 所需
  NPU 数量**，不是 runner 池的规模（replicas/minRunners/maxRunners 均不存在）。
- **裁定**：claim_wrong（字面量 "ascend-1980" 和 "2" 拼写正确，但位置和量纲均说错）
- **修正后事实**：`ascend-1980` 是 `template.metadata.labels` 下的 pod 标签
  （`ascend-ci.com/npu-resource-model`），不是 nodeSelector；该文件唯一的 nodeSelector 是
  `beta.kubernetes.io/arch: amd64`。`"2"` 来自 `ascend-ci.com/required-npu-count`，指每个
  runner pod 需要 2 张 NPU，不是 2 个 runner 的池规模；文件中不存在
  minRunners/maxRunners/replicas 字段。
- **严重度**：fact_conflict　**check_type**：structural

### K03 manifests/arc-controller-0.14.2/values.yaml：镜像与资源限制主体错配

- **三方件断言**：raw.json page（path=`manifests/arc-controller-0.14.2/values.yaml`）
  content：「Helm values configuration for ARC controller 0.14.2 with **custom image
  registry**, **resource limits**, and node selectors.」
- **来源**：raw.json，path=`manifests/arc-controller-0.14.2/values.yaml`
- **规则依据**：CLAUDE.md「ARC >= 0.14.0 定制镜像固定为
  swr.cn-southwest-2.myhuaweicloud.com/modelfoundry/gha-runner-scale-set-controller:0.14.201」
- **实际核验**：
  ```
  grep -n "image:\|repository:\|resources:\|limits:\|requests:\|nodeSelector" \
    manifests/arc-controller-0.14.2/values.yaml
  grep -c "myhuaweicloud\|swr\." manifests/arc-controller-0.14.2/values.yaml
  grep -n "myhuaweicloud" argocd/controllers/arc-controller-cn12-001.yaml
  ```
- **核验结果**：
  ```
  13:  image:
  14:    repository: "ghcr.nju.edu.cn/actions/gha-runner-scale-set-controller"
  17:    tag: ""
  59:  resources: {}
  64:  # limits:
  65:  #   cpu: 100m
  66:  #   memory: 128Mi
  67:  # requests:
  68:  #   cpu: 100m
  69:  #   memory: 128Mi
  71:  nodeSelector:
  72:    kubernetes.io/arch: amd64
  ```
  `manifests/arc-controller-0.14.2/values.yaml` 中 `myhuaweicloud`/`swr.` 出现次数为
  **0**；该文件的 `image.repository` 是默认的 NJU 镜像 `ghcr.nju.edu.cn/...`，不是
  Huawei 定制镜像。`resources` 为空对象 `{}`，limits/requests 整块被注释，**没有实际
  生效的资源限制**。CLAUDE.md 要求的定制镜像实际写在另一个文件
  `argocd/controllers/arc-controller-cn12-001.yaml` 第 17 行（ArgoCD Application 的
  inline helm values 覆盖），而不是这份 chart 自带的 values.yaml。
- **裁定**：claim_wrong（主体错配：把跨文件的集群级覆盖值误归为 chart 自带
  values.yaml 的内容；且 "resource limits" 与文件内容不符——limits 块被注释未生效）
- **修正后事实**：`manifests/arc-controller-0.14.2/values.yaml` 自身的 `image.repository`
  是默认的 `ghcr.nju.edu.cn/actions/gha-runner-scale-set-controller`（NJU 镜像），`tag`
  为空；`resources: {}`，limits/requests 均被注释，未配置实际资源限制。CLAUDE.md 要求的
  Huawei SWR 定制镜像（`swr.cn-southwest-2.myhuaweicloud.com/modelfoundry/
  gha-runner-scale-set-controller:0.14.201`）是通过每个集群的 ArgoCD Application（如
  `argocd/controllers/arc-controller-cn12-001.yaml` 第 17-18 行）以 inline helm values
  覆盖注入的，不在这份 chart 的 values.yaml 中声明。
- **严重度**：fact_conflict　**check_type**：structural

### K04 scripts/argocd-app-lint.sh：规则检查函数计数错误（缺 r3）

- **三方件断言**：raw.json page（path=`scripts/argocd-app-lint.sh`）content：
  「validating ArgoCD Application YAML files ... (**r1-r7 checks**).」
- **来源**：raw.json，path=`scripts/argocd-app-lint.sh`
- **规则依据**：源文件自身实际结构
- **实际核验**：
  ```
  grep -n "^r[0-9]_check()" scripts/argocd-app-lint.sh
  ```
- **核验结果**：
  ```
  115:r1_check() {
  139:r2_check() {
  168:r4_check() {
  240:r5_check() {
  287:r6_check() {
  322:r7_check() {
  ```
  文件中共定义 **6 个** `rN_check` 函数：r1、r2、r4、r5、r6、r7，**不存在 r3_check**。
  "r1-r7 checks" 的表述暗示存在连续 7 个检查，与实际的 6 个（且序号有缺口）不符。
- **裁定**：claim_wrong（数量错：应为 6 个检查函数，序号非连续，缺 r3）
- **修正后事实**：`scripts/argocd-app-lint.sh` 定义了 6 个规则检查函数：`r1_check`
  （115 行）、`r2_check`（139 行）、`r4_check`（168 行）、`r5_check`（240 行）、
  `r6_check`（287 行）、`r7_check`（322 行）；不存在 `r3_check`。
- **严重度**：fact_conflict　**check_type**：structural

### K05 monitoring/prometheus/values.yaml：「HA」表述与实际副本数矛盾

- **三方件断言**：raw.json page（path=`monitoring/prometheus/values.yaml`）content：
  「Configures kube-prometheus-stack 85.1.3 with **Prometheus HA (1 replica)**,
  Alertmanager, ...」
- **来源**：raw.json，path=`monitoring/prometheus/values.yaml`
- **规则依据**：源文件自身实际结构（`Chart.yaml` description 作为设计意图对照）
- **实际核验**：
  ```
  grep -n "replicas:\|Anti-affinity\|恢复 replicas" monitoring/prometheus/values.yaml
  ```
- **核验结果**：
  ```
  15:      replicas: 1
  25:      # # Anti-affinity: 两个 Prometheus 实例分散到不同节点（正式上线时恢复 replicas: 2 并取消注释）
  88:      replicas: 1
  93:      # # Anti-affinity: 两个 Alertmanager 分散（正式上线时恢复 replicas: 2 并取消注释）
  ```
  Prometheus 与 Alertmanager 的 `replicas` 均为 **1**，实现 HA 所需的反亲和性配置整段
  被注释，并附注「正式上线时恢复 replicas: 2」，说明当前尚未启用 HA。`Chart.yaml` 的
  description（"Prometheus HA pair + Alertmanager for central CI monitoring cluster"）
  是设计意图，不是当前 values.yaml 的实际部署状态。「HA (1 replica)」自相矛盾——
  单副本不构成 HA。
- **裁定**：claim_wrong（主体/状态错配：把 Chart 设计意图当成了 values.yaml 的当前
  实际配置）
- **修正后事实**：`monitoring/prometheus/values.yaml` 当前将 Prometheus 与
  Alertmanager 的 `replicas` 都设为 1（15、88 行），尚未启用 HA；实现 HA 所需的跨节点
  反亲和性配置目前被注释（25-32、93-100 行），注释说明将在"正式上线"时恢复为
  `replicas: 2`。当前实际部署是单副本，不是 HA。
- **严重度**：fact_conflict　**check_type**：structural

### K06 README.md：与 script.sh 的「documents」关系无文本依据

- **三方件断言**：raw.json page（path=`README.md`）metadata.relations：
  `{"direction": "outgoing", "type": "documents", "with": "file:script.sh"}`
- **来源**：raw.json，path=`README.md`，metadata.relations
- **规则依据**：源文件 README.md 全文
- **实际核验**：
  ```
  grep -in "script" README.md
  ```
- **核验结果**：无匹配（grep exit code 1）。`README.md` 全文（60 行）未提及
  `script.sh` 或任何 "script" 字样。
- **裁定**：claim_wrong（存在性错误：所声明的 "documents" 关系在 README.md 文本中
  找不到依据）
- **修正后事实**：`README.md` 全文未引用 `script.sh`；README.md 与 script.sh 之间
  不存在文档化关系，该关系边缺乏文本依据。
- **严重度**：fact_conflict　**check_type**：structural

### 结构性核验通过项（无冲突，不逐条展开为独立条目）

- `argocd/controllers/arc-controller-cn12-001.yaml`：镜像地址、版本、命名空间、
  集群名均与源文件逐字一致，位置层级（`spec.source.helm.values` inline 覆盖）
  正确对应。
- `manifests/arc-controller-0.14.2/Chart.yaml`：apiVersion/name/version/dependencies
  与源文件逐字一致。
- `manifests/arc-controller-0.14.2/templates/clusterrole-management.yaml`：
  ClusterRole + ClusterRoleBinding 双文档结构，与摘要"multi-document YAML"一致。
- `argocd/clusters/cn12-001/vllm-project-vllm-ascend-cn12-001-config.yaml`：
  Kustomize config Application，source.path 层级正确。
- `argocd/clusters/cn12-001/vllm-project-vllm-ascend-cn12-001-linux-aarch64-a3.yaml`：
  多个 Helm Application（a3-0/2/4/8/16），"Multiple ArgoCD Helm Applications" 与实际
  5 个文档一致。
- `projects/vllm-project/vllm-ascend/config-cn12-001/kustomization.yaml`：聚合
  namespace/storage/permissions/secrets/docker-cli/configmap，与 18 个 resources
  条目逐一对应。
- `projects/vllm-project/vllm-ascend/config-cn12-001/linux-aarch64-a3-2-configmap.yaml`：
  "2 Ascend A3 NPUs" 对应 `huawei.com/ascend-1980: "2"` 的 limits/requests（第
  41、45 行），位置（`containers[].resources`）与量纲（每 pod 2 张卡）均正确——
  与 K02 的 values.yaml 形成对照，说明同一数字在不同文件中三方件的处理不一致。
- `projects/vllm-project/vllm-ascend/config-cn12-001/runner-pod-permission.yaml`：
  ServiceAccount/Role/RoleBinding 结构正确；"ephemeral pods" 措辞略宽泛（RBAC 实际
  授权对象是 `pods` 资源本身，未见 "ephemeral" 限定），归为 description_vague，
  不升级为冲突。
- `projects/vllm-project/vllm-ascend/linux-aarch64-a3-2/Chart.yaml`：chart name
  "linux-arrch64-a3-2"（源文件笔误，非三方件笔误）、version 0.14.2、依赖声明
  与摘要一致。
- `other/Ascend/Ascend-CI/linux-aarch64-310p-1/Chart.yaml`：版本 0.12.0、NJU 镜像
  地址逐字正确。
- `monitoring/prometheus/Chart.yaml`：kube-prometheus-stack 85.1.3 依赖声明正确。
- `.claude/skills/arc-deploy/SKILL.md`：核心逻辑（存储类型判断、生成文件清单、
  输出位置）与源文件结构一致。
- `docs/ci-checks.md` / `scripts/check-projects-coverage.py`：摘要中的 RA/RC 规则
  引用与源文件 docstring（`RA:` 第 3 行、`RC:` 第 6 行）及 main() 输出文本一致；
  未见 "RB" 被虚构。

## 校验声明

- 本次校验严格遵循「不武断」原则：对存储类作用域冲突，未直接采信 CLAUDE.md，而是用
  `grep -rl` 实际统计了两种存储类各自的文件出现次数（304 vs 99）及涉及的集群清单，
  并抽查 `other/opensourceways/config/local-storage-pvc.yaml` 印证 hk-ci 目的地的实际取值，
  以此为依据裁定规则依据本身有误。
- 未发现三方件重现「资源键名大小写错误」「作用域放大到全仓」「集群数量矛盾」等已知历史事故模式，
  但发现了与已知事故完全同构的**结构性错误**（K02：字面量拼对但位置/量纲说错，与提示词中
  「ascend-1980 node selector」「2-way runner pool」的示例完全吻合，本次校验独立复现并确认）。
- K03/K05 是新发现的结构性主体错配：把跨文件的集群级覆盖值/Chart 设计意图误当作目标文件的
  当前实际内容。K04 是数量断言错误。K06 是关系边存在性错误。
- 本次校验存在 6 个未修正的 fact_conflict（K01-K06），全部已给出 corrected_fact，
  均为 claim_wrong 或 rule_basis_wrong，无 unresolved，故不设 blocking。
