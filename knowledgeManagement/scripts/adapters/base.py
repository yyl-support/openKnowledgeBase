"""
BaseAdapter 抽象基类
定义知识提取适配器的统一接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List
from datetime import datetime


class BaseAdapter(ABC):
    """知识提取适配器抽象基类"""

    @abstractmethod
    def extract(self, repo_path: str, output_dir: str) -> Dict:
        """
        从代码仓提取知识

        Args:
            repo_path: 代码仓路径（本地路径或 URL）
            output_dir: 工作目录，用于存储中间文件

        Returns:
            {
                "pages": [
                    {
                        "title": str,           # 页面标题
                        "content": str,         # 页面内容（Markdown格式）
                        "metadata": dict,       # 元数据（sources, tags, type等）
                        "path": str            # 原始文件路径（如果有）
                    }
                ],
                "tool": "mk" | "zread" | "ua",  # 工具名称
                "timestamp": str,                # 提取时间戳
                "repo": str                      # 仓库路径
            }
        """
        pass

    def get_tool_name(self) -> str:
        """返回适配器对应的工具名称"""
        raise NotImplementedError
