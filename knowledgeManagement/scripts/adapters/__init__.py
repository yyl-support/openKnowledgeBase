"""
Adapters package
提供多种知识提取工具的统一适配器接口
"""
from .base import BaseAdapter
from .mk_adapter import MKAdapter
from .zread_adapter import ZreadAdapter
from .ua_adapter import UAAdapter

__all__ = ['BaseAdapter', 'MKAdapter', 'ZreadAdapter', 'UAAdapter']
