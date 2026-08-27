#!/usr/bin/env python3
"""
依赖检查脚本
用途：检查指定 Phase 所需的 Python 依赖是否已安装
"""

import sys
import argparse
from importlib.metadata import version, PackageNotFoundError

# 各 Phase 的依赖清单
PHASE_DEPENDENCIES = {
    1: ["pyyaml", "pydantic"],
    2: ["PyGithub", "requests"],
    3: ["langchain", "langchain-community", "chromadb", "openai"],
    4: ["apscheduler", "python-daemon"],
    5: [],  # Phase 5 无新增依赖
}


def check_package(package_name):
    """
    检查包是否已安装

    Returns:
        tuple: (installed, version_str)
    """
    try:
        ver = version(package_name)
        return True, ver
    except PackageNotFoundError:
        return False, None


def main():
    parser = argparse.ArgumentParser(description="检查 Phase 依赖")
    parser.add_argument("--phase", type=int, required=True, help="Phase 编号 (1-5)")
    args = parser.parse_args()

    phase = args.phase
    if phase not in PHASE_DEPENDENCIES:
        print(f"错误: Phase {phase} 不存在，支持的范围是 1-5")
        return 2

    dependencies = PHASE_DEPENDENCIES[phase]

    if not dependencies:
        print(f"========================================")
        print(f"Phase {phase} 依赖检查")
        print(f"========================================")
        print("✅ 该 Phase 无新增依赖")
        print(f"========================================")
        return 0

    print(f"========================================")
    print(f"Phase {phase} 依赖检查")
    print(f"========================================")

    missing = []
    for pkg in dependencies:
        installed, ver = check_package(pkg)
        if installed:
            print(f"✅ {pkg} (已安装: {ver})")
        else:
            print(f"❌ {pkg} (未安装)")
            missing.append(pkg)

    print()

    if missing:
        print("安装缺失依赖：")
        print(f"  pip3 install {' '.join(missing)} --user")
        print(f"========================================")
        return 1
    else:
        print("所有依赖已安装")
        print(f"========================================")
        return 0


if __name__ == "__main__":
    sys.exit(main())
