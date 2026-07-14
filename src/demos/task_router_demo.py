import argparse

from src.agents.fixed_workflow import (
    run_file_stats_workflow,
)
from src.agents.research_workflow import (
    run_research_workflow,
)
from src.agents.router import route_task


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="根据任务选择固定工作流。")

    parser.add_argument(
        "task",
        help="用户任务。",
    )

    parser.add_argument(
        "--file",
        default=None,
        help="文件统计任务对应的文件路径。",
    )

    return parser.parse_args()


def main():
    """程序入口。"""

    args = parse_args()
    workflow_name = route_task(args.task)

    print("Selected workflow:", workflow_name)

    if workflow_name == "file_stats":
        if not args.file:
            raise ValueError("文件统计任务必须通过 --file 指定文件路径。")

        result = run_file_stats_workflow(
            file_path=args.file,
        )

        print("文件统计结果：")
        print(result)
        return

    if workflow_name == "research":
        result = run_research_workflow(
            question=args.task,
        )

        print("研究回答：")
        print(result["answer"])
        print("报告路径：")
        print(result["report_path"])
        return

    print("暂时不支持该任务类型。")


if __name__ == "__main__":
    main()
