#!/usr/bin/env python3
"""
测试 ascend-ci-deployment 项目的知识更新

测试 Issue: #1789 - [缺陷] verl项目hb003集群a3机器分配的内存过小，导致经常OOM
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from orchestration.gh_client import GitHubCLI
from extraction.issue_extractor import IssueKnowledgeExtractor
from update.decision_chain import UpdateDecisionChain
from update.update_chain import KnowledgeUpdateChain

print("=" * 80)
print("ascend-ci-deployment 项目知识更新测试")
print("=" * 80)

# 配置
TEST_ISSUE_NUMBER = 1789
PROJECT_NAME = "ascend-ci-deployment"
BACKLOG_REPO = "opensourceways/backlog"
PROJECT_REPO = "opensourceways/ascend-ci-deployment"

# ============================================================================
# 1. 获取 Issue 详情
# ============================================================================
print(f"\n1. 获取 Issue #{TEST_ISSUE_NUMBER} 详情...")

gh_client = GitHubCLI()

issue = gh_client.get_issue(BACKLOG_REPO, TEST_ISSUE_NUMBER)

print(f"\n✅ Issue 信息:")
print(f"   - 编号: #{issue.number}")
print(f"   - 标题: {issue.title}")
print(f"   - 状态: {issue.state}")
print(f"   - 标签: {issue.labels}")
print(f"   - 评论数: {len(issue.comments)}")

# ============================================================================
# 2. 提取知识
# ============================================================================
print(f"\n2. 提取 Issue #{TEST_ISSUE_NUMBER} 的知识...")

extractor = IssueKnowledgeExtractor(gh_client)

try:
    knowledge_package = extractor.extract(
        backlog_repo=BACKLOG_REPO,
        issue_number=TEST_ISSUE_NUMBER,
        project_repo=PROJECT_REPO
    )

    print(f"\n✅ 知识提取完成:")
    print(f"   - Issue: #{knowledge_package.issue_number}")
    print(f"   - 标题: {knowledge_package.issue_title}")
    print(f"   - 标签: {knowledge_package.issue_labels}")
    print(f"   - 需求文档: {'✅' if knowledge_package.requirement else '❌'}")
    print(f"   - 代码变更: {'✅' if knowledge_package.code_change else '❌'}")

    if knowledge_package.code_change:
        print(f"   - 变更文件数: {knowledge_package.get_changed_files_count()}")
        print(f"   - 变更统计: +{knowledge_package.code_change.total_additions}/-{knowledge_package.code_change.total_deletions}")
        print(f"   - 变更文件:")
        for f in knowledge_package.code_change.files[:5]:  # 只显示前5个
            print(f"     • {f['path']} (+{f.get('additions', 0)}/-{f.get('deletions', 0)})")

    if knowledge_package.requirement:
        print(f"   - 需求文档大小: {knowledge_package.get_requirement_doc_size()} 字符")

    print(f"   - 测试报告: {'✅' if knowledge_package.test_report else '❌'}")
    print(f"   - 上线信息: {'✅' if knowledge_package.release_info else '❌'}")

except Exception as e:
    print(f"❌ 知识提取失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# 3. 决策更新模式
# ============================================================================
print(f"\n3. 决策更新模式...")

decision_chain = UpdateDecisionChain()

try:
    decision = decision_chain.decide(
        knowledge_package=knowledge_package,
        days_since_last_update=0.5  # 假设距上次更新0.5天
    )

    print(f"\n✅ 决策结果:")
    print(f"   - 更新模式: {decision['decision'].upper()}")
    print(f"   - 决策理由: {decision['reason']}")
    print(f"   - 置信度: {decision['confidence']:.2%}")

except Exception as e:
    print(f"❌ 决策失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# 4. 执行更新（增量或全量）
# ============================================================================
if decision['decision'] == 'incremental':
    print(f"\n4. 执行增量更新...")

    try:
        update_chain = KnowledgeUpdateChain(
            project_name=f"test-{PROJECT_NAME}"
        )

        result = update_chain.update_from_issue(knowledge_package)

        print(f"\n✅ 增量更新完成:")
        print(f"   - 处理需求文档: {result.get('requirement_processed', False)}")
        print(f"   - 处理代码变更: {result.get('code_processed', False)}")
        print(f"   - 需求文档 chunks: {result.get('requirement_chunks', 0)}")
        print(f"   - 代码 chunks: {result.get('code_chunks', 0)}")
        print(f"   - 总 chunks: {result.get('total_chunks', 0)}")

        # 测试检索
        if result.get('total_chunks', 0) > 0:
            print(f"\n测试向量检索:")
            test_queries = ["内存配置", "OOM", "集群资源"]

            for query in test_queries:
                results = update_chain.vector_store.similarity_search(query, k=2)
                print(f"   - 查询'{query}': 找到 {len(results)} 个相关文档")

        # 获取统计
        stats = update_chain.vector_store.get_stats()
        print(f"\n向量库统计:")
        print(f"   - 文档总数: {stats.get('count', 0)}")
        print(f"   - 集合名称: {stats.get('collection_name', 'unknown')}")

    except Exception as e:
        print(f"❌ 增量更新失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

else:
    print(f"\n4. 应执行全量更新")
    print(f"   （全量更新会调用现有的四层流水线）")
    print(f"   本测试跳过实际执行")

# ============================================================================
# 总结
# ============================================================================
print(f"\n" + "=" * 80)
print(f"测试完成")
print(f"=" * 80)

print(f"\n✅ {PROJECT_NAME} 项目知识更新测试成功！")
print(f"\n测试的 Issue:")
print(f"   • Issue #{knowledge_package.issue_number}")
print(f"   • {knowledge_package.issue_title}")
print(f"\n更新模式: {decision['decision'].upper()}")
print(f"理由: {decision['reason']}")

if decision['decision'] == 'incremental':
    print(f"\n增量更新统计:")
    print(f"   • 新增文档块: {result.get('total_chunks', 0)}")
    print(f"   • 向量库文档数: {stats.get('count', 0)}")

print(f"\n✅ 系统可以正常处理 {PROJECT_NAME} 项目的知识更新！")
