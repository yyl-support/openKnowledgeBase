"""
KnowledgeUpdateChain: 知识增量更新链

处理文档分块、向量化、增量更新向量库
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from .vector_store import VectorStore

# 导入 Phase 2 的数据模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from extraction.models import IssueKnowledgePackage

logger = logging.getLogger(__name__)


class CodeSplitter(RecursiveCharacterTextSplitter):
    """针对代码优化的文本分块器"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化代码分块器

        Args:
            chunk_size: 块大小（字符数）
            chunk_overlap: 块重叠大小（字符数）
        """
        # 按代码结构分块：类 > 函数 > 段落 > 行
        separators = [
            '\nclass ',      # Python 类定义
            '\ndef ',        # Python 函数定义
            '\n\n',          # 段落
            '\n',            # 行
            ' ',             # 词
        ]

        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            keep_separator=True
        )


class KnowledgeUpdateChain:
    """知识增量更新链"""

    def __init__(self, project_name: str):
        """
        初始化更新链

        Args:
            project_name: 项目名称
        """
        self.project_name = project_name

        # 初始化向量存储
        self.vector_store = VectorStore(project_name)

        # 初始化文本分块器
        self.code_splitter = CodeSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        self.doc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=['\n## ', '\n### ', '\n\n', '\n', ' ']
        )

        logger.info(f"知识更新链初始化完成: {project_name}")

    def update_from_issue(
        self,
        knowledge_package: IssueKnowledgePackage
    ) -> Dict[str, Any]:
        """
        从 Issue 知识包增量更新向量库

        Args:
            knowledge_package: Issue 知识包

        Returns:
            Dict[str, Any]: 更新结果
        """
        logger.info(
            f"开始增量更新 Issue #{knowledge_package.issue_number}"
        )

        result = {
            "issue_number": knowledge_package.issue_number,
            "documents_added": 0,
            "documents_deleted": 0,
            "chunks_created": 0,
            "success": True,
            # status 区分三态：updated（真的写入了）/ no_changes（空操作）/ failed
            # success 字段保留，语义不变，避免破坏现有调用方
            "status": "no_changes",
            "error": None
        }

        try:
            # 1. 处理需求分析文档
            if knowledge_package.requirement:
                logger.info("处理需求分析文档...")
                req_docs = self._process_requirement_doc(knowledge_package)
                if req_docs:
                    result["chunks_created"] += len(req_docs)
                    self.vector_store.add_documents(
                        req_docs,
                        metadata_override={
                            "issue_number": knowledge_package.issue_number,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    result["documents_added"] += len(req_docs)

            # 2. 处理代码变更
            if knowledge_package.code_change:
                logger.info("处理代码变更...")
                code_docs = self._process_code_changes(knowledge_package)
                if code_docs:
                    result["chunks_created"] += len(code_docs)

                    # 删除旧版本的代码文档
                    for file_info in knowledge_package.code_change.files:
                        file_path = file_info.get("path") or file_info.get("filename", "")
                        if file_path:
                            self.vector_store.delete_by_source(file_path)
                            result["documents_deleted"] += 1

                    # 添加新版本
                    self.vector_store.add_documents(
                        code_docs,
                        metadata_override={
                            "issue_number": knowledge_package.issue_number,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    result["documents_added"] += len(code_docs)

            # 真的写入了文档才算 updated，否则维持 no_changes
            result["status"] = (
                "updated" if result["documents_added"] > 0 else "no_changes"
            )

            if result["status"] == "no_changes":
                logger.info("增量更新：无可写入内容（空操作）")

            logger.info(
                f"增量更新完成: "
                f"状态={result['status']}, "
                f"添加={result['documents_added']}, "
                f"删除={result['documents_deleted']}, "
                f"分块={result['chunks_created']}"
            )

            return result

        except Exception as e:
            logger.error(f"增量更新失败: {e}")
            result["success"] = False
            result["status"] = "failed"
            result["error"] = str(e)
            return result

    def _process_requirement_doc(
        self,
        knowledge_package: IssueKnowledgePackage
    ) -> List[Document]:
        """
        处理需求分析文档

        Args:
            knowledge_package: Issue 知识包

        Returns:
            List[Document]: 文档块列表
        """
        if not knowledge_package.requirement:
            return []

        documents = []

        # 处理 Specification
        if knowledge_package.requirement.specification:
            spec_text = knowledge_package.requirement.specification

            # 分块
            chunks = self.doc_splitter.split_text(spec_text)

            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": f"issue_{knowledge_package.issue_number}_specification",
                        "type": "requirement_specification",
                        "issue_number": knowledge_package.issue_number,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc)

        # 处理 QA Checklist
        if knowledge_package.requirement.qa_checklist:
            qa_text = knowledge_package.requirement.qa_checklist

            # QA 通常较短，可能不需要分块
            if len(qa_text) > 1000:
                chunks = self.doc_splitter.split_text(qa_text)
            else:
                chunks = [qa_text]

            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": f"issue_{knowledge_package.issue_number}_qa",
                        "type": "requirement_qa",
                        "issue_number": knowledge_package.issue_number,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc)

        logger.info(f"需求文档分块: {len(documents)} 个 chunks")
        return documents

    def _process_code_changes(
        self,
        knowledge_package: IssueKnowledgePackage
    ) -> List[Document]:
        """
        处理代码变更

        Args:
            knowledge_package: Issue 知识包

        Returns:
            List[Document]: 文档块列表
        """
        if not knowledge_package.code_change:
            return []

        documents = []

        # 处理每个变更文件
        for file_info in knowledge_package.code_change.files:
            file_path = file_info.get("path") or file_info.get("filename", "")
            patch = file_info.get("patch", "")

            if not patch:
                continue

            # 使用代码分块器
            chunks = self.code_splitter.split_text(patch)

            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": file_path,
                        "type": "code_change",
                        "issue_number": knowledge_package.issue_number,
                        "file_path": file_path,
                        "additions": file_info.get("additions", 0),
                        "deletions": file_info.get("deletions", 0),
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc)

        logger.info(f"代码变更分块: {len(documents)} 个 chunks")
        return documents

    def vectorize_all(self, knowledge_base_dir: str) -> Dict[str, Any]:
        """
        全量向量化知识库（用于全量更新后）

        Args:
            knowledge_base_dir: 知识库目录路径

        Returns:
            Dict[str, Any]: 向量化结果
        """
        logger.info(f"开始全量向量化: {knowledge_base_dir}")

        result = {
            "documents_processed": 0,
            "chunks_created": 0,
            "success": True,
            "error": None
        }

        try:
            import os

            # 清空现有向量库
            self.vector_store.clear()

            # 遍历知识库目录
            documents = []
            for root, dirs, files in os.walk(knowledge_base_dir):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)

                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            # 分块
                            chunks = self.doc_splitter.split_text(content)

                            for i, chunk in enumerate(chunks):
                                doc = Document(
                                    page_content=chunk,
                                    metadata={
                                        "source": file_path,
                                        "type": "knowledge_doc",
                                        "file_name": file,
                                        "chunk_index": i,
                                        "total_chunks": len(chunks)
                                    }
                                )
                                documents.append(doc)

                            result["documents_processed"] += 1
                            result["chunks_created"] += len(chunks)

                        except Exception as e:
                            logger.warning(f"读取文件失败 {file_path}: {e}")
                            continue

            # 批量添加到向量库
            if documents:
                self.vector_store.add_documents(
                    documents,
                    metadata_override={
                        "timestamp": datetime.now().isoformat()
                    }
                )

            logger.info(
                f"全量向量化完成: "
                f"文档={result['documents_processed']}, "
                f"分块={result['chunks_created']}"
            )

            return result

        except Exception as e:
            logger.error(f"全量向量化失败: {e}")
            result["success"] = False
            result["error"] = str(e)
            return result
