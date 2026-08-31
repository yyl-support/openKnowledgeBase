"""
Phase 5 任务 1：验证重复 daemon start 被正确拒绝

设计方案要求第二次 start 满足三点：
1. 退出码非 0
2. 输出含已运行提示
3. PID 文件内容不变

实测结论：第 2、3 点满足；第 1 点不满足——daemon_mgr.main() 在
start() 返回后没有 sys.exit(1)，所以重复启动的退出码仍是 0。
本任务不允许改动 daemon_mgr.py，故该断言以 xfail(strict=True) 固化，
待授权后修复 daemon_mgr.py 时会自动转为 XPASS 提醒收紧。

测试会真实拉起守护进程，用临时 PID 文件隔离，结束后强制清理。
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _run_start(pid_file):
    """执行一次 daemon start，返回 CompletedProcess"""
    return subprocess.run(
        [
            sys.executable, "-m", "triggers.daemon_mgr", "start",
            "--pid-file", str(pid_file),
            # 间隔调大，避免测试期间真的触发轮询任务
            "--interval", "30",
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )


def _read_pid(pid_file):
    try:
        return Path(pid_file).read_text().strip()
    except OSError:
        return ""


def _kill(pid):
    if pid <= 0:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.kill(pid, sig)
        except OSError:
            return
        for _ in range(10):
            try:
                os.kill(pid, 0)
            except OSError:
                return
            time.sleep(0.3)


@pytest.fixture
def pid_file(tmp_path):
    """临时 PID 文件；测试结束无论成败都清理进程和文件"""
    path = tmp_path / "scheduler_test.pid"
    yield path

    pid_text = _read_pid(path)
    if pid_text.isdigit():
        _kill(int(pid_text))
    if path.exists():
        path.unlink()


@pytest.fixture
def started_daemon(pid_file):
    """先成功启动一个守护进程，作为重复启动的前置条件"""
    result = _run_start(pid_file)

    # 等待守护进程写入 PID 文件
    pid_text = ""
    for _ in range(30):
        pid_text = _read_pid(pid_file)
        if pid_text.isdigit():
            break
        time.sleep(0.5)

    assert pid_text.isdigit(), (
        f"首次启动未写入有效 PID 文件，测试前提不成立。"
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    pid = int(pid_text)
    # 确认进程真的活着，否则「重复启动」的检测无从谈起
    os.kill(pid, 0)

    return {"pid_file": pid_file, "pid": pid, "first_result": result}


def test_first_start_succeeds(started_daemon):
    """前提校验：首次启动真的拉起了进程

    注意：首次启动的 "启动调度器守护进程" 提示在非 tty 下拿不到——
    print 写进了缓冲区，DaemonContext 分离进程时直接关闭 fd，缓冲区
    未 flush 就被丢弃。因此这里以 PID 文件和进程存活作为判据。
    """
    assert started_daemon["first_result"].returncode == 0
    assert started_daemon["pid"] > 0
    os.kill(started_daemon["pid"], 0)


def test_duplicate_start_prints_already_running(started_daemon):
    """第二次 start 输出必须含已运行提示，并带上正在运行的 PID"""
    second = _run_start(started_daemon["pid_file"])
    output = second.stdout + second.stderr

    assert "已在运行" in output, f"未输出已运行提示: {output!r}"
    assert "拒绝重复启动" in output
    assert str(started_daemon["pid"]) in output


def test_duplicate_start_keeps_pid_file_unchanged(started_daemon):
    """第二次 start 不得改动 PID 文件内容"""
    pid_file = started_daemon["pid_file"]
    before = _read_pid(pid_file)

    _run_start(pid_file)

    after = _read_pid(pid_file)
    assert after == before, f"PID 文件被改动: {before!r} -> {after!r}"
    assert after == str(started_daemon["pid"])
    # 原进程仍在运行，没被顶掉
    os.kill(started_daemon["pid"], 0)


def test_duplicate_start_does_not_spawn_second_process(started_daemon):
    """第二次 start 不应产生新的调度器进程"""
    pid_file = started_daemon["pid_file"]
    second = _run_start(pid_file)

    # 子进程自身已退出，且 PID 文件仍指向第一个进程
    assert second.returncode is not None
    assert _read_pid(pid_file) == str(started_daemon["pid"])


def test_duplicate_start_exit_code_nonzero(started_daemon):
    """设计方案要求：第二次 start 退出码非 0"""
    second = _run_start(started_daemon["pid_file"])
    assert second.returncode != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
