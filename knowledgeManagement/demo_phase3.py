"""
Phase 3 Demo: 增量更新层（RAG 系统）演示

演示 UpdateDecisionChain、VectorStore、KnowledgeUpdateChain 的功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from update.decision_chain import UpdateDecisionChain
from update.vector_store import VectorStore
from update.update_chain import KnowledgeUpdateChain
from update.regeneration_chain import SectionRegenerationChain
from extraction.models import (
    IssueKnowledgePackage,
    RequirementDoc,
    CodeChange,
    PRReference
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_decision_chain():
    """演示决策链"""
    print("\n" + "=" * 60)
    print("Demo 1: UpdateDecisionChain - 更新决策")
    print("=" * 60)

    chain = UpdateDecisionChain()

    # 测试场景 1: 架构变更 -> 全量更新
    print("\n场景 1: 架构设计变更（need_design 标签）")
    package1 = IssueKnowledgePackage(
        issue_number=1734,
        issue_title="[架构优化] 重构日志系统",
        issue_labels=["need_design", "forum-reply-robot"],
        issue_body="重构整个日志系统架构",
        requirement=RequirementDoc(
            specification="详细的架构设计文档...",
            qa_checklist="",
            pr=PRReference(repo="test/repo", number=1)
        ),
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=2),
            diff="test diff",
            files=[
                {"filename": "src/logger.py", "patch": "..."},
                {"filename": "src/handler.py", "patch": "..."}
            ],
            total_additions=200,
            total_deletions=100
        )
    )

    result1 = chain.decide(package1, days_since_last_update=2.0)
    print(f"  决策结果: {result1['decision']}")
    print(f"  决策理由: {result1['reason']}")
    print(f"  置信度: {result1['confidence']:.2f}")

    # 测试场景 2: 小优化 -> 增量更新
    print("\n场景 2: 小功能优化")
    package2 = IssueKnowledgePackage(
        issue_number=1750,
        issue_title="优化日志输出格式",
        issue_labels=["forum-reply-robot"],
        issue_body="调整日志时间格式",
        requirement=RequirementDoc(
            specification="简短需求：将日志时间格式从 HH:mm:ss 改为 HH:mm:ss.SSS",
            qa_checklist="",
            pr=PRReference(repo="test/repo", number=1)
        ),
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=2),
            diff="test diff",
            files=[
                {"filename": "src/logger.py", "patch": "..."}
            ],
            total_additions=5,
            total_deletions=3
        )
    )

    result2 = chain.decide(package2, days_since_last_update=1.0)
    print(f"  决策结果: {result2['decision']}")
    print(f"  决策理由: {result2['reason']}")
    print(f"  置信度: {result2['confidence']:.2f}")


def demo_vector_store():
    """演示向量存储"""
    print("\n" + "=" * 60)
    print("Demo 2: VectorStore - 向量存储（项目隔离）")
    print("=" * 60)

    from langchain.schema import Document

    # 创建两个项目的向量存储
    store_a = VectorStore(
        project_name="project-a",
        base_dir="/tmp/demo_vectordb"
    )
    store_b = VectorStore(
        project_name="project-b",
        base_dir="/tmp/demo_vectordb"
    )

    print("\n1. 项目 A 添加文档")
    docs_a = [
        Document(
            page_content="项目 A 使用 Python FastAPI 框架开发",
            metadata={"source": "a_overview.md", "type": "doc"}
        ),
        Document(
            page_content="项目 A 的日志系统基于 Python logging 模块",
            metadata={"source": "a_techstack.md", "type": "doc"}
        )
    ]
    ids_a = store_a.add_documents(docs_a)
    print(f"  添加了 {len(ids_a)} 个文档")

    print("\n2. 项目 B 添加文档")
    docs_b = [
        Document(
            page_content="项目 B 使用 Node.js Express 框架开发",
            metadata={"source": "b_overview.md", "type": "doc"}
        ),
        Document(
            page_content="项目 B 的日志系统基于 Winston",
            metadata={"source": "b_techstack.md", "type": "doc"}
        )
    ]
    ids_b = store_b.add_documents(docs_b)
    print(f"  添加了 {len(ids_b)} 个文档")

    print("\n3. 项目 A 搜索（只返回项目 A 的文档）")
    results_a = store_a.similarity_search("日志系统", k=2)
    print(f"  找到 {len(results_a)} 个结果:")
    for i, doc in enumerate(results_a, 1):
        print(f"    [{i}] {doc.metadata['source']}: {doc.page_content[:50]}...")
        assert doc.metadata["project"] == "project-a", "项目隔离失败！"

    print("\n4. 项目 B 搜索（只返回项目 B 的文档）")
    results_b = store_b.similarity_search("日志系统", k=2)
    print(f"  找到 {len(results_b)} 个结果:")
    for i, doc in enumerate(results_b, 1):
        print(f"    [{i}] {doc.metadata['source']}: {doc.page_content[:50]}...")
        assert doc.metadata["project"] == "project-b", "项目隔离失败！"

    print("\n5. 获取统计信息")
    stats_a = store_a.get_stats()
    stats_b = store_b.get_stats()
    print(f"  项目 A: {stats_a['document_count']} 个文档")
    print(f"  项目 B: {stats_b['document_count']} 个文档")

    print("\n✅ 项目隔离验证通过！")


def demo_update_chain():
    """演示增量更新链"""
    print("\n" + "=" * 60)
    print("Demo 3: KnowledgeUpdateChain - 增量更新")
    print("=" * 60)

    chain = KnowledgeUpdateChain(project_name="demo-project")

    # 构造测试 Issue 知识包
    package = IssueKnowledgePackage(
        issue_number=1750,
        issue_title="优化日志输出格式",
        issue_labels=["forum-reply-robot"],
        issue_body="调整日志时间格式",
        requirement=RequirementDoc(
            specification="""
