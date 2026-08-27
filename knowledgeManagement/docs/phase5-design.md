# Phase 5 设计方案：收尾验证 + 脚本固化 + 提交 + 多项目

> 日期：2026-08-26
> 执行顺序：**任务1（补完未验证项） → 任务4（脚本固化） → 任务3（提交代码） → 任务2（多项目验证）**
> 顺序理由：先把功能缺口补齐，再把重复操作固化成脚本，然后提交这一批干净成果，最后用固化好的脚本去做多项目验证（验证时能直接复用脚本，且出问题可回滚到已提交的干净点）

---

## 任务 1：补完未验证项

### 1.1 现状（引自 `PHASE_E2E_TEST_REPORT.md`）

| 缺口 | 具体表现 |
|---|---|
| `regeneration_chain.py` | 387 行，3 个公开方法，**零测试、零调用入口** |
| 完整调用链 | scheduler → orchestrator → extractor → decision → update 从未一次跑通（轮询间隔未到被跳过） |
| 失败重试 | `max_retries: 3` / `retry_delay_seconds: 300` 配置存在，**是否生效未验证** |
| 重复 daemon start | 是否正确拒绝未验证 |

### 1.2 目标与验证标准

**1.2.1 给 `regeneration_chain.py` 建测试**

三个方法逐个覆盖：

| 方法 | 测试点 | 验证标准 |
|---|---|---|
| `identify_affected_sections` | 给定知识包 + 现有文档，识别受影响章节 | 返回非空章节列表，且章节名能在源文档中找到 |
| `regenerate_section` | 单章节重新生成 | 返回文本非空、长度 > 100 字符、不含 LLM 报错串 |
| `regenerate_all_affected` | 批量重生成 | 返回结果数 == 受影响章节数，无静默跳过 |
| `_extract_section` | 章节切分（纯函数） | 边界情况：章节不存在返回空、末章节能取到结尾 |

**关键约束**：`regenerate_section` 走真实 LLM（火山 ARK minimax-m3）。测试必须断言"返回内容是真的生成结果"，不能只断言 `success == True`——这正是之前踩的假成功坑。

**1.2.2 打通完整调用链**

问题根因：`scheduler.py` 检查 `last_update_time`，3.5 天未到就跳过。

方案：**加 `--force` 参数绕过间隔检查**，不改动正常逻辑。

- `orchestration/cli.py` 加 `--force` 传递给 `orchestrator.schedule_project(force=True)`
- `schedule_project` 在 `force=True` 时跳过 `_should_poll` 判断
- 验证：`python -m orchestration.cli run --project forum-reply-robot --force`，日志必须依次出现 Issue 检测 → 知识提取 → 决策 → 向量写入四段，且 `documents_added > 0`

**1.2.3 验证失败重试**

方案：注入可控失败。在测试中 mock `gh_client.search_issues` 前两次抛异常、第三次成功。

验证标准：
- 日志出现 2 次 retry 记录
- 最终 `success == True`
- 若 mock 三次都失败，`success == False` 且不吞异常

**1.2.4 验证重复 daemon start**

`daemon_mgr.py start` 两次，第二次必须：退出码非 0、输出含已运行提示、PID 文件内容不变。

### 1.3 产出

- `tests/phase5/test_regeneration_chain.py`
- `tests/phase5/test_retry.py`
- `tests/phase5/test_daemon_duplicate.py`
- `orchestration/cli.py` 与 `orchestrator.py` 的 `--force` 改动
- `docs/phase5-task1-report.md`

---

## 任务 4：脚本固化

### 4.1 只做 3 个核心脚本

来源：`scripts-automation-plan.md` 标记 ⭐⭐⭐ 的项。**不做**中低优先级的（文档生成、目录初始化、代码规范、性能基准）——那些是推测性需求，等真的重复三次以上再说。

| 脚本 | 解决的重复劳动 | 验证标准 |
|---|---|---|
| `scripts/test_phase.sh` | 每个 Phase 我都手写一遍 pytest 命令 + 统计 | `./scripts/test_phase.sh 3` 输出通过/失败/跳过数，退出码反映结果 |
| `scripts/check_deps.py` | 每个 Phase 都手动 pip list \| grep | `python scripts/check_deps.py --phase 4` 列出缺失包并给出安装命令 |
| `scripts/verify_no_fake_success.py` | 反复手查"返回 True 但实际啥也没干" | 扫描向量库文档数、检查 `documents_added` 与实际写入是否一致 |

### 4.2 第三个脚本的设计要点

这是最有价值的一个，因为假成功是本项目反复踩的坑。检查项：

1. 向量库目录存在且非空（`vectordb/{project}/` 下有 chroma.sqlite3 且 size > 0）
2. `similarity_search` 随机查询返回结果数 > 0
3. 返回文档的 `page_content` 长度 > 50（不是空串占位）
4. 最近一次 update 的 `documents_added` 与向量库文档数增量一致

任一失败 → 退出码 1 + 明确指出哪一项。

