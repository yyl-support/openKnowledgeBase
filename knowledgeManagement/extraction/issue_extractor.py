"""
Issue 知识提取器：从 Issue 工作流中提取完整知识

整合 PR 链接解析、文档读取、代码变更提取等功能，
构建完整的 Issue 知识包
"""

import logging
from typing import Optional
from .models import (
    IssueKnowledgePackage,
    PRReference,
    RequirementDoc,
    CodeChange,
    TestReport,
    ReleaseInfo
)
from .pr_link_parser import PRLinkParser
from .backlog_cache import BacklogCache

# 导入 Phase 1 的 gh_client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from orchestration.gh_client import GitHubCLI

logger = logging.getLogger(__name__)


class IssueKnowledgeExtractor:
    """从 Issue 工作流中提取完整知识"""

    def __init__(
        self,
        gh_client: GitHubCLI,
        backlog_cache: Optional[BacklogCache] = None
    ):
        """
        初始化提取器

        Args:
            gh_client: GitHub CLI 客户端
            backlog_cache: backlog 缓存管理器（可选）
        """
        self.gh_client = gh_client
        self.pr_parser = PRLinkParser()
        self.backlog_cache = backlog_cache or BacklogCache()

    def extract(
        self,
        backlog_repo: str,
        issue_number: int,
        project_repo: str
    ) -> IssueKnowledgePackage:
        """
        提取 Issue 的完整知识

        Args:
            backlog_repo: backlog 仓库（如 "opensourceways/backlog"）
            issue_number: Issue 编号
            project_repo: 项目仓库（如 "opensourceways/forum-reply-robot"）

        Returns:
            IssueKnowledgePackage: 知识包
        """
        logger.info(
            f"开始提取 Issue #{issue_number} 的知识 "
            f"(项目: {project_repo})"
        )

        # 1. 获取 Issue 基本信息
        issue = self.gh_client.get_issue(backlog_repo, issue_number)

        logger.info(
            f"Issue #{issue_number}: {issue.title}, "
            f"标签: {issue.labels}"
        )

        # 2. 解析 PR 链接
        logger.info("解析评论中的 PR 链接...")

        requirement_pr_ref = self.pr_parser.parse_requirement_pr(
            issue.comments
        )
        development_pr_ref = self.pr_parser.parse_development_pr(
            issue.comments,
            project_repo
        )
        test_pr_ref = self.pr_parser.parse_test_pr(issue.comments)
        release_pr_ref = self.pr_parser.parse_release_pr(issue.comments)

        # 3. 提取需求分析文档
        requirement_doc = None
        if requirement_pr_ref:
            requirement_doc = self._extract_requirement_doc(
                requirement_pr_ref,
                issue_number
            )

        # 4. 提取代码变更
        code_change = None
        if development_pr_ref:
            code_change = self._extract_code_change(development_pr_ref)

        # 5. （可选）提取测试报告
        test_report = None
        if test_pr_ref:
            test_report = self._extract_test_report(test_pr_ref, issue_number)

        # 6. （可选）提取上线信息
        release_info = None
        if release_pr_ref:
            release_info = self._extract_release_info(release_pr_ref)

        # 7. 构建知识包
        knowledge_package = IssueKnowledgePackage(
            issue_number=issue.number,
            issue_title=issue.title,
            issue_labels=issue.labels,
            issue_body=issue.body,
            requirement=requirement_doc,
            code_change=code_change,
            test_report=test_report,
            release_info=release_info
        )

        logger.info(
            f"知识提取完成: "
            f"需求文档={requirement_doc is not None}, "
            f"代码变更={code_change is not None}, "
            f"测试报告={test_report is not None}, "
            f"上线信息={release_info is not None}"
        )

        return knowledge_package

    def _extract_requirement_doc(
        self,
        pr_ref: PRReference,
        issue_number: int
    ) -> Optional[RequirementDoc]:
        """
        提取需求分析文档

        Args:
            pr_ref: PR 引用
            issue_number: Issue 编号

        Returns:
            Optional[RequirementDoc]: 需求文档
        """
        logger.info(f"提取需求分析文档 (PR #{pr_ref.number})...")

        # 1. 获取 PR 详情
        pr = self.gh_client.get_pull_request(pr_ref.repo, pr_ref.number)

        # 更新 PR 引用信息
        pr_ref.title = pr.title
        pr_ref.state = pr.state
        pr_ref.branch = pr.head_ref

        # 2. 尝试从本地 backlog 仓库读取（如果 PR 已合入）
        if pr.state == "MERGED":
            logger.info("PR 已合入，尝试从本地 backlog 仓库读取...")

            spec_content = self.backlog_cache.get_requirement_doc(
                issue_number,
                "Specification.md"
            )
            qa_content = self.backlog_cache.get_requirement_doc(
                issue_number,
                "QA.md"
            )

            if spec_content:
                return RequirementDoc(
                    specification=spec_content,
                    qa_checklist=qa_content or "",
                    pr=pr_ref
                )

        # 3. 如果本地没有，从 gh API 读取（指定分支）
        logger.info(f"从 gh API 读取文档（分支: {pr.head_ref}）...")

        try:
            # 尝试多个可能的文件名
            spec_filenames = [
                f"#{issue_number} Requirement Analysis Specification.md",
                f"#{issue_number} Architecture Design Specification.md",
                "Specification.md"
            ]

            spec_content = None
            for filename in spec_filenames:
                try:
                    file_path = (
                        f"issue_docs/{issue_number}/Requirement Analysis/{filename}"
                    )
                    spec_content = self.gh_client.get_file_content(
                        pr_ref.repo,
                        file_path,
                        ref=pr.head_ref
                    )
                    if spec_content:
                        logger.info(f"成功读取文档: {filename}")
                        break
                except Exception as e:
                    logger.debug(f"尝试读取 {filename} 失败: {e}")
                    continue

            # QA 文档
            qa_content = None
            try:
                qa_path = (
                    f"issue_docs/{issue_number}/Requirement Analysis/"
                    f"#{issue_number} Requirement Analysis QA.md"
                )
                qa_content = self.gh_client.get_file_content(
                    pr_ref.repo,
                    qa_path,
                    ref=pr.head_ref
                )
            except Exception as e:
                logger.debug(f"读取 QA 文档失败: {e}")

            if spec_content:
                return RequirementDoc(
                    specification=spec_content,
                    qa_checklist=qa_content or "",
                    pr=pr_ref
                )

        except Exception as e:
            logger.error(f"从 gh API 读取文档失败: {e}")

        logger.warning("无法获取需求分析文档")
        return None

    def _extract_code_change(
        self,
        pr_ref: PRReference
    ) -> Optional[CodeChange]:
        """
        提取代码变更

        Args:
            pr_ref: PR 引用

        Returns:
            Optional[CodeChange]: 代码变更
        """
        logger.info(f"提取代码变更 (PR #{pr_ref.number})...")

        try:
            # 1. 获取 PR 详情
            pr = self.gh_client.get_pull_request(pr_ref.repo, pr_ref.number)

            # 更新 PR 引用信息
            pr_ref.title = pr.title
            pr_ref.state = pr.state
            pr_ref.branch = pr.head_ref

            # 2. 获取 diff
            diff = self.gh_client.get_pr_diff(pr_ref.repo, pr_ref.number)

            # 3. 统计变更
            total_additions = sum(f.get('additions', 0) for f in pr.files)
            total_deletions = sum(f.get('deletions', 0) for f in pr.files)

            logger.info(
                f"代码变更: {len(pr.files)} 个文件, "
                f"+{total_additions} -{total_deletions}"
            )

            return CodeChange(
                pr=pr_ref,
                diff=diff,
                files=pr.files,
                total_additions=total_additions,
                total_deletions=total_deletions
            )

        except Exception as e:
            logger.error(f"提取代码变更失败: {e}")
            return None

    def _extract_test_report(
        self,
        pr_ref: PRReference,
        issue_number: int
    ) -> Optional[TestReport]:
        """
        提取测试报告（可选）

        Args:
            pr_ref: PR 引用
            issue_number: Issue 编号

        Returns:
            Optional[TestReport]: 测试报告
        """
        logger.info(f"提取测试报告 (PR #{pr_ref.number})...")

        try:
            # 1. 获取 PR 详情
            pr = self.gh_client.get_pull_request(pr_ref.repo, pr_ref.number)

            # 更新 PR 引用信息
            pr_ref.title = pr.title
            pr_ref.state = pr.state
            pr_ref.branch = pr.head_ref

            # 2. 尝试从本地 backlog 仓库读取
            if pr.state == "MERGED":
                test_content = self.backlog_cache.get_requirement_doc(
                    issue_number,
                    "Test Report.md"
                )
                if test_content:
                    return TestReport(pr=pr_ref, content=test_content)

            # 3. 从 gh API 读取
            try:
                test_path = (
                    f"issue_docs/{issue_number}/Test Report/"
                    f"#{issue_number} Test Report.md"
                )
                test_content = self.gh_client.get_file_content(
                    pr_ref.repo,
                    test_path,
                    ref=pr.head_ref
                )
                if test_content:
                    return TestReport(pr=pr_ref, content=test_content)
            except Exception as e:
                logger.debug(f"读取测试报告失败: {e}")

        except Exception as e:
            logger.error(f"提取测试报告失败: {e}")

        logger.info("测试报告提取失败（可选）")
        return None

    def _extract_release_info(
        self,
        pr_ref: PRReference
    ) -> Optional[ReleaseInfo]:
        """
        提取上线信息（可选）

        Args:
            pr_ref: PR 引用

        Returns:
            Optional[ReleaseInfo]: 上线信息
        """
        logger.info(f"提取上线信息 (PR #{pr_ref.number})...")

        try:
            # 1. 获取 PR 详情
            pr = self.gh_client.get_pull_request(pr_ref.repo, pr_ref.number)

            # 更新 PR 引用信息
            pr_ref.title = pr.title
            pr_ref.state = pr.state
            pr_ref.branch = pr.head_ref

            # 2. 获取 PR diff（包含变更计划内容）
            diff = self.gh_client.get_pr_diff(pr_ref.repo, pr_ref.number)

            return ReleaseInfo(pr=pr_ref, content=diff)

        except Exception as e:
            logger.error(f"提取上线信息失败: {e}")

        logger.info("上线信息提取失败（可选）")
        return None
