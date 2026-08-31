"""
Phase 5 任务 1：验证 scheduler 的失败重试机制真的生效

重试逻辑位于 triggers/scheduler.py 的 schedule_all_projects()（第 133-181 行）：
首次尝试失败后最多重试 max_retries 次，每次间隔 retry_delay_seconds 秒。

测试中把 retry_delay_seconds 调为 0，不真实等待 300 秒。
"""

import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from triggers.scheduler import KnowledgeScheduler
from orchestration.orchestrator import UpdateResult


@pytest.fixture
def mock_orchestrator():
    """假的 Orchestrator，避免真实调用 gh CLI"""
    orchestrator = MagicMock()
    orchestrator.schedule_all_projects.return_value = []
    return orchestrator


@pytest.fixture
def scheduler(mock_orchestrator):
    """使用假 Orchestrator 的调度器，retry_delay 调小避免真等 300 秒"""
    with patch(
        "triggers.scheduler.KnowledgeOrchestrator",
        return_value=mock_orchestrator,
    ):
        instance = KnowledgeScheduler(config_path="config/projects.yaml")

    instance.retry_delay_seconds = 0
    yield instance
    shutil.rmtree("logs", ignore_errors=True)


def _ok_result():
    return UpdateResult(
        project_name="forum-reply-robot",
        success=True,
        mode="incremental",
        issue_number=1750,
        elapsed_seconds=1.0,
        cost_usd=0.1,
    )


def test_retry_config_loaded_from_yaml(scheduler):
    """配置里的 max_retries / retry_delay_seconds 真的被读进来"""
    with patch("triggers.scheduler.KnowledgeOrchestrator", return_value=MagicMock()):
        fresh = KnowledgeScheduler(config_path="config/projects.yaml")

    assert fresh.max_retries == 3
    assert fresh.retry_delay_seconds == 300
    shutil.rmtree("logs", ignore_errors=True)


def test_retry_two_failures_then_success(scheduler, mock_orchestrator, caplog):
    """前两次失败、第三次成功：日志出现 2 次重试记录，最终成功"""
    scheduler.max_retries = 3
    mock_orchestrator.schedule_all_projects.side_effect = [
        RuntimeError("第 1 次模拟失败"),
        RuntimeError("第 2 次模拟失败"),
        [_ok_result()],
    ]

    with caplog.at_level("WARNING"):
        result = scheduler.schedule_all_projects()

    retry_logs = [r for r in caplog.records if "次重试" in r.getMessage()]

    assert result["success"] is True
    assert result["success_count"] == 1
    assert result["failed_count"] == 0
    # 首次 + 2 次重试 = 3 次调用
    assert mock_orchestrator.schedule_all_projects.call_count == 3
    # 日志里确实有 2 条重试记录
    assert len(retry_logs) == 2, f"期望 2 条重试日志，实际 {len(retry_logs)}"
    assert "1/3" in retry_logs[0].getMessage()
    assert "2/3" in retry_logs[1].getMessage()


def test_retry_delay_is_honored(scheduler, mock_orchestrator):
    """每次重试前确实按 retry_delay_seconds 休眠（用 mock 验证入参，不真等）"""
    scheduler.max_retries = 2
    scheduler.retry_delay_seconds = 7
    mock_orchestrator.schedule_all_projects.side_effect = [
        RuntimeError("失败 1"),
        [_ok_result()],
    ]

    with patch("triggers.scheduler.time.sleep") as mock_sleep:
        result = scheduler.schedule_all_projects()

    assert result["success"] is True
    mock_sleep.assert_called_once_with(7)


def test_retry_all_attempts_fail(scheduler, mock_orchestrator, caplog):
    """三次全失败：success 为 False，错误信息透出，异常不被静默吞掉"""
    scheduler.max_retries = 3
    mock_orchestrator.schedule_all_projects.side_effect = RuntimeError("持续失败")

    with caplog.at_level("WARNING"):
        result = scheduler.schedule_all_projects()

    assert result["success"] is False
    assert "持续失败" in result["error"]
    # 首次 + 3 次重试 = 4 次调用
    assert mock_orchestrator.schedule_all_projects.call_count == 4

    # 最终失败必须有 ERROR 级日志，且带 exc_info（异常没被吞掉）
    error_records = [r for r in caplog.records if r.levelname == "ERROR"]
    assert error_records, "全部重试失败后没有 ERROR 日志"
    final = error_records[-1]
    assert "已重试 3 次" in final.getMessage()
    assert final.exc_info is not None, "异常堆栈被吞掉了"


def test_retry_no_retry_on_success(scheduler, mock_orchestrator):
    """首次就成功时不应触发任何重试"""
    mock_orchestrator.schedule_all_projects.return_value = [_ok_result()]

    with patch("triggers.scheduler.time.sleep") as mock_sleep:
        result = scheduler.schedule_all_projects()

    assert result["success"] is True
    assert mock_orchestrator.schedule_all_projects.call_count == 1
    mock_sleep.assert_not_called()


def test_run_once_propagates_failure(scheduler, mock_orchestrator):
    """run_once 在重试耗尽后返回失败，不谎报成功"""
    scheduler.max_retries = 1
    mock_orchestrator.schedule_all_projects.side_effect = RuntimeError("run_once 失败")

    result = scheduler.run_once()

    assert result["success"] is False
    assert "run_once 失败" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
