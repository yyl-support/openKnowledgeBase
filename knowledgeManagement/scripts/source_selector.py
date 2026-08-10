"""
源文件选择器
从代码仓中选择一批具有代表性的源文件，用于喂给 MKAdapter 做知识提取，
避免把仓库中全部文件（尤其是海量 YAML）都上传导致 ingest 耗时过长。

选择规则：
1. 全部 .md 文件
2. 全部 .py / .sh 文件
3. YAML 抽样：按文件所在目录的「前 group_depth 级路径」分组，每组随机抽样
   yaml_sample_per_group 个（默认 2）。
   （注：曾评估过"每个含 YAML 的目录抽 2 个"的方案，在目标仓库
   ascend-ci-deployment 上实测得到 539 个目录 × 2 = 1067 个文件，
   相对 2104 个 YAML 总数几乎没有起到筛选作用，故改为按前两级路径分组，
   该仓库实测可收敛到 75 组 / 148 个抽样文件，筛选效果符合预期。）
4. 额外生成 1 份合成的目录清单 .md 文件（目录树 + 各目录文件统计 + Helm Chart 清单），
   弥补 YAML 抽样丢失的目录全貌信息。

输出的所有文件名都以 .md 或 .txt 结尾（方便直接喂给 MK 的 raw/write，
其内容会被当作文档处理）。非 .md/.txt 的原始文件（.py/.sh/.yaml/.yml）会：
- 生成一个「转义后的扁平文件名」（原始相对路径中的 / 替换为 __，末尾追加 .md）
- 内容用带语言标记的代码块包裹，并在开头注明原始路径

超过大小阈值（低于 MK 单文件 512KB 硬限制，留出扁平化/代码块包裹的余量）的文件会被截断，
保留头部内容并注明截断行数/字节数。
"""
import logging
import os
import random
from typing import Dict, List, Optional, Tuple

import yaml


logger = logging.getLogger(__name__)


# 扫描时跳过的目录（与其他 adapter 保持一致的忽略列表，外加知识提取工具自身的产物目录）
DEFAULT_IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".ua", ".understand-anything", ".open-zread",
}

# MK /raw/write 的单文件硬限制（见 routes/wiki.ts MAX_FILE_SIZE）
MK_MAX_FILE_SIZE = 512 * 1024

# 本模块的截断阈值：明显低于 MK 硬限制，为扁平化文件名/代码块包裹/清单表格等
# 附加开销留出余量
TRUNCATION_THRESHOLD = 400 * 1024


def select_sources(
    repo_path: str,
    *,
    seed: int = 42,
    yaml_sample_per_group: int = 2,
    group_depth: int = 2,
) -> List[Dict[str, str]]:
    """
    从代码仓中选择一批代表性源文件

    Args:
        repo_path: 代码仓本地路径
        seed: 随机抽样种子，保证同一个仓库每次运行结果一致
        yaml_sample_per_group: 每个 YAML 分组抽样的文件数（默认 2）
        group_depth: YAML 分组时取目录路径的前几级作为分组键（默认 2）

    Returns:
        [{"filename": str, "content": str}, ...]，filename 均以 .md/.txt 结尾
    """
    if not os.path.isdir(repo_path):
        raise ValueError(f"仓库路径不存在或不是目录: {repo_path}")

    md_files: List[str] = []
    py_sh_files: List[str] = []
    yaml_groups: Dict[str, List[str]] = {}
    all_files: List[str] = []
    helm_charts: List[str] = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = sorted(d for d in dirs if d not in DEFAULT_IGNORE_DIRS)
        for fname in sorted(files):
            abspath = os.path.join(root, fname)
            relpath = os.path.relpath(abspath, repo_path).replace(os.sep, "/")
            all_files.append(relpath)
            lower = fname.lower()

            if lower.endswith(".md"):
                md_files.append(relpath)
            elif lower.endswith(".py") or lower.endswith(".sh"):
                py_sh_files.append(relpath)
            elif lower.endswith(".yaml") or lower.endswith(".yml"):
                dirname = os.path.dirname(relpath)
                parts = [p for p in dirname.split("/") if p]
                key = "/".join(parts[:group_depth])
                yaml_groups.setdefault(key, []).append(relpath)
                if fname == "Chart.yaml":
                    helm_charts.append(relpath)

    md_files.sort()
    py_sh_files.sort()

    total_yaml = sum(len(v) for v in yaml_groups.values())
    logger.info(
        "source_selector: 扫描完成 md=%d py+sh=%d yaml总数=%d yaml分组数=%d（分组深度=%d）",
        len(md_files), len(py_sh_files), total_yaml, len(yaml_groups), group_depth,
    )

    sampled_yaml = _sample_yaml_groups(yaml_groups, yaml_sample_per_group, seed)

    sources: List[Dict[str, str]] = []
    total_bytes = 0

    for relpath in md_files:
        content = _read_text(os.path.join(repo_path, relpath))
        if content is None:
            continue
        content = _truncate_if_needed(content)
        sources.append({"filename": _escape_path_to_filename(relpath), "content": content})
        total_bytes += len(content.encode("utf-8"))

    for relpath in py_sh_files:
        content = _read_text(os.path.join(repo_path, relpath))
        if content is None:
            continue
        content = _truncate_if_needed(content)
        lang = "python" if relpath.lower().endswith(".py") else "bash"
        wrapped = _wrap_non_md(relpath, content, lang)
        sources.append({"filename": _escape_path_to_filename(relpath), "content": wrapped})
        total_bytes += len(wrapped.encode("utf-8"))

    for relpath in sampled_yaml:
        content = _read_text(os.path.join(repo_path, relpath))
        if content is None:
            continue
        content = _truncate_if_needed(content)
        wrapped = _wrap_non_md(relpath, content, "yaml")
        sources.append({"filename": _escape_path_to_filename(relpath), "content": wrapped})
        total_bytes += len(wrapped.encode("utf-8"))

    manifest_content = _build_directory_manifest(
        repo_path, all_files, yaml_groups, sampled_yaml, helm_charts, group_depth
    )
    sources.append({"filename": "_directory-manifest.md", "content": manifest_content})
    total_bytes += len(manifest_content.encode("utf-8"))

    logger.info(
        "source_selector: 完成选择 md=%d py+sh=%d yaml抽样=%d（共%d组，总数%d）"
        " +1份目录清单 => 总源文件=%d 总字节=%d",
        len(md_files), len(py_sh_files), len(sampled_yaml), len(yaml_groups), total_yaml,
        len(sources), total_bytes,
    )

    return sources


