"""
测试 VectorStore
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from update.vector_store import VectorStore
from langchain.schema import Document


@pytest.fixture
def temp_vector_dir():
    """创建临时向量库目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_vector_store_initialization(temp_vector_dir):
    """测试向量存储初始化"""
    store = VectorStore(
        project_name="test-project",
        base_dir=temp_vector_dir
    )

    assert store.project_name == "test-project"
    assert store.embeddings is not None
    assert store.vectorstore is not None


def test_add_documents(temp_vector_dir):
    """测试添加文档"""
    store = VectorStore(
        project_name="test-project",
        base_dir=temp_vector_dir
    )

    # 创建测试文档
    docs = [
        Document(
            page_content="这是第一个测试文档",
            metadata={"source": "test1.md", "type": "test"}
        ),
        Document(
            page_content="这是第二个测试文档",
            metadata={"source": "test2.md", "type": "test"}
        )
    ]

    # 添加文档
    ids = store.add_documents(docs)

    assert len(ids) == 2

    # 验证文档已添加
    stats = store.get_stats()
    assert stats["document_count"] == 2


def test_similarity_search(temp_vector_dir):
    """测试相似度搜索"""
    store = VectorStore(
        project_name="test-project",
        base_dir=temp_vector_dir
    )

    # 添加测试文档
    docs = [
        Document(
            page_content="Python 是一门编程语言",
            metadata={"source": "python.md"}
        ),
        Document(
            page_content="Java 是一门编程语言",
            metadata={"source": "java.md"}
        ),
        Document(
            page_content="今天天气很好",
            metadata={"source": "weather.md"}
        )
    ]

    store.add_documents(docs)

    # 搜索
    results = store.similarity_search("编程语言", k=2)

    assert len(results) <= 2
    # 前两个结果应该与编程相关
    if len(results) > 0:
        assert "编程" in results[0].page_content or "Python" in results[0].page_content or "Java" in results[0].page_content


def test_delete_by_source(temp_vector_dir):
    """测试按来源删除文档"""
    store = VectorStore(
        project_name="test-project",
        base_dir=temp_vector_dir
    )

    # 添加文档
    docs = [
        Document(
            page_content="文档1内容",
            metadata={"source": "file1.py"}
        ),
        Document(
            page_content="文档2内容",
            metadata={"source": "file2.py"}
        )
    ]

    store.add_documents(docs)

    # 删除 file1.py
    store.delete_by_source("file1.py")

    # 验证只剩 1 个文档
    stats = store.get_stats()
    assert stats["document_count"] == 1


def test_project_isolation(temp_vector_dir):
    """测试项目隔离"""
    store1 = VectorStore(
        project_name="project-a",
        base_dir=temp_vector_dir
    )
    store2 = VectorStore(
        project_name="project-b",
        base_dir=temp_vector_dir
    )

    # 项目 A 添加文档
    docs_a = [
        Document(
            page_content="项目 A 的文档",
            metadata={"source": "a.md"}
        )
    ]
    store1.add_documents(docs_a)

    # 项目 B 添加文档
    docs_b = [
        Document(
            page_content="项目 B 的文档",
            metadata={"source": "b.md"}
        )
    ]
    store2.add_documents(docs_b)

    # 项目 A 搜索，不应该找到项目 B 的文档
    results_a = store1.similarity_search("文档", k=10)
    for doc in results_a:
        assert doc.metadata["project"] == "project-a"

    # 项目 B 搜索，不应该找到项目 A 的文档
    results_b = store2.similarity_search("文档", k=10)
    for doc in results_b:
        assert doc.metadata["project"] == "project-b"


def test_clear(temp_vector_dir):
    """测试清空向量库"""
    store = VectorStore(
        project_name="test-project",
        base_dir=temp_vector_dir
    )

    # 添加文档
    docs = [
        Document(page_content="测试文档", metadata={"source": "test.md"})
    ]
    store.add_documents(docs)

    # 清空
    store.clear()

    # 验证已清空
    stats = store.get_stats()
    assert stats["document_count"] == 0


def test_get_stats(temp_vector_dir):
    """测试获取统计信息"""
    store = VectorStore(
        project_name="test-project",
        base_dir=temp_vector_dir
    )

    stats = store.get_stats()

    assert "project" in stats
    assert "document_count" in stats
    assert "persist_directory" in stats
    assert stats["project"] == "test-project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
