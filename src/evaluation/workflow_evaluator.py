"""对 LangGraph 工作流的最终状态进行轻量工程评测。"""

import json
from pathlib import Path


def evaluate_workflow_result(
    result: dict,
    expected_workflow_type: str | None = None,
) -> dict:
    """检查分支、节点、轨迹和回答是否满足基本要求。"""

    score = 10
    notes = []
    completed_steps = set(result.get("completed_steps", []))
    trace = result.get("execution_trace", [])
    workflow_type = result.get("workflow_type", "research")

    if expected_workflow_type and workflow_type != expected_workflow_type:
        score -= 3
        notes.append(
            f"Expected workflow type {expected_workflow_type}, got {workflow_type}"
        )

    if not result.get("answer", "").strip():
        score -= 3
        notes.append("Answer is empty")

    if not trace:
        score -= 2
        notes.append("Execution trace is empty")

    if workflow_type == "direct_answer":
        if "retriever" in completed_steps:
            score -= 2
            notes.append("direct_answer should not run retriever")
    else:
        required_nodes = {"planner", "plan_validator", "writer"}
        missing_nodes = required_nodes - completed_steps
        if missing_nodes:
            score -= 1
            notes.append(f"Missing workflow nodes: {sorted(missing_nodes)}")

    return {
        "score": max(score, 0),
        "notes": notes,
        "workflow_type": workflow_type,
    }


def evaluate_state_file(
    path: str = "outputs/langgraph_final_state.json",
) -> dict:
    """读取最终状态文件并生成评测结果。"""

    state_path = Path(path)
    result = json.loads(state_path.read_text(encoding="utf-8"))
    evaluation = evaluate_workflow_result(result)

    report_path = Path("outputs/workflow_evaluation.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return evaluation


if __name__ == "__main__":
    print(json.dumps(evaluate_state_file(), ensure_ascii=False, indent=2))
