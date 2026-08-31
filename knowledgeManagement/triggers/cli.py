import argparse
import logging
import sys
from orchestration.orchestrator import KnowledgeOrchestrator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="知识工程管理系统 - 手动触发工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 调度所有项目
  python3 cli.py schedule-all

  # 调度单个项目
  python3 cli.py schedule forum-reply-robot

  # 强制更新（忽略轮询间隔）
  python3 cli.py schedule forum-reply-robot --force
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # schedule-all 命令
    subparsers.add_parser(
        "schedule-all",
        help="调度所有项目"
    )

    # schedule 命令
    schedule_parser = subparsers.add_parser(
        "schedule",
        help="调度单个项目"
    )
    schedule_parser.add_argument(
        "project_name",
        help="项目名称"
    )
    schedule_parser.add_argument(
        "--force",
        action="store_true",
        help="强制更新（忽略轮询间隔）"
    )

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # 初始化调度器
        orchestrator = KnowledgeOrchestrator()

        if args.command == "schedule-all":
            logger.info("执行命令: schedule-all")
            results = orchestrator.schedule_all_projects()

            # 打印结果
            print("\n" + "=" * 60)
            print("调度结果")
            print("=" * 60)
            for result in results:
                status = "成功" if result.success else "失败"
                print(
                    f"{status} | {result.project_name} | "
                    f"Issue #{result.issue_number} | "
                    f"耗时 {result.elapsed_seconds:.1f}s | "
                    f"成本 ${result.cost_usd:.2f}"
                )
                if result.error:
                    print(f"  错误: {result.error}")
            print("=" * 60)

        elif args.command == "schedule":
            logger.info(f"执行命令: schedule {args.project_name}")
            result = orchestrator.schedule_project(
                args.project_name,
                force=args.force
            )

            if result:
                status = "成功" if result.success else "失败"
                print(
                    f"\n{status} | {result.project_name} | "
                    f"Issue #{result.issue_number} | "
                    f"耗时 {result.elapsed_seconds:.1f}s | "
                    f"成本 ${result.cost_usd:.2f}"
                )
                if result.error:
                    print(f"错误: {result.error}")
            else:
                print(f"\n项目 {args.project_name} 没有需要更新的内容")

    except Exception as e:
        logger.exception("执行失败")
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
