"""
测试 SchedulerDaemon
"""

import os
import sys
import time
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from triggers.daemon_mgr import SchedulerDaemon


@pytest.fixture
def temp_pid_dir():
    """创建临时 PID 文件目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def scheduler_daemon(temp_pid_dir):
    """构造使用临时 PID 文件的守护进程管理器"""
    pid_file = str(Path(temp_pid_dir) / "scheduler.pid")
    return SchedulerDaemon(
        config_path="config/projects.yaml",
        pid_file=pid_file,
    )


def test_pid_file_management(scheduler_daemon):
    """测试 PID 文件管理"""
    # 未启动时没有 PID 文件
    assert scheduler_daemon._get_pid() == 0

    # 写入一个假的 PID
    scheduler_daemon.pid_file.write_text(str(os.getpid()))
    assert scheduler_daemon._get_pid() == os.getpid()

    # 当前进程一定在运行
    assert scheduler_daemon._is_process_running(os.getpid()) is True

    # 一个几乎不可能存在的 PID
    assert scheduler_daemon._is_process_running(999999) is False


def test_duplicate_start_prevention(scheduler_daemon, capsys):
    """测试防止重复启动"""
    # 模拟一个"正在运行"的进程（用当前测试进程的 PID 代替）
    scheduler_daemon.pid_file.write_text(str(os.getpid()))

    with patch("triggers.daemon_mgr.daemon.DaemonContext") as mock_context:
        scheduler_daemon.start()
        # DaemonContext 不应被调用，因为检测到已有进程运行
        mock_context.assert_not_called()

    captured = capsys.readouterr()
    assert "已在运行" in captured.out


def test_daemon_start(scheduler_daemon):
    """测试守护进程启动（不真正 fork 进程，验证调用链）"""
    with patch("triggers.daemon_mgr.daemon.DaemonContext") as mock_context_cls, \
         patch.object(scheduler_daemon, "_run_scheduler") as mock_run:
        mock_context = mock_context_cls.return_value
        mock_context.__enter__ = lambda self: None
        mock_context.__exit__ = lambda self, *a: None

        scheduler_daemon.start()

        mock_context_cls.assert_called_once()
        mock_run.assert_called_once()


def test_daemon_stop(scheduler_daemon):
    """测试守护进程停止"""
    # 未运行时停止应该是安全的空操作
    scheduler_daemon.stop()
    assert not scheduler_daemon.pid_file.exists()

    # 模拟一个正在运行的进程：启动一个真实子进程用于接收信号
    import subprocess
    proc = subprocess.Popen(["sleep", "30"])
    scheduler_daemon.pid_file.write_text(str(proc.pid))

    scheduler_daemon.stop()

    # 等待进程真正退出
    proc.wait(timeout=5)
    assert not scheduler_daemon._is_process_running(proc.pid)
    assert not scheduler_daemon.pid_file.exists()


def test_daemon_restart(scheduler_daemon):
    """测试守护进程重启"""
    with patch.object(scheduler_daemon, "stop") as mock_stop, \
         patch.object(scheduler_daemon, "start") as mock_start, \
         patch("time.sleep"):
        scheduler_daemon.restart()

        mock_stop.assert_called_once()
        mock_start.assert_called_once()


def test_daemon_status(scheduler_daemon):
    """测试守护进程状态查询"""
    # 未运行状态
    status = scheduler_daemon.status()
    assert status["running"] is False
    assert status["pid"] is None

    # 模拟运行状态
    scheduler_daemon.pid_file.write_text(str(os.getpid()))
    status = scheduler_daemon.status()
    assert status["running"] is True
    assert status["pid"] == os.getpid()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
