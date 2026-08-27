#!/bin/bash
# Phase 1 集成测试

set -e

echo "=== Phase 1 集成测试 ==="

# 1. 测试配置加载
echo ""
echo "1. 测试配置加载..."
python3 -c "
from config.loader import load_system_config
config = load_system_config('config/projects.yaml')
print(f'✅ 加载 {len(config.projects)} 个项目')
"

# 2. 测试 gh CLI 封装
echo ""
echo "2. 测试 gh CLI 封装..."
python3 -c "
from orchestration.gh_client import GitHubCLI
gh = GitHubCLI()
issues = gh.search_issues('opensourceways/backlog', 'forum-reply-robot state:closed', limit=3)
print(f'✅ 搜索到 {len(issues)} 个 Issue')
"

# 3. 测试 Issue 检测
echo ""
echo "3. 测试 Issue 检测..."
python3 -c "
from orchestration.gh_client import GitHubCLI
from orchestration.issue_detector import IssueChangeDetector
from config.loader import load_system_config

config = load_system_config('config/projects.yaml')
gh = GitHubCLI()
detector = IssueChangeDetector(gh)

project = config.projects['forum-reply-robot']
new_issues = detector.detect_new_issues(project)
print(f'✅ 检测到 {len(new_issues)} 个新 Issue')
"

# 4. 测试调度器
echo ""
echo "4. 测试调度器（不执行实际更新）..."
python3 -c "
from orchestration.orchestrator import KnowledgeOrchestrator
orchestrator = KnowledgeOrchestrator()
print('✅ 调度器初始化成功')
"

# 5. 测试 CLI
echo ""
echo "5. 测试 CLI..."
PYTHONPATH=. python3 triggers/cli.py --help > /dev/null
echo "✅ CLI 工具可用"

echo ""
echo "=== ✅ 所有集成测试通过 ==="
