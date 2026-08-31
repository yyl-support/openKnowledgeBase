# Phase 6 设计方案：接通决策分叉 + 给 regeneration_chain 装上入口

> 日期：2026-08-27
> 范围：只解决架构文档第 10 节的缺口 1 和缺口 2（缺口 3、5 按指示不处理，缺口 4 未在本次范围）

---

## 一、问题现状

### 缺口 1：决策层判了但没人听

`orchestrator.schedule_project()` 拿到 Issue 后直接调 `_execute_full_update()`，硬编码走全量流水线。

`decision_chain.decide()` 能返回 `{"decision": "incremental", ...}`，但 orchestrator 从头到尾没有 import 过它，更没有消费方。也就是说决策链目前是**孤立组件**——Phase 3 的测试单独调它能通，但生产链路上它不存在。

### 缺口 2：regeneration_chain 只有测试没有调用者

387 行代码，19 个测试（含 2 个真实 LLM 用例），零生产调用。

它的定位本来很明确：增量更新时，向量库写完了，但 `knowledgeBase/{project}/*.md` 这些**给人读的文档**还是旧的。`regenerate_all_affected()` 就是负责把受影响章节重新生成并写回去的。

### 两个缺口是同一件事

```
现在：Issue → 提取 → 【硬编码全量】→ pipeline.py 重建全部文档

应该：Issue → 提取 → 决策 → full        → pipeline.py 重建全部文档
                          └→ incremental → update_chain 写向量库
                                        → regeneration_chain 更新受影响章节
```

缺口 2 的入口就在缺口 1 要新建的增量路径里。分开做没意义，一起做。

---

## 二、实现方案

### 2.1 orchestrator 引入决策

在 `schedule_project()` 里，提取完知识包后先决策，再分派。

**改动点**：`schedule_project()` 现在是「检测 Issue → `_execute_full_update(project_name, project, issue_number)`」，只传了 issue 编号，知识提取发生在 `_execute_full_update` 内部。这个结构不利于决策——决策需要知识包，但知识包在全量方法里面。

**调整**：把知识提取从 `_execute_full_update` 里提出来，放到 `schedule_project()`：

```
schedule_project():
    检测新 Issue
    knowledge_package = issue_extractor.extract(...)      # 上移
    保存 issue_knowledge.json                              # 上移
    decision = decision_chain.decide(pkg, days_since)     # 新增
    if decision == "full" 或 update_policy.incremental 为 False:
        _execute_full_update(project_name, project, pkg)
    else:
        _execute_incremental_update(project_name, project, pkg)
```

`_execute_full_update` 的签名从 `(project_name, project, issue_number)` 改成 `(project_name, project, knowledge_package)`，内部删掉提取逻辑，直接用传入的包。

**`update_policy.incremental` 的作用**：配置里这个开关是 `True`/`False`。为 `False` 时强制全量，不管 LLM 怎么判。这是人工兜底，优先级高于决策链。

### 2.2 新增 `_execute_incremental_update()`

```
_execute_incremental_update(project_name, project, knowledge_package):
    start_time = now

    # 第一步：写向量库
    update_chain = KnowledgeUpdateChain(project_name)
    upd_result = update_chain.update_from_issue(knowledge_package)

    if upd_result["status"] == "failed":
        return UpdateResult(success=False, mode="incremental", error=...)

    # 第二步：更新人读文档
    knowledge_base_dir = {base_dir}/{knowledge_dir}/{project_name}
    regen_chain = SectionRegenerationChain(project_name)
    regen_result = regen_chain.regenerate_all_affected(pkg, knowledge_base_dir)

    # 汇总
    return UpdateResult(
        success = upd_result 未失败 and regen_result["success"],
        mode = "incremental",
        ...
    )
```

**成功判定的取舍**：`update_from_issue` 返回 `status: "no_changes"`（空操作）时算不算成功？

我的判断：**算成功，但要在日志和 UpdateResult 里明确标出来**。因为「这个 Issue 确实没带来需要索引的变更」是合法结果，不是故障。但绝不能像以前那样悄无声息——`UpdateResult` 加一个 `detail` 字段承载 `status` 和章节统计，日志明确打印 `no_changes`。

如果 `regeneration_chain` 因为缺 `ARK_API_KEY` 而所有章节都生成失败，那 `regen_result["sections_failed"] > 0` 且 `sections_regenerated == 0`，这种情况**判定为失败**——因为用户预期是文档被更新了，结果没更新，静默放过就是假成功。

### 2.3 UpdateResult 扩展

现有字段：`project_name` / `success` / `mode` / `issue_number` / `elapsed_seconds` / `cost_usd` / `error`。

新增一个 `detail: Optional[dict] = None`，增量路径填入：

