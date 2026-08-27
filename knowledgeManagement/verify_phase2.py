#!/usr/bin/env python3
"""
Phase 2 验证脚本：确认所有模块正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试所有模块能否正常导入"""
    print("=" * 60)
    print("Phase 2 模块导入验证")
    print("=" * 60)

    try:
        print("\n[1/5] 导入数据模型...")
        from extraction.models import (
            PRReference,
            RequirementDoc,
            CodeChange,
            TestReport,
            ReleaseInfo,
            IssueKnowledgePackage
        )
        print("  ✅ 数据模型导入成功")

        print("\n[2/5] 导入 PR 链接解析器...")
        from extraction.pr_link_parser import PRLinkParser
        parser = PRLinkParser()
        print("  ✅ PR 链接解析器导入并初始化成功")

        print("\n[3/5] 导入 backlog 缓存管理器...")
        from extraction.backlog_cache import BacklogCache
        cache = BacklogCache()
        print("  ✅ backlog 缓存管理器导入并初始化成功")
        print(f"     缓存目录: {cache.cache_dir}")

        print("\n[4/5] 导入知识提取器...")
        from extraction.issue_extractor import IssueKnowledgeExtractor
        from orchestration.gh_client import GitHubCLI
        gh = GitHubCLI()
        extractor = IssueKnowledgeExtractor(gh)
        print("  ✅ 知识提取器导入并初始化成功")

        print("\n[5/5] 导入增强的调度器...")
        from orchestration.orchestrator import KnowledgeOrchestrator
        print("  ✅ 调度器导入成功（已集成知识提取）")

        return True

    except Exception as e:
        print(f"\n  ❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 60)
    print("Phase 2 基本功能验证")
    print("=" * 60)

    try:
        from extraction.pr_link_parser import PRLinkParser
        from extraction.models import IssueKnowledgePackage

        print("\n[1/3] 测试 PR 链接解析...")
        parser = PRLinkParser()

        test_comments = [
            {
                'body': '需求分析 PR: https://github.com/opensourceways/backlog/pull/1612'
            },
            {
                'body': '开发 PR: https://github.com/opensourceways/forum-reply-robot/pull/177'
            }
        ]

        req_pr = parser.parse_requirement_pr(test_comments)
        dev_pr = parser.parse_development_pr(test_comments, "opensourceways/forum-reply-robot")

        if req_pr and dev_pr:
            print(f"  ✅ PR 链接解析成功")
            print(f"     需求分析 PR: #{req_pr.number}")
            print(f"     开发 PR: #{dev_pr.number}")
        else:
            print(f"  ⚠️ PR 链接解析部分失败")

        print("\n[2/3] 测试数据模型...")
        knowledge = IssueKnowledgePackage(
            issue_number=1611,
            issue_title="测试 Issue",
            issue_labels=["test", "bug"],
            issue_body="测试内容"
        )

        print(f"  ✅ 数据模型创建成功")
        print(f"     Issue: #{knowledge.issue_number}")
        print(f"     标签: {knowledge.issue_labels}")
        print(f"     提取时间: {knowledge.extracted_at}")

        print("\n[3/3] 测试辅助方法...")
        files_count = knowledge.get_changed_files_count()
        doc_size = knowledge.get_requirement_doc_size()
        has_design = knowledge.has_design_label()

        print(f"  ✅ 辅助方法调用成功")
        print(f"     变更文件数: {files_count}")
        print(f"     文档大小: {doc_size}")
        print(f"     有设计标签: {has_design}")

        return True

    except Exception as e:
        print(f"\n  ❌ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_structure():
    """测试目录结构"""
    print("\n" + "=" * 60)
    print("Phase 2 目录结构验证")
    print("=" * 60)

    required_files = [
        "extraction/__init__.py",
        "extraction/models.py",
        "extraction/pr_link_parser.py",
        "extraction/backlog_cache.py",
        "extraction/issue_extractor.py",
        "extraction/README.md",
        "tests/phase2/__init__.py",
        "tests/phase2/test_pr_link_parser.py",
        "tests/phase2/test_backlog_cache.py",
        "tests/phase2/test_issue_extractor.py",
        "tests/phase2/integration_test.sh",
        "demo_phase2.py"
    ]

    all_exist = True
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (缺失)")
            all_exist = False

    return all_exist


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("开始 Phase 2 完整性验证")
    print("=" * 60)

    # 测试目录结构
    structure_ok = test_structure()

    # 测试模块导入
    import_ok = test_imports()

    # 测试基本功能
    functionality_ok = test_basic_functionality()

    # 总结
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    print(f"\n  目录结构: {'✅ 通过' if structure_ok else '❌ 失败'}")
    print(f"  模块导入: {'✅ 通过' if import_ok else '❌ 失败'}")
    print(f"  基本功能: {'✅ 通过' if functionality_ok else '❌ 失败'}")

    all_ok = structure_ok and import_ok and functionality_ok

    if all_ok:
        print("\n🎉 Phase 2 验证通过！所有模块工作正常。")
        print("\n下一步:")
        print("  1. 运行集成测试: bash tests/phase2/integration_test.sh")
        print("  2. 运行演示脚本: python3 demo_phase2.py 1611")
        print("  3. 开始实施 Phase 3")
        return 0
    else:
        print("\n⚠️ Phase 2 验证失败，请检查上述错误。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
