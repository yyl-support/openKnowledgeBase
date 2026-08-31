#!/usr/bin/env python3
"""
Phase 2 演示脚本：展示 Issue 知识提取功能

用法:
    python3 demo_phase2.py [issue_number]

示例:
    python3 demo_phase2.py 1611
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from extraction.issue_extractor import IssueKnowledgeExtractor
from orchestration.gh_client import GitHubCLI


def main():
    """主函数"""
    # 默认使用 Issue #1611
    issue_number = 1611
    if len(sys.argv) > 1:
        issue_number = int(sys.argv[1])

    print("=" * 60)
    print(f"Phase 2 演示：提取 Issue #{issue_number} 的知识")
    print("=" * 60)

    # 初始化提取器
    print("\n初始化 GitHub CLI 客户端...")
    gh = GitHubCLI()

    print("初始化知识提取器...")
    extractor = IssueKnowledgeExtractor(gh)

    # 提取知识
    print(f"\n开始提取 Issue #{issue_number} 的知识...\n")

    knowledge = extractor.extract(
        backlog_repo="opensourceways/backlog",
        issue_number=issue_number,
        project_repo="opensourceways/forum-reply-robot"
    )

    # 显示结果
    print("\n" + "=" * 60)
    print("提取结果")
    print("=" * 60)

    print(f"\n【基本信息】")
    print(f"  Issue 编号: #{knowledge.issue_number}")
    print(f"  Issue 标题: {knowledge.issue_title}")
    print(f"  标签: {', '.join(knowledge.issue_labels)}")
    print(f"  提取时间: {knowledge.extracted_at}")

    print(f"\n【需求分析】")
    if knowledge.requirement:
        print(f"  ✅ 有需求文档")
        print(f"  PR: {knowledge.requirement.pr.url}")
        print(f"  PR 状态: {knowledge.requirement.pr.state}")
        print(f"  文档大小: {len(knowledge.requirement.specification)} 字符")
        if knowledge.requirement.qa_checklist:
            print(f"  QA 清单大小: {len(knowledge.requirement.qa_checklist)} 字符")
    else:
        print(f"  ❌ 未找到需求文档")

    print(f"\n【代码变更】")
    if knowledge.code_change:
        print(f"  ✅ 有代码变更")
        print(f"  PR: {knowledge.code_change.pr.url}")
        print(f"  PR 状态: {knowledge.code_change.pr.state}")
        print(f"  变更文件数: {len(knowledge.code_change.files)}")
        print(f"  新增行数: +{knowledge.code_change.total_additions}")
        print(f"  删除行数: -{knowledge.code_change.total_deletions}")
        print(f"\n  变更文件列表:")
        for file_info in knowledge.code_change.files[:10]:  # 只显示前10个
            path = file_info.get('path', 'unknown')
            additions = file_info.get('additions', 0)
            deletions = file_info.get('deletions', 0)
            print(f"    - {path} (+{additions}, -{deletions})")
        if len(knowledge.code_change.files) > 10:
            print(f"    ... 还有 {len(knowledge.code_change.files) - 10} 个文件")
    else:
        print(f"  ❌ 未找到代码变更")

    print(f"\n【测试报告】")
    if knowledge.test_report:
        print(f"  ✅ 有测试报告")
        print(f"  PR: {knowledge.test_report.pr.url}")
    else:
        print(f"  ❌ 未找到测试报告（可选）")

    print(f"\n【上线信息】")
    if knowledge.release_info:
        print(f"  ✅ 有上线信息")
        print(f"  PR: {knowledge.release_info.pr.url}")
    else:
        print(f"  ❌ 未找到上线信息（可选）")

    print(f"\n【统计信息】")
    print(f"  变更文件总数: {knowledge.get_changed_files_count()}")
    print(f"  需求文档大小: {knowledge.get_requirement_doc_size()} 字符")
    print(f"  有设计标签: {knowledge.has_design_label()}")
    print(f"  有安全标签: {knowledge.has_security_label()}")

    # 保存到 JSON 文件
    output_file = f"work/issue_{issue_number}_knowledge.json"
    Path("work").mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'issue_number': knowledge.issue_number,
            'issue_title': knowledge.issue_title,
            'issue_labels': knowledge.issue_labels,
            'has_requirement': knowledge.requirement is not None,
            'has_code_change': knowledge.code_change is not None,
            'has_test_report': knowledge.test_report is not None,
            'has_release_info': knowledge.release_info is not None,
            'changed_files_count': knowledge.get_changed_files_count(),
            'requirement_doc_size': knowledge.get_requirement_doc_size(),
            'extracted_at': knowledge.extracted_at.isoformat()
        }, f, indent=2, ensure_ascii=False)

    print(f"\n知识包已保存到: {output_file}")
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
