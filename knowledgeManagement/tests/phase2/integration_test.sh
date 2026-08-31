#!/bin/bash
# Phase 2 集成测试

set -e

echo "=== Phase 2 集成测试 ==="

# 切换到项目根目录
cd "$(dirname "$0")/../.."

# 1. 测试 PR 链接解析
echo ""
echo "1. 测试 PR 链接解析..."
python3 -m pytest tests/phase2/test_pr_link_parser.py -v

# 2. 测试 backlog 缓存
echo ""
echo "2. 测试 backlog 缓存（基本功能）..."
python3 -c "
import sys
sys.path.insert(0, '.')
from extraction.backlog_cache import BacklogCache

cache = BacklogCache()
print(f'✅ BacklogCache 初始化成功')
print(f'   缓存目录: {cache.cache_dir}')
print(f'   仓库 URL: {cache.repo_url}')
"

# 3. 测试知识提取器（需要网络）
echo ""
echo "3. 测试知识提取器（使用 Issue #1611）..."
echo "   注意：此测试需要网络连接和 gh CLI 认证"

python3 -c "
import sys
sys.path.insert(0, '.')
from extraction.issue_extractor import IssueKnowledgeExtractor
from orchestration.gh_client import GitHubCLI

try:
    gh = GitHubCLI()
    extractor = IssueKnowledgeExtractor(gh)

    print('开始提取 Issue #1611...')
    knowledge = extractor.extract(
        backlog_repo='opensourceways/backlog',
        issue_number=1611,
        project_repo='opensourceways/forum-reply-robot'
    )

    print(f'✅ Issue #{knowledge.issue_number}: {knowledge.issue_title}')
    print(f'   标签: {knowledge.issue_labels}')
    print(f'   变更文件数: {knowledge.get_changed_files_count()}')
    print(f'   需求文档大小: {knowledge.get_requirement_doc_size()} 字符')
    print(f'   有需求文档: {knowledge.requirement is not None}')
    print(f'   有代码变更: {knowledge.code_change is not None}')
    print(f'   有测试报告: {knowledge.test_report is not None}')
    print(f'   有上线信息: {knowledge.release_info is not None}')

except Exception as e:
    print(f'❌ 提取失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "=== ✅ Phase 2 集成测试通过 ==="
