---
tags:
  - project-evolution
  - 团队知识系统
  - LLM-Wiki
  - 架构设计
status: draft
authors:
  - human-team-sponsor
  - model-opencode
created_at: 2026-07-20
updated_at: 2026-08-04
---

# AI 时代团队知识系统：第一阶段架构设计

## 1. 文档目的

本文定义一套从零构建的团队知识系统第一阶段架构。系统目标不是搭建一个传统文档站，也不是把文件放进向量数据库后进行临时问答，而是构建一个由 **人类负责事实、判断与审核，AI 负责规整、提取、关联、综合与维护** 的持久化知识体系。

本文只描述已达成共识的第一阶段方案。具体数据库、对象存储、搜索引擎、模型和开发框架尚未选型，不在本文中预设。

## 2. 核心目标

第一阶段需要验证的核心假设是：

> AI 能否基于可信且可回溯的 Source，生成可审核、可更新、可持续积累的团队 Wiki，并由人类有效治理。

系统必须做到：

- 原始资料始终可查，AI 结论可以回到不可变的来源证据核验。
- 多模态资料先经过规整，再进入 Claim 提取和 Wiki 综合。
- AI 生成的是候选知识，不能自行批准或发布。
- 人类不直接无痕修补模型结论，而是修正 Source、纠正标注或生成规则，然后重新生成。
- 人类仍然可以直接输出更高层次的洞察、原则和决策。
- 内部信息绝不发送给外部托管模型 API。
- 公开知识可以通过白名单 GitHub 仓库单向进入内网。

## 3. 第一阶段边界

### 3.1 两条黄金链路

第一阶段只跑通两条完整链路，不追求批量接入。

#### 黄金链路 A：公开 GitHub 工程

```text
一个指定的 GitHub 工程
  → 获取代码、README、Commit、Issue、PR、Review 和公开 CI 信息
  → 保存 Source 快照
  → 规整成标准内容
  → 提取 Claim
  → 生成项目 Wiki 候选
  → 人工审核
  → 发布到 GitHub 公开知识仓
  → 内网通过白名单仓库 git pull
```

#### 黄金链路 B：内部正式制度

```text
source-owner 人工上传一份正式 PDF
  → 保存不可无痕修改的 Source
  → 提取章节、正文和表格
  → 提取 Claim
  → 生成制度解释 Wiki 候选
  → 负责人审核
  → 发布到内部 Wiki
  → 内网搜索和问答引用已批准知识
```

### 3.2 第一阶段不包含

- 聊天、邮件、会议录音、自动转录和私人笔记接入。
- Word、Excel、PPT、音视频等内部格式的全面支持。
- 批量接入所有 GitHub 项目和内部文档系统。
- 独立的模型评测平台、模型排行榜和 A/B 测试。
- 自动选模、自动路由和模型灰度系统。
- 复杂知识图谱可视化。
- 外网 AI 问答门户。
- 微服务架构。
- 逐段级复杂权限。
- 自动公开发布。

## 4. 总体架构

### 4.1 信任边界

```text
                              Internet / 公开域
┌──────────────────────────────────────────────────────────────────┐
│ GitHub 代码、README、Commit、Issue、PR、Review、公开 CI           │
│                              │                                   │
│                              ▼                                   │
│                    公开 Source 与规整流水线                       │
│                              │                                   │
│                              ▼                                   │
│                  公开 Claim / Wiki 候选                          │
│                              │                                   │
│                        人工审核与发布                              │
│                              │                                   │
│                              ▼                                   │
│                    GitHub 公开知识仓                              │
└──────────────────────────────┬───────────────────────────────────┘
                               │ 白名单仓库，只读 git pull
===============================│==================================== 安全边界
                               ▼
                              公司内网
┌──────────────────────────────────────────────────────────────────┐
│ GitHub 公开知识副本                                               │
│                              +                                   │
│ 内部正式 PDF → 内部 Source → 内部规整 → Claim → Wiki 候选          │
│                                              │                   │
│                                              ▼                   │
│                                      人工审核与批准                │
│                                              │                   │
│                                              ▼                   │
│                 内部 Wiki / 搜索 / AI 问答 / Source 溯源           │
│                                                                  │
│ 模型、Embedding、Reranker、日志和全部内部数据均留在内网             │
└──────────────────────────────────────────────────────────────────┘
```

