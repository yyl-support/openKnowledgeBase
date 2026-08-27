"""
数据模型：Issue 知识包的数据结构定义

定义了从 Issue 工作流中提取的各类知识的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class PRReference:
    """PR 引用"""
    repo: str           # 仓库（如 "opensourceways/backlog"）
    number: int         # PR 编号
    title: str          # PR 标题
    state: str          # 状态（OPEN | CLOSED | MERGED）
    url: str            # PR URL
    branch: Optional[str] = None  # 分支名（未合入时需要）


@dataclass
class RequirementDoc:
    """需求分析文档"""
    specification: str  # Specification.md 内容
    qa_checklist: str   # QA.md 内容
    pr: PRReference     # 需求分析 PR 引用


@dataclass
class CodeChange:
    """代码变更"""
    pr: PRReference             # 开发 PR 引用
    diff: str                   # 完整 diff
    files: List[Dict]           # 文件列表 [{path, additions, deletions}]
    total_additions: int        # 总新增行数
    total_deletions: int        # 总删除行数


@dataclass
class TestReport:
    """测试报告（可选）"""
    pr: PRReference     # 测试报告 PR 引用
    content: str        # 测试报告内容


@dataclass
class ReleaseInfo:
    """上线信息（可选）"""
    pr: PRReference     # 变更计划 PR 引用
    content: str        # 变更计划内容


@dataclass
class IssueKnowledgePackage:
    """Issue 知识包（完整）"""
    # 基本信息
    issue_number: int
    issue_title: str
    issue_labels: List[str]
    issue_body: str

    # 需求分析
    requirement: Optional[RequirementDoc] = None

    # 代码变更
    code_change: Optional[CodeChange] = None

    # 测试报告
    test_report: Optional[TestReport] = None

    # 上线信息
    release_info: Optional[ReleaseInfo] = None

    # 元数据
    extracted_at: Optional[datetime] = None

    def __post_init__(self):
        if self.extracted_at is None:
            self.extracted_at = datetime.now()

    def has_design_label(self) -> bool:
        """是否有设计标签"""
        return "need_design" in self.issue_labels

    def has_security_label(self) -> bool:
        """是否有安全标签"""
        return "need_security" in self.issue_labels

    def get_changed_files_count(self) -> int:
        """获取变更文件数量"""
        if self.code_change:
            return len(self.code_change.files)
        return 0

    def get_requirement_doc_size(self) -> int:
        """获取需求文档大小（字符数）"""
        if self.requirement:
            return len(self.requirement.specification)
        return 0