```python
{
    "vector_status": "updated" | "no_changes",
    "documents_added": int,
    "documents_deleted": int,
    "chunks_created": int,
    "sections_regenerated": int,
    "sections_failed": int,
    "sections_skipped": [...],
    "updated_documents": [...]
}
```

全量路径保持 `detail=None`，不动它。

用 `Optional` 带默认值，现有构造调用不受影响。

### 2.4 知识库目录的取法

`regenerate_all_affected` 需要 `knowledge_base_dir`。从配置拼：

```python
storage = self.config.global_config.storage
knowledge_base_dir = os.path.join(
    storage["base_dir"],        # /Users/gorden/huawei/code/openKnowledgeBase
    storage["knowledge_dir"],   # knowledgeBase
    project_name                # forum-reply-robot
)
```

**得确认 `GlobalConfig` 在 SystemConfig 里的字段名**——`models.py` 里叫 `global`（YAML 键）还是 `global_config`（Python 属性）需要实现时核对，`global` 是 Python 关键字，肯定做了别名处理。

**目录不存在时怎么办**：`regenerate_all_affected` 内部已经处理了——文档不存在会记进 `sections_skipped` 并标 `document_not_found`。所以不需要额外建目录，但要在日志里提示「知识库目录不存在，本次增量只更新了向量库」。

### 2.5 成本记录：真实 token 统计

**已实测确认**可行：`get_openai_callback()` 能从火山 ARK 拿到 token 数（测试调用返回 `prompt_tokens: 180, completion_tokens: 38`）。但 `cb.total_cost` 是 `0.0`——LangChain 的内置价格表只认 OpenAI 模型，`minimax-m3` 的价格得自己算。

**实现**：

```python
from langchain_community.callbacks.manager import get_openai_callback

with get_openai_callback() as cb:
    result = self.chain.run(**input_data)

tokens = {"prompt": cb.prompt_tokens, "completion": cb.completion_tokens}
cost = calc_cost("minimax-m3", tokens)   # 用配置里的单价算
```

`decision_chain.decide()` 和 `regeneration_chain.regenerate_section()` 各包一层，返回值里带上 token 数和成本。

**定价配置**（`config/projects.yaml` 的 `global` 段新增）：

```yaml
  pricing:
    # 单位：美元/百万 token。渠道方定价可能与官方价不同，以控制台账单为准后修正。
    minimax-m3:
      input_per_1m: 0.60
      output_per_1m: 2.40
      # 来源：MiniMax 官方公开价
    deepseek-v4-flash:
      input_per_1m: 0.44
      output_per_1m: 1.32
      # 来源：单一来源 morphllm.com 称 2026-08-16 调价后的高峰价，
      # 与其他五家来源的 $0.14/$0.28 冲突，未能取到官方一手价证实
      # （api-docs.deepseek.com 与 deepseek.ai 均被网络策略拦截）。
      # 按用户指示取高峰价。本条目当前未被使用，见下方说明。
    Qwen/Qwen3-Embedding-8B:
      input_per_1m: 0.28
      output_per_1m: 0.0
      currency: CNY
      # 来源：用户提供的 SiliconFlow 实际单价 ¥0.000280/K tokens。
      # embedding 只计输入，无输出计费。
```

**币种混用的处理**：minimax 与 deepseek 是美元，embedding 是人民币。不做汇率折算——汇率会过期，折算出来的合计又成了一个「看着精确其实在编」的数字。

改为**分币种累加**：`UpdateResult.detail` 里记 `cost_usd` 和 `cost_cny` 两个字段，各自独立汇总，不相加。`ProjectMetadata.total_cost_usd` 保持原样只累加美元部分（该字段已存在，不破坏），人民币部分记在 `detail` 里。

每条定价必须带 `currency`，缺失时视为 `USD` 并打 warning。

**能统计与不能统计的边界**：

| 模型 | 用在哪 | 本次能否统计 | 原因 |
|---|---|---|---|
| `minimax-m3` | 决策、章节重生成 | ✅ | LangChain 直接调，callback 可取 |
| `Qwen3-Embedding-8B` | 向量化 | ✅ | 同上 |
| `deepseek-v4-flash` | 四层流水线 Layer 2（UA） | ❌ | `subprocess.run(pipeline.py)` → UA → 再起 Claude Code subagent，隔两层独立进程，callback 伸不进去 |

所以**全量路径的 `estimated_cost = 6.0` 本次不修**，继续留着并在注释里标明是占位值。要统计得解析 pipeline 的 stdout，属独立工作。

DeepSeek 的定价条目先写进配置备查，本次代码不读它。

### 2.6 定价读取的降级

