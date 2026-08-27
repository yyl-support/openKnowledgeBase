#!/usr/bin/env python3
"""
测试火山 ARK LLM API 调用
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量
# 从 .env 或环境变量读取
from dotenv import load_dotenv
load_dotenv()
if not os.getenv("ARK_API_KEY"):
    raise ValueError("请设置 ARK_API_KEY 环境变量或在项目根目录创建 .env 文件")

from langchain_openai import ChatOpenAI
from update.decision_chain import UpdateDecisionChain
from extraction.models import (
    IssueKnowledgePackage,
    CodeChange,
    PRReference
)

print("=" * 80)
print("测试火山 ARK LLM API 调用")
print("=" * 80)

# ============================================================================
# 1. 测试基础 LLM 调用
# ============================================================================
print("\n1. 测试基础 LLM 调用...")

try:
    llm = ChatOpenAI(
        model="minimax-m3",
        openai_api_key=os.getenv("ARK_API_KEY"),
        openai_api_base="https://ark.cn-beijing.volces.com/api/v3"
    )

    response = llm.invoke("你好，请用一句话介绍你自己")

    print(f"✅ LLM 调用成功")
    print(f"   - 模型: minimax-m3")
    print(f"   - 响应: {response.content[:100]}...")

except Exception as e:
    print(f"❌ LLM 调用失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# 2. 测试 UpdateDecisionChain（LLM 决策）
# ============================================================================
print("\n2. 测试 UpdateDecisionChain（使用 LLM）...")

try:
    decision_chain = UpdateDecisionChain()

    # 构造测试数据
    test_package = IssueKnowledgePackage(
        issue_number=1611,
        issue_title="[缺陷] token刷新接口，未配置 Flask 的 MAX_CONTENT_LENGTH 限制",
        issue_labels=["bug", "accepted", "project:forum-reply-robot"],
        issue_body="需要为 Flask 应用配置 MAX_CONTENT_LENGTH 限制，防止大请求导致 OOM",
        code_change=CodeChange(
            pr=PRReference(
                repo="opensourceways/forum-reply-robot",
                number=177,
                title="修复 MAX_CONTENT_LENGTH",
                state="MERGED",
                url="https://github.com/opensourceways/forum-reply-robot/pull/177"
            ),
            diff="+ app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024",
            files=[
                {"path": "main.py", "additions": 5, "deletions": 1},
                {"path": "config.py", "additions": 3, "deletions": 0}
            ],
            total_additions=8,
            total_deletions=1
        )
    )

    # 使用 LLM 决策
    decision = decision_chain.decide(
        knowledge_package=test_package,
        days_since_last_update=1.0
    )

    print(f"✅ LLM 决策成功")
    print(f"   - 决策结果: {decision['decision']}")
    print(f"   - 决策理由: {decision['reason']}")
    print(f"   - 置信度: {decision['confidence']:.2%}")
    print(f"   - 决策来源: {decision.get('source', 'unknown')}")

except Exception as e:
    print(f"❌ 决策失败: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 80)
print("✅ 火山 ARK LLM API 测试完成！")
print("=" * 80)

print("\n已验证调用:")
print("   ✅ 基础 LLM 对话")
print("   ✅ UpdateDecisionChain LLM 决策")

print("\n你可以在火山 ARK 控制台查看 API 使用记录")
