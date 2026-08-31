# Phase 5 任务 1 实施报告

> 日期：2026-08-07
> 依据：`docs/phase5-design.md` 任务 1
> 范围：只改动被点名的文件（`update/regeneration_chain.py`、`update/update_chain.py`）+ 3 个新测试文件

---

## 一、代码改动

### 1.1 字段名错配（真 bug，已修）

gh CLI 返回的文件字段是 `path`，代码读的是 `filename`，导致变更文件列表全是空串，
受影响章节识别恒为空。照 `update/update_chain.py:132,246` 已有的兼容写法修复。

| 文件:行号 | 改动 |
|---|---|
| `update/regeneration_chain.py:91` | `identify_affected_sections` 内 `f.get("filename", "")` → `f.get("path") or f.get("filename", "")` |
| `update/regeneration_chain.py:196` | `regenerate_section` 检索 query 构建处，同样改法 |

### 1.2 `regenerate_all_affected` 假成功（真 bug，已修）

原第 339 行是 `# TODO: 将新内容写回文档`，内容从未落盘，但第 341 行照样
`sections_regenerated += 1`。现在改为写回成功才计数。

| 文件:行号 | 改动 |
|---|---|
| `update/regeneration_chain.py:295` | 结果字典新增 `sections_skipped: []` 字段 |
| `update/regeneration_chain.py:315-341` | 文档不存在 / 读取失败 → 记入 `sections_skipped`（`document_not_found` / `read_failed: ...`）后 continue，不再静默跳过 |
| `update/regeneration_chain.py:343-356` | 章节不存在 → 记入 `sections_skipped`（`section_not_found`）后 continue |
| `update/regeneration_chain.py:365-378` | 生成为空 → `sections_failed += 1`；写回成功才 `sections_regenerated += 1`，写回失败计入 `sections_failed` |
| `update/regeneration_chain.py:381-386` | 完成日志补上「跳过」计数 |
| `update/regeneration_chain.py:422-450` | 新增 `_replace_section()`：与 `_extract_section` 对称的正则，定位 `## {section}` 到下一个 `##`，保留标题行只替换正文。用切片拼接而非 `re.sub`，避免新内容里的反斜杠被当转义序列 |
| `update/regeneration_chain.py:452-487` | 新增 `_write_section()`：替换后写文件，定位失败或 IO 失败返回 False |

### 1.3 `update_from_issue` 空操作语义（已修）

原来空操作返回 `success: True, documents_added: 0`，调用方无法区分「成功更新」和「什么都没干」。
新增 `status` 三态字段，`success` 语义保持不变。

| 文件:行号 | 改动 |
|---|---|
| `update/update_chain.py:106` | 结果字典新增 `status`，初值 `"no_changes"` |
| `update/update_chain.py:151-161` | 收尾时按 `documents_added > 0` 判定 `"updated"` / `"no_changes"`，空操作打明确日志 |
| `update/update_chain.py:171` | 异常分支置 `status = "failed"` |

**调用方兼容性核查**：`demo_phase3.py:223`、`test_ascend_ci.py:120`、`verify_fixes.py:111`、
`test_e2e.py:174`、`tests/phase3/test_update_chain.py:93` 五处均只读取
`success` / `documents_added` / `documents_deleted` / `chunks_created`，`status` 是纯新增字段，
无需适配。已跑 `tests/phase3` 回归确认。

---

## 二、测试运行结果

### 2.1 `tests/phase5/`（新增，30 个用例）

```
27 passed, 2 skipped, 1 xfailed, 1 warning in 6.35s
```

| 文件 | 结果 |
|---|---|
| `tests/phase5/test_regeneration_chain.py` | 17 passed, 2 skipped |
| `tests/phase5/test_retry.py` | 6 passed |
| `tests/phase5/test_daemon_duplicate.py` | 4 passed, 1 xfailed |

**2 个 skipped 的原因**（skip 信息已在输出中明确打出）：

```
SKIPPED tests/phase5/test_regeneration_chain.py:310: SKIP 原因：环境变量 ARK_API_KEY
  未设置，无法调用真实 LLM（火山 ARK minimax-m3）。设置后重跑本用例。
SKIPPED tests/phase5/test_regeneration_chain.py:336: 同上
```

真实 LLM 用例（`test_regenerate_section_real_llm`、
`test_regenerate_all_affected_real_llm_writes_back`）的断言按要求写死：
非空、`len > 100`、不含 11 个报错串、且不等于原样输入。**但本次未实际执行**，
因为环境里没有 `ARK_API_KEY`（已确认 shell 环境和 profile 均未设置，
按约束不从任何文件读 key）。

写回链路的验证不依赖 LLM：`test_regenerate_all_affected_writes_back` 用受控生成内容
读回文件断言 `after != before`、新内容在、旧内容（"旧的核心流程描述"）不在、
未受影响章节保持原样。

