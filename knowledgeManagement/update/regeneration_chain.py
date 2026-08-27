"""
SectionRegenerationChain: 章节重新生成链

基于 RAG 检索相关知识，使用 LLM 重新生成受影响的文档章节
"""

import logging
import os
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.callbacks.manager import get_openai_callback

from .vector_store import VectorStore

# 导入 Phase 2 的数据模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from extraction.models import IssueKnowledgePackage
from config.pricing import calc_cost, split_by_currency
import config.env  # noqa: F401  加载 .env，使下方 os.getenv 能读到密钥

logger = logging.getLogger(__name__)

MODEL_NAME = "minimax-m3"


class SectionRegenerationChain:
    """章节重新生成链：基于 RAG 重新生成受影响的文档章节"""

    def __init__(self, project_name: str, pricing: Optional[dict] = None):
        """
        初始化章节生成链

        Args:
            project_name: 项目名称
            pricing: 模型单价表（global.pricing），缺省时成本记 0 并打 warning
        """
        self.project_name = project_name
        self.pricing = pricing
        # 每次 regenerate_section 调用产生的成本记录，供 regenerate_all_affected 汇总
        self.cost_records = []

        # 初始化向量存储
        self.vector_store = VectorStore(project_name)

        # 初始化 LLM（火山 ARK MiniMax M3）
        ark_api_key = os.getenv("ARK_API_KEY")
        if not ark_api_key:
            logger.warning(
                "ARK_API_KEY 环境变量未设置，章节生成功能将不可用"
            )
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model=MODEL_NAME,
                openai_api_key=ark_api_key,
                openai_api_base="https://ark.cn-beijing.volces.com/api/coding/v3",
                temperature=0.3  # 适中温度，保持生成质量和一致性
            )

        logger.info(f"章节生成链初始化完成: {project_name}")

    def identify_affected_sections(
        self,
        knowledge_package: IssueKnowledgePackage
    ) -> List[Dict[str, str]]:
        """
        识别受影响的文档章节

        Args:
            knowledge_package: Issue 知识包

        Returns:
            List[Dict[str, str]]: 受影响的章节列表
                [
                    {
                        "document": "overview.md",
                        "section": "核心流程",
                        "reason": "main.py 文件变更"
                    },
                    ...
                ]
        """
        logger.info(
            f"识别 Issue #{knowledge_package.issue_number} 受影响的章节"
        )

        affected_sections = []

        # 如果没有代码变更，返回空列表
        if not knowledge_package.code_change:
            logger.info("没有代码变更，无受影响章节")
            return affected_sections

        # 获取变更的文件列表
        changed_files = [
            f.get("path") or f.get("filename", "")
            for f in knowledge_package.code_change.files
        ]

        logger.info(f"变更文件: {changed_files}")

        # 映射规则：文件 -> 文档章节
        for file_path in changed_files:
            # 规则 1: 主程序文件 -> overview.md 的核心流程
            if "main.py" in file_path or "app.py" in file_path:
                affected_sections.append({
                    "document": "overview.md",
                    "section": "核心流程",
                    "reason": f"{file_path} 变更"
                })

            # 规则 2: requirements.txt -> techstack.md 的依赖管理
            if "requirements.txt" in file_path or "pyproject.toml" in file_path:
                affected_sections.append({
                    "document": "techstack.md",
                    "section": "依赖管理",
                    "reason": f"{file_path} 变更"
                })

            # 规则 3: .github/workflows/ -> standards.md 的 CI/CD
            if ".github/workflows" in file_path:
                affected_sections.append({
                    "document": "standards.md",
                    "section": "CI/CD",
                    "reason": f"{file_path} 变更"
                })

            # 规则 4: Dockerfile -> techstack.md 的容器化
            if "Dockerfile" in file_path or "docker-compose" in file_path:
                affected_sections.append({
                    "document": "techstack.md",
                    "section": "容器化",
                    "reason": f"{file_path} 变更"
                })

            # 规则 5: 配置文件 -> techstack.md 的配置管理
            if "config" in file_path.lower() or file_path.endswith(('.yaml', '.yml', '.toml', '.ini')):
                affected_sections.append({
                    "document": "techstack.md",
                    "section": "配置管理",
                    "reason": f"{file_path} 变更"
                })

            # 规则 6: 测试文件 -> standards.md 的测试规范
            if "test" in file_path.lower():
                affected_sections.append({
                    "document": "standards.md",
                    "section": "测试规范",
                    "reason": f"{file_path} 变更"
                })

        # 去重
        unique_sections = []
        seen = set()
        for section in affected_sections:
            key = (section["document"], section["section"])
            if key not in seen:
                seen.add(key)
                unique_sections.append(section)

        logger.info(f"识别到 {len(unique_sections)} 个受影响的章节")
        for section in unique_sections:
            logger.info(
                f"  - {section['document']} / {section['section']} "
                f"({section['reason']})"
            )

        return unique_sections

    def regenerate_section(
        self,
        document_name: str,
        section_name: str,
        knowledge_package: IssueKnowledgePackage,
        current_content: Optional[str] = None
    ) -> Optional[str]:
        """
        重新生成文档章节

        Args:
            document_name: 文档名称（如 "overview.md"）
            section_name: 章节名称（如 "核心流程"）
            knowledge_package: Issue 知识包
            current_content: 当前章节内容（可选）

        Returns:
            Optional[str]: 新生成的章节内容
        """
        logger.info(f"重新生成章节: {document_name} / {section_name}")

        if not self.llm:
            logger.error("LLM 不可用，无法生成章节")
            return None

        try:
            # 1. 从向量库检索相关知识
            query = f"{section_name} {document_name}"
            if knowledge_package.code_change:
                # 添加变更文件作为上下文
                changed_files = [
                    f.get("path") or f.get("filename", "")
                    for f in knowledge_package.code_change.files
                ]
                query += " " + " ".join(changed_files)

            retrieved_docs = self.vector_store.similarity_search(
                query,
                k=5
            )

            # 构建检索到的上下文
            retrieved_context = "\n\n---\n\n".join([
                f"**来源**: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
                for doc in retrieved_docs
            ])

            # 2. 构建 Prompt
            prompt_template = """你是一个技术文档生成专家，需要根据最新的代码变更和相关知识，重新生成文档的特定章节。

**文档**: {document_name}
**章节**: {section_name}

**Issue 信息**:
- Issue #{issue_number}: {issue_title}
- 变更文件数: {changed_files_count}

**从向量库检索到的相关知识**:
{retrieved_context}

**当前章节内容** (如果存在):
{current_content}

**要求**:
1. 基于检索到的知识和 Issue 变更，更新章节内容
2. 保持原有的文档风格和结构
3. 只更新与变更相关的部分，保留不变的内容
4. 使用 Markdown 格式
5. 内容要专业、准确、易懂

请生成新的章节内容："""

            prompt = PromptTemplate(
                input_variables=[
                    "document_name",
                    "section_name",
                    "issue_number",
                    "issue_title",
                    "changed_files_count",
                    "retrieved_context",
                    "current_content"
                ],
                template=prompt_template
            )

            # 3. 调用 LLM 生成
            input_data = {
                "document_name": document_name,
                "section_name": section_name,
                "issue_number": knowledge_package.issue_number,
                "issue_title": knowledge_package.issue_title,
                "changed_files_count": knowledge_package.get_changed_files_count(),
                "retrieved_context": retrieved_context or "（无相关知识）",
                "current_content": current_content or "（章节不存在，需要新建）"
            }

            from langchain.chains import LLMChain
            chain = LLMChain(llm=self.llm, prompt=prompt)

            # 用 callback 取真实 token 数
            with get_openai_callback() as cb:
                new_content = chain.run(**input_data)
                prompt_tokens = cb.prompt_tokens
                completion_tokens = cb.completion_tokens

            cost = calc_cost(
                MODEL_NAME,
                prompt_tokens,
                completion_tokens,
                self.pricing
            )
            self.cost_records.append(cost)

            logger.info(
                f"章节生成成功: {len(new_content)} 字符, "
                f"token 输入={cost['prompt_tokens']} 输出={cost['completion_tokens']}, "
                f"金额={cost['cost']:.6f} {cost['currency']}"
                f"{'' if cost['priced'] else '（无定价配置，记 0）'}"
            )

            return new_content

        except Exception as e:
            logger.error(f"章节生成失败: {e}")
            return None

    def regenerate_all_affected(
        self,
        knowledge_package: IssueKnowledgePackage,
        knowledge_base_dir: str
    ) -> Dict[str, Any]:
        """
        重新生成所有受影响的章节

        Args:
            knowledge_package: Issue 知识包
            knowledge_base_dir: 知识库目录

        Returns:
            Dict[str, Any]: 生成结果
        """
        logger.info("开始重新生成所有受影响的章节")

        # 每次批量调用独立统计成本，避免跨调用累加
        self.cost_records = []

        result = {
            "sections_regenerated": 0,
            "sections_failed": 0,
            "sections_skipped": [],
            "updated_documents": [],
            "success": True,
            "error": None,
            "cost_usd": 0.0,
            "cost_cny": 0.0,
            "total_tokens": 0
        }

        try:
            # 1. 识别受影响的章节
            affected_sections = self.identify_affected_sections(
                knowledge_package
            )

            if not affected_sections:
                logger.info("没有受影响的章节，跳过重新生成")
                self._fill_cost(result)
                return result

            # 2. 逐个重新生成
            for section_info in affected_sections:
                document_name = section_info["document"]
                section_name = section_info["section"]

                doc_path = os.path.join(knowledge_base_dir, document_name)

                # 文档不存在：明确记录跳过原因，不静默忽略
                if not os.path.exists(doc_path):
                    logger.warning(f"文档不存在，跳过: {doc_path}")
                    result["sections_skipped"].append({
                        "document": document_name,
                        "section": section_name,
                        "reason": "document_not_found"
                    })
                    continue

                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        full_content = f.read()
                except Exception as e:
                    logger.warning(f"读取文档失败 {doc_path}: {e}")
                    result["sections_skipped"].append({
                        "document": document_name,
                        "section": section_name,
                        "reason": f"read_failed: {e}"
                    })
                    continue

                current_content = self._extract_section(
                    full_content,
                    section_name
                )

                # 章节不存在：明确记录跳过原因，不静默忽略
                if current_content is None:
                    logger.warning(
                        f"章节不存在，跳过: {document_name} / {section_name}"
                    )
                    result["sections_skipped"].append({
                        "document": document_name,
                        "section": section_name,
                        "reason": "section_not_found"
                    })
                    continue

                # 重新生成章节
                new_content = self.regenerate_section(
                    document_name,
                    section_name,
                    knowledge_package,
                    current_content
                )

                if not new_content:
                    logger.warning(f"章节生成失败: {document_name} / {section_name}")
                    result["sections_failed"] += 1
                    continue

                # 将新内容写回文档，只有写回成功才计入 regenerated
                if self._write_section(doc_path, full_content, section_name, new_content):
                    logger.info(f"章节写回成功: {document_name} / {section_name}")
                    result["sections_regenerated"] += 1

                    if document_name not in result["updated_documents"]:
                        result["updated_documents"].append(document_name)
                else:
                    logger.warning(f"章节写回失败: {document_name} / {section_name}")
                    result["sections_failed"] += 1

            self._fill_cost(result)

            logger.info(
                f"章节重新生成完成: "
                f"成功={result['sections_regenerated']}, "
                f"失败={result['sections_failed']}, "
                f"跳过={len(result['sections_skipped'])}, "
                f"成本=${result['cost_usd']:.6f} / ¥{result['cost_cny']:.6f}, "
                f"token={result['total_tokens']}"
            )

            return result

        except Exception as e:
            logger.error(f"批量重新生成失败: {e}")
            result["success"] = False
            result["error"] = str(e)
            self._fill_cost(result)
            return result

    def _fill_cost(self, result: Dict[str, Any]):
        """把本次累积的成本记录按币种汇总写入 result（不做汇率折算）"""
        totals = split_by_currency(self.cost_records)
        result["cost_usd"] = totals["cost_usd"]
        result["cost_cny"] = totals["cost_cny"]
        result["total_tokens"] = sum(
            r.get("total_tokens", 0) for r in self.cost_records
        )

    def _extract_section(
        self,
        content: str,
        section_name: str
    ) -> Optional[str]:
        """
        从文档中提取指定章节的内容

        Args:
            content: 完整文档内容
            section_name: 章节名称

        Returns:
            Optional[str]: 章节内容
        """
        # 简单实现：查找 ## section_name 到下一个 ## 之间的内容
        import re

        pattern = rf"##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()

        return None

    def _replace_section(
        self,
        content: str,
        section_name: str,
        new_section_content: str
    ) -> Optional[str]:
        """
        用新内容替换文档中指定章节的正文（与 _extract_section 对称）

        Args:
            content: 完整文档内容
            section_name: 章节名称
            new_section_content: 新的章节正文

        Returns:
            Optional[str]: 替换后的完整文档内容；章节不存在返回 None
        """
        import re

        # 与 _extract_section 相同的定位规则，但保留 ## 标题行本身
        pattern = rf"(##\s+{re.escape(section_name)}\s*\n)(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return None

        # 用 lambda 做替换，避免新内容中的反斜杠被当作转义序列解释
        body = new_section_content.strip() + "\n"
        return content[:match.start(2)] + body + content[match.end(2):]

    def _write_section(
        self,
        doc_path: str,
        full_content: str,
        section_name: str,
        new_section_content: str
    ) -> bool:
        """
        将新章节内容写回文档文件

        Args:
            doc_path: 文档路径
            full_content: 当前完整文档内容
            section_name: 章节名称
            new_section_content: 新的章节正文

        Returns:
            bool: 写回是否成功
        """
        updated = self._replace_section(
            full_content,
            section_name,
            new_section_content
        )

        if updated is None:
            logger.warning(f"章节定位失败，无法写回: {doc_path} / {section_name}")
            return False

        try:
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(updated)
            return True
        except Exception as e:
            logger.error(f"写回文档失败 {doc_path}: {e}")
            return False
