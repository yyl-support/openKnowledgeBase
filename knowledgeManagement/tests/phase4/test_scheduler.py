"""
测试 KnowledgeScheduler
"""

import sys
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from triggers.scheduler import KnowledgeScheduler
from orchestration.orchestrator import UpdateResult


@pytest.fixture
def mock_orchestrator():
    """构造一个假的 KnowledgeOrchestrator，避免真实调用 gh CLI"""
    orchestrator = MagicMock()
    orchestrator.schedule_all_projects.return_value = []
    return orchestrator


@pytest.fixture
def scheduler(mock_orchestrator):
    """构造一个使用假 Orchestrator 的调度器实例"""
    with patch(
        "triggers.scheduler.KnowledgeOrchestrator",
        return_value=mock_orchestrator,
    ):
        instance = KnowledgeScheduler(config_path="config/projects.yaml")
        yield instance

    # 清理测试产生的日志文件
    shutil.rmtree("logs", ignore_errors=True)


def test_scheduler_initialization(scheduler):
    """测试调度器初始化"""
    assert scheduler.orchestrator is not None
    assert scheduler.scheduler is not None
    assert scheduler.max_retries == 3
    assert scheduler.retry_delay_seconds == 300


def test_add_polling_job(scheduler):
    """测试添加轮询任务"""
    scheduler.add_polling_job(days=3.5, job_id="issue_polling")

    jobs = scheduler.scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "issue_polling"


def test_run_once(scheduler, mock_orchestrator):
    """测试立即执行一次"""
    mock_orchestrator.schedule_all_projects.return_value = []

    result = scheduler.run_once()

    assert result["success"] is True
    assert result["processed_count"] == 0
    mock_orchestrator.schedule_all_projects.assert_called_once()


def test_job_execution_success(scheduler, mock_orchestrator):
    """测试任务执行成功"""
    mock_orchestrator.schedule_all_projects.return_value = [
        UpdateResult(
            project_name="forum-reply-robot",
            success=True,
            mode="full",
            issue_number=1750,
            elapsed_seconds=1.0,
            cost_usd=1.0,
        )
    ]

    result = scheduler.schedule_all_projects()

    assert result["success"] is True
    assert result["success_count"] == 1
    assert result["failed_count"] == 0


def test_job_execution_failure(scheduler, mock_orchestrator):
    """测试任务执行失败（重试机制）"""
    scheduler.max_retries = 2
    scheduler.retry_delay_seconds = 0  # 测试中不真正等待

    mock_orchestrator.schedule_all_projects.side_effect = RuntimeError("模拟调度失败")

    result = scheduler.schedule_all_projects()

    assert result["success"] is False
    assert "模拟调度失败" in result["error"]
    # 首次尝试 + 2 次重试 = 3 次调用
    assert mock_orchestrator.schedule_all_projects.call_count == 3


def test_event_listeners(scheduler):
    """测试事件监听器"""
    listeners = scheduler.scheduler._listeners
    assert len(listeners) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
