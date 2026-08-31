"""
测试 backlog 缓存管理器
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extraction.backlog_cache import BacklogCache


def test_backlog_cache_initialization():
    """测试缓存初始化"""
    cache = BacklogCache()

    assert cache.cache_dir.name == "backlog-cache"
    assert cache.repo_url == "https://github.com/opensourceways/backlog.git"
    assert cache.repo_path == cache.cache_dir / "backlog"


def test_custom_cache_dir():
    """测试自定义缓存目录"""
    custom_dir = "/tmp/custom-backlog-cache"
    cache = BacklogCache(cache_dir=custom_dir)

    assert str(cache.cache_dir) == custom_dir
    assert cache.repo_path == Path(custom_dir) / "backlog"


@pytest.mark.slow
def test_ensure_repo():
    """测试仓库确保存在（慢测试，需要网络）"""
    cache = BacklogCache()

    # 这个测试会实际 clone/pull 仓库，比较慢
    cache.ensure_repo()

    assert cache.repo_path.exists()
    assert (cache.repo_path / ".git").exists()


def test_get_requirement_doc_not_found():
    """测试读取不存在的文档"""
    cache = BacklogCache()

    # 不实际 clone，只测试逻辑
    # 如果仓库不存在，会触发 clone
    # 这里我们只测试一个肯定不存在的 Issue

    # 跳过这个测试，因为它需要实际的仓库
    pytest.skip("需要实际的 backlog 仓库")


def test_list_issue_docs_not_found():
    """测试列出不存在的 Issue 文档"""
    cache = BacklogCache()

    # 跳过这个测试，因为它需要实际的仓库
    pytest.skip("需要实际的 backlog 仓库")


# 集成测试（需要实际网络和仓库）
@pytest.mark.integration
@pytest.mark.slow
def test_get_requirement_doc_real_issue():
    """集成测试：读取真实 Issue 的文档"""
    cache = BacklogCache()
    cache.ensure_repo()

    # 测试一个已知存在的 Issue（需要根据实际情况调整）
    # 这个测试依赖于 Issue #1611 的 PR 是否已合入
    docs = cache.list_issue_docs(1611)

    # 如果 PR 已合入，应该有文档
    # 否则列表为空
    print(f"Found {len(docs)} documents for Issue #1611")
    for doc in docs:
        print(f"  - {doc}")


@pytest.mark.integration
@pytest.mark.slow
def test_read_specification_real_issue():
    """集成测试：读取真实的 Specification.md"""
    cache = BacklogCache()
    cache.ensure_repo()

    # 尝试读取 Issue #1611 的需求文档
    spec = cache.get_requirement_doc(1611, "Specification.md")

    if spec:
        print(f"Specification size: {len(spec)} characters")
        assert len(spec) > 0
        assert "Specification" in spec or "specification" in spec
    else:
        print("Specification not found (PR may not be merged yet)")
