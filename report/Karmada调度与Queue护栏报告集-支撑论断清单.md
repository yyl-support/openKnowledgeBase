---
tags:
  - 知识实验
  - Karmada
  - Queue护栏
  - 候选知识
wiki: Karmada 调度与 Queue 护栏报告集（v3 候选）——支撑论断清单
type: claim-list
status: pending-review
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

# 支撑论断清单

> 本文是 [Karmada 调度与 Queue 护栏报告集验证候选](Karmada调度与Queue护栏报告集-验证候选.md) 的附属文件，列出支撑该 Wiki 的全部论断。所有论断均未审核，禁止作为已确认知识使用。

## 类型说明

- `事实`：原文直接陈述的内容。
- `推断`：基于多个事实的分析解释。
- `建议`：对行动的建议。
- `决策`：已作出的决策边界或操作顺序。

## 论断列表

### 一、Karmada 新集群接入指南

1. **事实** · `claim-cede4211edd0303d`
   - 陈述：截至 2026-07-30 核验，guiyang-ipv6 集群的 volcano-system 没有任何 Deployment，说明 Volcano scheduler、admission 和 controllers 尚未部署或不可用。
   - 证据（程序提取，待人工核验）：block b20，第 241-259 行
   - 状态：待审核 / 证据未核验

2. **事实** · `claim-534544f26d12f696`
   - 陈述：截至 2026-07-30 核验，guiyang-ipv6 集群仅有 root、default Queue，缺少业务 canary 和现有任务使用的 shared-flexible-queue。
   - 证据（程序提取，待人工核验）：block b20，第 241-259 行
   - 状态：待审核 / 证据未核验

3. **事实** · `claim-c5e2cf6330729e1c`
   - 陈述：截至 2026-07-30 核验，guiyang-ipv6 集群的 argo 命名空间存在 3 个已持续 13 天的 Pending Pod，必须先定位其调度失败原因，避免将已有异常带入接入后的灰度判断。
   - 证据（程序提取，待人工核验）：block b20，第 241-259 行
   - 状态：待审核 / 证据未核验

4. **事实** · `claim-db6e1c798088c6a7`
   - 陈述：截至 2026-07-30 核验，guiyang-ipv6 集群唯一无污点的 amd64 节点仅有约 57.7Gi 可分配内存，当前无法承接主流 31 CPU / 80Gi amd64 生产任务。
   - 证据（程序提取，待人工核验）：block b20，第 241-259 行
   - 状态：待审核 / 证据未核验

5. **事实** · `claim-9c9542b10ee28362`
   - 陈述：截至 2026-07-30 核验，guiyang-ipv6 成员集群中 karmada-guiyang-ipv6-token Secret 不存在，但本地接入清单曾保存该 ServiceAccount 的 JWT，该 token 当前可用，正式注册前应在已获二次确认后重新签发或轮换 token，并将凭据移出版本库后由受控方式提供。
   - 证据（程序提取，待人工核验）：block b21，第 261-275 行
   - 状态：待审核 / 证据未核验

6. **事实** · `claim-d02343c215c84d9f`
   - 陈述：截至本次核验，guiyang-ipv6 尚未注册到正式 Karmada，当前不具备开启正式调度的条件，禁止添加 dispatch/auto=true 或 has-cpu=true。
   - 证据（程序提取，待人工核验）：block b22，第 277-289 行
   - 状态：待审核 / 证据未核验

### 二、Karmada 调度优化与 Queue 护栏完整交接

7. **推断** · `claim-3fc98b03c1ffa892`
   - 陈述：Queue 的 core trade-off：cap 越大 = 并发越多 = ECS 抑制效果越弱但等待时间越短。
   - 证据（程序提取，待人工核验）：block b30，第 258-270 行
   - 状态：待审核 / 证据未核验

### 三、优化效果观测分析

8. **推断** · `claim-c5e6f8d21297a77a`
   - 陈述：在 2026-07-20 20:45 至 2026-07-21 09:47 的观测中，22:00 前后 post-paid 峰值达 40 台，与历史 22:00 CI 批次吻合；22:08 有 80 个活跃作业和 27 个 Pending，远超 21 台固定机承载上限，溢出到 post-paid 是 COP 软偏好的设计行为。
   - 证据（程序提取，待人工核验）：block b15，第 131-137 行
   - 状态：待审核 / 证据未核验

### 四、非 NPU 队列护栏验证路径

9. **建议** · `claim-5522561303415b90`
   - 陈述：Queue 护栏验证的正式灰度成功标准需与同类高峰基线比较，至少观察两个高峰/回收周期，并检查十分钟 post-paid 节点增量、post-paid 峰值、Pending 等待时长、Job/Work 成功率、新非 NPU Pod 落点及非目标业务回归等指标。
   - 证据（程序提取，待人工核验）：block b17，第 163-174 行
   - 状态：待审核 / 证据未核验

10. **决策** · `claim-ad879f3745e592ba`
    - 陈述：回滚时不得通过删除 post-paid 节点、修改 HNA/Autoscaler 或去除 NPU 硬排除作为回滚方式；应停止创建新的灰度测试 Job、移除 queue override、等待灰度 Job 自然完成。
    - 证据（程序提取，待人工核验）：block b18，第 176-186 行
    - 状态：待审核 / 证据未核验

---

## 审核状态

- [ ] 逐条核对 10 条论断的证据范围
- [ ] 处理已知问题：claim-c5e6f8d21297a77a（时间窗口/历史比较混入）、混合类型拆分
- [ ] 补充 Queue 未验证、argo 超时回滚等遗漏主题
- [ ] 批准后转为 `approved` 并进入 knowledgebase
