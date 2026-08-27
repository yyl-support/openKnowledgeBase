"""
测试 PR 链接解析器
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extraction.pr_link_parser import PRLinkParser


@pytest.fixture
def sample_comments():
    """模拟 Issue #1611 的评论"""
    return [
        {
            'body': '''
### ✅ Workflow Requirement

[需求分析 PR](https://github.com/opensourceways/backlog/pull/1612) 已完成。
            '''
        },
        {
            'body': '''
开发 PR: https://github.com/opensourceways/forum-reply-robot/pull/177
            '''
        },
        {
            'body': '''
测试报告 PR: https://github.com/opensourceways/backlog/pull/1618
            '''
        },
        {
            'body': '''
变更计划 PR: https://github.com/opensourceways/release-mgmt/pull/226
            '''
        }
    ]


def test_parse_requirement_pr(sample_comments):
    """测试解析需求分析 PR"""
    parser = PRLinkParser()

    pr_ref = parser.parse_requirement_pr(sample_comments)

    assert pr_ref is not None
    assert pr_ref.repo == "opensourceways/backlog"
    assert pr_ref.number == 1612
    assert pr_ref.url == "https://github.com/opensourceways/backlog/pull/1612"


def test_parse_development_pr(sample_comments):
    """测试解析开发 PR"""
    parser = PRLinkParser()

    pr_ref = parser.parse_development_pr(
        sample_comments,
        project_repo="opensourceways/forum-reply-robot"
    )

    assert pr_ref is not None
    assert pr_ref.repo == "opensourceways/forum-reply-robot"
    assert pr_ref.number == 177
    assert pr_ref.url == "https://github.com/opensourceways/forum-reply-robot/pull/177"


def test_parse_test_pr(sample_comments):
    """测试解析测试报告 PR"""
    parser = PRLinkParser()

    pr_ref = parser.parse_test_pr(sample_comments)

    assert pr_ref is not None
    assert pr_ref.repo == "opensourceways/backlog"
    assert pr_ref.number == 1618


def test_parse_release_pr(sample_comments):
    """测试解析变更计划 PR"""
    parser = PRLinkParser()

    pr_ref = parser.parse_release_pr(sample_comments)

    assert pr_ref is not None
    assert pr_ref.repo == "opensourceways/release-mgmt"
    assert pr_ref.number == 226


def test_parse_no_match():
    """测试没有匹配时返回 None"""
    parser = PRLinkParser()

    comments = [{'body': 'No PR links here'}]

    assert parser.parse_requirement_pr(comments) is None
    assert parser.parse_development_pr(comments, "opensourceways/test") is None
    assert parser.parse_test_pr(comments) is None
    assert parser.parse_release_pr(comments) is None


def test_parse_multiple_prs():
    """测试评论中有多个 PR 链接时，优先匹配正确的仓库"""
    parser = PRLinkParser()

    comments = [
        {
            'body': '''
需求分析完成：
- https://github.com/opensourceways/backlog/pull/100
- https://github.com/opensourceways/other-repo/pull/200
            '''
        }
    ]

    pr_ref = parser.parse_requirement_pr(comments)

    # 应该匹配 backlog 仓库的 PR
    assert pr_ref is not None
    assert pr_ref.repo == "opensourceways/backlog"
    assert pr_ref.number == 100
