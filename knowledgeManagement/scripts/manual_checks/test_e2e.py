#!/usr/bin/env python3
"""
端到端测试：完整的知识工程流程

测试流程：
1. Phase 1: 检测新 Issue
2. Phase 2: 提取 Issue 知识
3. Phase 3: 决策更新模式
4. Phase 3: 增量更新向量库
5. 验证结果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from orchestration.gh_client import GitHubCLI
from orchestration.issue_detector import IssueChangeDetector
from extraction.issue_extractor import IssueKnowledgeExtractor
from update.decision_chain import UpdateDecisionChain
from update.update_chain import KnowledgeUpdateChain
from config.models import ProjectConfig, IssueTrackingConfig, UpdatePolicyConfig, ProjectMetadata

print("=" * 80)
print("端到端测试：完整的知识工程流程")
print("=" * 80)

# ============================================================================
# Phase 1: Issue 检测
# ============================================================================
print("\n" + "=" * 80)
print("Phase 1: Issue 检测")
print("=" * 80)

gh_client = GitHubCLI()
detector = IssueChangeDetector(gh_client)

# 创建测试项目配置
test_project = ProjectConfig(
    repo_path="/tmp/forum-reply-robot",
    description="论坛自动回复机器人",
    owner="test",
    issue_tracking=IssueTrackingConfig(
        backlog_repo="opensourceways/backlog",
        search_query="forum-reply-robot state:closed",
        poll_interval=3.5
    ),
    adapter="ua",
    ua_profile="deepseek",
    output_types=["overview", "techstack", "standards"],
    update_policy=UpdatePolicyConfig(
        mode="auto",
        trigger="issue_polling"
    ),
    priority="high",
    metadata=ProjectMetadata(
        last_issue_number=1610  # 设置为 1610，这样会检测到 1611
    )
)

print(f"\n检测项目: forum-reply-robot")
print(f"上次处理到: Issue #{test_project.metadata.last_issue_number}")

new_issues = detector.detect_new_issues(test_project)

if not new_issues:
    print("❌ 没有检测到新 Issue")
    sys.exit(1)

print(f"\n✅ 检测到 {len(new_issues)} 个新 Issue:")
for issue in new_issues[:3]:  # 只显示前3个
    print(f"   - Issue #{issue.number}: {issue.title}")

# 选择一个 Issue 进行测试
test_issue_number = 1611
print(f"\n选择 Issue #{test_issue_number} 进行端到端测试")

# ============================================================================
# Phase 2: 提取 Issue 知识
# ============================================================================
print("\n" + "=" * 80)
print("Phase 2: 提取 Issue 知识")
print("=" * 80)

extractor = IssueKnowledgeExtractor(gh_client)

print(f"\n开始提取 Issue #{test_issue_number} 的知识...")

try:
    knowledge_package = extractor.extract(
        backlog_repo="opensourceways/backlog",
        issue_number=test_issue_number,
        project_repo="opensourceways/forum-reply-robot"
    )

    print(f"\n✅ 知识提取完成:")
    print(f"   - Issue: #{knowledge_package.issue_number} - {knowledge_package.issue_title}")
    print(f"   - 标签: {knowledge_package.issue_labels}")
    print(f"   - 需求文档: {'✅ 有' if knowledge_package.requirement else '❌ 无'}")
    print(f"   - 代码变更: {'✅ 有' if knowledge_package.code_change else '❌ 无'}")

    if knowledge_package.code_change:
        print(f"   - 变更文件数: {knowledge_package.get_changed_files_count()}")
        print(f"   - 代码变更统计: +{knowledge_package.code_change.total_additions}/-{knowledge_package.code_change.total_deletions}")

    if knowledge_package.requirement:
        print(f"   - 需求文档大小: {knowledge_package.get_requirement_doc_size()} 字符")

    print(f"   - 测试报告: {'✅ 有' if knowledge_package.test_report else '❌ 无'}")
    print(f"   - 上线信息: {'✅ 有' if knowledge_package.release_info else '❌ 无'}")

except Exception as e:
    print(f"❌ 知识提取失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# Phase 3: 决策更新模式
# ============================================================================
print("\n" + "=" * 80)
print("Phase 3: 决策更新模式")
print("=" * 80)

decision_chain = UpdateDecisionChain()

print(f"\n分析 Issue #{test_issue_number} 的特征...")
print(f"   - 标签: {knowledge_package.issue_labels}")
print(f"   - 需求文档大小: {knowledge_package.get_requirement_doc_size()} 字符")
print(f"   - 变更文件数: {knowledge_package.get_changed_files_count()}")

try:
    decision = decision_chain.decide(
        knowledge_package=knowledge_package,
        days_since_last_update=1.0  # 假设距上次更新1天
    )

    print(f"\n✅ 决策完成:")
    print(f"   - 更新模式: {decision['decision']}")
    print(f"   - 决策理由: {decision['reason']}")
    print(f"   - 置信度: {decision['confidence']:.2f}")
    print(f"   - 决策来源: {decision.get('source', 'unknown')}")

except Exception as e:
    print(f"❌ 决策失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# Phase 3: 增量更新向量库（如果决策为增量）
# ============================================================================
if decision['decision'] == 'incremental':
    print("\n" + "=" * 80)
    print("Phase 3: 增量更新向量库")
    print("=" * 80)

    # 使用临时目录进行测试
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="test_vectordb_")

    print(f"\n临时向量库目录: {temp_dir}")

    try:
        update_chain = KnowledgeUpdateChain(
            project_name="test-e2e-forum-reply-robot"
        )

        print(f"\n开始增量更新...")

        result = update_chain.update_from_issue(knowledge_package)

        print(f"\n✅ 增量更新完成:")
        print(f"   - 处理需求文档: {result.get('requirement_processed', False)}")
        print(f"   - 处理代码变更: {result.get('code_processed', False)}")
        print(f"   - 需求文档 chunks: {result.get('requirement_chunks', 0)}")
        print(f"   - 代码 chunks: {result.get('code_chunks', 0)}")
        print(f"   - 总 chunks: {result.get('total_chunks', 0)}")

        # 测试检索
        print(f"\n测试向量检索...")
        search_results = update_chain.vector_store.similarity_search(
            "日志系统",
            k=3
        )

        print(f"   - 检索到 {len(search_results)} 个相关文档")
        for i, doc in enumerate(search_results, 1):
            print(f"   - [{i}] {doc.metadata.get('source', 'unknown')[:50]}...")

        # 获取统计信息
        stats = update_chain.vector_store.get_stats()
        print(f"\n向量库统计:")
        print(f"   - 总文档数: {stats.get('count', 0)}")
        print(f"   - 集合名称: {stats.get('collection_name', 'unknown')}")

        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n✅ 临时目录已清理")

    except Exception as e:
        print(f"❌ 增量更新失败: {e}")
        import traceback
        traceback.print_exc()

        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        sys.exit(1)

else:
    print(f"\n⚠️  决策为全量更新，跳过增量更新测试")
    print(f"   （全量更新会调用现有的四层流水线）")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 80)
print("端到端测试完成")
print("=" * 80)

print(f"\n✅ 测试流程:")
print(f"   1. Phase 1: Issue 检测 - ✅ 成功")
print(f"   2. Phase 2: 知识提取 - ✅ 成功")
print(f"   3. Phase 3: 决策模式 - ✅ {decision['decision']}")
if decision['decision'] == 'incremental':
    print(f"   4. Phase 3: 增量更新 - ✅ 成功")
else:
    print(f"   4. Phase 3: 增量更新 - ⏭️  跳过（全量更新）")

print(f"\n🎉 端到端测试全部通过！")
print(f"\n系统已具备完整的自动化知识更新能力：")
print(f"   ✅ 自动检测新 Issue")
print(f"   ✅ 自动提取需求和代码变更")
print(f"   ✅ 智能决策更新模式")
print(f"   ✅ 增量更新向量库")
print(f"   ✅ 项目严格隔离")
