---
tags:
  - 知识实验
  - Karmada
  - Queue护栏
  - 候选知识
wiki: Karmada 调度与 Queue 护栏报告集（v3 候选）
type: wiki-candidate
status: pending-review
authority: informative
authors:
  - model-deepseek-v4-flash
source:
  canonical_url: https://github.com/yyl-support/file
  revision: 29d532c9579b5afdeec2a77b6083cbfcc2b94982
  scope: report/
  source_id: source-git-3e49138575e1aa39
generation_instruction_hash: eb5b31db3fd8fe2ffe46e00ddd1227a197df5857753d8cba4b816dec2aa9738e
candidate_id: wiki-candidate-09ed4a4dcc888eaf
claim_count: 10
reviewer_required: true
experiment: yyl-support-file-report-v3
---

# Karmada 调度与 Queue 护栏报告集

> ⚠️ **未审核候选知识**：本文由模型基于固定 Source revision 生成，所有论断均处于待审核状态，**不得作为已确认知识使用**。审批前禁止用于生产操作或制度依据。

---

## 一、构建信息

- Source：`https://github.com/yyl-support/file` @ `29d532c9579b`
- 范围：`report/`
- 规整：8 个文件 / 127 个语义块
- 生成模型：`model-deepseek-v4-flash`
- 再生成要求哈希：`eb5b31db3fd8fe2ffe46e00ddd1227a197df5857753d8cba4b816dec2aa9738e`
- 候选 ID：`wiki-candidate-09ed4a4dcc888eaf`

---

## 二、一句话说明

本文汇总了 Karmada 调度优化与 Queue 护栏的观测、验证路径及新集群接入前置条件，所有结论均基于未审核的原始报告，需人工复核后方可采信。

---

## 三、三十秒概览

- **调度优化**：通过 COP 软偏好、p20/Namespace CPP 选择器等手段，已观察到非 NPU Pod 优先落在 pre-paid 节点，但 22:00 高峰时作业量超固定机容量，溢出至 post-paid 属设计行为。
- **Queue 护栏**：Queue cap 与并发、ECS 抑制、等待时间存在权衡；验证需至少两个高峰/回收周期，并检查多项指标。
- **新集群接入**：guiyang-ipv6 尚未注册，存在 Volcano 组件缺失、Queue 不完整、长期 Pending Pod、容量不足及凭据轮换等阻塞项。
- **回滚边界**：回滚时不得删除 post-paid 节点或修改 HNA/Autoscaler，应停止灰度 Job、移除 override 并等待自然完成。

---

## 四、事实陈述

- 截至 2026-07-30 核验，guiyang-ipv6 集群仅有 root、default Queue，缺少业务 canary 和现有任务使用的 shared-flexible-queue。（来源：report/Karmada新集群接入指南_20260721.md, block b20, lines 241-259）
- 截至 2026-07-30 核验，guiyang-ipv6 集群的 volcano-system 没有任何 Deployment，说明 Volcano scheduler、admission 和 controllers 尚未部署或不可用。（来源：同上）
- 截至 2026-07-30 核验，guiyang-ipv6 集群的 argo 命名空间存在 3 个已持续 13 天的 Pending Pod，必须先定位其调度失败原因。（来源：同上）
- 截至 2026-07-30 核验，guiyang-ipv6 集群唯一无污点的 amd64 节点仅有约 57.7Gi 可分配内存，当前无法承接主流 31 CPU / 80Gi amd64 生产任务。（来源：同上）
- 截至 2026-07-30 核验，guiyang-ipv6 成员集群中 karmada-guiyang-ipv6-token Secret 不存在，但本地接入清单曾保存该 ServiceAccount 的 JWT，该 token 当前可用，正式注册前应在已获二次确认后重新签发或轮换 token，并将凭据移出版本库。（来源：report/Karmada新集群接入指南_20260721.md, block b21, lines 261-275）
- 截至本次核验，guiyang-ipv6 尚未注册到正式 Karmada，当前不具备开启正式调度的条件，禁止添加 dispatch/auto=true 或 has-cpu=true。（来源：report/Karmada新集群接入指南_20260721.md, block b22, lines 277-289）

---

## 五、综合推断

- Queue 的 core trade-off：cap 越大 = 并发越多 = ECS 抑制效果越弱但等待时间越短。（来源：report/Karmada调度优化与Queue护栏完整交接_20260721.md, block b30, lines 258-270）
- 在 2026-07-20 20:45 至 2026-07-21 09:47 的观测中，22:00 前后 post-paid 峰值达 40 台，与历史 22:00 CI 批次吻合；22:08 有 80 个活跃作业和 27 个 Pending，远超 21 台固定机承载上限，溢出到 post-paid 是 COP 软偏好的设计行为。（来源：report/优化效果观测分析_20260721.md, block b15, lines 131-137）

---

## 六、已知限制与待确认事项

- **所有提供的论断均待人工审核**，本 Wiki 仅为候选，不得视为已确认事实。
- 上述事实陈述均基于特定时间点的核验（如 2026-07-30），环境可能已变化，需复核。
- 综合推断基于多个事实的分析，可能受观测窗口限制，需进一步验证。
- 回滚边界、Queue 验证标准等建议/决策类型需确认前提条件是否满足。
- 新集群接入的阻塞项（Volcano 缺失、Queue 不完整、Pending Pod、容量不足、凭据轮换）需逐项解决并验证。

---

## 七、来源

- Git 仓库：https://github.com/yyl-support/file，revision 29d532c9579b5afdeec2a77b6083cbfcc2b94982，scope report/。
- 具体文件：
  - report/Karmada调度优化与Queue护栏完整交接_20260721.md
  - report/Karmada新集群接入指南_20260721.md
  - report/非NPU队列护栏验证路径_20260721.md
  - report/优化效果观测分析_20260721.md
- 人类可读位置：各文件中的 block 和行号已在事实陈述中标注。

---

## 八、支撑论断

- 完整论断清单见：[支撑论断清单（10 条，全部未审核）](Karmada调度与Queue护栏报告集-支撑论断清单.md)。

---

## 九、审核状态

- [ ] 逐条核对 10 条论断的证据范围
- [ ] 处理已知问题：claim-c5e6f8d21297a77a（时间窗口/历史比较混入）、混合类型拆分
- [ ] 补充 Queue 未验证、argo 超时回滚等遗漏主题
- [ ] 批准后转为 `approved` 并进入 knowledgebase
