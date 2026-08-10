#!/usr/bin/env python3
"""
代码知识提取 CLI 工具
整合第一层（Adapter）和第二层（Refiner）
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from adapters import MKAdapter, ZreadAdapter, UAAdapter
from refine import Refiner
from source_selector import select_sources


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 处理环境变量
    refiner_config = config.get('refiner', {})
    api_key = refiner_config.get('api_key', '')
    if api_key.startswith('${') and api_key.endswith('}'):
        env_var = api_key[2:-1]
        refiner_config['api_key'] = os.getenv(env_var, '')

    return config


def derive_project_name(repo_path: str) -> str:
    """
    从 --repo 推导项目名

    本地路径取 basename；Git URL 取仓库名并去掉 .git 后缀
    例如：
      https://github.com/opensourceways/forum-reply-robot.git -> forum-reply-robot
      /tmp/run2/forum-reply-robot/                             -> forum-reply-robot

    Args:
        repo_path: 代码仓路径（本地路径或 Git URL）

    Returns:
        项目名
    """
    normalized = repo_path.rstrip('/')
    name = os.path.basename(normalized)
    if name.endswith('.git'):
        name = name[:-len('.git')]
    return name


def resolve_output_root(config: dict, cli_output_root: Optional[str]) -> str:
    """
    解析输出根目录

    相对路径基于 scripts 目录（本文件所在目录）解析，而不是当前工作目录，
    这样从任意 cwd 调用结果都一致。优先级：--output-root > config.yaml > 默认值。

    Args:
        config: 配置字典
        cli_output_root: 命令行传入的 --output-root（可选）

    Returns:
        输出根目录绝对路径
    """
    if cli_output_root:
        root = cli_output_root
    else:
        output_config = config.get('output', {})
        root = output_config.get('root', '../../output')

    root_path = Path(root)
    if not root_path.is_absolute():
        scripts_dir = Path(__file__).resolve().parent
        root_path = scripts_dir / root_path

    return str(root_path.resolve())


def compute_output_path(output_root: str, project_name: str, tool_name: str,
                        output_type: str, user_output: Optional[str]) -> str:
    """
    计算最终产物文件路径

    未指定 --output 时，按 <output_root>/<项目名>/<工具>/<输出类型>.md 自动生成；
    指定了 --output 则直接使用用户给定路径（保留手动覆盖能力）。

    Args:
        output_root: 输出根目录
        project_name: 项目名
        tool_name: 工具名
        output_type: 输出类型（architecture / quickstart / api-reference）
        user_output: 用户手动指定的 --output（可选）

    Returns:
        输出文件绝对路径
    """
    if user_output:
        return os.path.abspath(user_output)

    output_dir = os.path.join(output_root, project_name, tool_name)
    return os.path.join(output_dir, f"{output_type}.md")


def compute_raw_path(output_root: str, project_name: str, tool_name: str) -> str:
    """
    计算 raw.json 保存路径

    落在 <output_root>/<项目名>/.raw/ 下，文件名带工具名和时间戳，
    避免多次运行相互覆盖。

    Args:
        output_root: 输出根目录
        project_name: 项目名
        tool_name: 工具名

    Returns:
        raw.json 绝对路径
    """
    raw_dir = os.path.join(output_root, project_name, '.raw')
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    return os.path.join(raw_dir, f"{tool_name}-{timestamp}.json")


def create_adapter(adapter_name: str, config: dict):
    """
    创建适配器实例

    Args:
        adapter_name: 适配器名称（mk / zread / ua）
        config: 配置字典

    Returns:
        适配器实例
    """
    adapters_config = config.get('adapters', {})

    if adapter_name == 'mk':
        mk_config = adapters_config.get('mk', {})
        return MKAdapter(
            api_url=mk_config.get('api_url', 'http://localhost:8421'),
            service_name=mk_config.get('service_name', 'trial-svc'),
            team_name=mk_config.get('team_name', 'trial-team'),
            api_prefix=mk_config.get('api_prefix', '/v3')
        )
    elif adapter_name == 'zread':
        return ZreadAdapter()
    elif adapter_name == 'ua':
        ua_config = adapters_config.get('ua', {})
        return UAAdapter(
            data_dir=ua_config.get('data_dir')
        )
    else:
        raise ValueError(f"不支持的适配器: {adapter_name}")


def create_refiner(config: dict) -> Refiner:
    """
    创建 Refiner 实例

    Args:
        config: 配置字典

    Returns:
        Refiner 实例
    """
    refiner_config = config.get('refiner', {})

    return Refiner(
        model=refiner_config.get('model', 'claude-opus-4'),
        base_url=refiner_config.get('base_url'),
        api_key=refiner_config.get('api_key')
    )


def main():
    parser = argparse.ArgumentParser(
        description='代码知识提取工具 - 两层架构：Adapter + Refiner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用 open-zread 提取并生成架构文档（不传 --output，按规则自动落盘到
  # output/<项目名>/zread/architecture.md）
  python extract.py --adapter zread --repo https://github.com/user/repo --output-type architecture

  # 使用 MemoryKnowledge 提取并生成快速开始指南（同样自动计算输出路径）
  python extract.py --adapter mk --repo /path/to/repo --output-type quickstart

  # 手动指定输出路径（覆盖自动计算）
  python extract.py --adapter ua --repo /path/to/repo --output-type api-reference --output api.md

  # 覆盖默认输出根目录
  python extract.py --adapter zread --repo /path/to/repo --output-type architecture --output-root /tmp/my-output

  # 使用自定义配置文件
  python extract.py --adapter ua --repo /path/to/repo --output-type api-reference --config my-config.yaml
        """
    )

    parser.add_argument('--adapter', required=True, choices=['mk', 'zread', 'ua'],
                        help='适配器类型：mk=MemoryKnowledge, zread=open-zread, ua=Understand-Anything')
    parser.add_argument('--repo', required=True,
                        help='代码仓路径（本地路径或 Git URL）')
    parser.add_argument('--output-type', required=True, choices=['architecture', 'quickstart', 'api-reference'],
                        help='输出文档类型')
    parser.add_argument('--output',
                        help='输出文件路径（Markdown 格式）。不传则按 '
                             '<output-root>/<项目名>/<工具>/<输出类型>.md 自动计算')
    parser.add_argument('--output-root',
                        help='输出根目录，覆盖 config.yaml 中的 output.root（默认: ../../output，相对 scripts 目录）')
    parser.add_argument('--config', default='config.yaml',
                        help='配置文件路径（默认: config.yaml）')
    parser.add_argument('--work-dir', default='./work',
                        help='工作目录（三方工具运行时的临时工作目录，与产物输出路径无关，默认: ./work）')
    parser.add_argument('--save-raw', action='store_true',
                        help='保存 Adapter 原始输出到 output/<项目名>/.raw/<工具>-<时间戳>.json')
    parser.add_argument('--source-select', action='store_true',
                        help='仅对 --adapter mk 生效：启用 source_selector 挑选代表性源文件'
                             '（全部 md/py/sh + 分组抽样的 yaml + 目录清单），'
                             '而不是让 MKAdapter 内部扫描整个仓库')
    parser.add_argument('--yaml-sample-per-group', type=int, default=2,
                        help='配合 --source-select：每个 YAML 分组抽样的文件数（默认: 2）')
    parser.add_argument('--yaml-group-depth', type=int, default=2,
                        help='配合 --source-select：YAML 分组时取目录路径的前几级作为分组键（默认: 2）')

    args = parser.parse_args()

    try:
        # 加载配置
        logger.info(f"加载配置文件: {args.config}")
        config = load_config(args.config)

        # 创建工作目录（三方工具运行时的临时工作目录，与产物输出路径无关）
        work_dir = os.path.abspath(args.work_dir)
        os.makedirs(work_dir, exist_ok=True)
        logger.info(f"工作目录: {work_dir}")

        # 解析输出路径规则
        adapter = create_adapter(args.adapter, config)
        tool_name = adapter.get_tool_name()
        project_name = derive_project_name(args.repo)
        output_root = resolve_output_root(config, args.output_root)
        output_path = compute_output_path(output_root, project_name, tool_name,
                                          args.output_type, args.output)
        logger.info(f"项目名: {project_name} | 工具: {tool_name} | 产物路径: {output_path}")

        # 第一层：使用 Adapter 提取知识
        logger.info(f"=== 第一层：使用 {args.adapter} 适配器提取知识 ===")
        if args.source_select:
            if args.adapter != 'mk':
                raise ValueError("--source-select 仅支持 --adapter mk")
            logger.info(
                f"使用 source_selector 挑选源文件（yaml_sample_per_group="
                f"{args.yaml_sample_per_group}, group_depth={args.yaml_group_depth}）"
            )
            source_files = select_sources(
                args.repo,
                yaml_sample_per_group=args.yaml_sample_per_group,
                group_depth=args.yaml_group_depth,
            )
            total_bytes = sum(len(f["content"].encode("utf-8")) for f in source_files)
            logger.info(f"source_selector 选中 {len(source_files)} 个源文件，共 {total_bytes} 字节")
            pages_data = adapter.extract(args.repo, work_dir, source_files=source_files)
        else:
            pages_data = adapter.extract(args.repo, work_dir)

        # 保存原始数据（可选）
        if args.save_raw:
            raw_path = compute_raw_path(output_root, project_name, tool_name)
            os.makedirs(os.path.dirname(raw_path), exist_ok=True)
            with open(raw_path, 'w', encoding='utf-8') as f:
                json.dump(pages_data, f, ensure_ascii=False, indent=2)
            logger.info(f"原始数据已保存: {raw_path}")

        # 第二层：使用 Refiner 二次提炼
        logger.info(f"=== 第二层：使用 Refiner 生成 {args.output_type} 文档 ===")
        refiner = create_refiner(config)
        output_path = refiner.refine(pages_data, args.output_type, output_path)

        logger.info(f"✅ 完成！输出文件: {output_path}")

    except Exception as e:
        logger.error(f"❌ 执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
