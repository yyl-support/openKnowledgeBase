"""
VectorStore: 向量存储封装

基于 ChromaDB，提供项目隔离的向量存储能力
"""

import logging
import os
from typing import List, Optional, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储封装（项目隔离）"""

    def __init__(self, project_name: str, base_dir: str = "vectordb"):
        """
        初始化向量存储

        Args:
            project_name: 项目名称（用于隔离）
            base_dir: 向量库根目录
        """
        self.project_name = project_name
        self.persist_directory = os.path.join(
            base_dir,
            project_name
        )

        # 创建目录
        os.makedirs(self.persist_directory, exist_ok=True)

        # 初始化 Embeddings（SiliconFlow Qwen3-Embedding-8B）
        siliconflow_api_key = os.getenv("SILICONFLOW_API_KEY")
        if not siliconflow_api_key:
            raise ValueError(
                "SILICONFLOW_API_KEY 环境变量未设置，无法初始化向量库。"
                "请先 export SILICONFLOW_API_KEY=<your_key>"
            )

        self.embeddings = OpenAIEmbeddings(
            model="Qwen/Qwen3-Embedding-8B",
            openai_api_key=siliconflow_api_key,
            openai_api_base="https://api.siliconflow.cn/v1"
        )

        # 初始化 Chroma
        self.vectorstore = Chroma(
            collection_name=f"project_{project_name}",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        logger.info(
            f"向量存储初始化完成: {project_name} "
            f"(路径: {self.persist_directory})"
        )

    def add_documents(
        self,
        documents: List[Document],
        metadata_override: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        添加文档到向量库

        Args:
            documents: 文档列表
            metadata_override: 元数据覆盖（会添加到每个文档的 metadata）

        Returns:
            List[str]: 文档 ID 列表
        """
        if not documents:
            logger.warning("没有文档需要添加")
            return []

        # 添加项目隔离标识
        for doc in documents:
            doc.metadata["project"] = self.project_name
            if metadata_override:
                doc.metadata.update(metadata_override)

        logger.info(f"添加 {len(documents)} 个文档到向量库")

        try:
            ids = self.vectorstore.add_documents(documents)
            self.vectorstore.persist()
            logger.info(f"成功添加 {len(ids)} 个文档")
            return ids
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise

    def delete_by_source(self, source: str):
        """
        删除指定来源的文档（用于增量更新）

        Args:
            source: 文档来源（通常是文件路径）
        """
        logger.info(f"删除来源为 {source} 的文档")

        try:
            # Chroma 的删除需要使用 where 条件
            # 注意：这里需要先查询出符合条件的文档 ID
            results = self.vectorstore.get(
                where={"source": source}
            )

            if results and results.get("ids"):
                ids = results["ids"]
                self.vectorstore.delete(ids=ids)
                self.vectorstore.persist()
                logger.info(f"成功删除 {len(ids)} 个文档")
            else:
                logger.info(f"没有找到来源为 {source} 的文档")

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            # 删除失败不应该阻止流程继续
            pass

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量
            filter: 过滤条件

        Returns:
            List[Document]: 相关文档列表
        """
        logger.info(f"执行相似度搜索: query='{query[:50]}...', k={k}")

        try:
            # 确保只搜索当前项目的文档
            if filter is None:
                filter = {}
            filter["project"] = self.project_name

            results = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter
            )

            logger.info(f"找到 {len(results)} 个相关文档")
            return results

        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return []

    def as_retriever(self, **kwargs):
        """
        转换为 LangChain Retriever

        Returns:
            VectorStoreRetriever
        """
        # 确保只检索当前项目的文档
        search_kwargs = kwargs.get("search_kwargs", {})
        if "filter" not in search_kwargs:
            search_kwargs["filter"] = {}
        search_kwargs["filter"]["project"] = self.project_name

        return self.vectorstore.as_retriever(
            search_kwargs=search_kwargs,
            **{k: v for k, v in kwargs.items() if k != "search_kwargs"}
        )

    def clear(self):
        """清空向量库（慎用）"""
        logger.warning(f"清空项目 {self.project_name} 的向量库")

        try:
            # 获取所有文档 ID
            results = self.vectorstore.get()
            if results and results.get("ids"):
                ids = results["ids"]
                self.vectorstore.delete(ids=ids)
                self.vectorstore.persist()
                logger.info(f"成功删除 {len(ids)} 个文档")
            else:
                logger.info("向量库为空，无需清空")

        except Exception as e:
            logger.error(f"清空向量库失败: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        获取向量库统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            results = self.vectorstore.get()
            doc_count = len(results.get("ids", []))

            return {
                "project": self.project_name,
                "document_count": doc_count,
                "persist_directory": self.persist_directory
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "project": self.project_name,
                "document_count": 0,
                "persist_directory": self.persist_directory,
                "error": str(e)
            }
