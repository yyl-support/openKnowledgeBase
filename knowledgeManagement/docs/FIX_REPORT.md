# 修复报告

**日期**: 2026-08-21  
**修复人员**: 开发工程师  
**测试报告**: PHASE_E2E_TEST_REPORT.md

---

## 修复的问题

### 问题 1: gh CLI 搜索结果排序错误

**严重程度**: 阻塞

**问题描述**:  
`gh issue list` 命令返回的 Issue 列表没有按创建时间降序排序，导致 `IssueChangeDetector.detect_new_issues()` 无法正确检测最新的 Issue。

**根因**:  
`orchestration/gh_client.py:87` 的 `--search` 参数缺少排序指令。

**修复方案**:  
在 `--search` 参数中添加 `sort:created-desc`。

**修复代码**:

```python
# 修复前
"--search", search_query,

# 修复后
"--search", f"{search_query} sort:created-desc",
```

**影响文件**:
- `orchestration/gh_client.py` (第 87 行)

**验证结果**: ✅ 通过
- 搜索返回的第一个 Issue (#1826) 创建时间晚于第二个 Issue (#1789)
- 排序逻辑正确

---

### 问题 2: 向量化字段名错配 `filename` vs `path`

**严重程度**: 阻塞

**问题描述**:  
`update_chain.py` 期望从 `file_info` 中读取 `filename` 字段，但 GitHub API 返回的字段名是 `filename`（通过 `gh pr view`）或 `path`（可能的其他来源）。当字段不存在时，`file_path` 为空字符串，导致代码变更无法向量化。

**根因**:  
字段名假设与实际 API 返回不一致。

**修复方案**:  
使用兼容性读取：优先读取 `path`，如果不存在则回退到 `filename`。

**修复代码**:

```python
# 修复前
file_path = file_info.get("filename", "")

# 修复后
file_path = file_info.get("path") or file_info.get("filename", "")
```

**影响文件**:
- `update/update_chain.py` (第 132 行 - 删除旧文档时)
- `update/update_chain.py` (第 246 行 - 处理代码变更时)

**验证结果**: ✅ 通过
- 成功读取文件路径 `main.py`
- 向量化添加了 17 个文档

---

### 问题 3: `patch` 字段缺失

**严重程度**: 阻塞

**问题描述**:  
`update_chain.py:247` 期望从 `file_info` 中读取 `patch` 字段，但 `gh pr view --json files` 返回的文件列表**不包含 patch 内容**。导致所有代码变更的 patch 都是空字符串，向量化时被跳过。

**根因**:  
`gh pr view --json files` 只返回文件元数据（路径、增删行数），不包含具体的代码差异。

**修复方案**:  
在 `gh_client.py` 的 `get_pull_request()` 方法中，额外调用 GitHub API 的 `/repos/{owner}/{repo}/pulls/{pr_number}/files` 端点（通过 `gh api` 命令）获取包含 patch 的完整文件信息。

**修复代码**:

```python
def get_pull_request(self, repo: str, pr_number: int) -> PullRequest:
    # 1. 获取基本信息
    cmd = [
        self.cli_path, "pr", "view", str(pr_number),
        "--repo", repo,
        "--json", "number,title,state,headRefName"
    ]
    result = self._run_command(cmd)
    data = json.loads(result)

    # 2. 通过 GitHub API 获取包含 patch 的文件列表
    api_cmd = [
        self.cli_path, "api",
        f"repos/{repo}/pulls/{pr_number}/files",
        "--paginate"
    ]
    try:
        api_result = self._run_command(api_cmd)
        files_with_patch = json.loads(api_result)
    except Exception as e:
        logger.warning(f"获取 PR files 失败: {e}，使用空列表")
        files_with_patch = []

    return PullRequest(
        number=data["number"],
        title=data["title"],
        state=data["state"],
        head_ref=data["headRefName"],
        files=files_with_patch  # 包含 patch 字段
    )
```

**影响文件**:
- `orchestration/gh_client.py` (第 140-166 行)

**验证结果**: ✅ 通过
- 成功获取 patch 字段，第一个文件的 patch 长度为 1019 字符
- patch 内容预览正确（包含 `@app.errorhandler(413)` 等代码）
- 向量化成功创建 17 个 chunks
- 相似度搜索 "logger" 返回 3 个相关结果

---

## 端到端验证

**验证脚本**: `verify_fixes.py`

**验证步骤**:

1. **修复 1 验证**:
   - 调用 `gh.search_issues()` 搜索 10 个 Issue
   - 验证返回结果按创建时间降序排列
   - 结果: ✅ 第一个 Issue (#1826) 创建时间 > 第二个 Issue (#1789)

2. **修复 2 & 3 验证**:
   - 提取 Issue #1611 的知识包
   - 检查 `code_change.files[0]` 是否包含 `filename`/`path` 和 `patch` 字段
   - 执行向量化 `update_from_issue()`
   - 检查 `documents_added > 0`
   - 检查 `vector_store.get_stats()["document_count"] > 0`
   - 执行相似度搜索验证内容可检索
   - 结果: ✅ 所有检查通过

**验证输出**:

```
修复 1: gh CLI 排序: ✅ 通过
修复 2 & 3: 向量化: ✅ 通过
```

**向量化统计**:
- 添加文档数: 17
- 删除文档数: 5
- 创建块数: 17
- 向量库文档总数: 17
- 相似度搜索结果数: 3

---

## 单元测试回归

**命令**: `PYTHONPATH=. python3 -m pytest tests/phase2/test_issue_extractor.py tests/phase3/test_vector_store.py -v`

**结果**:
- 通过: 11
- 跳过: 1
- 失败: 0
- 执行时间: 80.11s

**关键测试用例**:
- ✅ `test_extract_issue_1611` - Issue 提取测试
- ✅ `test_add_documents` - 向量库添加文档测试
- ✅ `test_similarity_search` - 相似度搜索测试
- ✅ `test_delete_by_source` - 按来源删除测试
- ✅ `test_project_isolation` - 项目隔离测试

---

## 修复影响范围

### 受益模块

1. **orchestration/issue_detector.py**:
   - `detect_new_issues()` 现在能正确检测最新的 Issue

2. **extraction/issue_extractor.py**:
   - `_extract_code_change()` 现在能获取完整的 patch 内容

3. **update/update_chain.py**:
   - `_process_code_changes()` 现在能正确读取文件路径和 patch
   - 代码变更能够成功向量化

4. **update/vector_store.py**:
   - 能够存储和检索真实的代码内容

### 不影响的模块

- `config/` - 配置模块未修改
- `triggers/` - 调度触发器未修改
- `extraction/pr_link_parser.py` - PR 链接解析器未修改
- `extraction/backlog_cache.py` - Backlog 缓存未修改

---

## 遗留问题

测试报告中发现的其他问题（未在本次修复范围内）:

### 问题 4: `delete_by_source` 返回值不一致

**严重程度**: 体验问题

**现状**: 函数返回 `None`，调用方无法知道删除了多少文档

**建议**: 修改 `vector_store.py:92-119` 返回删除的文档数量

### 问题 5: 空操作但返回成功

**严重程度**: 已通过问题 2 & 3 的修复解决

**现状**: 修复后不再出现空操作，向量化正常工作

### 问题 6: `regeneration_chain.py` 无测试无调用

**严重程度**: 功能缺失

**现状**: 文件存在但未被使用，无测试覆盖

**建议**: 添加测试或移除未使用的代码

### 问题 7: 需求文档提取失败时日志掩盖问题

**严重程度**: 体验问题

**现状**: 无法区分"数据不存在"和"提取失败"

**建议**: 改进日志级别，区分正常缺失和异常失败

---

## 总结

所有 3 个阻塞问题已修复并验证通过:

1. ✅ gh CLI 搜索结果现在按创建时间降序排列
2. ✅ 向量化能正确读取文件路径（兼容 `path` 和 `filename`）
3. ✅ 向量化能获取完整的代码 patch 内容

**系统状态**: 
- Issue 检测功能恢复正常
- 代码变更提取功能恢复正常
- 向量化功能恢复正常
- 端到端流程可以正常工作

**测试覆盖**:
- 单元测试: 11/12 通过
- 端到端测试: 2/2 通过
- 验证脚本: 所有检查通过

**下一步建议**:
1. 在真实环境中运行 orchestrator，观察完整的 Issue → 提取 → 向量化流程
2. 修复遗留的体验问题（问题 4、7）
3. 为 `regeneration_chain.py` 添加测试或移除未使用代码
