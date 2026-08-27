import yaml
import os
from pathlib import Path
from typing import Dict
from .models import SystemConfig, ProjectConfig


def load_system_config(config_path: str = "config/projects.yaml") -> SystemConfig:
    """
    加载系统配置

    Args:
        config_path: 配置文件路径

    Returns:
        SystemConfig: 系统配置对象

    Raises:
        FileNotFoundError: 配置文件不存在
        ValidationError: 配置验证失败
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_file, 'r', encoding='utf-8') as f:
        raw_config = yaml.safe_load(f)

    # 解析环境变量占位符
    _resolve_env_vars(raw_config)

    # 验证并构造配置对象
    config = SystemConfig(**raw_config)

    return config


def _resolve_env_vars(config: dict):
    """
    递归解析配置中的环境变量占位符 ${VAR_NAME}

    Args:
        config: 配置字典（原地修改）
    """
    for key, value in config.items():
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            config[key] = os.getenv(env_var, '')
        elif isinstance(value, dict):
            _resolve_env_vars(value)


def save_system_config(config: SystemConfig, config_path: str = "config/projects.yaml"):
    """
    保存系统配置（主要用于更新元数据）

    Args:
        config: 系统配置对象
        config_path: 配置文件路径
    """
    config_file = Path(config_path)

    # 转换为字典并写入
    config_dict = config.model_dump(by_alias=True, exclude_none=True)

    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, allow_unicode=True, sort_keys=False)
