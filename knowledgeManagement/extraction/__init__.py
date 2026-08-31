"""
extraction 包：Issue 知识提取层

负责从 Issue 工作流中提取完整的变更知识，包括：
- 需求分析文档（从 backlog 仓库）
- 代码变更（从开发 PR）
- 测试报告（从测试 PR）
- 上线信息（从 release-mgmt PR）
"""

from .models import (
    PRReference,
    RequirementDoc,
    CodeChange,
    TestReport,
    ReleaseInfo,
    IssueKnowledgePackage
)
from .pr_link_parser import PRLinkParser
from .backlog_cache import BacklogCache
from .issue_extractor import IssueKnowledgeExtractor

__all__ = [
    'PRReference',
    'RequirementDoc',
    'CodeChange',
    'TestReport',
    'ReleaseInfo',
    'IssueKnowledgePackage',
    'PRLinkParser',
    'BacklogCache',
    'IssueKnowledgeExtractor',
]