跨域规则：

- 公开域到内部域：允许，只通过白名单 GitHub 仓库拉取。
- 内部域到公开域：默认禁止。第一阶段不自动发布内部知识；如需公开，必须由 `publisher` 在内网生成独立发布包，经人工脱敏、重新分类为 `public` 后，由受控发布终端创建 GitHub PR。
- 员工不能从外网访问内部团队知识系统。
- 外网第一阶段只提供 GitHub 公开 Wiki，不建设公开 AI 问答门户。

这里的“公开域”表示只处理公开数据的独立执行环境，不表示 GitHub 等外部服务天然可信。GitHub 输入应按不可信内容处理，防范敏感信息误提交、恶意文本和 Prompt Injection。

公开规整流水线部署在公司控制、可访问互联网但不能访问内网的独立公开数据处理区。GitHub Token、公开模型凭据和公开运行日志只存在于该区域。内网发布包如获准公开，由受控发布终端导出到该区域后创建 PR，公开流水线本身不能主动读取内网。

### 4.2 内网部署架构

```text
┌──────────────────────── 内网知识门户 ─────────────────────────┐
│                                                              │
│  Source 管理  |  规整与纠错  |  知识审核  |  Wiki/搜索/问答   │
│                              │                               │
│                              ▼                               │
│                Knowledge API（模块化单体）                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Identity/RBAC | Source | Normalization | Claim          │  │
│  │ Wiki | Review | Search | Query | Publish                │  │
│  └──────────────────────────┬─────────────────────────────┘  │
│                             │                                │
│                      异步任务队列                             │
│                             │                                │
│                             ▼                                │
│                         AI Worker                            │
│                             │                                │
│                    人工选择任务所用模型                       │
│                             │                                │
│                             ▼                                │
│                       内网模型能力库                          │
└──────────────────────────────────────────────────────────────┘

底层存储：

  对象存储       Source 原稿、图片、PDF、代码快照、规整产物
  关系数据库     身份、权限、元数据、Claim、依赖和审核状态
  内部 Git       已批准 Wiki 的版本、Diff 和回滚历史
  搜索索引       全文和向量索引，均属于可重建派生数据
  审计日志       AI 任务、审核、发布和跨域操作记录
```

第一阶段采用模块化单体 API 加异步 AI Worker，不拆分微服务。内外网共用 `knowledge-core` 和统一 Schema，但部署、数据、凭据、模型上下文和内部扩展完全分离。

## 5. 知识分层模型

```text
Source 原始来源
       ↓
NormalizedDocument 规整内容
       ↓
Claim 原子事实或主张
       ↓
WikiPage 人类可读综合页面
       ↓
Search / RAG / Agent
```

### 5.1 Source：不可变的来源证据

Source 保存进入系统时的原始资料，包括 Git 快照、Issue/PR 内容和内部正式 PDF。它是争议发生时可核验的原始证据，而不是自动成立的业务事实。不同 Source 可能互相矛盾、过期或包含错误。

规则：

- 不允许无痕修改或覆盖历史版本。
- 记录唯一 ID、版本、哈希、拥有者、权限和状态。
- 原稿错误时，新增纠正标注或 Source 新版本，并保留旧版本。
- 只有相应知识空间的 `source-owner` 有权使 Source 更新生效。

需要区分：Source 对“当时原文是什么”具有权威性；某项业务结论是否成立，仍取决于来源有效性、适用范围、证据关系和人工审核。

### 5.2 NormalizedDocument：规整层

规整层将多模态、异构、嘈杂的 Source 转换为 AI 容易理解、总结和引用的标准内容。

第一阶段处理：

- GitHub 工程资料的结构化快照。
- 内部正式 PDF 的标题、章节、正文和表格。

规整层负责：

- 格式转换。
- 内容提取。
- 基础结构识别。
- 提取警告和低置信度区域标记。
- 保留人类可读和机器精确两类来源定位。

