import subprocess
import json
import base64
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Issue:
    """Issue 数据结构"""
    number: int
    title: str
    state: str
    labels: List[str]
    created_at: str
    closed_at: Optional[str]
    body: str
    comments: List[dict]


@dataclass
class PullRequest:
    """PR 数据结构"""
    number: int
    title: str
    state: str
    head_ref: str  # 分支名
    files: List[dict]
    diff: Optional[str] = None


class GitHubCLI:
    """GitHub CLI 封装类（强制使用 gh CLI）"""

    def __init__(self, cli_path: str = "gh"):
        """
        初始化 GitHub CLI 客户端

        Args:
            cli_path: gh CLI 可执行文件路径（默认 "gh"）
        """
        self.cli_path = cli_path
        self._verify_installation()

    def _verify_installation(self):
        """验证 gh CLI 是否正确安装和配置"""
        try:
            result = subprocess.run(
                [self.cli_path, "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"gh CLI 未正确配置，请运行: echo $GH_TOKEN | gh auth login --with-token"
                )
            logger.info("gh CLI 已正确配置")
        except FileNotFoundError:
            raise RuntimeError(f"gh CLI 未找到，请安装: brew install gh")
        except subprocess.TimeoutExpired:
            raise RuntimeError("gh CLI 验证超时")

    def search_issues(
        self,
        repo: str,
        search_query: str,
        limit: int = 50
    ) -> List[Issue]:
        """
        搜索 Issue

        Args:
            repo: 仓库（如 "opensourceways/backlog"）
            search_query: 搜索条件（如 "forum-reply-robot state:closed"）
            limit: 返回数量限制

        Returns:
            List[Issue]: Issue 列表
        """
        cmd = [
            self.cli_path, "issue", "list",
            "--repo", repo,
            "--search", f"{search_query} sort:created-desc",
            "--limit", str(limit),
            "--json", "number,title,state,labels,createdAt,closedAt"
        ]

        result = self._run_command(cmd)
        issues_data = json.loads(result)

        return [
            Issue(
                number=item["number"],
                title=item["title"],
                state=item["state"],
                labels=[label["name"] for label in item.get("labels", [])],
                created_at=item["createdAt"],
                closed_at=item.get("closedAt"),
                body="",  # 需要单独获取
                comments=[]  # 需要单独获取
            )
            for item in issues_data
        ]

    def get_issue(self, repo: str, issue_number: int) -> Issue:
        """
        获取 Issue 详情

        Args:
            repo: 仓库
            issue_number: Issue 编号

        Returns:
            Issue: Issue 对象（包含 body 和 comments）
        """
        cmd = [
            self.cli_path, "issue", "view", str(issue_number),
            "--repo", repo,
            "--json", "number,title,state,labels,createdAt,closedAt,body,comments"
        ]

        result = self._run_command(cmd)
        data = json.loads(result)

        return Issue(
            number=data["number"],
            title=data["title"],
            state=data["state"],
            labels=[label["name"] for label in data.get("labels", [])],
            created_at=data["createdAt"],
            closed_at=data.get("closedAt"),
            body=data.get("body", ""),
            comments=data.get("comments", [])
        )

    def get_pull_request(self, repo: str, pr_number: int) -> PullRequest:
        """
        获取 PR 详情

        Args:
            repo: 仓库
            pr_number: PR 编号

        Returns:
            PullRequest: PR 对象
        """
        # 1. 获取基本信息
        cmd = [
            self.cli_path, "pr", "view", str(pr_number),
            "--repo", repo,
            "--json", "number,title,state,headRefName"
        ]

        result = self._run_command(cmd)
        data = json.loads(result)

        # 2. 通过 GitHub API 获取包含 patch 的文件列表
        api_cmd = [
            self.cli_path, "api",
            f"repos/{repo}/pulls/{pr_number}/files",
            "--paginate"
        ]

        try:
            api_result = self._run_command(api_cmd)
            files_with_patch = json.loads(api_result)
        except Exception as e:
            logger.warning(f"获取 PR files 失败: {e}，使用空列表")
            files_with_patch = []

        return PullRequest(
            number=data["number"],
            title=data["title"],
            state=data["state"],
            head_ref=data["headRefName"],
            files=files_with_patch
        )

    def get_pr_diff(self, repo: str, pr_number: int) -> str:
        """
        获取 PR 的代码 diff

        Args:
            repo: 仓库
            pr_number: PR 编号

        Returns:
            str: diff 内容
        """
        cmd = [
            self.cli_path, "pr", "diff", str(pr_number),
            "--repo", repo
        ]

        return self._run_command(cmd)

    def get_file_content(
        self,
        repo: str,
        file_path: str,
        ref: Optional[str] = None
    ) -> str:
        """
        获取文件内容

        Args:
            repo: 仓库
            file_path: 文件路径
            ref: 分支/tag/commit（可选，默认主分支）

        Returns:
            str: 文件内容
        """
        # 构建 API URL
        url = f"repos/{repo}/contents/{file_path}"
        if ref:
            url += f"?ref={ref}"

        cmd = [
            self.cli_path, "api", url,
            "--jq", ".content"
        ]

        # 获取 base64 编码的内容
        base64_content = self._run_command(cmd).strip().strip('"')

        # 解码
        return base64.b64decode(base64_content).decode('utf-8')

    def _run_command(self, cmd: List[str], timeout: int = 60) -> str:
        """
        运行 gh CLI 命令

        Args:
            cmd: 命令列表
            timeout: 超时时间（秒）

        Returns:
            str: 命令输出

        Raises:
            RuntimeError: 命令执行失败
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"gh CLI 命令失败: {' '.join(cmd)}\n"
                    f"错误: {result.stderr}"
                )

            return result.stdout

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"gh CLI 命令超时: {' '.join(cmd)}")
        except Exception as e:
            raise RuntimeError(f"gh CLI 命令异常: {e}")
