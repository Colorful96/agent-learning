import argparse

from src.agents.research_workflow import (
    run_research_workflow,
)


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="运行固定式文献调研工作流。")

    parser.add_argument(
        "question",
        help="要研究的问题。",
    )

    parser.add_argument(
        "--output",
        default="outputs/research_report.md",
        help="Markdown 报告保存路径。",
    )

    return parser.parse_args()


def main():
    """程序入口。"""

    args = parse_args()

    result = run_research_workflow(
        question=args.question,
        output_path=args.output,
    )

    print("\n研究回答：")
    print(result["answer"])

    print("\n报告已保存到：")
    print(result["report_path"])


if __name__ == "__main__":
    main()