规整层不负责宣布最终业务结论。规整结果可以审核和纠正，但不能被无痕手改；纠正应以标注、规则修改或重新生成完成。

### 5.3 Claim：原子事实和主张

Claim 是适合机器增量维护的细粒度知识，例如：

> Volcano Queue 的 capability 表示队列可使用资源的硬上限。

每条 Claim 可以连接一个或多个来源。每条来源关系必须记录精确定位和证据关系：

```text
supports | contradicts | supersedes
```

Claim 的审核状态和证据状态分开记录：

```text
review_status: pending-review | approved | rejected
evidence_status: supported | disputed | unsupported | stale
```

Claim 用于：

- 精确溯源。
- 新旧资料冲突检测。
- 判断哪些 Wiki 页面受到 Source 更新影响。
- 细粒度审核与增量重建。

### 5.4 WikiPage：面向人的综合知识

Wiki 页面由 Claim 和 Source 综合而成，是面向人类阅读、学习、搜索和问答的持久知识产物。

Wiki 页面可以来自：

- 模型综合。
- 人类原创洞察或总结。
- 人机共同创作。

模型综合的 Wiki 是可重新生成的构建产物。人类发现问题时，应查看依据并修正 Source、提交纠正标注、调整规整规则或综合要求，再重新生成。人类正式决策、制度批准和高层洞察则作为人类创建的权威 Source 或有痕 Wiki 版本进入系统，不要求模型重新推导。

## 6. 数据模型

第一阶段只建立四种核心实体。

### 6.1 Source

```yaml
id: source-...
title: ...
source_type: github | internal-pdf
visibility: public | internal
owner: human-<id>
revision: ...
status: active | superseded | withdrawn
content_hash: sha256:...
human_location: ...
machine_locator: ...
created_at: ...
updated_at: ...
```

### 6.2 NormalizedDocument

```yaml
id: normalized-...
source_id: source-...
content_ref: ...
warnings: []
status: generated | needs-correction | accepted
generated_by: model-<name>
source_revision: ...
created_at: ...
```

### 6.3 Claim

```yaml
id: claim-...
statement: ...
source_refs:
  - source_id: source-...
    source_revision: ...
    relation: supports
    human_location: ...
    machine_locator: ...
authors:
  - model-<name>
review_status: pending-review | approved | rejected
evidence_status: supported | disputed | unsupported | stale
confidence: ...
created_at: ...
```

### 6.4 WikiPage

```yaml
id: wiki-...
title: ...
type: knowledge | insight | decision | procedure | policy-explanation
authors:
  - model-<name>
  - human-<id>
reviewers:
  - human-<id>
status: draft | pending-review | approved | superseded
authority: informative | team-consensus | official
claim_ids: []
direct_source_refs: []
visibility: public | internal
created_at: ...
updated_at: ...
tags: []
```

作者只使用 `model-<模型名称>` 和 `human-<归一化身份ID>`。Agent 版本、模型具体版本、Prompt、工作流版本和任务 ID 不进入 Wiki 页面，而保存在后台运行日志中。主题标签只描述内容，不承担作者和权限语义。

所有派生产物都必须绑定具体的 Source revision。后台运行日志保留处理器、模型、任务和配置等技术信息，并与产物建立关联，但这些信息不进入面向读者的 Wiki 元数据。

## 7. 来源定位与身份归一化

### 7.1 双层溯源

人类默认看到：

- 谁产生了信息。
- 什么时候产生。
- 在哪里产生。
- 处于什么上下文。
- 当前是否仍然有效。

例如：

> 张三于 2026-07-15 在 GitHub 的 `backlog #921` 方案讨论中提出……

系统内部同时保留机器精确定位：

- Source ID。
- Commit SHA。
- Comment ID。
- 文件路径和行号。
- PDF 页码。
- 内容哈希。

机器定位默认折叠，只在技术详情和审计场景展示。

### 7.2 统一人员身份

系统建立内部统一人员目录，将 GitHub、内网系统等账号映射到同一 `human-<id>`：

```yaml
id: human-u-000173
display_name: 张三
organization: AI Infra
roles:
  - source-owner
  - reviewer
domains:
  - karmada
accounts:
  github:
    - zhangsan-gh
  internal:
    - "00291374"
```