def _sample_yaml_groups(
    yaml_groups: Dict[str, List[str]], yaml_sample_per_group: int, seed: int
) -> List[str]:
    """
    对每个分组做可复现的随机抽样：固定 seed，候选列表先排序后再抽样。
    按分组键排序遍历，保证多次运行时抽样序列完全一致。
    """
    rng = random.Random(seed)
    sampled: List[str] = []
    for key in sorted(yaml_groups.keys()):
        candidates = sorted(yaml_groups[key])
        if len(candidates) <= yaml_sample_per_group:
            sampled.extend(candidates)
        else:
            sampled.extend(rng.sample(candidates, yaml_sample_per_group))
    return sorted(sampled)


def _read_text(abspath: str) -> Optional[str]:
    """读取文本文件，失败时记录 warning 并返回 None（不中断整体流程）。"""
    try:
        with open(abspath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError as e:
        logger.warning("source_selector: 读取文件失败 %s: %s", abspath, e)
        return None


def _truncate_if_needed(content: str, threshold: int = TRUNCATION_THRESHOLD) -> str:
    """超过阈值时保留头部内容并截断，注明省略的字节数/行数。"""
    encoded = content.encode("utf-8")
    if len(encoded) <= threshold:
        return content

    truncated_text = encoded[:threshold].decode("utf-8", errors="ignore")
    total_lines = content.count("\n") + 1
    kept_lines = truncated_text.count("\n") + 1
    cut_lines = total_lines - kept_lines
    note = (
        f"\n\n... [内容过大已截断：保留前 {len(truncated_text.encode('utf-8'))} 字节，"
        f"省略约 {cut_lines} 行，原始大小 {len(encoded)} 字节] ...\n"
    )
    return truncated_text + note


def _wrap_non_md(relpath: str, content: str, lang: str) -> str:
    """将非 md/txt 原始文件的内容包裹成带语言标记的代码块，并在开头注明原始路径。"""
    return f"原始路径：`{relpath}`\n\n```{lang}\n{content}\n```\n"


def _escape_path_to_filename(relpath: str) -> str:
    """把原始相对路径转义为扁平文件名。

    必须扁平：MK 的 /wiki/raw/write 不会创建中间目录，filename 带 `/` 会直接
    ENOENT。已是 .md 的不再追加后缀，避免 `x.md.md`。
    """
    escaped = relpath.replace("/", "__")
    return escaped if escaped.endswith((".md", ".txt")) else f"{escaped}.md"


def _compute_dir_stats(all_files: List[str]) -> Dict[str, Dict[str, int]]:
    """按所在目录统计文件数量（总数 / yaml / md / py+sh / 其他）。"""
    stats: Dict[str, Dict[str, int]] = {}
    for relpath in all_files:
        dirname = os.path.dirname(relpath)
        s = stats.setdefault(dirname, {"total": 0, "yaml": 0, "md": 0, "py_sh": 0, "other": 0})
        s["total"] += 1
        lower = relpath.lower()
        if lower.endswith((".yaml", ".yml")):
            s["yaml"] += 1
        elif lower.endswith(".md"):
            s["md"] += 1
        elif lower.endswith((".py", ".sh")):
            s["py_sh"] += 1
        else:
            s["other"] += 1
    return stats


def _render_dir_tree(repo_path: str, max_depth: int = 4, max_lines: int = 400) -> List[str]:
    """渲染仅含目录（不含文件）的简易缩进树，限制深度和总行数避免清单过大。"""
    root_name = os.path.basename(repo_path.rstrip("/")) or repo_path
    lines: List[str] = [f"{root_name}/"]

    def walk(dir_path: str, depth: int) -> None:
        if depth > max_depth or len(lines) >= max_lines:
            return
        try:
            entries = sorted(os.listdir(dir_path))
        except OSError:
            return
        for entry in entries:
            if entry in DEFAULT_IGNORE_DIRS:
                continue
            full = os.path.join(dir_path, entry)
            if os.path.isdir(full):
                if len(lines) >= max_lines:
                    lines.append("... [已达显示上限，剩余目录省略]")
                    return
                lines.append("  " * depth + entry + "/")
                walk(full, depth + 1)

    walk(repo_path, 1)
    return lines


def _read_chart_meta(chart_path: str) -> Tuple[str, str]:
    """读取 Helm Chart.yaml 的 name/version 字段，读取失败时返回 "?"。"""
    try:
        with open(chart_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return str(data.get("name", "?")), str(data.get("version", "?"))
    except Exception:
        return "?", "?"


def _build_directory_manifest(
    repo_path: str,
    all_files: List[str],
    yaml_groups: Dict[str, List[str]],
    sampled_yaml: List[str],
    helm_charts: List[str],
    group_depth: int,
) -> str:
    """生成合成的目录清单文档：目录树 + 各目录文件统计 + Helm Chart 清单。"""
    repo_name = os.path.basename(repo_path.rstrip("/")) or repo_path
    sampled_set = set(sampled_yaml)
    lines: List[str] = []

    lines.append(f"# 目录结构清单：{repo_name}")
    lines.append("")
    lines.append(
        "本文件由 source_selector 自动生成，用于在采样式源文件提取中保留仓库的整体目录结构信息，"
        "弥补 YAML 抽样导致的目录全貌丢失。"
    )
    lines.append("")

    lines.append("## 目录树")
    lines.append("")
    lines.append("```")
    lines.extend(_render_dir_tree(repo_path))
    lines.append("```")
    lines.append("")

    lines.append("## 各目录文件统计（按文件总数排序，Top 50）")
    lines.append("")
    lines.append("| 目录 | 文件总数 | .yaml/.yml | .md | .py/.sh | 其他 |")
    lines.append("|---|---|---|---|---|---|")
    stats = _compute_dir_stats(all_files)
    for dirname, s in sorted(stats.items(), key=lambda kv: -kv[1]["total"])[:50]:
        lines.append(
            f"| {dirname or '.'} | {s['total']} | {s['yaml']} | {s['md']} | {s['py_sh']} | {s['other']} |"
        )
    lines.append("")

    total_yaml = sum(len(v) for v in yaml_groups.values())
    lines.append(f"## YAML 分组抽样情况（分组深度={group_depth}）")
    lines.append("")
    lines.append(f"- YAML 文件总数：{total_yaml}")
    lines.append(f"- 分组数：{len(yaml_groups)}")
    lines.append(f"- 抽样文件数：{len(sampled_yaml)}")
    lines.append("")
    lines.append("| 分组 | 组内文件数 | 抽样数 |")
    lines.append("|---|---|---|")
    for key in sorted(yaml_groups.keys()):
        candidates = yaml_groups[key]
        sampled_count = sum(1 for f in candidates if f in sampled_set)
        lines.append(f"| {key or '.'} | {len(candidates)} | {sampled_count} |")
    lines.append("")

    lines.append("## Helm Chart 清单")
    lines.append("")
    if helm_charts:
        lines.append("| Chart.yaml 路径 | name | version |")
        lines.append("|---|---|---|")
        for chart_path in sorted(helm_charts):
            name, version = _read_chart_meta(os.path.join(repo_path, chart_path))
            lines.append(f"| {chart_path} | {name} | {version} |")
    else:
        lines.append("（未发现 Chart.yaml）")
    lines.append("")

    return "\n".join(lines)