### 4.3 产出

- 3 个脚本 + `scripts/README.md`（用法说明）

---

## 任务 3：提交代码

### 3.1 现状

`git status` 显示 22 个未跟踪项，其中混杂了：
- 正式代码：`config/` `extraction/` `orchestration/` `triggers/` `update/` `tests/`
- 临时测试脚本：`test_ark_all.py` `test_ark_api.py` `test_embeddings_api.py` `test_e2e.py` `test_ascend_ci.py`
- 运行时产物：`vectordb/` `logs/` `run/` `work/` `.pytest_cache/` `.DS_Store`
- 报告文档：`PHASE*_DELIVERY.md` `FIX_REPORT.md` `PHASE_E2E_TEST_REPORT.md`

### 3.2 处理方案

**先加 `.gitignore`**：
```
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
vectordb/
logs/
run/
work/
.env
```

**临时测试脚本**：根目录那 5 个 `test_*.py` 是调 API 时的一次性验证脚本，移到 `scripts/manual_checks/` 归档，不删（里面有已验证的正确 URL 和调用方式，有参考价值）。

**报告文档**：`PHASE*_DELIVERY.md` 和 `FIX_REPORT.md` 移到 `docs/` 下统一管理。

**分批提交**（不做一个巨型 commit）：
1. `chore: 添加 .gitignore`
2. `feat(phase1): Issue 检测与调度编排`
3. `feat(phase2): Issue 知识提取`
4. `feat(phase3): 增量更新与向量存储`
5. `feat(phase4): 定时调度与守护进程`
6. `feat(phase5): 补完测试 + 脚本工具`
7. `docs: 各阶段设计与测试报告`

### 3.3 安全检查（提交前必做）

- `grep -rn "sk-\|ark-\|ghp_\|gho_"` 扫描待提交文件，命中即停下报告
- 确认 `config.yaml` 里是 `${ENV_VAR}` 占位而非明文
- 确认 `.env` 不在待提交列表

**分支**：在 `feat/knowledge-engineering-phase1-5` 上提交，不直接动 master。

### 3.4 产出

- 7 个 commit + 提交前安全扫描结果

---

## 任务 2：多项目验证

### 2.1 目标

验证"切忌不能串项目"这条硬约束真的成立。

### 2.2 配置

`projects.yaml` 加入第二个项目 `ascend-ci-deployment`（此前已单独跑通过一次）：

```yaml
  ascend-ci-deployment:
    repo_path: /tmp/ascend-ci-deployment
    issue_tracking:
      backlog_repo: opensourceways/backlog
      search_query: ascend-ci-deployment state:closed
      poll_interval: 3.5
    ...
```

### 2.3 隔离验证矩阵

| 隔离维度 | 验证方法 | 通过标准 |
|---|---|---|
| Issue 搜索 | 两项目各跑一次，比对返回 issue 列表 | 交集为空；每个 issue 的 project 标签与项目名一致 |
| 向量库 | 检查 `vectordb/` 子目录 | 两个独立目录；A 的 similarity_search 不返回 B 的内容 |
| 知识文档 | 检查 `knowledgeBase/` | 两个独立目录，无交叉写入 |
| metadata | 检查 `projects.yaml` 的 metadata 段 | 两项目的 `last_issue_number` 独立更新 |
| 并发 | `max_concurrent_updates: 3` 下同时跑 | 无文件写入冲突，两项目结果都正确 |

**串项目的判定**：只要 A 项目的向量库里出现 B 项目的代码内容，或 metadata 被写到对方名下，即为失败，立即停下报告。

### 2.4 产出

- `projects.yaml` 更新
- `docs/phase5-task2-multiproject-report.md`（含隔离验证矩阵实测结果）

---

## 执行方式

严格遵守测试与开发分离：

```
任务1 → 开发 subagent 实施 → 测试 subagent 验证 → 我审报告 → 有问题再派修复 subagent
任务4 → 开发 subagent 实施 → 我自己跑一遍脚本验证
任务3 → 我自己做（涉及 git 与密钥扫描，不外派）
任务2 → 测试 subagent 验证（只读，禁止改代码）→ 我审报告
```

每个任务完成后我向你汇报，不连续推进。

---

## 风险与取舍

1. **`--force` 参数是新增能力**，不是纯测试改动。理由：没有它就无法验证完整链路，且这个参数本身在运维时也需要（手动触发更新）。如果你觉得不该加，我改用直接改 metadata 时间戳的方式绕过。

2. **regeneration_chain 测试要花真钱**（调 ARK）。预估 3-5 次调用，成本可忽略。

3. **提交前的临时脚本移动**会改变文件路径，如果你想保持原位我就只加 .gitignore 不动它们。

4. **`update_from_issue()` 空操作仍返回 success: True** 这个设计问题本方案未处理。我的判断：这是语义定义问题（"没有需要更新的内容"确实不算失败），但应该在返回值里明确区分。如果你要修，我加到任务 1。