### 2.2 回归

```
tests/phase3/ + tests/phase4/：31 passed, 12 warnings in 116.88s
```

环境清理已确认：无残留 daemon 进程、无残留 PID 文件、测试向量库目录已删除。

---

## 三、没能完成的事 / 发现的问题

### 3.1 重试机制：已实现，且验证通过（与设计方案的「未验证」表述不同）

设计方案 1.1 把失败重试列为「是否生效未验证」。实际读码后确认
**重试逻辑是真的实现了**，位于 `triggers/scheduler.py:133-181`：
`while attempt <= self.max_retries` 循环，失败后 `time.sleep(retry_delay_seconds)` 再重试。

实测结论（`test_retry.py`，retry_delay 在测试里置 0 / 用 mock 校验入参，未真等 300 秒）：

- 前两次失败第三次成功 → `success == True`，调用 3 次，日志出现恰好 2 条重试记录（含 `1/3`、`2/3`）
- 重试间隔真的按配置休眠 → `time.sleep` 被以 `7` 调用一次
- 三次全失败 → `success == False`，`error` 透出原始异常消息，ERROR 日志带 `exc_info`（异常未被吞掉），共调用 4 次（首次 + 3 次重试）
- `max_retries: 3` / `retry_delay_seconds: 300` 确实从 `config/projects.yaml` 读入

需要说明的语义边界：这个重试包的是**整体调度调用**（如 gh CLI 不可用、配置错误），
单个项目内部的失败由 Orchestrator 隔离处理，不走这个重试。

### 3.2 重复 daemon start：退出码要求不满足，我没改（超出授权范围）

设计方案要求第二次 `start` 满足三点。实测：

| 要求 | 实际 | 结论 |
|---|---|---|
| 输出含已运行提示 | `调度器已在运行 (PID: 82754)，拒绝重复启动` | 通过 |
| PID 文件内容不变 | 前后一致，原进程仍存活，未产生第二个进程 | 通过 |
| 退出码非 0 | **实测为 0** | **不满足** |

根因：`triggers/daemon_mgr.py:99-100` 的 `start()` 只 `print` 后 `return`，
`main()`（第 210-211 行）拿到返回后没有 `sys.exit(1)`。

**我没有修**，因为任务硬约束是「只改上面点名的文件」，`daemon_mgr.py` 不在点名列表里。
该断言以 `xfail(strict=True)` 固化在 `test_duplicate_start_exit_code_nonzero`，
一旦后续授权修复 `daemon_mgr.py`，它会变成 XPASS 提醒收紧。
建议的最小修法：`main()` 里让 `start()` 返回布尔值，重复启动时 `sys.exit(1)`。

### 3.3 首次 start 的 stdout 拿不到（方案里的隐含假设不成立）

`daemon_mgr.py:106` 的「启动调度器守护进程」提示在非 tty 下取不到：
`print` 进了缓冲区，`DaemonContext` 分离进程时直接关闭 fd，缓冲区未 flush 就丢了。
所以首次启动的验证改用「PID 文件写入 + 进程存活」作为判据，已在测试注释里写明。
这不影响功能，但如果将来要靠 stdout 做启动确认，需要在 print 后加 `flush=True`。

### 3.4 向量库初始化的测试陷阱（已绕过，记录备查）

chromadb 0.4.22 会按 settings 缓存 System 实例。如果在每个用例后删除
`persist_directory`，后续用例复用缓存的 System 时会报
`Could not connect to tenant default_tenant`。第一版 fixture 就是这么写的，
16 个用例全 error。已改为 module 级 autouse fixture 统一清理，并在代码注释里写明原因。

### 3.5 安全问题：`update/vector_store.py:40` 硬编码了 SiliconFlow API key

`OpenAIEmbeddings(openai_api_key="sk-...")` 明文写在源码里。
这与设计方案任务 3「提交前 `grep -rn "sk-"` 命中即停下报告」直接冲突——
**这个文件一旦提交，key 就进了 git 历史**。

我没有改动它（不在点名文件列表内），但这是提交前必须处理的阻塞项。
建议：改为 `os.getenv("SILICONFLOW_API_KEY")`，并轮换这把已泄露的 key。

---

## 四、遗留建议（未执行，等你决定）

1. 修 `daemon_mgr.py` 的退出码（见 3.2），顺手给 print 加 `flush=True`（见 3.3）
2. 处理 `vector_store.py` 硬编码 key（见 3.5），提交前阻塞项
3. 设置 `ARK_API_KEY` 后重跑 `pytest tests/phase5/test_regeneration_chain.py -rs`，
   补齐 2 个真实 LLM 用例的实测结果
4. 设计方案 1.2.2 的 `--force` 参数（打通完整调用链）本次未做——
   我收到的任务清单里没有这一项，未擅自扩大范围
