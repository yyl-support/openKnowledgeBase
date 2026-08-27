import pytest
from orchestration.gh_client import GitHubCLI


def test_search_issues():
    """测试搜索 Issue"""
    gh = GitHubCLI()

    issues = gh.search_issues(
        repo="opensourceways/backlog",
        search_query="forum-reply-robot state:closed",
        limit=3
    )

    assert len(issues) > 0
    assert all(issue.number > 0 for issue in issues)
    assert all("forum-reply-robot" in issue.title.lower() or
               "project:forum-reply-robot" in issue.labels
               for issue in issues)


def test_get_issue():
    """测试获取 Issue 详情"""
    gh = GitHubCLI()

    issue = gh.get_issue(
        repo="opensourceways/backlog",
        issue_number=1611
    )

    assert issue.number == 1611
    assert issue.state == "CLOSED"
    assert len(issue.comments) > 0
    assert "project:forum-reply-robot" in issue.labels


def test_get_pull_request():
    """测试获取 PR 详情"""
    gh = GitHubCLI()

    pr = gh.get_pull_request(
        repo="opensourceways/forum-reply-robot",
        pr_number=177
    )

    assert pr.number == 177
    assert pr.state == "MERGED"
    assert len(pr.files) > 0


def test_get_pr_diff():
    """测试获取 PR diff"""
    gh = GitHubCLI()

    diff = gh.get_pr_diff(
        repo="opensourceways/forum-reply-robot",
        pr_number=177
    )

    assert "diff --git" in diff
    assert len(diff) > 100
