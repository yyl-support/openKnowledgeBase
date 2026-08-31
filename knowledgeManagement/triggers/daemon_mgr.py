"""
Phase 4: 触发器层 - 守护进程管理

将 KnowledgeScheduler 以后台守护进程方式运行，提供：
- start/stop/restart/status 命令
- PID 文件管理，防止重复启动
- 基于 python-daemon 的进程分离
"""

import os
import sys
import signal
import time
from pathlib import Path

import daemon
from daemon import pidfile

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from triggers.scheduler import KnowledgeScheduler


class SchedulerDaemon:
    """调度器守护进程管理"""

    def __init__(
        self,
        config_path: str = "config/projects.yaml",
        pid_file: str = "run/scheduler.pid",
        interval_days: float = 3.5,
    ):
        """
        初始化守护进程管理器

        Args:
            config_path: 项目配置文件路径
            pid_file: PID 文件路径
            interval_days: 轮询间隔（天）
        """
        self.config_path = config_path
        self.pid_file = Path(pid_file)
        self.interval_days = interval_days
        self.working_directory = str(Path(__file__).parent.parent)

        # 确保 PID 文件所在目录存在
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_pid(self) -> int:
        """
        读取 PID 文件中记录的进程号

        Returns:
            int: 进程号，如果文件不存在或内容无效返回 0
        """
        if not self.pid_file.exists():
            return 0

        try:
            content = self.pid_file.read_text().strip()
            return int(content)
        except (ValueError, OSError):
            return 0

    def _is_process_running(self, pid: int) -> bool:
        """
        检查指定 PID 的进程是否仍在运行

        Args:
            pid: 进程号

        Returns:
            bool: 进程是否存在
        """
        if pid <= 0:
            return False

        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _run_scheduler(self):
        """守护进程内实际执行的入口：启动调度器"""
        scheduler = KnowledgeScheduler(config_path=self.config_path)
        scheduler.add_polling_job(days=self.interval_days)
        scheduler.start()

    def start(self):
        """
        启动守护进程

        如果检测到已有进程在运行，拒绝重复启动。

        Returns:
            bool: True 成功启动，False 重复启动被拒绝
        """
        pid = self._get_pid()
        if self._is_process_running(pid):
            print(f"调度器已在运行 (PID: {pid})，拒绝重复启动", flush=True)
            return False

        # 清理失效的 PID 文件（进程已不存在）
        if self.pid_file.exists():
            self.pid_file.unlink()

        print(f"启动调度器守护进程 (配置: {self.config_path}, 间隔: {self.interval_days} 天)", flush=True)

        context = daemon.DaemonContext(
            working_directory=self.working_directory,
            umask=0o022,
            pidfile=pidfile.PIDLockFile(str(self.pid_file)),
            detach_process=True,
        )

        with context:
            self._run_scheduler()

        return True

    def stop(self):
        """停止守护进程"""
        pid = self._get_pid()

        if not self._is_process_running(pid):
            print("调度器未在运行")
            if self.pid_file.exists():
                self.pid_file.unlink()
            return

        print(f"停止调度器守护进程 (PID: {pid})")
        os.kill(pid, signal.SIGTERM)

        # 等待进程退出
        for _ in range(10):
            if not self._is_process_running(pid):
                break
            time.sleep(1)

        if self._is_process_running(pid):
            print(f"进程未响应 SIGTERM，强制终止 (PID: {pid})")
            os.kill(pid, signal.SIGKILL)

        if self.pid_file.exists():
            self.pid_file.unlink()

        print("调度器已停止")

    def restart(self):
        """重启守护进程"""
        self.stop()
        time.sleep(1)
        self.start()

    def status(self) -> dict:
        """
        查询守护进程状态

        Returns:
            dict: 包含 running 和 pid 字段的状态信息
        """
        pid = self._get_pid()
        running = self._is_process_running(pid)

        result = {
            "running": running,
            "pid": pid if running else None,
        }

        if running:
            print(f"调度器正在运行 (PID: {pid})")
        else:
            print("调度器未在运行")

        return result


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="知识工程调度器守护进程管理")
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "status"],
        help="守护进程命令"
    )
    parser.add_argument(
        "--config",
        default="config/projects.yaml",
        help="项目配置文件路径"
    )
    parser.add_argument(
        "--pid-file",
        default="run/scheduler.pid",
        help="PID 文件路径"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.5,
        help="轮询间隔（天），默认 3.5 天"
    )

    args = parser.parse_args()

    scheduler_daemon = SchedulerDaemon(
        config_path=args.config,
        pid_file=args.pid_file,
        interval_days=args.interval,
    )

    if args.command == "start":
        success = scheduler_daemon.start()
        sys.exit(0 if success else 1)
    elif args.command == "stop":
        scheduler_daemon.stop()
    elif args.command == "restart":
        scheduler_daemon.restart()
    elif args.command == "status":
        scheduler_daemon.status()


if __name__ == "__main__":
    main()
