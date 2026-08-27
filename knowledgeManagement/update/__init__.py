"""
Phase 3: 增量更新层（RAG 系统）

提供基于 RAG 的知识增量更新能力
"""

from .decision_chain import UpdateDecisionChain
from .vector_store import VectorStore
from .update_chain import KnowledgeUpdateChain
from .regeneration_chain import SectionRegenerationChain

__all__ = [
    'UpdateDecisionChain',
    'VectorStore',
    'KnowledgeUpdateChain',
    'SectionRegenerationChain',
]
