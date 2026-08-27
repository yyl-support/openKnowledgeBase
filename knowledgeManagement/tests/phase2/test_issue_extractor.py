"""
测试 Issue 知识提取器
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extraction.issue_extractor import IssueKnowledgeExtractor
from extraction.backlog_cache import BacklogCache
from orchestration.gh_client import GitHubCLI


@pytest.fixture
def gh_client():
    """GitHub CLI 客户端"""
    return GitHubCLI()


@pytest.fixture
def extractor(gh_client):
    """知识提取器"""
    return IssueKnowledgeExtractor(gh_client)


# 单元测试（不需要网络）
def test_extractor_initialization(gh_client):
    """测试提取器初始化"""
    extractor = IssueKnowledgeExtractor(gh_client)

    assert extractor.gh_client == gh_client
    assert extractor.pr_parser is not None
    assert extractor.backlog_cache is not None


def test_extractor_with_custom_cache(gh_client):
    """测试使用自定义缓存"""
    custom_cache = BacklogCache(cache_dir="/tmp/custom-cache")
    extractor = IssueKnowledgeExtractor(gh_client, custom_cache)

    assert extractor.backlog_cache == custom_cache


# 集成测试（需要网络和 gh CLI 认证）
@pytest.mark.integration
@pytest.mark.slow
def test_extract_issue_1611(extractor):
    """集成测试：提取 Issue #1611 的知识"""
    knowledge_package = extractor.extract(
        backlog_repo="opensourceways/backlog",
        issue_number=1611,
        project_repo="opensourceways/forum-reply-robot"
    )

    # 基本信息
    assert knowledge_package.issue_number == 1611
    assert knowledge_package.issue_title is not None
    assert len(knowledge_package.issue_labels) > 0

    # 应该有代码变更
    if knowledge_package.code_change:
        assert knowledge_package.code_change.pr.number == 177
        assert len(knowledge_package.code_change.files) > 0
        assert knowledge_package.code_change.diff is not None
        print(f"代码变更: {len(knowledge_package.code_change.files)} 个文件")
    else:
        print("警告: 未找到代码变更")

    # 可能有需求分析文档（取决于 PR 是否已合入）
    if knowledge_package.requirement:
        assert knowledge_package.requirement.specification is not None
        print(f"需求文档: {len(knowledge_package.requirement.specification)} 字符")
    else:
        print("提示: 需求文档未找到（PR 可能未合入）")

    # 测试辅助方法
    print(f"变更文件数: {knowledge_package.get_changed_files_count()}")
    print(f"需求文档大小: {knowledge_package.get_requirement_doc_size()}")
    print(f"有设计标签: {knowledge_package.has_design_label()}")
    print(f"有安全标签: {knowledge_package.has_security_label()}")


@pytest.mark.integration
@pytest.mark.slow
def test_knowledge_package_methods(extractor):
    """集成测试：测试知识包的辅助方法"""
    knowledge_package = extractor.extract(
        backlog_repo="opensourceways/backlog",
        issue_number=1611,
        project_repo="opensourceways/forum-reply-robot"
    )

    # 测试辅助方法
    changed_files_count = knowledge_package.get_changed_files_count()
    assert isinstance(changed_files_count, int)
    assert changed_files_count >= 0

    requirement_doc_size = knowledge_package.get_requirement_doc_size()
    assert isinstance(requirement_doc_size, int)
    assert requirement_doc_size >= 0

    has_design_label = knowledge_package.has_design_label()
    assert isinstance(has_design_label, bool)

    has_security_label = knowledge_package.has_security_label()
    assert isinstance(has_security_label, bool)

    # 提取时间应该被自动设置
    assert knowledge_package.extracted_at is not None


@pytest.mark.integration
@pytest.mark.slow
def test_extract_multiple_issues(extractor):
    """集成测试：测试提取多个 Issue（压力测试）"""
    # 这个测试比较慢，可以用来验证批量提取的稳定性
    pytest.skip("压力测试，默认跳过")

    issue_numbers = [1611, 1610, 1609]  # 根据实际情况调整

    for issue_num in issue_numbers:
        try:
            knowledge_package = extractor.extract(
                backlog_repo="opensourceways/backlog",
                issue_number=issue_num,
                project_repo="opensourceways/forum-reply-robot"
            )
            print(f"Issue #{issue_num}: 提取成功")
        except Exception as e:
            print(f"Issue #{issue_num}: 提取失败 - {e}")
