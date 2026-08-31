#!/bin/bash
# Phase 测试执行脚本
# 用途：自动运行指定 Phase 的所有测试并统计结果

set -e

PHASE=$1

if [ -z "$PHASE" ]; then
    echo "用法: $0 <phase_number>"
    echo "示例: $0 3"
    exit 1
fi

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DIR="$PROJECT_ROOT/tests/phase$PHASE"

# 检查测试目录是否存在
if [ ! -d "$TEST_DIR" ]; then
    echo "错误: Phase $PHASE 测试目录不存在: $TEST_DIR"
    exit 1
fi

# 检查是否有测试文件
TEST_FILES=$(find "$TEST_DIR" -name "test_*.py" 2>/dev/null || true)
if [ -z "$TEST_FILES" ]; then
    echo "错误: Phase $PHASE 目录下无测试文件"
    exit 1
fi

# 切换到项目根目录执行测试
cd "$PROJECT_ROOT"

# 运行测试并捕获输出
echo "正在运行 Phase $PHASE 测试..."
OUTPUT=$(pytest "$TEST_DIR" -q 2>&1 || true)

# 解析测试结果
PASSED=$(echo "$OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
FAILED=$(echo "$OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
SKIPPED=$(echo "$OUTPUT" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' || echo "0")
TOTAL=$((PASSED + FAILED + SKIPPED))

# 输出格式化结果
echo "========================================"
echo "Phase $PHASE 测试结果"
echo "========================================"
echo "通过: $PASSED"
echo "失败: $FAILED"
echo "跳过: $SKIPPED"
echo "总计: $TOTAL"
echo "========================================"

# 根据失败数决定退出码
if [ "$FAILED" -gt 0 ]; then
    exit 1
else
    exit 0
fi