普通页面展示姓名和团队语义，后台使用唯一 ID 进行权限、审计和历史关联。

## 8. 权限与治理

### 8.1 第一阶段角色

| 角色 | 权限 |
|---|---|
| `reader` | 阅读有权限的 Wiki、搜索和问答 |
| `source-owner` | 创建、更新、纠正和废弃所属 Source |
| `reviewer` | 审核 Claim 和 Wiki 候选版本 |
| `publisher` | 批准高权威内部内容和公开发布 |

同一人可以兼任多个角色，但权限同时受知识空间和领域约束。AI 不是权限角色，只能在任务授权范围内读取 Source 并生成候选内容。

第一阶段允许低风险知识由同一人兼任多个角色，但以下操作必须由不同人员完成：

- `official` 内容不能由作者本人单独批准。
- 内部内容公开时，内容负责人和 `publisher` 必须是不同身份。
- Source Owner 不能独自完成同一 Source 的纠正、知识批准和公开发布全流程。

### 8.2 权限继承

- Source 保留原始权限。
- NormalizedDocument 继承 Source 权限。
- Claim 继承其所有来源中最严格的权限。
- Wiki 页面继承其 Claim 和 Source 中最严格的权限。
- 权限过滤必须在检索和模型调用之前完成。
- 放宽权限、跨空间发布或公开发布必须单独审核，不能通过删除受限来源引用来绕过权限继承。

如果公开内容的结论来自内部资料，不能通过删除引用来绕过权限。必须先由有权人员创建一份经过脱敏、审核并重新分类为 `public` 的新 Source，公开 Wiki 只能依赖该公开 Source。

第一阶段采用空间级 RBAC 和文档级来源继承，不引入逐段权限。

## 9. 生成、纠错与审核

### 9.1 纠错闭环

```text
人类发现 Wiki 结论有问题
  → 查看系统提供的来源、关键依据、冲突与不确定性
  → 判断问题发生在 Source、规整、Claim 还是综合规则
  → 提交 Source 新版本 / 纠正标注 / 规整纠正 / 生成要求调整
  → 系统重新规整或重新综合
  → 生成新的候选版本
  → 人类审核新旧 Diff
```

人类不能无痕覆盖模型生成的当前页面。第一阶段优先通过上游纠正和重新生成解决问题；如果只是措辞或结构调整，也允许提交有痕人工 Patch，但必须保留模型原始候选、修改人、修改原因，并重新进入审核。

为保持四实体最小模型，第一阶段不新增独立 Correction 实体。纠正以受审计的 Annotation 记录存在，可指向 Source revision、NormalizedDocument、Claim 或 Wiki 候选，包含提交人、原因、修改建议、状态和审核人。需要改变原稿事实时，仍必须创建 Source 新版本。

### 9.2 候选知识与当前知识

```text
AI 生成 Wiki 候选
  → status: pending-review
  → 可以在审核区查看和讨论
  → 普通搜索与问答默认只使用 approved 内容
  → 用户显式选择“包含候选知识”时才允许检索 pending-review，并逐条警告
  → Reviewer 批准
  → status: approved
  → 写入内部 Git 主分支，成为当前有效 Wiki
```

问答引用优先级：

```text
正式制度 / 人工决策
  > approved Wiki
  > pending-review Wiki
  > 即时模型推断
```

引用未审核知识时必须提示其状态，不得直接用于生产操作、安全规范或制度执行。

### 9.3 审核方式

内部审核以门户和数据库状态机为主：

- 展示触发原因。
- 展示新增或变化的 Source。
- 展示 Claim 及其来源。
- 展示 Wiki 新旧版本 Diff。
- 展示权限和影响页面。
- 支持批准、驳回、要求补充来源和重新生成。

批准后的 Wiki 才提交到内部 Git。内部候选不要求逐次创建 Git MR。数据库中的批准记录必须保存对应 Git Commit SHA；Git 写入失败时不得把候选标记为已发布。

公开 GitHub 来源生成的 Wiki 经过 `publisher` 审核后创建 GitHub PR。内部来源派生内容的公开发布不作为第一阶段自动化能力，只保留受控人工流程；内网 Agent 不拥有直接 push 公网仓库的权限。

