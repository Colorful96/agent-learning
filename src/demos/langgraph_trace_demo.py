import argparse
import json

from src.agents.research_state import ResearchGraphState
from src.workflows.langgraph_research_workflow import (
    build_research_graph,
)


def main():
    """逐节点查看 LangGraph 的运行过程。"""

    parser = argparse.ArgumentParser(
        description="查看 LangGraph 节点执行过程。",
    )

    parser.add_argument(
        "question",
        help="要研究的问题。",
    )

    args = parser.parse_args()

    graph = build_research_graph()

    initial_state: ResearchGraphState = {
        "question": args.question,
        "output_path": "outputs/trace_research_report.md",
        "status": "started",
        "planned_tools": [],
        "plan_valid": False,
        "plan_error": "",
        "review_count": 0,
        "review_status": "",
        "review_feedback": "",
    }

    print("开始执行 Graph...\n")

    # updates 模式会返回每个节点产生的状态更新
    for update in graph.stream(
        initial_state,
        stream_mode="updates",
    ):
        for node_name, node_update in update.items():
            print(f"节点：{node_name}")
            print(
                json.dumps(
                    node_update,
                    ensure_ascii=False,
                    indent=2,
                )
            )
            print("-" * 50)


if __name__ == "__main__":
    main()
