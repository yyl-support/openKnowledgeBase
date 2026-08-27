"""配置包

导入本包即加载 .env（见 env.py），因此 config 的任何使用方
都能直接通过 os.getenv 读到密钥。
"""

from . import env  # noqa: F401  仅为触发 .env 加载
from .env import require_env, PROJECT_ROOT

__all__ = ["require_env", "PROJECT_ROOT"]
