"""
open-zread 适配器
通过命令行调用 open-zread 并解析生成的 wiki 文档
"""
import logging
import os
import subprocess
import shutil
import tempfile
from typing import Dict, List
from datetime import datetime
from pathlib import Path
from .base import BaseAdapter


logger = logging.getLogger(__name__)


class ZreadAdapter(BaseAdapter):
    """open-zread 适配器"""

    def get_tool_name(self) -> str:
        return "zread"

    def extract(self, repo_path: str, output_dir: str) -> Dict:
        """
        使用 open-zread 提取知识

        流程：
        1. 克隆仓库到临时目录（如果是 URL）
        2. 执行 open-zread 命令生成 wiki
        3. 解析 .open-zread/wiki/ 下的所有 md 文件
        4. 提取 frontmatter 和内容

        Args:
            repo_path: 代码仓路径（本地路径或 Git URL）
            output_dir: 工作目录

        Returns:
            提取结果字典
        """
        logger.info(f"ZreadAdapter: 开始提取知识，仓库路径: {repo_path}")

        # 判断是否为 URL
        is_url = repo_path.startswith(('http://', 'https://', 'git@'))

        if is_url:
            # 克隆到临时目录
            work_dir = tempfile.mkdtemp(dir=output_dir)
            logger.info(f"克隆仓库到: {work_dir}")
            self._clone_repo(repo_path, work_dir)
        else:
            # 使用本地路径
            if not os.path.isdir(repo_path):
                raise ValueError(f"仓库路径不存在: {repo_path}")
            work_dir = repo_path

        try:
            # 执行 open-zread
            self._run_zread(work_dir)

            # 解析 wiki 文档
            pages_data = self._parse_wiki_docs(work_dir)

            result = {
                "pages": pages_data,
                "tool": self.get_tool_name(),
                "timestamp": datetime.now().isoformat(),
                "repo": repo_path
            }

            logger.info(f"ZreadAdapter: 提取完成，共 {len(pages_data)} 个页面")
            return result

        finally:
            # 如果是临时目录，清理
            if is_url and os.path.exists(work_dir):
                logger.info(f"清理临时目录: {work_dir}")
                shutil.rmtree(work_dir, ignore_errors=True)

    def _clone_repo(self, repo_url: str, target_dir: str):
        """
        克隆 Git 仓库

        Args:
            repo_url: 仓库 URL
            target_dir: 目标目录
        """
        cmd = ["git", "clone", "--depth", "1", repo_url, target_dir]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
            logger.info(f"仓库克隆成功")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"克隆仓库失败: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"克隆仓库超时")

    def _run_zread(self, repo_dir: str):
        """
        执行 open-zread 命令

        Args:
            repo_dir: 仓库目录
        """
        cmd = ["python", "-m", "open_zread.main", "--output", ".open-zread/wiki"]

        logger.info(f"执行 open-zread: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=600
            )
            logger.info("open-zread 执行成功")
            if result.stdout:
                logger.debug(f"stdout: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"stderr: {e.stderr}")
            raise RuntimeError(f"执行 open-zread 失败: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("执行 open-zread 超时")

    def _parse_wiki_docs(self, repo_dir: str) -> List[Dict]:
        """
        解析 .open-zread/wiki/ 下的所有 markdown 文件

        Args:
            repo_dir: 仓库目录

        Returns:
            页面列表
        """
        wiki_dir = os.path.join(repo_dir, ".open-zread", "wiki")

        if not os.path.isdir(wiki_dir):
            raise RuntimeError(f"wiki 目录不存在: {wiki_dir}")

        pages_data = []

        # 递归查找所有 .md 文件
        for root, dirs, files in os.walk(wiki_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, wiki_dir)

                    try:
                        page = self._parse_markdown_file(file_path, rel_path)
                        if page:
                            pages_data.append(page)
                    except Exception as e:
                        logger.warning(f"解析文件失败 {file_path}: {e}")

        return pages_data

    def _parse_markdown_file(self, file_path: str, rel_path: str) -> Dict:
        """
        解析单个 markdown 文件（包含 frontmatter）

        Args:
            file_path: 文件路径
            rel_path: 相对路径

        Returns:
            页面数据字典
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 frontmatter
        frontmatter = {}
        body = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # 简单解析 YAML frontmatter
                frontmatter_text = parts[1].strip()
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip().strip('"')

                body = parts[2].strip()

        # 提取标题（从 frontmatter 或文件名）
        title = frontmatter.get('title', Path(file_path).stem)

        return {
            "title": title,
            "content": body,
            "metadata": {
                "slug": frontmatter.get('slug', ''),
                "frontmatter": frontmatter,
                "type": "wiki-page"
            },
            "path": rel_path
        }
