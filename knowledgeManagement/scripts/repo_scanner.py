"""
仓库结构扫描器（预处理层的确定性部分）

清点文件、统计目录、收集 CLAUDE.md 与依赖清单，产出一份结构化清单交给
预处理层 subagent 做分类判断。

分工原则：能用代码数清的事不交给模型 —— 模型数数会错（已核实：三方件对同一集群
数量给出 6 和 27，真实 20）。模型只做「这个文件属于规则还是功能」这类判断。
"""
import logging
import os
from typing import Dict, List

logger = logging.getLogger(__name__)

IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".ua", ".understand-anything", ".open-zread", ".mypy_cache", "dist", "build",
    ".idea", ".vscode", "target", ".next", "coverage",
}

# 约定与规则类文件名（大小写不敏感）
#
# 注意 values.yaml 不在此列。它装的是部署参数，在 GitOps 仓里就是要被解读的功能
# 内容本身，不是项目规则。实测把它算作规则候选的后果：ascend-ci-deployment 的
# 714 个规则候选里 354 个是 values.yaml，逼着预处理层去给部署参数逐个摘「规则断言」，
# 而真正该解读的内容反倒被划到了规则侧。
# Chart.yaml 保留：它声明 chart 的 name/version/dependencies，是货真价实的依赖信息。
RULE_FILENAMES = {
    "claude.md", "agents.md", ".cursorrules", "contributing.md",
    "package.json", "go.mod", "go.sum", "requirements.txt", "pyproject.toml",
    "pom.xml", "build.gradle", "cargo.toml", "chart.yaml",
    "dockerfile", "makefile", ".eslintrc.json", ".eslintrc.js", "tsconfig.json",
    ".pre-commit-config.yaml", "setup.py", "setup.cfg", "tox.ini",
}

RULE_PATH_PREFIXES = (".github/workflows/", ".gitlab-ci", "jenkinsfile", ".circleci/")

# 二进制/生成物后缀，扫描时记录但标记为不可读
BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz",
    ".so", ".dylib", ".dll", ".exe", ".bin", ".jar", ".woff", ".woff2", ".ttf",
    ".lock", ".pyc", ".class",
}


def scan_repo(repo_path: str, *, claude_md_max_bytes: int = 40000) -> Dict:
    """
    扫描仓库，产出结构化清单。

    Args:
        repo_path: 仓库本地路径
        claude_md_max_bytes: 单个 CLAUDE.md 读取上限。超限时**不静默截断**，
            而是在 oversized_rule_files 中记录，由上层决定如何处理。

    Returns:
        {"repo_path", "project_name", "total_files", "files", "dir_stats",
         "claude_md", "rule_candidates", "oversized_rule_files"}
    """
    if not os.path.isdir(repo_path):
        raise ValueError(f"仓库路径不存在或不是目录: {repo_path}")

    files: List[Dict] = []
    claude_md: List[Dict] = []
    rule_candidates: List[str] = []
    oversized: List[Dict] = []

    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)
        for fname in sorted(filenames):
            abspath = os.path.join(root, fname)
            relpath = os.path.relpath(abspath, repo_path).replace(os.sep, "/")
            try:
                size = os.path.getsize(abspath)
            except OSError:
                continue

            ext = os.path.splitext(fname)[1].lower()
            files.append({
                "path": relpath,
                "bytes": size,
                "binary": ext in BINARY_EXTS,
            })

            lower_name = fname.lower()
            lower_rel = relpath.lower()
            is_rule = (
                lower_name in RULE_FILENAMES
                or any(lower_rel.startswith(p) for p in RULE_PATH_PREFIXES)
            )
            if is_rule:
                rule_candidates.append(relpath)

            if lower_name in ("claude.md", "agents.md"):
                if size > claude_md_max_bytes:
                    oversized.append({"path": relpath, "bytes": size,
                                      "limit": claude_md_max_bytes})
                    continue
                try:
                    with open(abspath, "r", encoding="utf-8", errors="replace") as f:
                        claude_md.append({"path": relpath, "content": f.read()})
                except OSError as e:
                    logger.warning("读取失败 %s: %s", relpath, e)

    dir_stats = _dir_stats(files)
    project_name = os.path.basename(repo_path.rstrip("/")) or repo_path

    logger.info(
        "repo_scanner: %s 文件=%d 目录=%d CLAUDE.md=%d 规则候选=%d",
        project_name, len(files), len(dir_stats), len(claude_md), len(rule_candidates),
    )

    return {
        "repo_path": os.path.abspath(repo_path),
        "project_name": project_name,
        "total_files": len(files),
        "files": files,
        "dir_stats": dir_stats,
        "claude_md": claude_md,
        "rule_candidates": sorted(rule_candidates),
        "oversized_rule_files": oversized,
    }


def _dir_stats(files: List[Dict]) -> List[Dict]:
    """按目录统计文件数与总字节数，按文件数降序。"""
    stats: Dict[str, Dict[str, int]] = {}
    for f in files:
        d = os.path.dirname(f["path"]) or "."
        s = stats.setdefault(d, {"files": 0, "bytes": 0})
        s["files"] += 1
        s["bytes"] += f["bytes"]
    return [
        {"dir": d, "files": s["files"], "bytes": s["bytes"]}
        for d, s in sorted(stats.items(), key=lambda kv: -kv[1]["files"])
    ]


def build_manifest_text(scan: Dict, *, dir_top: int = 60) -> str:
    """
    把扫描结果渲染成给 subagent 的文本清单。

    文件列表全量给出（不抽样、不截断）—— 预处理层的分类判断必须基于完整清单，
    抽样会让它对不在样本里的文件无从判断，进而静默漏掉。
    """
    lines = [
        f"# 仓库扫描清单：{scan['project_name']}",
        "",
        f"- 仓库路径：{scan['repo_path']}",
        f"- 文件总数：{scan['total_files']}",
        f"- 目录数：{len(scan['dir_stats'])}",
        "",
        f"## 目录统计（按文件数降序，前 {dir_top}）",
        "",
        "| 目录 | 文件数 | 字节数 |",
        "|---|---|---|",
    ]
    for s in scan["dir_stats"][:dir_top]:
        lines.append(f"| {s['dir']} | {s['files']} | {s['bytes']} |")
    if len(scan["dir_stats"]) > dir_top:
        lines.append(f"\n（另有 {len(scan['dir_stats']) - dir_top} 个目录未列出，"
                     f"完整文件清单见下方）")

    lines += ["", "## 规则候选文件", ""]
    lines += [f"- {p}" for p in scan["rule_candidates"]] or ["（无）"]

    if scan["oversized_rule_files"]:
        lines += ["", "## 超限未读取的约定文件（需用户决策如何处理）", ""]
        for o in scan["oversized_rule_files"]:
            lines.append(f"- {o['path']}：{o['bytes']} 字节，超过上限 {o['limit']}")

    lines += ["", "## CLAUDE.md 全文", ""]
    if scan["claude_md"]:
        for c in scan["claude_md"]:
            lines += [f"### {c['path']}", "", "```markdown", c["content"], "```", ""]
    else:
        lines.append("（仓库内没有 CLAUDE.md / AGENTS.md）")

    lines += ["", "## 全量文件清单", "",
              "| 路径 | 字节数 | 二进制 |", "|---|---|---|"]
    for f in scan["files"]:
        lines.append(f"| {f['path']} | {f['bytes']} | {'是' if f['binary'] else '否'} |")

    return "\n".join(lines)
