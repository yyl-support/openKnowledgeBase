"""
测试 UpdateDecisionChain
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from update.decision_chain import UpdateDecisionChain
from extraction.models import (
    IssueKnowledgePackage,
    RequirementDoc,
    CodeChange,
    PRReference
)


def test_decision_chain_initialization():
    """测试决策链初始化"""
    chain = UpdateDecisionChain()
    assert chain is not None


def test_rule_based_decision_full_need_design():
    """测试规则引擎：need_design 标签 -> 全量更新"""
    chain = UpdateDecisionChain()

    # 构造测试数据
    package = IssueKnowledgePackage(
        issue_number=1734,
        issue_title="测试 Issue",
        issue_labels=["need_design", "forum-reply-robot"],
        issue_body="测试描述",
        requirement=RequirementDoc(
            specification="简短的需求文档",
            qa_checklist="",
            pr=PRReference(
                repo="test/repo",
                number=1,
                title="测试 PR",
                state="MERGED",
                url="https://github.com/test/repo/pull/1"
            )
        ),
        code_change=None
    )

    result = chain._rule_based_decision(package, days_since_last_update=1.0)

    assert result["decision"] == "full"
    assert "need_design" in result["reason"]
    assert result["confidence"] > 0.9


def test_rule_based_decision_full_large_doc():
    """测试规则引擎：需求文档过大 -> 全量更新"""
    chain = UpdateDecisionChain()

    # 构造大文档（> 15,000 字符）
    large_spec = "x" * 20000

    package = IssueKnowledgePackage(
        issue_number=1735,
        issue_title="测试 Issue",
        issue_labels=["forum-reply-robot"],
        issue_body="测试描述",
        requirement=RequirementDoc(
            specification=large_spec,
            qa_checklist="",
            pr=PRReference(
                repo="test/repo",
                number=1,
                title="测试 PR",
                state="MERGED",
                url="https://github.com/test/repo/pull/1"
            )
        ),
        code_change=None
    )

    result = chain._rule_based_decision(package, days_since_last_update=1.0)

    assert result["decision"] == "full"
    assert "需求文档过大" in result["reason"]


def test_rule_based_decision_full_many_files():
    """测试规则引擎：变更文件过多 -> 全量更新"""
    chain = UpdateDecisionChain()

    # 构造多文件变更
    files = [{"filename": f"file_{i}.py", "patch": "test"} for i in range(10)]

    package = IssueKnowledgePackage(
        issue_number=1736,
        issue_title="测试 Issue",
        issue_labels=["forum-reply-robot"],
        issue_body="测试描述",
        requirement=None,
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=1, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/1"),
            diff="test diff",
            files=files,
            total_additions=100,
            total_deletions=50
        )
    )

    result = chain._rule_based_decision(package, days_since_last_update=1.0)

    assert result["decision"] == "full"
    assert "变更文件过多" in result["reason"]


def test_rule_based_decision_full_long_time():
    """测试规则引擎：距上次更新时间过长 -> 全量更新"""
    chain = UpdateDecisionChain()

    package = IssueKnowledgePackage(
        issue_number=1737,
        issue_title="测试 Issue",
        issue_labels=["forum-reply-robot"],
        issue_body="测试描述",
        requirement=None,
        code_change=None
    )

    result = chain._rule_based_decision(package, days_since_last_update=8.0)

    assert result["decision"] == "full"
    assert "距上次更新时间过长" in result["reason"]


def test_rule_based_decision_incremental():
    """测试规则引擎：小变更 -> 增量更新"""
    chain = UpdateDecisionChain()

    # 构造小变更
    files = [
        {"filename": "src/logger.py", "patch": "test"},
        {"filename": "tests/test_logger.py", "patch": "test"}
    ]

    package = IssueKnowledgePackage(
        issue_number=1738,
        issue_title="优化日志输出",
        issue_labels=["forum-reply-robot"],
        issue_body="测试描述",
        requirement=RequirementDoc(
            specification="简短需求（< 1000 字符）",
            qa_checklist="",
            pr=PRReference(repo="test/repo", number=1, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/1")
        ),
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=2, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/2"),
            diff="test diff",
            files=files,
            total_additions=20,
            total_deletions=10
        )
    )

    result = chain._rule_based_decision(package, days_since_last_update=2.0)

    assert result["decision"] == "incremental"
    assert "影响范围小" in result["reason"]


def test_decide_with_mock_package():
    """测试完整决策流程"""
    chain = UpdateDecisionChain()

    package = IssueKnowledgePackage(
        issue_number=1739,
        issue_title="测试 Issue",
        issue_labels=["forum-reply-robot"],
        issue_body="测试描述",
        requirement=RequirementDoc(
            specification="测试需求",
            qa_checklist="",
            pr=PRReference(repo="test/repo", number=1, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/1")
        ),
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=2, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/2"),
            diff="test diff",
            files=[{"filename": "test.py", "patch": "test"}],
            total_additions=10,
            total_deletions=5
        )
    )

    result = chain.decide(package, days_since_last_update=1.0)

    assert "decision" in result
    assert result["decision"] in ["full", "incremental"]
    assert "reason" in result
    assert "confidence" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
