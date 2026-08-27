#!/usr/bin/env python3
"""
验证修复效果的端到端测试脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from orchestration.gh_client import GitHubCLI
from extraction.issue_extractor import IssueKnowledgeExtractor
from update.update_chain import KnowledgeUpdateChain

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_fix_1_gh_sorting():
    """验证修复 1: gh CLI 搜索结果排序"""
    logger.info("=== 验证修复 1: gh CLI 搜索结果排序 ===")

    gh = GitHubCLI()
    issues = gh.search_issues(
        repo="opensourceways/backlog",
        search_query="forum-reply-robot state:closed",
        limit=10
    )

    logger.info(f"搜索到 {len(issues)} 个 Issue")
    if len(issues) >= 2:
        first_issue = issues[0]
        second_issue = issues[1]
        logger.info(f"第一个 Issue: #{first_issue.number} (创建时间: {first_issue.created_at})")
        logger.info(f"第二个 Issue: #{second_issue.number} (创建时间: {second_issue.created_at})")

        # 验证按创建时间降序
        if first_issue.created_at >= second_issue.created_at:
            logger.info("✅ 排序正确: 按创建时间降序")
            return True
        else:
            logger.error("❌ 排序错误: 第一个 Issue 创建时间早于第二个")
            return False
    else:
        logger.warning("Issue 数量不足，无法验证排序")
        return True


def verify_fix_2_and_3_vectorization():
    """验证修复 2 和 3: 字段名修复和 patch 获取"""
    logger.info("\n=== 验证修复 2 & 3: 向量化字段名和 patch ===")

    # 1. 提取 Issue #1611
    logger.info("提取 Issue #1611...")
    gh = GitHubCLI()
    extractor = IssueKnowledgeExtractor(gh)

    knowledge_pkg = extractor.extract(
        backlog_repo="opensourceways/backlog",
        issue_number=1611,
        project_repo="opensourceways/forum-reply-robot"
    )

    logger.info(f"Issue #{knowledge_pkg.issue_number}: {knowledge_pkg.issue_title}")

    # 2. 检查代码变更是否包含 patch
    if not knowledge_pkg.code_change:
        logger.error("❌ 没有代码变更数据")
        return False

    logger.info(f"代码变更文件数: {len(knowledge_pkg.code_change.files)}")

    # 检查第一个文件
    if len(knowledge_pkg.code_change.files) > 0:
        first_file = knowledge_pkg.code_change.files[0]
        logger.info(f"第一个文件: {first_file}")

        # 验证字段名
        has_path = "path" in first_file or "filename" in first_file
        has_patch = "patch" in first_file

        if has_path:
            file_path = first_file.get("path") or first_file.get("filename", "")
            logger.info(f"✅ 文件路径字段存在: {file_path}")
        else:
            logger.error("❌ 文件路径字段缺失")
            return False

        if has_patch:
            patch = first_file.get("patch", "")
            patch_preview = patch[:200] if patch else "(空)"
            logger.info(f"✅ patch 字段存在，长度: {len(patch)} 字符")
            logger.info(f"patch 预览: {patch_preview}")
        else:
            logger.error("❌ patch 字段缺失")
            return False

    # 3. 向量化测试
    logger.info("\n开始向量化测试...")
    update_chain = KnowledgeUpdateChain("test_forum_reply_robot")

    # 清空测试向量库
    update_chain.vector_store.clear()

    # 执行更新
    result = update_chain.update_from_issue(knowledge_pkg)

    logger.info(f"更新结果: {result}")
    logger.info(f"  - 成功: {result['success']}")
    logger.info(f"  - 添加文档数: {result['documents_added']}")
    logger.info(f"  - 删除文档数: {result['documents_deleted']}")
    logger.info(f"  - 创建块数: {result['chunks_created']}")

    if not result['success']:
        logger.error(f"❌ 向量化失败: {result.get('error')}")
        return False

    if result['documents_added'] == 0:
        logger.error("❌ 没有添加任何文档到向量库")
        return False

    # 4. 验证向量库状态
    stats = update_chain.vector_store.get_stats()
    logger.info(f"\n向量库统计: {stats}")

    if stats['document_count'] == 0:
        logger.error("❌ 向量库文档数为 0")
        return False

    logger.info(f"✅ 向量库包含 {stats['document_count']} 个文档")

    # 5. 相似度搜索测试
    logger.info("\n测试相似度搜索...")
    search_results = update_chain.vector_store.similarity_search("logger", k=3)

    if len(search_results) == 0:
        logger.error("❌ 相似度搜索返回空结果")
        return False

    logger.info(f"✅ 搜索 'logger' 返回 {len(search_results)} 个结果")
    for i, doc in enumerate(search_results[:2]):
        preview = doc.page_content[:100].replace("\n", " ")
        logger.info(f"  结果 {i+1}: {preview}...")

    # 清理测试数据
    update_chain.vector_store.clear()
    logger.info("\n测试向量库已清理")

    return True


def main():
    """主函数"""
    logger.info("开始验证修复效果\n")

    results = []

    # 验证修复 1
    try:
        result_1 = verify_fix_1_gh_sorting()
        results.append(("修复 1: gh CLI 排序", result_1))
    except Exception as e:
        logger.error(f"验证修复 1 时出错: {e}", exc_info=True)
        results.append(("修复 1: gh CLI 排序", False))

    # 验证修复 2 和 3
    try:
        result_2_3 = verify_fix_2_and_3_vectorization()
        results.append(("修复 2 & 3: 向量化", result_2_3))
    except Exception as e:
        logger.error(f"验证修复 2 & 3 时出错: {e}", exc_info=True)
        results.append(("修复 2 & 3: 向量化", False))

    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("验证结果汇总")
    logger.info("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{name}: {status}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("✅ 所有修复验证通过！")
        return 0
    else:
        logger.error("❌ 部分修复验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