### 9.4 来源失效传播

Source 被标记为 `superseded` 或 `withdrawn` 时，系统立即将其直接依赖的 Claim 标记为 `stale`，并将受影响 Wiki 标记为需要重新审核：

```text
Source 失效
  → 依赖 Claim: evidence_status=stale
  → 依赖 Wiki: review_required=true
  → 制度、生产操作和安全类页面暂停进入问答
  → 生成候选更新并通知 Reviewer
```

低风险知识在重新审核期间可以继续显示旧版本，但必须展示过期警告；`official`、生产操作和安全类页面默认停止作为问答依据，直到新版本批准。

## 10. 更新机制

目标架构采用事件驱动和定期对账结合的方式：

```text
Webhook / 上传 / 人工提交
  → 事件队列
  → Source 登记或更新
  → 规整
  → Claim 更新
  → 通过依赖关系识别受影响 Wiki
  → 生成候选版本
  → 进入审核队列
```

第一阶段只实现人工触发或单来源同步触发、任务重试和幂等处理。以下自动化作为第一阶段后半程能力，不阻塞最小闭环验收：

- 每日增量对账，补齐遗漏事件和失败任务。
- 每周巡检过期页面、冲突、孤立页面和待审核积压。
- 定期全量重建，验证派生内容能否从 Source 重现。

任务必须幂等，同一 Source 事件重复执行不能产生重复知识。

## 11. 内网门户

第一阶段建设四个工作区。

### 11.1 Source 管理

- GitHub 单仓导入。
- 内部正式 PDF 上传。
- Source 版本、状态、负责人、权限和原稿查看。
- 更新、纠正和废弃操作。

### 11.2 规整与纠错

```text
左侧：Source 原稿
右侧：NormalizedDocument
底部：提取警告、人工纠正和重新生成
```

### 11.3 Claim / Wiki 审核

- Source 变化说明。
- Claim 列表与来源。
- Wiki 新旧 Diff。
- 权限和影响范围。
- 批准、驳回、要求补充来源、调整要求后重新生成。

### 11.4 知识消费

- 已批准 Wiki。
- 基础全文搜索和简单语义搜索。
- 内网 AI 问答。
- 人类可读来源。
- 未审核知识警告。
- 相关知识跳转。

## 12. 模型能力平台

知识系统不绑定具体模型。内网维护可持续演进的模型库，至少可包含生成模型、Embedding、Reranker、OCR、图像理解和代码理解模型。

第一阶段不实现自动路由。管理员为规整、Claim 提取、Wiki 综合和问答分别人工选择并批准默认模型配置，流水线按该配置执行；操作人员可以在重试或专项任务中人工覆盖。系统记录实际所选模型，以便排查和复现；模型具体版本和 Agent 技术细节只进入后台日志。

所有内部模型调用都发生在公司受控环境中，任何内部原文、规整结果、Claim、Wiki、检索上下文、Prompt、Embedding 和运行日志都不能发送到外部托管服务。

## 13. 存储职责

| 存储 | 内容 | 权威性 |
|---|---|---|
| 对象存储 | 原始 PDF、图片、代码快照、规整产物 | Source 原稿的内容存储 |
| 关系数据库 | 身份、权限、Source 元数据、Claim、依赖、审核状态 | 业务状态和治理权威 |
| 内部 Git | 已批准 Wiki Markdown | 当前人类可读知识及历史版本 |
| GitHub 公开知识仓 | 已批准公开 Wiki | 公开域知识权威版本 |
| 全文/向量索引 | Wiki 与 Claim 的查询索引 | 可重建派生数据 |
| 审计日志 | AI 任务、审核、发布和跨域操作 | 运行与安全审计 |

数据库负责审核流程，Git 负责批准后 Wiki 的版本管理，二者不互相替代。

## 14. MVP 验收标准

第一阶段完成时，应至少满足：

