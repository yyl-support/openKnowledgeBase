#!/usr/bin/env python3
"""
假成功检查脚本
用途：验证向量库是否真实写入数据，而非只是返回 success: True
"""

import sys
import os
import argparse
from pathlib import Path


def check_vectordb_directory(project_name, base_dir="vectordb"):
    """
    检查向量库目录是否存在且非空

    Returns:
        tuple: (passed, message)
    """
    project_dir = Path(base_dir) / project_name

    if not project_dir.exists():
        return False, f"向量库目录不存在: {project_dir}"

    # 检查 chroma.sqlite3 文件
    sqlite_file = project_dir / "chroma.sqlite3"
    if not sqlite_file.exists():
        return False, f"chroma.sqlite3 文件不存在"

    size = sqlite_file.stat().st_size
    if size == 0:
        return False, f"chroma.sqlite3 文件为空"

    # 转换为 KB
    size_kb = size / 1024
    return True, f"chroma.sqlite3 ({size_kb:.1f} KB)"


def check_similarity_search(project_name, base_dir="vectordb"):
    """
    检查相似度搜索是否返回结果

    Returns:
        tuple: (passed, message, results)
    """
    # 需要导入 VectorStore
    try:
        # 动态导入以避免路径问题
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from update.vector_store import VectorStore
    except ImportError as e:
        return False, f"无法导入 VectorStore: {e}", []

    # 检查环境变量
    if not os.getenv("SILICONFLOW_API_KEY"):
        return False, "SILICONFLOW_API_KEY 环境变量未设置", []

    try:
        store = VectorStore(project_name, base_dir)
        results = store.similarity_search("test", k=5)

        if not results:
            return False, "相似度搜索返回空结果", []

        return True, f"{len(results)} 个", results

    except Exception as e:
        return False, f"相似度搜索失败: {e}", []


def check_document_content(results):
    """
    检查文档内容是否非空

    Returns:
        tuple: (passed, message)
    """
    if not results:
        return False, "无文档可检查"

    total_length = 0
    empty_count = 0

    for doc in results:
        content = doc.page_content
        if len(content) < 50:
            empty_count += 1
        total_length += len(content)

    if empty_count == len(results):
        return False, "所有文档内容都为空或过短"

    avg_length = total_length / len(results)

    if avg_length < 50:
        return False, f"文档内容过短，平均长度 {avg_length:.0f} 字符"

    return True, f"page_content 平均长度 {avg_length:.0f} 字符"


def main():
    parser = argparse.ArgumentParser(description="检查向量库假成功")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--base-dir", default="vectordb", help="向量库根目录")
    args = parser.parse_args()

    project = args.project
    base_dir = args.base_dir

    print(f"========================================")
    print(f"假成功检查: {project}")
    print(f"========================================")

    # 检查1: 向量库目录存在且非空
    passed1, msg1 = check_vectordb_directory(project, base_dir)
    if passed1:
        print(f"✅ 向量库目录存在: {base_dir}/{project}/")
        print(f"✅ 向量库非空: {msg1}")
    else:
        print(f"❌ 向量库目录检查失败: {msg1}")
        print(f"========================================")
        print("结论: 检查失败（向量库目录问题）")
        return 1

    # 检查2: 相似度搜索返回结果
    passed2, msg2, results = check_similarity_search(project, base_dir)
    if passed2:
        print(f"✅ 相似度检索返回结果: {msg2}")
    else:
        if "SILICONFLOW_API_KEY" in msg2:
            print(f"⚠️  无法检查相似度搜索: {msg2}")
            print(f"========================================")
            print("结论: 无法完成检查（缺少 API Key）")
            return 2
        else:
            print(f"❌ 相似度检索失败: {msg2}")
            print(f"========================================")
            print("结论: 检查失败（相似度搜索无结果）")
            return 1

    # 检查3: 文档内容非空
    passed3, msg3 = check_document_content(results)
    if passed3:
        print(f"✅ 文档内容非空: {msg3}")
    else:
        print(f"❌ 文档内容检查失败: {msg3}")
        print(f"========================================")
        print("结论: 检查失败（文档内容为空）")
        return 1

    print(f"========================================")
    print("结论: 未发现假成功")
    return 0


if __name__ == "__main__":
    sys.exit(main())
