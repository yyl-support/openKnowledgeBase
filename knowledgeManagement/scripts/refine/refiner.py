"""
Refiner 二次提炼层
使用大模型对提取的知识进行二次提炼，生成特定类型的文档
"""
import logging
import os
from typing import Dict, List
from datetime import datetime


logger = logging.getLogger(__name__)


class Refiner:
    """知识二次提炼器"""

    # Prompt 模板
    PROMPTS = {
        "architecture": """你是一位资深的软件架构分析师。基于以下从代码仓提取的知识页面，生成一份清晰、结构化的项目架构文档。

要求：
1. **项目定位**：项目是什么，解决什么问题，核心价值主张
2. **架构设计**：核心模块划分、依赖关系、数据流
3. **关键机制**：值得关注的设计模式、技术选型、核心算法
4. **目录结构**：重要文件/目录的作用
5. 使用 Mermaid 流程图（flowchart TD）展示架构，禁止使用 ASCII 框线字符（┌─┐│等）
6. 引用来源时给出具体的文件路径

输入的知识页面：
{pages_summary}

请生成架构文档（Markdown 格式）：""",

        "quickstart": """你是一位技术文档工程师。基于以下从代码仓提取的知识页面，生成一份快速开始指南。

要求：
1. **安装步骤**：依赖安装、环境配置
2. **配置说明**：必需的配置项、环境变量
3. **运行方法**：如何启动服务/运行程序
4. **验证方法**：如何确认成功运行
5. **常见问题**：新手容易遇到的问题及解决方案
6. 步骤清晰，命令可复制粘贴执行
7. 引用来源时给出具体的文件路径

输入的知识页面：
{pages_summary}

请生成快速开始指南（Markdown 格式）：""",

        "api-reference": """你是一位 API 文档专家。基于以下从代码仓提取的知识页面，生成一份 API 参考文档。

要求：
1. **API 概览**：提供的接口类型（REST API / SDK / CLI 等）
2. **认证方式**：如何认证、Token 管理
3. **接口列表**：每个接口的方法、路径、参数、返回值、示例
4. **错误码**：常见错误及处理方法
5. **SDK 使用示例**（如果是库项目）
6. 格式规范，易于查阅
7. 引用来源时给出具体的文件路径

输入的知识页面：
{pages_summary}

请生成 API 参考文档（Markdown 格式）："""
    }

    def __init__(self, model: str = "claude-opus-4", base_url: str = None, api_key: str = None):
        """
        初始化 Refiner

        Args:
            model: 模型名称（claude-opus-4, deepseek-chat 等）
            base_url: API 基础 URL（可选）
            api_key: API 密钥（可选，默认从环境变量读取）
        """
        self.model = model
        self.base_url = base_url
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
        prompt = self.PROMPTS[output_type].format(pages_summary=pages_summary)

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

            # 限制每个页面的长度，避免超出 token 限制
            if len(content) > 3000:
                content = content[:3000] + "\n...[内容过长已截断]"

            lines.append(f"## 页面 {i}: {title}")
            if path:
                lines.append(f"路径: {path}")
            lines.append(f"\n{content}\n")
            lines.append("---\n")

        return "\n".join(lines)

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
