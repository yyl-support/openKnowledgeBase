"""
PR 链接解析器：从 Issue 评论中解析 PR 链接

根据评论中的关键词和 GitHub PR URL 模式，提取不同类型的 PR 引用
"""

import re
import logging
from typing import List, Optional
from .models import PRReference

logger = logging.getLogger(__name__)


class PRLinkParser:
    """从 Issue 评论中解析 PR 链接"""

    # 正则模式
    GITHUB_PR_PATTERN = re.compile(
        r'https://github\.com/([\w-]+/[\w-]+)/pull/(\d+)'
    )

    # 关键词映射
    KEYWORDS = {
        'requirement': ['需求分析', 'Requirement Analysis', '设计文档', 'Architecture Design'],
        'development': ['开发', 'develop', '实现', 'implementation'],
        'test': ['测试', 'test'],
        'release': ['变更计划', 'release', '上线', 'deploy']
    }

    def parse_requirement_pr(self, comments: List[dict]) -> Optional[PRReference]:
        """
        解析需求分析 PR

        Args:
            comments: Issue 评论列表

        Returns:
            Optional[PRReference]: 需求分析 PR 引用
        """
        for comment in comments:
            body = comment.get('body', '')

            # 查找包含需求分析关键词的评论
            if any(kw in body for kw in self.KEYWORDS['requirement']):
                # 提取 PR 链接
                matches = self.GITHUB_PR_PATTERN.findall(body)

                for repo, pr_number in matches:
                    # 需求分析 PR 通常在 backlog 仓库
                    if 'backlog' in repo:
                        logger.info(
                            f"找到需求分析 PR: {repo}/pull/{pr_number}"
                        )

                        return PRReference(
                            repo=repo,
                            number=int(pr_number),
                            title="",  # 后续通过 gh pr view 获取
                            state="",
                            url=f"https://github.com/{repo}/pull/{pr_number}"
                        )

        logger.warning("未找到需求分析 PR")
        return None

    def parse_development_pr(
        self,
        comments: List[dict],
        project_repo: str
    ) -> Optional[PRReference]:
        """
        解析开发 PR

        Args:
            comments: Issue 评论列表
            project_repo: 项目仓库（如 "opensourceways/forum-reply-robot"）

        Returns:
            Optional[PRReference]: 开发 PR 引用
        """
        for comment in comments:
            body = comment.get('body', '')

            # 查找包含开发关键词的评论
            if any(kw in body for kw in self.KEYWORDS['development']):
                # 提取 PR 链接
                matches = self.GITHUB_PR_PATTERN.findall(body)

                for repo, pr_number in matches:
                    # 开发 PR 在项目仓库
                    if project_repo in repo:
                        logger.info(
                            f"找到开发 PR: {repo}/pull/{pr_number}"
                        )

                        return PRReference(
                            repo=repo,
                            number=int(pr_number),
                            title="",
                            state="",
                            url=f"https://github.com/{repo}/pull/{pr_number}"
                        )

        logger.warning(f"未找到开发 PR（项目仓库: {project_repo}）")
        return None

    def parse_test_pr(self, comments: List[dict]) -> Optional[PRReference]:
        """
        解析测试报告 PR

        Args:
            comments: Issue 评论列表

        Returns:
            Optional[PRReference]: 测试报告 PR 引用
        """
        for comment in comments:
            body = comment.get('body', '')

            if any(kw in body for kw in self.KEYWORDS['test']):
                matches = self.GITHUB_PR_PATTERN.findall(body)

                for repo, pr_number in matches:
                    if 'backlog' in repo:
                        logger.info(
                            f"找到测试报告 PR: {repo}/pull/{pr_number}"
                        )

                        return PRReference(
                            repo=repo,
                            number=int(pr_number),
                            title="",
                            state="",
                            url=f"https://github.com/{repo}/pull/{pr_number}"
                        )

        logger.info("未找到测试报告 PR（可选）")
        return None

    def parse_release_pr(self, comments: List[dict]) -> Optional[PRReference]:
        """
        解析变更计划 PR（release-mgmt）

        Args:
            comments: Issue 评论列表

        Returns:
            Optional[PRReference]: 变更计划 PR 引用
        """
        for comment in comments:
            body = comment.get('body', '')

            if any(kw in body for kw in self.KEYWORDS['release']):
                matches = self.GITHUB_PR_PATTERN.findall(body)

                for repo, pr_number in matches:
                    if 'release-mgmt' in repo:
                        logger.info(
                            f"找到变更计划 PR: {repo}/pull/{pr_number}"
                        )

                        return PRReference(
                            repo=repo,
                            number=int(pr_number),
                            title="",
                            state="",
                            url=f"https://github.com/{repo}/pull/{pr_number}"
                        )

        logger.info("未找到变更计划 PR（可选）")
        return None
