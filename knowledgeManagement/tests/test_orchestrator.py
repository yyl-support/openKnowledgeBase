import pytest
from orchestration.orchestrator import KnowledgeOrchestrator


def test_orchestrator_initialization():
    """测试调度器初始化"""
    orchestrator = KnowledgeOrchestrator(
        config_path="config/projects.yaml"
    )

    assert orchestrator.gh_client is not None
    assert orchestrator.issue_detector is not None
    assert len(orchestrator.config.projects) > 0


def test_schedule_project():
    """测试调度单个项目"""
    orchestrator = KnowledgeOrchestrator()

    # 强制模式（忽略轮询间隔）
    result = orchestrator.schedule_project(
        "forum-reply-robot",
        force=True
    )

    # 可能没有新 Issue，返回 None 也是正常的
    if result:
        assert result.project_name == "forum-reply-robot"
        assert result.mode in ["full", "incremental"]
