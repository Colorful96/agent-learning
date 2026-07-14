import argparse

from src.workflows.langgraph_research_workflow import (
    run_langgraph_research_workflow,
)


def main():
    """程序入口。"""

    parser = argparse.ArgumentParser(
        description="运行 LangGraph 研究工作流。",
    )

    parser.add_argument(
        "question",
        help="要研究的问题。",
    )

    parser.add_argument(
        "--output",
        default="outputs/langgraph_research_report.md",
        help="报告保存路径。",
    )

    args = parser.parse_args()

    result = run_langgraph_research_workflow(
        question=args.question,
        output_path=args.output,
    )

    print("\nPlanner 生成的计划：")

    for index, step in enumerate(result.get("plan", []), start=1):
        print(f"{index}. {step}")

    print("\n当前步骤：")
    print(result.get("current_step"))

    print("\n已完成步骤：")
    print(result.get("completed_steps"))

    print("\n最终状态文件：")
    print(result.get("state_path"))

    print("工作流状态：")
    print(result.get("status"))

    print("\n最终回答：")
    print(result.get("answer"))

    print("\n报告保存到：")
    print(result.get("report_path"))

    print("\n审核次数：")
    print(result.get("review_count", 0))

    print("\n图结构文件：")
    print(result.get("graph_path"))


if __name__ == "__main__":
    main()
