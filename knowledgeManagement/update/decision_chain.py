"""
UpdateDecisionChain: 更新决策链

基于 LLM 分析 Issue 变更情况，决定全量更新还是增量更新
"""

import logging
import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 导入 Phase 2 的数据模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from extraction.models import IssueKnowledgePackage
import config.env  # noqa: F401  加载 .env，使下方 os.getenv 能读到密钥

logger = logging.getLogger(__name__)


class UpdateDecisionChain:
    """更新决策链：基于 LLM 智能决策全量/增量更新"""

    def __init__(self):
        """
        初始化决策链

        使用火山 ARK MiniMax M3 模型
        """
        # 初始化 LLM（火山 ARK）
        ark_api_key = os.getenv("ARK_API_KEY")
        if not ark_api_key:
            logger.warning(
                "ARK_API_KEY 环境变量未设置，决策功能将不可用"
            )
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model="minimax-m3",
                openai_api_key=ark_api_key,
                openai_api_base="https://ark.cn-beijing.volces.com/api/coding/v3",
                temperature=0.1  # 低温度，保证决策稳定性
            )

        # 决策 Prompt
        self.prompt = PromptTemplate(
            input_variables=[
                "issue_number",
                "issue_title",
                "issue_labels",
                "changed_files_count",
                "requirement_doc_size",
                "days_since_last_update"
            ],
            template="""你是一个知识库更新策略专家，需要根据 Issue 的变更情况决定使用「全量更新」还是「增量更新」。

**Issue 信息**:
- Issue 编号: #{issue_number}
- Issue 标题: {issue_title}
- Issue 标签: {issue_labels}
- 变更文件数: {changed_files_count}
- 需求文档大小: {requirement_doc_size} 字符
- 距上次更新: {days_since_last_update} 天

**决策规则**:
1. 全量更新（以下任一条件满足）:
   - Issue 标签包含 need_design 或 need_security（架构或安全相关）
   - 需求文档 > 500 行（约 15,000 字符）
   - 变更文件数 >= 30% 总文件数（假设总文件数约 30，即 >= 9 个文件）
   - 距上次更新 > 7 天（定期全量兜底）

2. 增量更新:
   - 以上条件都不满足，且变更影响范围小

**输出格式**（必须严格遵守）:
{{
  "decision": "full" 或 "incremental",
  "reason": "决策理由（1-2 句话）",
  "confidence": 0.0-1.0（决策置信度）
}}

请分析并输出决策："""
        )

        if self.llm:
            self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        else:
            self.chain = None

    def decide(
        self,
        knowledge_package: IssueKnowledgePackage,
        days_since_last_update: float = 0.0
    ) -> Dict[str, Any]:
        """
        决策更新模式

        Args:
            knowledge_package: Issue 知识包
            days_since_last_update: 距上次更新的天数

        Returns:
            Dict[str, Any]: 决策结果
                {
                    "decision": "full" | "incremental",
                    "reason": str,
                    "confidence": float
                }
        """
        logger.info(f"开始决策 Issue #{knowledge_package.issue_number} 的更新模式")

        # 如果 LLM 不可用，使用规则引擎降级
        if not self.chain:
            logger.warning("LLM 不可用，使用规则引擎降级决策")
            return self._rule_based_decision(
                knowledge_package,
                days_since_last_update
            )

        # 准备输入数据
        input_data = {
            "issue_number": knowledge_package.issue_number,
            "issue_title": knowledge_package.issue_title,
            "issue_labels": ", ".join(knowledge_package.issue_labels),
            "changed_files_count": knowledge_package.get_changed_files_count(),
            "requirement_doc_size": knowledge_package.get_requirement_doc_size(),
            "days_since_last_update": round(days_since_last_update, 1)
        }

        logger.info(
            f"决策输入: 变更文件={input_data['changed_files_count']}, "
            f"需求文档={input_data['requirement_doc_size']} 字符, "
            f"距上次更新={input_data['days_since_last_update']} 天"
        )

        try:
            # 调用 LLM
            response = self.chain.run(**input_data)

            # 解析响应（尝试提取 JSON）
            import json
            import re

            # 尝试提取 JSON 块
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                # 简单解析
                if "incremental" in response.lower():
                    result = {
                        "decision": "incremental",
                        "reason": "LLM 建议增量更新",
                        "confidence": 0.7
                    }
                else:
                    result = {
                        "decision": "full",
                        "reason": "LLM 建议全量更新",
                        "confidence": 0.7
                    }

            logger.info(
                f"决策结果: {result['decision']} "
                f"(置信度={result.get('confidence', 0.0):.2f})"
            )
            logger.info(f"决策理由: {result['reason']}")

            return result

        except Exception as e:
            logger.error(f"LLM 决策失败: {e}，降级到规则引擎")
            return self._rule_based_decision(
                knowledge_package,
                days_since_last_update
            )

    def _rule_based_decision(
        self,
        knowledge_package: IssueKnowledgePackage,
        days_since_last_update: float
    ) -> Dict[str, Any]:
        """
        规则引擎决策（降级方案）

        Args:
            knowledge_package: Issue 知识包
            days_since_last_update: 距上次更新的天数

        Returns:
            Dict[str, Any]: 决策结果
        """
        labels = knowledge_package.issue_labels
        changed_files = knowledge_package.get_changed_files_count()
        doc_size = knowledge_package.get_requirement_doc_size()

        # 规则 1: 架构或安全相关
        if "need_design" in labels or "need_security" in labels:
            return {
                "decision": "full",
                "reason": "Issue 涉及架构设计或安全（标签包含 need_design/need_security）",
                "confidence": 0.95
            }

        # 规则 2: 需求文档过大
        if doc_size > 15000:  # 约 500 行
            return {
                "decision": "full",
                "reason": f"需求文档过大（{doc_size} 字符 > 15,000）",
                "confidence": 0.9
            }

        # 规则 3: 变更文件过多
        if changed_files >= 9:  # 假设 30% 总文件数
            return {
                "decision": "full",
                "reason": f"变更文件过多（{changed_files} 个文件 >= 9）",
                "confidence": 0.85
            }

        # 规则 4: 距上次更新时间过长
        if days_since_last_update > 7:
            return {
                "decision": "full",
                "reason": f"距上次更新时间过长（{days_since_last_update:.1f} 天 > 7）",
                "confidence": 0.8
            }

        # 默认：增量更新
        return {
            "decision": "incremental",
            "reason": f"影响范围小（{changed_files} 个文件，{doc_size} 字符）",
            "confidence": 0.8
        }

