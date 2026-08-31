#!/usr/bin/env python3
"""
测试 Embeddings API 是否真正调用
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from update.vector_store import VectorStore

print("=" * 80)
print("测试 Embeddings API 调用")
print("=" * 80)

# 测试文档
test_docs = [
    Document(
        page_content="这是一个测试文档，用于验证向量化是否工作。",
        metadata={"source": "test.md", "type": "test"}
    ),
    Document(
        page_content="第二个测试文档，包含了一些关于数据库配置的内容。",
        metadata={"source": "config.md", "type": "test"}
    ),
    Document(
        page_content="Issue #1611 修复了 MAX_CONTENT_LENGTH 限制的问题。",
        metadata={"source": "issue.md", "type": "test"}
    )
]

print(f"\n1. 初始化向量存储（使用 SiliconFlow Embeddings）...")

try:
    vector_store = VectorStore(project_name="test-embeddings-api")
    print(f"✅ 向量存储初始化成功")
    print(f"   - 项目: test-embeddings-api")
    print(f"   - 持久化目录: {vector_store.persist_directory}")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n2. 向量化文档（调用 SiliconFlow API）...")
print(f"   - 文档数: {len(test_docs)}")

try:
    # 这里会调用 SiliconFlow 的 Embeddings API
    doc_ids = vector_store.add_documents(test_docs)

    print(f"✅ 向量化完成")
    print(f"   - 新增文档: {len(doc_ids)}")
    print(f"   - 文档 IDs: {doc_ids[:3]}...")
except Exception as e:
    print(f"❌ 向量化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n3. 测试相似度搜索...")

try:
    # 这里会再次调用 Embeddings API（查询向量化）
    results = vector_store.similarity_search("MAX_CONTENT_LENGTH", k=2)

    print(f"✅ 检索成功")
    print(f"   - 查询: MAX_CONTENT_LENGTH")
    print(f"   - 返回文档数: {len(results)}")

    for i, doc in enumerate(results, 1):
        print(f"   - [{i}] {doc.page_content[:50]}...")
        print(f"       来源: {doc.metadata.get('source', 'unknown')}")
except Exception as e:
    print(f"❌ 检索失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n4. 获取统计信息...")

try:
    stats = vector_store.get_stats()
    print(f"✅ 统计信息:")
    print(f"   - 文档数: {stats.get('count', 0)}")
    print(f"   - 集合名称: {stats.get('collection_name', 'unknown')}")
except Exception as e:
    print(f"❌ 获取统计失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n5. 清理测试数据...")

try:
    vector_store.clear()
    print(f"✅ 清理完成")
except Exception as e:
    print(f"⚠️  清理失败: {e}")

print(f"\n" + "=" * 80)
print(f"✅ Embeddings API 测试完成！")
print(f"=" * 80)

print(f"\n如果你看到 ✅ 向量化完成，说明 SiliconFlow API 已被调用")
print(f"你可以在 SiliconFlow 控制台查看 API 使用记录")
