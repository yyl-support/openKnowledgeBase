"""
测试 KnowledgeUpdateChain
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from update.update_chain import KnowledgeUpdateChain, CodeSplitter
from extraction.models import (
    IssueKnowledgePackage,
    RequirementDoc,
    CodeChange,
    PRReference
)


@pytest.fixture
def temp_vector_dir():
    """创建临时向量库目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_code_splitter():
    """测试代码分块器"""
    splitter = CodeSplitter(chunk_size=100, chunk_overlap=20)

    code = """
class MyClass:
    def method1(self):
        pass

def function1():
    pass

def function2():
    pass
"""

    chunks = splitter.split_text(code)
    assert len(chunks) > 0


def test_update_chain_initialization(temp_vector_dir):
    """测试更新链初始化"""
    chain = KnowledgeUpdateChain(project_name="test-project")

    assert chain.project_name == "test-project"
    assert chain.vector_store is not None
    assert chain.code_splitter is not None
    assert chain.doc_splitter is not None


def test_update_from_issue(temp_vector_dir):
    """测试从 Issue 增量更新"""
    chain = KnowledgeUpdateChain(project_name="test-project")

    # 构造测试数据
    package = IssueKnowledgePackage(
        issue_number=1750,
        issue_title="测试 Issue",
        issue_labels=["test"],
        issue_body="测试描述",
        requirement=RequirementDoc(
            specification="这是需求分析文档的内容",
            qa_checklist="这是 QA 检查清单",
            pr=PRReference(repo="test/repo", number=1, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/1")
        ),
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=2, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/2"),
            diff="test diff",
            files=[
                {
                    "filename": "src/main.py",
                    "patch": "def main():\n    print('hello')",
                    "additions": 2,
                    "deletions": 0
                }
            ],
            total_additions=2,
            total_deletions=0
        )
    )

    # 执行更新
    result = chain.update_from_issue(package)

    assert result["success"] is True
    assert result["issue_number"] == 1750
    assert result["documents_added"] > 0
    assert result["chunks_created"] > 0


def test_process_requirement_doc(temp_vector_dir):
    """测试处理需求文档"""
    chain = KnowledgeUpdateChain(project_name="test-project")

    package = IssueKnowledgePackage(
        issue_number=1751,
        issue_title="测试",
        issue_labels=["test"],
        issue_body="测试",
        requirement=RequirementDoc(
            specification="这是一个测试需求文档" * 100,  # 足够长以触发分块
            qa_checklist="QA 检查清单",
            pr=PRReference(repo="test/repo", number=1, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/1")
        ),
        code_change=None
    )

    docs = chain._process_requirement_doc(package)

    assert len(docs) > 0
    for doc in docs:
        assert doc.metadata["type"] in ["requirement_specification", "requirement_qa"]
        assert doc.metadata["issue_number"] == 1751


def test_process_code_changes(temp_vector_dir):
    """测试处理代码变更"""
    chain = KnowledgeUpdateChain(project_name="test-project")

    package = IssueKnowledgePackage(
        issue_number=1752,
        issue_title="测试",
        issue_labels=["test"],
        issue_body="测试",
        requirement=None,
        code_change=CodeChange(
            pr=PRReference(repo="test/repo", number=2, title="测试 PR", state="MERGED", url="https://github.com/test/repo/pull/2"),
            diff="test diff",
            files=[
                {
                    "filename": "src/test.py",
                    "patch": "def test():\n    pass\n" * 50,  # 足够长以触发分块
                    "additions": 50,
                    "deletions": 0
                }
            ],
            total_additions=50,
            total_deletions=0
        )
    )

    docs = chain._process_code_changes(package)

    assert len(docs) > 0
    for doc in docs:
        assert doc.metadata["type"] == "code_change"
        assert doc.metadata["issue_number"] == 1752
        assert doc.metadata["file_path"] == "src/test.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
