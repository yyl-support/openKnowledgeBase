"""
backlog 仓库缓存管理器

负责管理 backlog 仓库的本地缓存，提供需求文档的读取功能
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BacklogCache:
    """backlog 仓库本地缓存管理"""

    def __init__(self, cache_dir: str = "/tmp/backlog-cache"):
        """
        初始化缓存管理器

        Args:
            cache_dir: 本地缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.repo_url = "https://github.com/opensourceways/backlog.git"
        self.repo_path = self.cache_dir / "backlog"

    def ensure_repo(self):
        """确保本地仓库存在且是最新的"""
        if not self.repo_path.exists():
            logger.info(f"本地仓库不存在，开始 clone: {self.repo_url}")
            self._clone_repo()
        else:
            logger.info("本地仓库已存在，更新中...")
            self._pull_repo()

    def _clone_repo(self):
        """Clone 仓库"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.run(
                ["git", "clone", self.repo_url, str(self.repo_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            logger.info("Clone 完成")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Clone 失败: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Clone 超时")

    def _pull_repo(self):
        """更新仓库"""
        try:
            subprocess.run(
                ["git", "pull"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            logger.info("Pull 完成")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Pull 失败: {e.stderr}，将重新 clone")
            # Pull 失败可能是仓库损坏，删除后重新 clone
            import shutil
            shutil.rmtree(self.repo_path)
            self._clone_repo()

    def get_requirement_doc(
        self,
        issue_number: int,
        filename: str
    ) -> Optional[str]:
        """
        从本地仓库读取需求分析文档

        Args:
            issue_number: Issue 编号
            filename: 文件名（如 "Specification.md"）

        Returns:
            Optional[str]: 文档内容（如果存在）
        """
        # 确保仓库是最新的
        self.ensure_repo()

        # 构建文件路径
        # 可能的路径：
        # - issue_docs/{issue_number}/Requirement Analysis/{filename}
        # - issue_docs/{issue_number}/Architecture Design/{filename}

        for subdir in ["Requirement Analysis", "Architecture Design"]:
            file_path = (
                self.repo_path / "issue_docs" / str(issue_number) /
                subdir / filename
            )

            if file_path.exists():
                logger.info(f"从本地读取文档: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

        logger.warning(
            f"本地仓库中未找到文档: issue_docs/{issue_number}/.../{filename}"
        )
        return None

    def list_issue_docs(self, issue_number: int) -> list:
        """
        列出 Issue 的所有文档

        Args:
            issue_number: Issue 编号

        Returns:
            list: 文档路径列表
        """
        self.ensure_repo()

        issue_dir = self.repo_path / "issue_docs" / str(issue_number)

        if not issue_dir.exists():
            return []

        docs = []
        for root, dirs, files in os.walk(issue_dir):
            for file in files:
                if file.endswith('.md'):
                    docs.append(os.path.join(root, file))

        return docs
