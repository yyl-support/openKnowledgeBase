import pytest
from datetime import datetime, timedelta
from orchestration.gh_client import GitHubCLI
from orchestration.issue_detector import IssueChangeDetector
from config.models import (
    ProjectConfig,
    IssueTrackingConfig,
    UpdatePolicyConfig,
    ProjectMetadata
)


@pytest.fixture
def detector():
    gh = GitHubCLI()
    return IssueChangeDetector(gh)


@pytest.fixture
def sample_project():
    return ProjectConfig(
        repo_path="/tmp/forum-reply-robot",
        description="测试项目",
        owner="test",
        issue_tracking=IssueTrackingConfig(
            backlog_repo="opensourceways/backlog",
            search_query="forum-reply-robot state:closed",
            poll_interval=3.5
        ),
        adapter="ua",
        output_types=["overview"],
        update_policy=UpdatePolicyConfig(
            mode="auto",
            trigger="issue_polling"
        ),
        priority="medium",
        metadata=ProjectMetadata(
            last_issue_number=1600  # 只检测 1600 之后的
        )
    )


def test_detect_new_issues(detector, sample_project):
    """测试检测新 Issue"""
    new_issues = detector.detect_new_issues(sample_project)

    # 应该能找到 1611 和 1734
    assert len(new_issues) >= 2
    assert all(issue.number > 1600 for issue in new_issues)

    # 应该按编号正序排列
    assert new_issues == sorted(new_issues, key=lambda x: x.number)


def test_should_trigger_update_interval(detector, sample_project):
    """测试轮询间隔判断"""
    # 情况1: 从未更新过，应该触发
    assert detector.should_trigger_update(sample_project)

    # 情况2: 1天前更新过，不应该触发（间隔 3.5 天）
    sample_project.metadata.last_update_time = datetime.now() - timedelta(days=1)
    assert not detector.should_trigger_update(sample_project)

    # 情况3: 4天前更新过，应该触发
    sample_project.metadata.last_update_time = datetime.now() - timedelta(days=4)
    assert detector.should_trigger_update(sample_project)


def test_should_trigger_update_manual_mode(detector, sample_project):
    """测试手动模式不自动触发"""
    sample_project.update_policy.mode = "manual"

    assert not detector.should_trigger_update(sample_project)
