"""Phase 6 测试共用夹具"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from extraction.models import IssueKnowledgePackage, CodeChange, PRReference


def make_knowledge_package(
    issue_number: int = 9999,
    files=None
) -> IssueKnowledgePackage:
    """构造一个带代码变更的知识包"""
    if files is None:
        files = [
            {"path": "main.py", "additions": 10, "deletions": 2, "patch": "@@ -1 +1 @@\n-a\n+b"},
        ]

    pr = PRReference(
        repo="opensourceways/backlog",
        number=1,
        title="test pr",
        state="MERGED",
        url="https://example.invalid/pr/1"
    )

    return IssueKnowledgePackage(
        issue_number=issue_number,
        issue_title="测试 Issue",
        issue_labels=["bug"],
        issue_body="body",
        code_change=CodeChange(
            pr=pr,
            diff="diff",
            files=files,
            total_additions=10,
            total_deletions=2
        ),
        extracted_at=datetime.now()
    )


@pytest.fixture
def knowledge_package():
    return make_knowledge_package()


@pytest.fixture
def orchestrator(monkeypatch, tmp_path):
    """
    构造一个不触碰真实 GitHub / LLM 的 orchestrator

    只 mock 外部依赖（gh_client / issue_extractor / decision_chain），
    被测的分派与增量逻辑保持真实。

    GitHubCLI 在 __init__ 里跑 `gh auth status`（10s 超时的网络调用），
    构造 orchestrator 时会连带触发，所以整个类都 mock 掉——本组用例
    不测 GitHub 交互。
    """
    from orchestration.orchestrator import KnowledgeOrchestrator

    # 元数据保存会重写 config/projects.yaml，测试里禁掉
    monkeypatch.setattr(
        "orchestration.orchestrator.save_system_config",
        lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "orchestration.orchestrator.GitHubCLI",
        lambda *a, **kw: MagicMock()
    )

    orch = KnowledgeOrchestrator(config_path="config/projects.yaml")
    orch.gh_client = MagicMock()
    orch.issue_extractor = MagicMock()
    return orch
