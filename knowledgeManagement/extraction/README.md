# Phase 2: Issue 知识提取层

## 概述

Phase 2 实现了从 Issue 工作流中提取完整变更知识的功能，包括：
- 需求分析文档（从 backlog 仓库）
- 代码变更（从开发 PR）
- 测试报告（从测试 PR，可选）
- 上线信息（从 release-mgmt PR，可选）

## 目录结构

```
extraction/                      # Phase 2 核心模块（独立目录）
├── __init__.py
├── models.py                    # 数据模型定义
├── pr_link_parser.py            # PR 链接解析器
├── backlog_cache.py             # backlog 仓库缓存管理
└── issue_extractor.py           # Issue 知识提取器

orchestration/                   # Phase 1 模块（已集成 Phase 2）
└── orchestrator.py              # 调度器（已增强）

tests/phase2/                    # Phase 2 测试
├── test_pr_link_parser.py       # PR 链接解析测试
├── test_backlog_cache.py        # 缓存管理测试
├── test_issue_extractor.py      # 知识提取测试
└── integration_test.sh          # 集成测试脚本

demo_phase2.py                   # 演示脚本
```

## 核心功能

### 1. PR 链接解析器 (PRLinkParser)

从 Issue 评论中解析不同类型的 PR 链接：

```python
from extraction.pr_link_parser import PRLinkParser

parser = PRLinkParser()

# 解析需求分析 PR
requirement_pr = parser.parse_requirement_pr(comments)

# 解析开发 PR
development_pr = parser.parse_development_pr(comments, project_repo)

# 解析测试报告 PR
test_pr = parser.parse_test_pr(comments)

# 解析变更计划 PR
release_pr = parser.parse_release_pr(comments)
```

### 2. backlog 缓存管理器 (BacklogCache)

管理 backlog 仓库的本地缓存：

```python
from extraction.backlog_cache import BacklogCache

cache = BacklogCache()

# 确保仓库存在且是最新的
cache.ensure_repo()

# 读取需求文档
spec = cache.get_requirement_doc(1611, "Specification.md")

# 列出 Issue 的所有文档
docs = cache.list_issue_docs(1611)
```

### 3. Issue 知识提取器 (IssueKnowledgeExtractor)

提取 Issue 的完整知识包：

```python
from extraction.issue_extractor import IssueKnowledgeExtractor
from orchestration.gh_client import GitHubCLI

gh = GitHubCLI()
extractor = IssueKnowledgeExtractor(gh)

# 提取知识
knowledge = extractor.extract(
    backlog_repo="opensourceways/backlog",
    issue_number=1611,
    project_repo="opensourceways/forum-reply-robot"
)

# 使用知识包
print(f"变更文件数: {knowledge.get_changed_files_count()}")
print(f"需求文档大小: {knowledge.get_requirement_doc_size()}")
```

## 使用方法

### 快速开始

运行演示脚本：

```bash
python3 demo_phase2.py 1611
```

### 集成到调度器

调度器已自动集成知识提取功能：

```python
from orchestration.orchestrator import KnowledgeOrchestrator

orchestrator = KnowledgeOrchestrator()

# 调度单个项目（会自动提取知识）
result = orchestrator.schedule_project("forum-reply-robot", force=True)
```

知识包会自动保存到 `work/{project_name}/issue_knowledge.json`

## 测试

### 运行单元测试

```bash
# 测试 PR 链接解析器
python3 -m pytest tests/phase2/test_pr_link_parser.py -v

# 测试 backlog 缓存（需要网络）
python3 -m pytest tests/phase2/test_backlog_cache.py -v -m integration

# 测试知识提取器（需要网络和 gh CLI 认证）
python3 -m pytest tests/phase2/test_issue_extractor.py -v -m integration
```

### 运行集成测试

```bash
bash tests/phase2/integration_test.sh
```

## 数据模型

### IssueKnowledgePackage

完整的 Issue 知识包：

```python
@dataclass
class IssueKnowledgePackage:
    # 基本信息
    issue_number: int
    issue_title: str
    issue_labels: List[str]
    issue_body: str
    
    # 需求分析
    requirement: Optional[RequirementDoc]
    
    # 代码变更
    code_change: Optional[CodeChange]
    
    # 测试报告
    test_report: Optional[TestReport]
    
    # 上线信息
    release_info: Optional[ReleaseInfo]
    
    # 元数据
    extracted_at: datetime
```

### 辅助方法

- `has_design_label()`: 是否有设计标签
- `has_security_label()`: 是否有安全标签
- `get_changed_files_count()`: 获取变更文件数量
- `get_requirement_doc_size()`: 获取需求文档大小

## 配置

### backlog 缓存目录

默认缓存目录：`/tmp/backlog-cache`

自定义缓存目录：

```python
from extraction.backlog_cache import BacklogCache

cache = BacklogCache(cache_dir="/path/to/custom/cache")
```

### GitHub CLI

确保 gh CLI 已安装并认证：

```bash
# 安装 gh CLI
brew install gh

# 认证
echo $GH_TOKEN | gh auth login --with-token

# 验证
gh auth status
```

## 性能

- 单个 Issue 提取耗时：约 10-30 秒
- backlog 仓库初次 clone：约 1-2 分钟
- backlog 仓库更新（pull）：约 5-10 秒

## 错误处理

提取器具有良好的错误处理机制：

- PR 链接缺失：记录警告，返回 None
- 文档不存在：尝试多种路径，优雅降级
- gh API 失败：捕获异常，记录错误日志
- 网络超时：设置合理的超时时间

## 与 Phase 1 的集成

Phase 2 完全兼容 Phase 1，不会修改 Phase 1 的代码。集成点：

1. **调度器增强**：`orchestrator.py` 在执行全量更新前先提取知识
2. **知识包保存**：提取的知识包保存到 `work/{project}/issue_knowledge.json`
3. **解耦设计**：extraction 模块独立，可单独使用

## 下一步：Phase 3

Phase 3 将基于 Phase 2 的知识包实现增量更新决策：

- 根据标签、文件数量、文档大小判断全量/增量
- 向量化知识
- 章节重新生成
- 成本优化

## 示例输出

```json
{
  "issue_number": 1611,
  "issue_title": "[缺陷] token刷新接口，未配置 Flask 的 MAX_CONTENT_LENGTH 限制，可能造成OOM",
  "issue_labels": ["bug", "accepted", "complete-develop"],
  "has_requirement": false,
  "has_code_change": true,
  "has_test_report": false,
  "has_release_info": true,
  "changed_files_count": 5,
  "requirement_doc_size": 0,
  "extracted_at": "2026-08-20T20:58:43.601581"
}
```

## 故障排除

### 问题：gh CLI 未认证

```bash
gh auth status
# 如果未认证，运行：
echo $GH_TOKEN | gh auth login --with-token
```

### 问题：backlog 仓库 clone 失败

检查网络连接，或手动 clone：

```bash
git clone https://github.com/opensourceways/backlog.git /tmp/backlog-cache/backlog
```

### 问题：找不到需求文档

可能原因：
1. PR 未合入到 backlog 仓库
2. 文档路径不标准
3. 分支名称错误

检查日志查看详细错误信息。

## 贡献

欢迎提交 Issue 和 PR！

## 许可证

与主项目相同
