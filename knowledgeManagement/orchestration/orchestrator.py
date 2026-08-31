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
from extraction.models import IssueKnowledgePackage

# Phase 6: 决策分派 + 增量两级执行
from update.decision_chain import UpdateDecisionChain
from update.update_chain import KnowledgeUpdateChain
from update.regeneration_chain import SectionRegenerationChain
from config.pricing import split_by_currency

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
    # Phase 6: 增量路径的执行明细（向量库状态 / 章节统计 / 分币种成本）。
    # 全量路径保持 None——跨进程取不到 token，无明细可填。
    detail: Optional[dict] = None


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

        # Phase 6: 决策链（延迟初始化，避免无密钥时构造即失败）
        self._decision_chain = None

        # 任务队列（按优先级）
        self.task_queue = PriorityQueue()

        logger.info(
            f"调度器初始化完成，加载 {len(self.config.projects)} 个项目"
        )

    @property
    def decision_chain(self) -> UpdateDecisionChain:
        """决策链（首次访问时构造，注入配置里的单价表）"""
        if self._decision_chain is None:
            self._decision_chain = UpdateDecisionChain(
                pricing=self.config.global_config.pricing
            )
        return self._decision_chain

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

                # Phase 6: 提取知识 → 决策 → 分派
                result = self._extract_and_dispatch(
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

        # Phase 6: 提取知识 → 决策 → 分派
        result = self._extract_and_dispatch(
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

    def _extract_and_dispatch(
        self,
        project_name: str,
        project: ProjectConfig,
        issue_number: int
    ) -> UpdateResult:
        """
        提取 Issue 知识 → 决策全量/增量 → 分派执行（Phase 6）

        知识提取从 _execute_full_update 上移到这里，因为决策需要知识包，
        而知识包原先只存在于全量方法内部。

        Args:
            project_name: 项目名称
            project: 项目配置
            issue_number: Issue 编号

        Returns:
            UpdateResult: 更新结果
        """
        start_time = datetime.now()

        # 1. 提取知识（原在 _execute_full_update 内部）
        try:
            knowledge_package = self._extract_knowledge(
                project_name,
                project,
                issue_number
            )
        except Exception as e:
            logger.exception(f"知识提取失败: {project_name} (Issue #{issue_number})")
            return UpdateResult(
                project_name=project_name,
                success=False,
                mode="unknown",
                issue_number=issue_number,
                elapsed_seconds=(datetime.now() - start_time).total_seconds(),
                cost_usd=0.0,
                error=f"知识提取失败: {e}"
            )

        # 2. 配置强制全量优先于 LLM 决策（人工兜底）
        if project.update_policy.incremental is False:
            logger.info(
                f"配置强制全量（update_policy.incremental=False），"
                f"忽略 LLM 决策: {project_name}"
            )
            return self._execute_full_update(
                project_name,
                project,
                knowledge_package
            )

        # 3. 决策。决策链抛异常时直接失败——不降级走全量，
        #    因为全量要烧掉约 $6，异常时误触发的代价远高于本次不更新。
        days_since = self._days_since_last_update(project)

        try:
            decision = self.decision_chain.decide(
                knowledge_package,
                days_since
            )
        except Exception as e:
            logger.exception(f"决策链异常，本次不执行更新: {project_name}")
            return UpdateResult(
                project_name=project_name,
                success=False,
                mode="unknown",
                issue_number=issue_number,
                elapsed_seconds=(datetime.now() - start_time).total_seconds(),
                cost_usd=0.0,
                error=f"决策链异常: {e}"
            )

        mode = decision.get("decision")
        logger.info(
            f"决策: {mode}（理由: {decision.get('reason')}, "
            f"置信度: {decision.get('confidence')}）"
        )

        # 4. 分派
        if mode == "full":
            return self._execute_full_update(
                project_name,
                project,
                knowledge_package
            )

        return self._execute_incremental_update(
            project_name,
            project,
            knowledge_package,
            decision_cost=decision.get("cost")
        )

    def _days_since_last_update(self, project: ProjectConfig) -> float:
        """距上次更新的天数；从未更新过时返回 0.0"""
        last = project.metadata.last_update_time
        if last is None:
            return 0.0
        return (datetime.now() - last).total_seconds() / 86400.0

    def _extract_knowledge(
        self,
        project_name: str,
        project: ProjectConfig,
        issue_number: int
    ) -> IssueKnowledgePackage:
        """
        提取 Issue 知识并落盘到 work/{project}/issue_knowledge.json

        Args:
            project_name: 项目名称
            project: 项目配置
            issue_number: Issue 编号

        Returns:
            IssueKnowledgePackage: 知识包
        """
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

        return knowledge_package

    def _execute_full_update(
        self,
        project_name: str,
        project: ProjectConfig,
        knowledge_package: IssueKnowledgePackage
    ) -> UpdateResult:
        """
        执行全量更新：调用四层流水线重建全部文档

        Phase 6 起知识提取上移到 _extract_and_dispatch，本方法直接收知识包。

        Args:
            project_name: 项目名称
            project: 项目配置
            knowledge_package: 已提取的 Issue 知识包

        Returns:
            UpdateResult: 更新结果
        """
        issue_number = knowledge_package.issue_number
        logger.info(f"开始全量更新: {project_name} (Issue #{issue_number})")

        start_time = datetime.now()

        try:
            # 调用四层流水线
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

                # 占位值，不是实测成本。全量走 subprocess.run(pipeline.py) →
                # UA → 再起 Claude Code subagent，隔两层独立进程，
                # get_openai_callback() 伸不进去，拿不到 token 数。
                # 要统计得解析 pipeline 的 stdout，属独立工作，Phase 6 不做。
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

    def _execute_incremental_update(
        self,
        project_name: str,
        project: ProjectConfig,
        knowledge_package: IssueKnowledgePackage,
        decision_cost: Optional[dict] = None
    ) -> UpdateResult:
        """
        执行增量更新（Phase 6）：两级执行

        第一级 update_chain 写向量库，第二级 regeneration_chain 更新
        knowledgeBase/{project}/*.md 这些给人读的文档。只写向量库不更新文档，
        人看到的还是旧内容。

        Args:
            project_name: 项目名称
            project: 项目配置
            knowledge_package: 已提取的 Issue 知识包
            decision_cost: 决策链的成本记录，计入本次总成本

        Returns:
            UpdateResult: 更新结果
        """
        issue_number = knowledge_package.issue_number
        logger.info(f"开始增量更新: {project_name} (Issue #{issue_number})")

        start_time = datetime.now()
        pricing = self.config.global_config.pricing

        # 决策成本先入账，无论后续成败都已经花掉了
        cost_records = [decision_cost] if decision_cost else []

        def _finish(success: bool, detail: dict, error: Optional[str] = None):
            """汇总分币种成本并构造返回值"""
            totals = split_by_currency(cost_records)
            detail["cost_usd"] = totals["cost_usd"]
            detail["cost_cny"] = totals["cost_cny"]

            return UpdateResult(
                project_name=project_name,
                success=success,
                mode="incremental",
                issue_number=issue_number,
                elapsed_seconds=(datetime.now() - start_time).total_seconds(),
                # ProjectMetadata.total_cost_usd 只累加美元部分，
                # 人民币部分记在 detail 里，不做汇率折算
                cost_usd=totals["cost_usd"],
                error=error,
                detail=detail
            )

        # ---- 第一级：写向量库 ----
        try:
            update_chain = KnowledgeUpdateChain(project_name)
            upd_result = update_chain.update_from_issue(knowledge_package)
        except Exception as e:
            logger.exception(f"向量库更新异常: {project_name}")
            return _finish(
                False,
                {"vector_status": "failed"},
                error=f"向量库更新异常: {e}"
            )

        vector_status = upd_result.get("status")

        if vector_status == "failed":
            logger.error(
                f"向量库更新失败，不继续做章节重生成: "
                f"{project_name} — {upd_result.get('error')}"
            )
            return _finish(
                False,
                {
                    "vector_status": "failed",
                    "documents_added": upd_result.get("documents_added", 0),
                    "documents_deleted": upd_result.get("documents_deleted", 0),
                    "chunks_created": upd_result.get("chunks_created", 0),
                },
                error=f"向量库更新失败: {upd_result.get('error')}"
            )

        if vector_status == "no_changes":
            # 空操作是合法结果，不是故障，但绝不能悄无声息
            logger.info(
                f"向量库状态: no_changes —— 本 Issue 没有带来需要索引的变更，"
                f"未写入任何文档（{project_name} Issue #{issue_number}）"
            )
        else:
            logger.info(
                f"向量库更新完成: 添加={upd_result.get('documents_added')}, "
                f"删除={upd_result.get('documents_deleted')}, "
                f"分块={upd_result.get('chunks_created')}"
            )

        # ---- 第二级：更新人读文档 ----
        storage = self.config.global_config.storage
        knowledge_base_dir = os.path.join(
            storage["base_dir"],
            storage["knowledge_dir"],
            project_name
        )

        if not os.path.isdir(knowledge_base_dir):
            logger.warning(
                f"知识库目录不存在: {knowledge_base_dir} —— "
                f"本次增量只更新了向量库，未更新任何人读文档"
            )

        try:
            regen_chain = SectionRegenerationChain(project_name, pricing=pricing)
            regen_result = regen_chain.regenerate_all_affected(
                knowledge_package,
                knowledge_base_dir
            )
        except Exception as e:
            logger.exception(f"章节重生成异常: {project_name}")
            return _finish(
                False,
                {
                    "vector_status": vector_status,
                    "documents_added": upd_result.get("documents_added", 0),
                    "documents_deleted": upd_result.get("documents_deleted", 0),
                    "chunks_created": upd_result.get("chunks_created", 0),
                },
                error=f"章节重生成异常: {e}"
            )

        # 章节生成的 LLM 成本入账
        cost_records.extend(getattr(regen_chain, "cost_records", []) or [])

        sections_regenerated = regen_result.get("sections_regenerated", 0)
        sections_failed = regen_result.get("sections_failed", 0)
        sections_skipped = regen_result.get("sections_skipped", [])

        detail = {
            "vector_status": vector_status,
            "documents_added": upd_result.get("documents_added", 0),
            "documents_deleted": upd_result.get("documents_deleted", 0),
            "chunks_created": upd_result.get("chunks_created", 0),
            "sections_regenerated": sections_regenerated,
            "sections_failed": sections_failed,
            "sections_skipped": sections_skipped,
            "updated_documents": regen_result.get("updated_documents", []),
        }

        # 成功判定：一个章节都没重生成却有失败的，判失败。
        # 用户预期是文档被更新了，结果没更新，静默放过就是假成功。
        if sections_failed > 0 and sections_regenerated == 0:
            logger.error(
                f"章节重生成全部失败（失败={sections_failed}，成功=0）: "
                f"{project_name}"
            )
            return _finish(
                False,
                detail,
                error=f"章节重生成全部失败（{sections_failed} 个章节）"
            )

        if not regen_result.get("success", True):
            return _finish(
                False,
                detail,
                error=f"章节重生成失败: {regen_result.get('error')}"
            )

        if sections_skipped:
            logger.warning(
                f"有 {len(sections_skipped)} 个章节被跳过: {sections_skipped}"
            )

        logger.info(
            f"增量更新成功: {project_name} "
            f"(向量库={vector_status}, 章节重生成={sections_regenerated}, "
            f"失败={sections_failed}, 跳过={len(sections_skipped)})"
        )

        return _finish(True, detail)

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