- 能完整处理一个指定 GitHub 工程。
- GitHub 黄金样本的仓库、分支、Commit/Issue/PR 时间范围和数据量上限在实施前固定，避免“一个仓库”成为无边界输入。
- 能由 `source-owner` 上传并处理一份正式、非扫描、可复制文本的 PDF；文件大小、页数和表格复杂度上限在实施前固定。
- Source、NormalizedDocument、Claim 和 WikiPage 四实体链路可以运行。
- Source 与规整产物严格分离，原稿不能被 AI 无痕修改。
- 验收样本中的每条关键 Claim 和 Wiki 结论都能打开对应的人类可读来源和机器精确定位。
- 模型生成内容默认进入 `pending-review`。
- Reviewer 可以查看 Source、Claim 和 Wiki Diff，并批准或驳回。
- 批准后的内部 Wiki 能够写入内部 Git。
- 公开知识可以发布到 GitHub 公开知识仓并被内网只读拉取。
- 内部内容全链路不访问外部模型 API。
- 搜索和问答在检索前执行权限过滤。
- 普通问答默认只引用正式制度和 approved Wiki；显式开启候选知识后，能够区分候选知识和即时推断并给出警告。
- 发现错误后可以通过 Source 新版本、纠正标注或规则调整重新生成知识。

第一阶段不建设模型评分、自动评测或大规模吞吐平台，只采用一组预先固定的人工验收样本和审核清单验证忠实性、完整性、来源、权限和可用性。验收样本属于项目测试材料，不构成独立评测体系。

## 15. 后续阶段候选方向

以下内容不属于第一阶段承诺：

- 内网文档系统自动同步。
- Word、Excel、PPT、图片、扫描件、音视频规整。
- 聊天、邮件和会议接入。
- 自动模型 Profile 和智能路由。
- 正式评测体系与回归数据集。
- 复杂知识图谱和可视化。
- 外网公开 AI 问答门户。
- 微服务拆分。
- 更细粒度权限。
- 自动过期策略和主动推荐。

## 16. 待后续确定的技术选型

第一阶段架构已经确定，但以下具体实现仍需单独选型：

- Web 前端与后端开发框架。
- PostgreSQL 或其他关系数据库的具体部署方式。
- 对象存储实现。
- 内部 Git 服务。
- 消息队列实现。
- 全文搜索与向量索引组件。
- 内网模型库及模型调用协议。
- GitHub 数据采集方式与同步频率。
- PDF 解析和 OCR 组件。
- 企业统一身份认证协议与人员目录接口。

技术选型必须服从本文确定的知识模型、安全边界和审核流程，而不能反过来改变这些原则。

## 17. 可运行骨架实现记录（2026-08-04）

> 本节记录本文档之外的真实实现进展。架构原则不变，本节反映"从纸面到可运行"的落地状态。

### 17.1 实现状态

第一条公开 GitHub 黄金链路已经实现并真实运行，代码位于 `knowledge-core/`（Python 标准库，无第三方依赖）：

- Source 快照（固定 revision + 子目录 scope + 内容哈希 + 完整性校验）
- 规整层（8 个文件 / 语义切块）
- Claim 提取（DeepSeek V4 Flash，块 ID 定位）
- Wiki 候选生成（DeepSeek，固定输出契约）
- 人工审核状态机（pending-review → approved，未批准不发布）
- approved-only 查询（只读已批准 Git 提交，不扫目录）

分层结构：

```text
knowledge-core/
├── src/knowledge_core/
│   ├── application.py     # Application Use Cases
│   ├── ports.py           # Store / Model / Git Source / Wiki 契约
│   ├── store.py           # SQLite Metadata Adapter
│   ├── git_adapter.py     # 本地 Git Source 与 Wiki Adapter
│   ├── model.py           # 确定性 Adapter + OpenAI-compatible Adapter
│   ├── wiki_validation.py # Wiki 生成后确定性质量门禁
│   └── cli.py             # Composition Root + CLI
├── schemas/
│   └── wiki-output-contract.md   # Wiki 输出契约
├── config/
│   └── models.json        # DeepSeek Profile（不含密钥）
└── tests/                 # 12 个 CLI 端到端与文档校验测试
```

### 17.2 真实知识灌入实验

