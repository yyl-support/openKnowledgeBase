"""
Phase 4: 触发器层 - 定时调度器

提供自动化的定时任务调度能力，实现：
- 周期性 Issue 轮询（每 3.5 天）
- 后台运行
- 日志记录
- 错误重试
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.orchestrator import KnowledgeOrchestrator
from config.loader import load_system_config


class KnowledgeScheduler:
    """知识工程定时调度器"""

    def __init__(self, config_path: str = "config/projects.yaml"):
        """
        初始化调度器

        Args:
            config_path: 项目配置文件路径
        """
        self.config_path = config_path
        self.scheduler = BlockingScheduler()
        self.orchestrator: Optional[KnowledgeOrchestrator] = None
        self.max_retries = 3
        self.retry_delay_seconds = 300

        # 配置日志
        self._setup_logging()

        # 加载配置
        self._load_config()

        # 配置调度器事件监听
        self._setup_event_listeners()

        self.logger.info("知识工程调度器初始化完成")

    def _setup_logging(self):
        """配置日志"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 配置日志格式
        log_file = log_dir / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)

    def _load_config(self):
        """加载配置"""
        try:
            system_config = load_system_config(self.config_path)
            self.max_retries = system_config.scheduler.max_retries
            self.retry_delay_seconds = system_config.scheduler.retry_delay_seconds

            self.orchestrator = KnowledgeOrchestrator(self.config_path)
            self.logger.info(f"配置加载成功: {self.config_path}")
        except Exception as e:
            self.logger.error(f"配置加载失败: {e}")
            raise

    def _setup_event_listeners(self):
        """配置调度器事件监听"""
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )

        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )

    def _job_executed_listener(self, event):
        """任务执行成功监听器"""
        self.logger.info(
            f"任务执行成功: {event.job_id} "
            f"(耗时: {event.retval.get('duration', 'N/A') if isinstance(event.retval, dict) else 'N/A'})"
        )

    def _job_error_listener(self, event):
        """任务执行失败监听器"""
        self.logger.error(
            f"任务执行失败: {event.job_id} "
            f"异常: {event.exception}"
        )

    def schedule_all_projects(self):
        """
        调度所有项目的知识更新（带失败重试）

        单个项目的失败由 Orchestrator 内部隔离处理，不会影响其他项目。
        此处的重试针对整体调度调用本身抛出异常的情况（如配置错误、
        GitHub CLI 不可用等），最多重试 max_retries 次，每次间隔
        retry_delay_seconds 秒。

        Returns:
            dict: 执行结果统计
        """
        start_time = time.time()

        self.logger.info("=" * 80)
        self.logger.info("开始调度所有项目的知识更新")
        self.logger.info("=" * 80)

        attempt = 0
        last_error = None

        while attempt <= self.max_retries:
            try:
                # 执行调度
                results = self.orchestrator.schedule_all_projects()

                duration = time.time() - start_time
                success_count = sum(1 for r in results if r.success)
                failed_count = len(results) - success_count

                self.logger.info("=" * 80)
                self.logger.info(f"调度完成 (耗时: {duration:.2f}秒)")
                self.logger.info(f"处理任务数: {len(results)}")
                self.logger.info(f"成功: {success_count}")
                self.logger.info(f"失败: {failed_count}")
                self.logger.info("=" * 80)

                return {
                    "success": True,
                    "duration": duration,
                    "processed_count": len(results),
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "results": results,
                }

            except Exception as e:
                last_error = e
                attempt += 1

                if attempt > self.max_retries:
                    break

                self.logger.warning(
                    f"调度失败，{self.retry_delay_seconds} 秒后进行第 "
                    f"{attempt}/{self.max_retries} 次重试: {e}"
                )
                time.sleep(self.retry_delay_seconds)

        duration = time.time() - start_time
        self.logger.error(f"调度失败（已重试 {self.max_retries} 次）: {last_error}", exc_info=True)

        return {
            "success": False,
            "duration": duration,
            "error": str(last_error)
        }

    def add_polling_job(self, days: float = 3.5, job_id: str = "issue_polling"):
        """
        添加 Issue 轮询任务

        Args:
            days: 轮询间隔（天）
            job_id: 任务 ID
        """
        self.scheduler.add_job(
            func=self.schedule_all_projects,
            trigger=IntervalTrigger(days=days),
            id=job_id,
            name=f"Issue 轮询任务（每 {days} 天）",
            replace_existing=True,
            max_instances=1  # 同时只运行一个实例
        )

        self.logger.info(f"添加轮询任务: {job_id} (间隔: {days} 天)")

    def start(self):
        """启动调度器（阻塞）"""
        self.logger.info("调度器启动...")
        self.logger.info(f"已配置任务数: {len(self.scheduler.get_jobs())}")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("收到停止信号，正在关闭调度器...")
            self.shutdown()

    def shutdown(self):
        """关闭调度器"""
        self.logger.info("调度器关闭")
        self.scheduler.shutdown()

    def run_once(self):
        """立即执行一次（用于测试）"""
        self.logger.info("立即执行一次调度...")
        return self.schedule_all_projects()


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description="知识工程定时调度器")
    parser.add_argument(
        "--config",
        default="config/projects.yaml",
        help="项目配置文件路径"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.5,
        help="轮询间隔（天），默认 3.5 天"
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="立即执行一次后退出（用于测试）"
    )

    args = parser.parse_args()

    # 创建调度器
    scheduler = KnowledgeScheduler(config_path=args.config)

    if args.run_once:
        # 测试模式：执行一次后退出
        result = scheduler.run_once()
        sys.exit(0 if result.get("success") else 1)
    else:
        # 正常模式：添加定时任务并启动
        scheduler.add_polling_job(days=args.interval)
        scheduler.start()


if __name__ == "__main__":
    main()
