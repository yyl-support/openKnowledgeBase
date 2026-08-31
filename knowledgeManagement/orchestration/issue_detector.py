import logging
from typing import List, Optional
from datetime import datetime
from .gh_client import GitHubCLI, Issue
from config.models import ProjectConfig

logger = logging.getLogger(__name__)


class IssueChangeDetector:
    """Issue 变更检测器（基于 gh CLI）"""

    def __init__(self, gh_client: GitHubCLI):
        """
        初始化检测器

        Args:
            gh_client: GitHub CLI 客户端
        """
        self.gh_client = gh_client

    def detect_new_issues(
        self,
        project: ProjectConfig
    ) -> List[Issue]:
        """
        检测自上次更新以来的新 Issue

        Args:
            project: 项目配置

        Returns:
            List[Issue]: 新 Issue 列表（按时间正序）
        """
        # 1. 搜索 Issue
        logger.info(
            f"检测项目 {project.repo_path} 的新 Issue，"
            f"搜索条件: {project.issue_tracking.search_query}"
        )

        all_issues = self.gh_client.search_issues(
            repo=project.issue_tracking.backlog_repo,
            search_query=project.issue_tracking.search_query,
            limit=100  # 最多检查最近 100 个
        )

        logger.info(f"搜索到 {len(all_issues)} 个符合条件的 Issue")

        # 2. 过滤：只保留新 Issue（编号大于 last_issue_number）
        last_issue_number = project.metadata.last_issue_number or 0
        new_issues = [
            issue for issue in all_issues
            if issue.number > last_issue_number
        ]

        logger.info(
            f"发现 {len(new_issues)} 个新 Issue "
            f"(last_issue_number={last_issue_number})"
        )

        # 3. 按 Issue 编号正序排序（先处理早的）
        new_issues.sort(key=lambda x: x.number)

        return new_issues

    def should_trigger_update(
        self,
        project: ProjectConfig
    ) -> bool:
        """
        判断是否应该触发更新检测

        Args:
            project: 项目配置

        Returns:
            bool: 是否应该触发
        """
        # 1. 如果 mode 是 manual，不自动触发
        if project.update_policy.mode == "manual":
            logger.info(f"项目 {project.repo_path} 配置为手动模式，跳过")
            return False

        # 2. 检查距上次更新的时间
        if project.metadata.last_update_time:
            elapsed_days = (
                datetime.now() - project.metadata.last_update_time
            ).days

            poll_interval = project.issue_tracking.poll_interval

            if elapsed_days < poll_interval:
                logger.info(
                    f"项目 {project.repo_path} 距上次更新 {elapsed_days} 天，"
                    f"小于轮询间隔 {poll_interval} 天，跳过"
                )
                return False

        return True