样本：`https://github.com/yyl-support/file` @ `29d532c9579b`，scope `report/`（8 个文件，34,942 字符）。

完整链路真实运行：

```text
固定 revision + report/ scope
  → Source 快照（哈希 a7e65a14…）
  → 规整（127 个语义块）
  → DeepSeek 提取 10 条 Claim
  → DeepSeek 生成 Wiki 候选
  → 独立审核
  → 全部保持 pending-review，未批准、未发布
```

实验产物位于 `knowledge-core/.knowledge/experiments/yyl-support-file-report-v3/`（已被 .gitignore 排除，仅本地）。

### 17.3 三轮迭代验证的核心结论

| 版本 | 定位方式 | 结果 |
|---|---|---|
| v1 | 模型返回行号 | 5/10 错位 |
| v2 | 模型返回行号 + 再生成要求 | 7/10 错位（主题/时间边界改善，行号仍不可靠） |
| v3 | 程序切块 + 模型返回块 ID + 词项重叠校验 | 定位 10/10 正确，进入人工审核标准 |

**核心架构结论：定位是程序问题，语义是模型问题。**

- 模型负责：statement 语义、claim_type、时间/环境/条件边界（prompt 在这些维度有效，v1→v2 已验证）。
- 程序负责：证据定位（切块 + 块 ID 映射行号 + 词项重叠校验），不依赖模型记忆行号。
- 人工负责：判断证据是否真正支持陈述（unverified → supported）。

### 17.4 实现过程中新增的能力

- `--include <dir>`：Source 限定子目录范围，scope 进入 identity、哈希和来源定位。
- `--canonical-url`：本地 clone 使用稳定远端 URL 作为 identity，不依赖机器路径。
- `--instruction-file`：可审计的再生成要求，内容哈希写入 Claim 和候选，能解释版本为何不同。
- OpenAI-compatible Adapter：模型 Profile 可配置（base_url/model/超时/输出上限/thinking），密钥只从环境变量或 OpenCode 认证存储读取，不进入产物。
- 语义切块：规整层按 Markdown 标题/段落切块，每块带稳定 ID 和行范围。
- Wiki 输出契约：固定 H1/编号章节/`---` 分隔/标题不中英混合，并要求“构建信息”置于最后、使用“整体概述”、读者文档不逐条堆叠证据定位（见 `schemas/wiki-output-contract.md`）。
- 生成后文档质量门禁：`wiki build` 自动校验，也可用 `wiki validate --file` 独立校验人工渲染文件；当前硬校验章节顺序、旧标题、事实区内联来源、数据密集列表、Markdown 表格列数和 Mermaid 围栏/图类型声明。
- 表达形式规范：数据罗列、状态对照和方案比较使用表格；代码流程、架构和系统关系在证据充分时使用 GitHub Mermaid。是否“应当绘图”仍属于模型规范和人工审核，程序只校验已生成 Mermaid 的基础格式。

### 17.5 安全与一致性不变量（已验证）

- 快照被篡改后所有下游阶段（规整/Claim/查询/Wiki/批准）全部阻断。
- 候选 Wiki 批准前不进入查询；查询只读已批准 Git commit。
- 同名 Source 不互相覆盖 Wiki 页面。
- 批准提交不夹带无关 staged 文件。
- Claim 引用原文由程序从冻结 Source 提取，模型 Claim 默认 unverified，人工批准后才转 supported。
- API/JSON/来源/契约校验失败不产生部分 Claim 或候选。
- 密钥不进入日志、产物或 Git。

### 17.6 与架构文档的差异说明

本文第 16 节列出的部分技术选型已经初步落地：

| 架构文档待选型项 | 实现状态 |
|---|---|
| 内网模型库及模型调用协议 | OpenAI-compatible Adapter + Profile，DeepSeek V4 Flash 已接入 |
| GitHub 数据采集方式 | 本地 clone + 固定 revision 只读导出 |
| 全文搜索与向量索引组件 | 第一阶段用 approved Wiki 全文匹配（未用向量） |
| 数据库实现 | SQLite（模块化单体阶段） |

其余选型（Web 门户、PostgreSQL、对象存储、内部 Git、消息队列等）维持原状，等待后续阶段。
