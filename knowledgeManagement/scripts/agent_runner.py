"""
Subagent 运行器

四层流水线的每一层都由一个独立的 subagent 执行，模型统一 sonnet-5。
每层的职责约束写在 agents/<layer>/CLAUDE.md 中，运行时以 --append-system-prompt
注入 —— 不依赖 CLAUDE.md 自动发现，避免因 cwd 不同而漏掉约束。

全局强约束（constraints.py）追加在层级约束之后，对每一次模型调用生效。
"""
import json
import logging
import os
import re
import subprocess
from typing import Dict, List, Optional

from constraints import build_constraints


logger = logging.getLogger(__name__)

AGENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents")

# 四层统一用 sonnet-5
DEFAULT_MODEL = "claude-sonnet-5"

# 各层允许的工具。预处理/校验层需要实际检索仓库；解读核对层只读 JSON。
LAYER_TOOLS = {
    "preprocess": ["Read", "Grep", "Glob"],
    "extract": ["Read"],
    "verify": ["Read", "Grep", "Glob", "Bash(grep *)", "Bash(rg *)", "Bash(wc *)", "Write"],
    "refine": ["Read", "Write"],
}


class AgentError(RuntimeError):
    """subagent 执行失败或产物不合契约"""


def load_layer_constraints(layer: str) -> str:
    """读取某一层的 CLAUDE.md 职责约束。"""
    path = os.path.join(AGENTS_DIR, layer, "CLAUDE.md")
    if not os.path.isfile(path):
        raise AgentError(f"缺少层级约束文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_system_prompt(layer: str) -> str:
    """层级职责约束 + 全局强约束。"""
    return (
        load_layer_constraints(layer)
        + "\n\n---\n\n# 全局强约束（对本次调用无条件生效）\n"
        + build_constraints()
    )


def run_agent(
    layer: str,
    prompt: str,
    *,
    cwd: str,
    model: str = DEFAULT_MODEL,
    extra_dirs: Optional[List[str]] = None,
    timeout: int = 1800,
) -> str:
    """
    调用一个 subagent，返回其 stdout 文本。

    Args:
        layer: preprocess / extract / verify / refine
        prompt: 本次任务的具体输入
        cwd: subagent 的工作目录（通常是被解读的仓库或输出目录）
        model: 模型名，默认 claude-sonnet-5
        extra_dirs: 额外允许访问的目录
        timeout: 超时秒数

    Raises:
        AgentError: 非零退出、超时、或输出为空
    """
    # prompt 走 stdin，不作为位置参数：--allowedTools 是可变参数，会把紧随其后的
    # prompt 当成工具名吞掉，导致 claude 报「Input must be provided」
    cmd = [
        "claude", "-p",
        "--model", model,
        "--append-system-prompt", build_system_prompt(layer),
        "--permission-mode", "bypassPermissions",
        "--allow-dangerously-skip-permissions",
        "--allowedTools", *LAYER_TOOLS[layer],
    ]
    for d in extra_dirs or []:
        cmd += ["--add-dir", d]

    logger.info("[%s] 启动 subagent，model=%s cwd=%s", layer, model, cwd)
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, input=prompt, capture_output=True, text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AgentError(f"[{layer}] subagent 超时（{timeout}s）")

    if proc.returncode != 0:
        raise AgentError(
            f"[{layer}] subagent 退出码 {proc.returncode}\n"
            f"stderr: {proc.stderr[-2000:]}"
        )

    out = proc.stdout.strip()
    if not out:
        raise AgentError(f"[{layer}] subagent 输出为空")

    logger.info("[%s] subagent 完成，输出 %d 字符", layer, len(out))
    return out


def parse_json_output(layer: str, text: str) -> Dict:
    """
    从 subagent 输出中解析 JSON。

    容忍模型用 ```json 包裹，但不容忍缺字段 —— 缺字段由调用方按契约校验。
    """
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*\n(.*?)\n```", stripped, re.DOTALL)
    if fenced:
        stripped = fenced.group(1).strip()
    else:
        # 取第一个 { 到最后一个 } —— 应对模型在 JSON 前后带了说明文字
        start, end = stripped.find("{"), stripped.rfind("}")
        if start != -1 and end > start:
            stripped = stripped[start:end + 1]

    try:
        return json.loads(stripped)
    except json.JSONDecodeError as e:
        # 尝试修复常见问题：数组元素内字符串值包含未转义的 "
        # 策略：在 ": "..." 模式中，如果 ... 内有未转义的 "，转义它
        # 用占位符法：先替换 \" 为占位符，然后替换剩余的 " 为 \"，最后恢复占位符
        fixed = stripped.replace(r'\"', '\x00ESCAPED_QUOTE\x00')

        # 正则替换：在 JSON 字符串值内部（": " 和 "[\,\}\]] 之间），转义所有 "
        def escape_inner_quotes(match):
            prefix = match.group(1)  # ": "
            content = match.group(2)  # 字符串内容
            suffix = match.group(3)  # " 和后续字符
            # content 内的所有 " 都应该被转义
            content = content.replace('"', '\\"')
            return prefix + content + suffix

        # 匹配模式：": "...<任何非反斜杠转义的内容>..."<,}]等>
        # 简化：匹配 ": " 开头，到下一个 ", 或 "} 或 "], 为止
        fixed = re.sub(
            r'(:\s*")((?:[^"\\]|\\.)*)("[\s\n]*[,\}\]])',
            escape_inner_quotes,
            fixed
        )

        # 恢复已转义的引号
        fixed = fixed.replace('\x00ESCAPED_QUOTE\x00', r'\"')

        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            raise AgentError(
                f"[{layer}] 产物不是合法 JSON: {e}\n原始输出前 1000 字符:\n{text[:1000]}"
            )


def require_keys(layer: str, data: Dict, keys: List[str]) -> None:
    """契约校验：缺任一必需字段即失败，不静默补默认值。"""
    missing = [k for k in keys if k not in data]
    if missing:
        raise AgentError(f"[{layer}] 产物缺少必需字段: {missing}")
