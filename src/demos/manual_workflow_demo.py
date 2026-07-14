import argparse

from src.workflows.manual_research_workflow import (
    run_manual_research_workflow,
)


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description="运行节点化研究工作流。",
    )

    parser.add_argument(
        "question",
        help="要研究的问题。",
    )

    parser.add_argument(
        "--output",
        default="outputs/manual_research_report.md",
        help="报告保存路径。",
    )

    return parser.parse_args()


def main():
    """程序入口。"""

    args = parse_args()

    state = run_manual_research_workflow(
        question=args.question,
        output_path=args.output,
    )

    print("工作流状态：")
    print(state.status)

    print("\n执行计划：")
    for index, step in enumerate(state.plan, start=1):
        print(f"{index}. {step}")

    print("\n最终回答：")
    print(state.answer)

    print("\n报告保存到：")
    print(state.report_path)


if __name__ == "__main__":
    main()
