"""
Refiner 二次提炼层
使用大模型对提取的知识进行二次提炼，生成特定类型的文档
"""
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

import sys as _sys

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS_DIR not in _sys.path:
    _sys.path.insert(0, _SCRIPTS_DIR)

from constraints import ALL_DISCIPLINES


logger = logging.getLogger(__name__)


class OverflowError_(RuntimeError):
    """输入超出单次调用容量。不静默截断，抛给上层做决策。"""


class Refiner:
    """知识二次提炼器"""

    # 强约束的唯一来源是 constraints.py，此处不再复制一份，避免两处漂移
    HARD_CONSTRAINTS = ALL_DISCIPLINES

    # 章节契约：四层流水线的 Layer 4 直接取用这里的定义，保证 subagent 路径与
    # 直连 API 路径（extract.py）用的是同一套章节要求
    SECTION_CONTRACTS = {
        "architecture": """1. **项目定位**：项目是什么，解决什么问题，核心价值主张
2. **架构设计**：核心模块划分、依赖关系、数据流
3. **关键机制**：值得关注的设计模式、技术选型、核心算法
4. **目录结构**：重要文件/目录的作用

格式要求（不是章节）：
- 使用 Mermaid 流程图（flowchart TD）展示架构，禁止 ASCII 框线字符（┌─┐│等）
- 引用来源时给出具体的文件路径

以上 1-4 为文档的全部章节。不要输出第 5 个及以后的章节。""",

        "quickstart": """1. **安装步骤**：依赖安装、环境配置
2. **配置说明**：必需的配置项、环境变量
3. **运行方法**：如何启动服务/运行程序
4. **验证方法**：如何确认成功运行
5. **常见问题**：新手容易遇到的问题及解决方案

格式要求（不是章节）：
- 步骤清晰，命令可复制粘贴执行
- 引用来源时给出具体的文件路径

以上 1-5 为文档的全部章节。不要输出第 6 个及以后的章节。""",

        "api-reference": """1. **API 概览**：提供的接口类型（REST API / SDK / CLI 等）
2. **认证方式**：如何认证、Token 管理
3. **接口列表**：每个接口的方法、路径、参数、返回值、示例
4. **错误码**：常见错误及处理方法
5. **SDK 使用示例**（如果是库项目）

格式要求（不是章节）：
- 格式规范，易于查阅
- 引用来源时给出具体的文件路径

以上 1-5 为文档的全部章节。不要输出第 6 个及以后的章节。
若项目确实不提供 API，仍按章节格式输出，在各节写明「该项目不提供此类接口」。""",

        # 以下三类构成新员工上手的标准文档集，替代单篇 onboarding。
        # 拆分原因：单篇把定位、技术栈、规范、风险全塞在一起，信息量大但杂糅，
        # 读者找不到自己要的那部分。
        "overview": """1. **职责**：这个项目负责什么，一句话说清；再用一段说明它解决的问题
2. **定位**：它在更大的系统里处于哪一环，上游是谁、下游是谁
3. **边界**：明确不属于它的职责。哪些事看起来相关但由别的系统负责
4. **核心能力**：它对外提供的能力清单，用表格列出「能力 → 承载模块」

格式要求（不是章节）：
- 全文控制在 150 行以内。这是给人第一次了解项目用的，不是参考手册
- 能力清单用表格
- 不写安装步骤、不写配置项、不写代码规范，那些在别的文档里

以上 1-4 为文档的全部章节。不要输出第 5 个及以后的章节。""",

        "techstack": """1. **语言与运行时**：用了哪些语言，各自负责什么部分；运行时版本要求
2. **构建与依赖**：构建工具、包管理、关键依赖及其版本。版本号必须逐字来自输入，
   查不到就写「输入中未提供，需查阅源码确认」
3. **整体架构**：模块划分与依赖关系，用 Mermaid flowchart TD 表达
4. **调用链**：从入口到产出的主链路，每一步落到具体文件。用 Mermaid flowchart TD 表达，
   并在图后用编号列表逐步说明，每步一到两句
5. **运行载体**：代码实际跑在什么之上——机型/节点规格/容器镜像/实例类型。必须穷举
   全部类型并给出各自数量，不能只举一例。若项目无此维度（如纯库项目），写「不适用」
6. **调度与编排**：任务如何被分派到运行载体上——调度器、队列、优先级、亲和性。
   同一维度存在多个取值时全部列出并给出分布数量，不要只写占比最高的那个

格式要求（不是章节）：
- 依赖与版本用表格，列为「组件 / 版本 / 声明位置」
- 两张 Mermaid 图各司其职：第 3 节讲静态结构，第 4 节讲动态流程，不要合并
- 第 5、6 节的枚举必须给出实测数量，禁止用「等」「多种」概括
- 禁止 ASCII 框线字符

以上 1-6 为文档的全部章节。不要输出第 7 个及以后的章节。""",

        "standards": """1. **命名规范**：目录、文件、资源、命名空间的命名规则。用表格列出
   「对象 → 规则 → 示例」
2. **安全要求**：认证、权限、密钥管理、访问控制方面的硬性规定
3. **DFX 要求**：可靠性、可维护性、可观测性方面的规定（高可用、监控、日志、
   告警、容量）。输入中没有对应规定的子项，直接写「未见相关规定」，不要编
4. **当前风险点**：已知的不一致、未完成项、与规范冲突的现状。每条给出所在文件路径，
   以及它可能导致的后果

格式要求（不是章节）：
- 前三节用表格，风险点用编号列表（因为每条需要展开后果）
- 规则要可执行：写出精确的命名格式与示例，不要写「命名要规范」这类空话
- 风险点只写有据可查的现状，不做主观评价，不提改进建议

以上 1-4 为文档的全部章节。不要输出第 5 个及以后的章节。""",

        # 新员工上手报告：对应交付标准 b（了解流程+结构+技术栈）与 c（辅助新需求分析）
        "onboarding": """1. **项目定位**：项目是什么，解决什么问题，在更大的系统里处于什么位置
2. **技术栈**：语言、框架、运行时、关键依赖及其版本。版本号必须逐字来自输入，
   查不到就写「输入中未提供，需查阅源码确认」
3. **主流程**：从入口到产出的完整链路，每一步落到具体文件。用 Mermaid flowchart TD 表达
4. **代码结构**：目录与模块划分，各模块职责边界。辅助能力只需一到两句说清作用
5. **项目规则约束**：来自 CLAUDE.md 与配置文件的硬性规定（路径约定、命名规范、
   CI 门禁、依赖版本要求），逐条给出来源文件路径
6. **新需求落点指引**：常见需求类型 → 应该改哪个模块/哪些文件 → 受第 5 节哪些规则约束。
   只写能从输入中推出落点的需求类型，推不出的不要凑

格式要求（不是章节）：
- 架构图与流程图用 Mermaid（flowchart TD），禁止 ASCII 框线字符
- 每条事实性断言给出来源文件路径

以上 1-6 为文档的全部章节。不要输出第 7 个及以后的章节。""",
    }

    ROLES = {
        "architecture": ("资深的软件架构分析师", "项目架构文档"),
        "quickstart": ("技术文档工程师", "快速开始指南"),
        "api-reference": ("API 文档专家", "API 参考文档"),
        "onboarding": ("负责新人上手的技术导师", "新员工上手报告"),
        "overview": ("负责新人上手的技术导师", "项目概述"),
        "techstack": ("资深的软件架构分析师", "技术栈与架构设计说明"),
        "standards": ("负责代码规范与质量的技术专家", "编码规范说明"),
    }

    PROMPT_TEMPLATE = """你是一位{role}。基于以下从代码仓提取的知识页面，生成一份{doc_name}。

## 章节契约
{contract}
{constraints}
输入的知识页面：
{pages_summary}

请生成{doc_name}（Markdown 格式）："""

    # PROMPTS 在类定义后由 _build_prompts() 拼装（类体内的推导式取不到类作用域名字），
    # 保证与 SECTION_CONTRACTS 单一来源
    PROMPTS: Dict[str, str] = {}

    # 单次调用的输入上限（字符）。按 4 字符 ≈ 1 token 粗估，留足输出与系统开销余量。
    # 超限时**不截断**，抛 OverflowError_ 交由上层决策 —— 旧实现的 3000 字符硬截断
    # 曾静默吃掉 MK 产物 29.8% 的内容，且全程无人知晓。
    DEFAULT_INPUT_CHAR_LIMIT = 600_000

    def __init__(self, model: str = "claude-opus-4", base_url: str = None,
                 api_key: str = None, input_char_limit: Optional[int] = None):
        """
        初始化 Refiner

        Args:
            model: 模型名称（claude-opus-4, deepseek-chat 等）
            base_url: API 基础 URL（可选）
            api_key: API 密钥（可选，默认从环境变量读取）
            input_char_limit: 单次调用输入字符上限，超限抛 OverflowError_
        """
        self.model = model
        self.base_url = base_url
        self.input_char_limit = input_char_limit or self.DEFAULT_INPUT_CHAR_LIMIT
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("未提供 API Key，请设置环境变量 ANTHROPIC_API_KEY 或 OPENAI_API_KEY")

        # 根据模型选择客户端
        if "claude" in model.lower():
            self._init_anthropic_client()
        else:
            self._init_openai_client()

    def _init_anthropic_client(self):
        """初始化 Anthropic 客户端"""
        try:
            from anthropic import Anthropic
            # base_url 为空时走 Anthropic 官方地址；配了中转（如 4router）必须透传，
            # 否则请求会打到官方端点，用中转的 key 必然认证失败
            if self.base_url:
                self.client = Anthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                self.client = Anthropic(api_key=self.api_key)
            self.client_type = "anthropic"
            logger.info(f"使用 Anthropic 客户端，模型: {self.model}, base_url: {self.base_url or '官方默认'}")
        except ImportError:
            raise ImportError("请安装 anthropic: pip install anthropic")

    def _init_openai_client(self):
        """初始化 OpenAI 兼容客户端"""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            self.client_type = "openai"
            logger.info(f"使用 OpenAI 客户端，模型: {self.model}, base_url: {self.base_url}")
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

    def refine(self, pages_data: Dict, output_type: str, output_path: str) -> str:
        """
        二次提炼知识

        Args:
            pages_data: adapter 输出的 JSON 数据
            output_type: 输出类型（architecture / quickstart / api-reference）
            output_path: 输出文件路径

        Returns:
            生成的文件路径
        """
        if output_type not in self.PROMPTS:
            raise ValueError(f"不支持的输出类型: {output_type}，支持: {list(self.PROMPTS.keys())}")

        logger.info(f"开始二次提炼，输出类型: {output_type}")

        # 构造页面摘要
        pages_summary = self._build_pages_summary(pages_data)

        # 构造 prompt
        prompt = self.PROMPTS[output_type].format(
            pages_summary=pages_summary,
            constraints=self.HARD_CONSTRAINTS,
        )

        # 调用 LLM
        logger.info(f"调用 {self.model} 生成文档...")
        content = self._call_llm(prompt)

        # 添加元信息头部
        header = self._build_header(pages_data, output_type)
        full_content = header + "\n\n" + content

        # 写入文件
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        logger.info(f"文档生成完成: {output_path}")
        return output_path

    def _build_pages_summary(self, pages_data: Dict) -> str:
        """
        构造页面摘要（供 LLM 阅读）

        Args:
            pages_data: 页面数据

        Returns:
            摘要文本
        """
        pages = pages_data.get("pages", [])
        lines = []

        for i, page in enumerate(pages, 1):
            title = page.get("title", "Untitled")
            content = page.get("content", "")
            path = page.get("path", "")

            lines.append(f"## 页面 {i}: {title}")
            if path:
                lines.append(f"路径: {path}")
            lines.append(f"\n{content}\n")
            lines.append("---\n")

        summary = "\n".join(lines)

        # 不截断。超限即抛，由上层（流水线或用户）决定分批或收窄范围。
        if len(summary) > self.input_char_limit:
            top = sorted(
                pages,
                key=lambda p: len(p.get("content", "")),
                reverse=True,
            )[:10]
            detail = "\n".join(
                f"  - {p.get('path') or p.get('title', '?')}：{len(p.get('content', ''))} 字符"
                for p in top
            )
            raise OverflowError_(
                f"输入超出单次调用上限：{len(summary)} 字符 > 上限 "
                f"{self.input_char_limit}（共 {len(pages)} 个页面）。\n"
                f"已拒绝执行，未做任何截断。请收窄提取范围或分批处理。\n"
                f"最大的 10 个页面：\n{detail}"
            )

        return summary

    def _build_header(self, pages_data: Dict, output_type: str) -> str:
        """
        构造文档头部元信息

        Args:
            pages_data: 页面数据
            output_type: 输出类型

        Returns:
            头部文本
        """
        tool = pages_data.get("tool", "unknown")
        timestamp = pages_data.get("timestamp", "")
        repo = pages_data.get("repo", "")
        page_count = len(pages_data.get("pages", []))

        lines = [
            "---",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"提取工具: {tool}",
            f"原始页面数: {page_count}",
            f"仓库: {repo}",
            f"文档类型: {output_type}",
            "---"
        ]

        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> str:
        """
        调用大模型

        Args:
            prompt: 提示词

        Returns:
            生成的内容
        """
        if self.client_type == "anthropic":
            return self._call_anthropic(prompt)
        else:
            return self._call_openai(prompt)

    def _call_anthropic(self, prompt: str) -> str:
        """调用 Anthropic API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI 兼容 API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=8000
        )
        return response.choices[0].message.content


def _build_prompts() -> None:
    """用章节契约拼出各输出类型的完整 prompt。"""
    for output_type, (role, doc_name) in Refiner.ROLES.items():
        Refiner.PROMPTS[output_type] = (
            Refiner.PROMPT_TEMPLATE
            .replace("{role}", role)
            .replace("{doc_name}", doc_name)
            .replace("{contract}", Refiner.SECTION_CONTRACTS[output_type])
        )


_build_prompts()
