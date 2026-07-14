import argparse

from src.agents.fixed_workflow import (
    run_file_stats_workflow,
)


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description="运行固定文件统计工作流。"
    )

    parser.add_argument(
        "file_path",
        help="要读取的文本文件路径。",
    )

    return parser.parse_args()


def main():
    """程序入口。"""

    args = parse_args()

    result = run_file_stats_workflow(
        file_path=args.file_path,
    )

    print("固定工作流执行完成：")
    print(result)


if __name__ == "__main__":
    main()