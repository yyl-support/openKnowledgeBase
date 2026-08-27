"""
环境变量加载

在项目根目录的 .env 中集中管理密钥，避免散落在 shell profile 或源码里。
导入本模块即完成加载，重复导入不会重复读文件（dotenv 自身幂等）。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录（config/ 的上一层）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加载 .env；override=False 表示已存在的环境变量优先，
# 这样 CI 或临时 export 能覆盖 .env 里的值
load_dotenv(PROJECT_ROOT / ".env", override=False)


def require_env(name: str, hint: str = "") -> str:
    """
    读取必需的环境变量，缺失时抛出带指引的异常

    Args:
        name: 环境变量名
        hint: 补充说明（如该变量用于哪个服务）

    Returns:
        str: 变量值

    Raises:
        ValueError: 变量未设置或为空
    """
    value = os.getenv(name)
    if not value:
        msg = f"环境变量 {name} 未设置"
        if hint:
            msg += f"（{hint}）"
        msg += f"。请在 {PROJECT_ROOT / '.env'} 中配置，参考 .env.example"
        raise ValueError(msg)
    return value
