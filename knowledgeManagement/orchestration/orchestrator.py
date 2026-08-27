import logging
import subprocess
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from queue import PriorityQueue

from config.models import SystemConfig, ProjectConfig
from config.loader import load_system_config, save_system_config
from .gh_client import GitHubCLI
from .issue_detector import IssueChangeDetector

# Phase 2: 导入知识提取器
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from extraction.issue_extractor import IssueKnowledgeExtractor
from extraction.backlog_cache import BacklogCache

logger = logging.getLogger(__name__)


@dataclass
class UpdateTask:
    """更新任务"""
    priority: int  # 数字越小优先级越高（high=1, medium=2, low=3）
    project_name: str
    project: ProjectConfig
    issue_number: Optional[int] = None
    mode: str = "full"  # full | incremental

    def __lt__(self, other):
        """用于优先级队列排序"""
        return self.priority < other.priority


@dataclass
class UpdateResult:
    """更新结果"""
    project_name: str
    success: bool
    mode: str
    issue_number: Optional[int]
    elapsed_seconds: float
    cost_usd: float
    error: Optional[str] = None


class KnowledgeOrchestrator:
    """知识工程总调度器"""

    def __init__(self, config_path: str = "config/projects.yaml"):
        """
        初始化调度器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = load_system_config(config_path)

        # 初始化 GitHub CLI 客户端
        self.gh_client = GitHubCLI(
            cli_path=self.config.global_config.github["cli_path"]
        )

        # 初始化 Issue 检测器
        self.issue_detector = IssueChangeDetector(self.gh_client)

        # Phase 2: 初始化 backlog 缓存
        self.backlog_cache = BacklogCache()

        # Phase 2: 初始化知识提取器
        self.issue_extractor = IssueKnowledgeExtractor(
            self.gh_client,
            self.backlog_cache
        )

        # 任务队列（按优先级）
        self.task_queue = PriorityQueue()

        logger.info(
            f"调度器初始化完成，加载 {len(self.config.projects)} 个项目"
        )

    def schedule_all_projects(self) -> List[UpdateResult]:
        """
        调度所有项目的更新检测

        Returns:
            List[UpdateResult]: 所有项目的更新结果
        """
        logger.info("=" * 60)
        logger.info("开始调度所有项目")
        logger.info("=" * 60)

        results = []

        for project_name, project in self.config.projects.items():
            logger.info(f"\n处理项目: {project_name}")

            # 检查是否应该触发
            if not self.issue_detector.should_trigger_update(project):
                logger.info(f"项目 {project_name} 暂不需要更新，跳过")
                continue

            # 检测新 Issue
            new_issues = self.issue_detector.detect_new_issues(project)

            if not new_issues:
                logger.info(f"项目 {project_name} 没有新 Issue，跳过")
                continue

            # 为每个新 Issue 创建更新任务
            for issue in new_issues:
                logger.info(
                    f"发现新 Issue #{issue.number}: {issue.title}"
                )

                # Phase 1 只实现全量更新
                result = self._execute_full_update(
                    project_name,
                    project,
                    issue.number
                )
                results.append(result)

                # 更新项目元数据
                if result.success:
                    self._update_project_metadata(
                        project_name,
                        issue.number,
                        result.mode,
                        result.cost_usd
                    )

        logger.info("=" * 60)
        logger.info(f"调度完成，共处理 {len(results)} 个任务")
        logger.info("=" * 60)

        return results

    def schedule_project(
        self,
        project_name: str,
        force: bool = False
    ) -> Optional[UpdateResult]:
        """
        调度单个项目的更新

        Args:
            project_name: 项目名称
            force: 是否强制更新（忽略轮询间隔）

        Returns:
            Optional[UpdateResult]: 更新结果（如果没有新 Issue 则返回 None）
        """
        if project_name not in self.config.projects:
            raise ValueError(f"项目不存在: {project_name}")

        project = self.config.projects[project_name]

        logger.info(f"调度项目: {project_name}")

        # 检查是否应该触发（force 模式跳过检查）
        if not force and not self.issue_detector.should_trigger_update(project):
            logger.info(f"项目 {project_name} 暂不需要更新")
            return None

        # 检测新 Issue
        new_issues = self.issue_detector.detect_new_issues(project)

        if not new_issues:
            logger.info(f"项目 {project_name} 没有新 Issue")
            return None

        # 只处理最新的一个 Issue
        latest_issue = new_issues[-1]
        logger.info(
            f"处理最新 Issue #{latest_issue.number}: {latest_issue.title}"
        )

        # Phase 1 只实现全量更新
        result = self._execute_full_update(
            project_name,
            project,
            latest_issue.number
        )

        # 更新项目元数据
        if result.success:
            self._update_project_metadata(
                project_name,
                latest_issue.number,
                result.mode,
                result.cost_usd
            )

        return result

    def _execute_full_update(
        self,
        project_name: str,
        project: ProjectConfig,
        issue_number: int
    ) -> UpdateResult:
        """
        执行全量更新（Phase 2 增强：先提取知识，再调用流水线）

        Args:
            project_name: 项目名称
            project: 项目配置
            issue_number: Issue 编号

        Returns:
            UpdateResult: 更新结果
        """
        logger.info(f"开始全量更新: {project_name} (Issue #{issue_number})")

        start_time = datetime.now()

        try:
            # Phase 2 新增：先提取 Issue 知识
            logger.info("提取 Issue 知识...")
            knowledge_package = self.issue_extractor.extract(
                backlog_repo=project.issue_tracking.backlog_repo,
                issue_number=issue_number,
                project_repo=self._get_project_repo_name(project.repo_path)
            )

            # 保存知识包到工作目录（供流水线使用）
            work_dir = f"work/{project_name}"
            os.makedirs(work_dir, exist_ok=True)

            knowledge_file = f"{work_dir}/issue_knowledge.json"
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'issue_number': knowledge_package.issue_number,
                    'issue_title': knowledge_package.issue_title,
                    'issue_labels': knowledge_package.issue_labels,
                    'has_requirement': knowledge_package.requirement is not None,
                    'has_code_change': knowledge_package.code_change is not None,
                    'has_test_report': knowledge_package.test_report is not None,
                    'has_release_info': knowledge_package.release_info is not None,
                    'changed_files_count': knowledge_package.get_changed_files_count(),
                    'requirement_doc_size': knowledge_package.get_requirement_doc_size(),
                    'extracted_at': knowledge_package.extracted_at.isoformat()
                }, f, indent=2, ensure_ascii=False)

            logger.info(
                f"知识提取完成: "
                f"变更文件数={knowledge_package.get_changed_files_count()}, "
                f"需求文档大小={knowledge_package.get_requirement_doc_size()} 字符"
            )
            logger.info(f"知识包已保存到: {knowledge_file}")

            # 原有代码：调用四层流水线
            # 构建 pipeline.py 命令
            cmd = [
                "python3",
                "pipeline.py",
                "--repo", project.repo_path,
                "--adapter", project.adapter,
                "--output-types"
            ] + project.output_types

            # 如果是 ua adapter，添加 profile 参数
            if project.adapter == "ua" and project.ua_profile:
                cmd.extend(["--ua-profile", project.ua_profile])

            logger.info(f"执行命令: {' '.join(cmd)}")

            # 执行流水线
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
                cwd="/Users/gorden/huawei/code/openKnowledgeBase/knowledgeManagement/scripts"
            )

            elapsed = (datetime.now() - start_time).total_seconds()

            if result.returncode == 0:
                logger.info(
                    f"全量更新成功: {project_name} "
                    f"(耗时 {elapsed:.1f}s)"
                )

                # TODO: 从日志中提取成本（Phase 1 先硬编码）
                estimated_cost = 6.0

                return UpdateResult(
                    project_name=project_name,
                    success=True,
                    mode="full",
                    issue_number=issue_number,
                    elapsed_seconds=elapsed,
                    cost_usd=estimated_cost
                )
            else:
                error_msg = result.stderr or result.stdout
                logger.error(
                    f"全量更新失败: {project_name}\n{error_msg}"
                )

                return UpdateResult(
                    project_name=project_name,
                    success=False,
                    mode="full",
                    issue_number=issue_number,
                    elapsed_seconds=elapsed,
                    cost_usd=0.0,
                    error=error_msg
                )

        except subprocess.TimeoutExpired:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"全量更新超时: {project_name}")

            return UpdateResult(
                project_name=project_name,
                success=False,
                mode="full",
                issue_number=issue_number,
                elapsed_seconds=elapsed,
                cost_usd=0.0,
                error="执行超时（1小时）"
            )

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.exception(f"全量更新异常: {project_name}")

            return UpdateResult(
                project_name=project_name,
                success=False,
                mode="full",
                issue_number=issue_number,
                elapsed_seconds=elapsed,
                cost_usd=0.0,
                error=str(e)
            )

    def _get_project_repo_name(self, repo_path: str) -> str:
        """从本地路径推断 GitHub 仓库名称"""
        # 简单实现：从路径中提取项目名，拼接到 opensourceways/
        project_name = os.path.basename(repo_path.rstrip('/'))
        return f"opensourceways/{project_name}"

    def _update_project_metadata(
        self,
        project_name: str,
        issue_number: int,
        mode: str,
        cost: float
    ):
        """
        更新项目元数据

        Args:
            project_name: 项目名称
            issue_number: Issue 编号
            mode: 更新模式（full | incremental）
            cost: 成本
        """
        project = self.config.projects[project_name]

        project.metadata.last_issue_number = issue_number
        project.metadata.last_update_time = datetime.now()
        project.metadata.last_update_mode = mode
        project.metadata.total_updates += 1
        project.metadata.total_cost_usd += cost

        # 保存配置
        save_system_config(self.config, self.config_path)

        logger.info(
            f"更新项目元数据: {project_name}, "
            f"last_issue={issue_number}, "
            f"total_updates={project.metadata.total_updates}, "
            f"total_cost=${project.metadata.total_cost_usd:.2f}"
        )