# 需求分析

## 背景
当前日志时间格式为 HH:mm:ss，不够精确。

## 目标
将日志时间格式改为 HH:mm:ss.SSS（包含毫秒）。

## 实现方案
修改 src/logger.py 中的 formatter 配置。
            """,
            qa_checklist="测试日志输出格式是否正确",
            pr=PRReference(repo="test/repo", number=1)
        ),
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=2),
            diff="test diff",
            files=[
                {
                    "filename": "src/logger.py",
                    "patch": """
@@ -10,7 +10,7 @@ class Logger:
     def __init__(self):
-        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
+        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S.%f')
         handler = logging.StreamHandler()
                    """,
                    "additions": 1,
                    "deletions": 1
                }
            ],
            total_additions=1,
            total_deletions=1
        )
    )

    print("\n1. 增量更新向量库")
    result = chain.update_from_issue(package)
    print(f"  更新结果: {'成功' if result['success'] else '失败'}")
    print(f"  添加文档: {result['documents_added']}")
    print(f"  删除文档: {result['documents_deleted']}")
    print(f"  分块数量: {result['chunks_created']}")

    print("\n2. 验证向量库内容")
    stats = chain.vector_store.get_stats()
    print(f"  向量库文档数: {stats['document_count']}")

    print("\n3. 搜索测试")
    results = chain.vector_store.similarity_search("日志时间格式", k=2)
    print(f"  找到 {len(results)} 个相关文档:")
    for i, doc in enumerate(results, 1):
        print(f"    [{i}] {doc.metadata.get('type', 'unknown')}: {doc.page_content[:80]}...")


def demo_regeneration_chain():
    """演示章节重新生成链"""
    print("\n" + "=" * 60)
    print("Demo 4: SectionRegenerationChain - 章节重新生成")
    print("=" * 60)

    chain = SectionRegenerationChain(project_name="demo-project")

    # 构造测试 Issue 知识包
    package = IssueKnowledgePackage(
        issue_number=1750,
        issue_title="优化日志输出格式",
        issue_labels=["forum-reply-robot"],
        issue_body="调整日志时间格式",
        requirement=None,
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=2),
            diff="test diff",
            files=[
                {"filename": "src/logger.py", "patch": "...", "additions": 5, "deletions": 3},
                {"filename": "requirements.txt", "patch": "...", "additions": 1, "deletions": 0},
                {"filename": ".github/workflows/test.yml", "patch": "...", "additions": 2, "deletions": 1}
            ],
            total_additions=8,
            total_deletions=4
        )
    )

    print("\n1. 识别受影响的章节")
    affected_sections = chain.identify_affected_sections(package)
    print(f"  找到 {len(affected_sections)} 个受影响的章节:")
    for section in affected_sections:
        print(f"    - {section['document']} / {section['section']} ({section['reason']})")

    print("\n2. 章节重新生成（需要 LLM）")
    if os.getenv("ARK_API_KEY"):
        print("  LLM 可用，可以测试章节生成")
        # 注意：实际生成需要向量库中有相关内容
    else:
        print("  ⚠️  ARK_API_KEY 未设置，跳过 LLM 生成测试")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Phase 3: 增量更新层（RAG 系统）演示")
    print("=" * 60)

    try:
        # Demo 1: 决策链
        demo_decision_chain()

        # Demo 2: 向量存储
        demo_vector_store()

        # Demo 3: 增量更新链
        demo_update_chain()

        # Demo 4: 章节重新生成链
        demo_regeneration_chain()

        print("\n" + "=" * 60)
        print("✅ Phase 3 所有 Demo 执行完成！")
        print("=" * 60)

    except Exception as e:
        logger.exception("Demo 执行失败")
        print(f"\n❌ Demo 执行失败: {e}")


if __name__ == "__main__":
    main()