单价缺失时（配置里没这个模型、或值为占位符）：记 `cost_usd = 0.0`，打一条 warning 说明「模型 X 无定价配置，成本记 0」。

**不能静默记 0**——那又是一个假成功。日志必须能看出「这次的 0 是因为没配单价」而不是「这次真的没花钱」。

---

## 三、测试方案

新建 `tests/phase6/`。

### 3.1 决策分派测试（mock，不烧钱）

| 用例 | 构造 | 断言 |
|---|---|---|
| 决策 full → 走全量 | mock `decide` 返回 `full` | `_execute_full_update` 被调用，`_execute_incremental_update` 未被调用 |
| 决策 incremental → 走增量 | mock `decide` 返回 `incremental` | 反之 |
| `update_policy.incremental=False` 强制全量 | 配置改 False + mock 决策返 `incremental` | 仍走全量，日志有「配置强制全量」 |
| 决策链异常不阻塞 | mock `decide` 抛异常 | 降级走全量，不让整个调度挂掉 |

### 3.2 增量路径测试

| 用例 | 断言 |
|---|---|
| 向量库写入成功 + 章节重生成成功 | `success=True`，`detail` 里两边计数都 > 0 |
| 向量库 `no_changes` | `success=True`，`detail["vector_status"] == "no_changes"`，日志明确 |
| 向量库 failed | `success=False`，不继续调 regeneration |
| 章节全部失败 | `success=False`（假成功防线） |
| 知识库目录不存在 | `sections_skipped` 非空，日志有提示 |

### 3.3 端到端（真实调用，1 次）

用 Issue #1611（有 5 个变更文件，之前验证过能提取到 patch）跑一次真实增量：

```bash
PYTHONPATH=. python3 triggers/cli.py schedule forum-reply-robot --force
```

**断言**：
- 日志出现「决策: incremental」或「决策: full」（明确打出来）
- 若走增量：向量库文档数增加，`knowledgeBase/forum-reply-robot/` 下有文件 mtime 变新
- `UpdateResult.detail` 非空且字段完整

**注意**：#1611 的决策结果取决于 LLM 判断，可能判全量。如果判了全量，就手动构造一个小变更的知识包直接调 `_execute_incremental_update` 验证增量路径。不为了走通增量而篡改决策。

---

## 四、不做的事

1. **不实现并发**（缺口 3，你说不管）
2. **不轮换密钥**（缺口 5，你说不管）
3. **不重构 pipeline.py 的契约校验**（缺口 4，未在本次范围）
4. **不给全量路径补真实成本统计**——那是另一件事，本次只保持现状并标注
5. **不改 decision_chain 的 prompt 或判定逻辑**——它工作正常，只是没人调用

---

## 五、执行方式

按既定流程：

```
方案（本文档）→ 你审核 → 开发 subagent 实施 → 测试 subagent 验证 → 我审报告 → 有问题再派修复
```

开发和测试严格分离，测试 subagent 只读禁改。

---

## 六、已确认的决策

以下四点已由用户拍定，实现时按此执行：

| 决策点 | 结论 |
|---|---|
| 成本统计方式 | 用 LangChain callback 取**真实 token 数**，单价放 config 可配置。不用估算公式。 |
| `no_changes` 是否算成功 | **算成功**，但 `detail` 和日志必须明确标出 `vector_status: no_changes` |
| 决策链异常时 | **直接失败**，不降级走全量（避免异常时烧掉约 $6） |
| `update_policy.incremental=False` | 强制全量，**优先级高于 LLM 决策**，作为人工兜底 |

DeepSeek 单价按高峰价 `$0.44/$1.32` 记入配置备查（该条目本次不被代码使用）。

---

## 七、遗留风险

1. **`schedule_project` 结构调整**：知识提取从 `_execute_full_update` 上移到 `schedule_project`，后者签名从收 `issue_number` 改成收 `knowledge_package`。这是必要重构（决策需要知识包），但动了 Phase 1 的既有结构，`tests/test_orchestrator.py` 的 mock 可能要跟着改。

2. **DeepSeek 单价来源不可靠**：五家来源说 `$0.14/$0.28`，一家说 8/16 调价后高峰 `$0.44/$1.32`，官方页取不到。已按指示取高峰价，但**未经官方证实**，注释里写明了冲突。将来做全量成本统计前必须核实，且要处理高峰/非高峰分档。

3. **币种不统一**：embedding 计价为人民币，两个生成模型为美元。本次不做汇率折算，改为分币种独立累加（`cost_usd` / `cost_cny`）。代价是拿不到「本次总共花了多少」的单一数字，需要时再补汇率配置。

4. **全量路径成本仍是占位值 `6.0`**：跨进程取不到 token，本次不修。
