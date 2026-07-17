from pathlib import Path
import json
import logging
from langgraph.graph import END, START, StateGraph
from src.agents.research_roles import (
    fallback_node,
    planner_node,
    plan_validator_node,
    direct_answer_node,
    reader_node,
    retriever_node,
    reviewer_node,
    route_after_plan_validation,
    route_after_retriever,
    route_after_review,
    unsupported_node,
    writer_node,
    query_rewriter_node,
)

from src.agents.research_state import ResearchGraphState


logger = logging.getLogger("agent_workflow")


def find_plan_step_for_node(state, node_name):
    """根据节点角色找到对应的计划步骤。"""

    plan_steps = state.get("plan_steps", [])

    for index, step in enumerate(plan_steps):
        tool_name = step.get("tool_name")
        action = str(step.get("action", ""))
        description = str(step.get("description", ""))
        step_text = action + description

        if node_name == "retriever" and tool_name == "search_knowledge_base":
            return index, step

        if node_name == "writer" and tool_name == "save_markdown_report":
            return index, step

        if node_name == "direct_answer" and tool_name is None:
            return index, step

        if node_name == "reader" and tool_name is None:
            keywords = ("生成", "回答", "总结", "generate", "answer")
            if any(keyword in step_text for keyword in keywords):
                return index, step

        if node_name == "reviewer" and tool_name is None:
            keywords = ("审核", "检查", "review", "evaluate")
            if any(keyword in step_text for keyword in keywords):
                return index, step

    return None


def tracked_node(node_name, node_function):
    """为节点增加当前步骤、已完成步骤和执行轨迹。"""

    def wrapped_node(state):
        execution_trace = list(state.get("execution_trace", []))

        execution_trace.append(
            {
                "event": "node_started",
                "node": node_name,
            }
        )
        logger.info("node_started node=%s", node_name)

        # 执行真正的角色逻辑
        updates = node_function(state)

        plan_progress = find_plan_step_for_node(
            state,
            node_name,
        )

        plan_index = state.get("plan_index", 0)
        current_plan_step = state.get("current_plan_step", "")
        completed_plan_steps = list(state.get("completed_plan_steps", []))

        if plan_progress is not None:
            step_index, plan_step = plan_progress
            step_id = plan_step.get("step_id", f"step-{step_index + 1}")

            plan_index = step_index
            current_plan_step = plan_step.get(
                "description",
                plan_step.get("action", ""),
            )

            if step_id not in completed_plan_steps:
                completed_plan_steps.append(step_id)

        completed_steps = list(state.get("completed_steps", []))

        if node_name not in completed_steps:
            completed_steps.append(node_name)

        execution_trace.append(
            {
                "event": "node_completed",
                "node": node_name,
                "status": updates.get("status"),
            }
        )
        logger.info(
            "node_completed node=%s status=%s",
            node_name,
            updates.get("status"),
        )

        return {
            **updates,
            "current_step": node_name,
            "completed_steps": completed_steps,
            "plan_index": plan_index,
            "current_plan_step": current_plan_step,
            "completed_plan_steps": completed_plan_steps,
            "execution_trace": execution_trace,
        }

    return wrapped_node


def build_research_graph():
    """构建 LangGraph 研究工作流。"""

    builder = StateGraph(ResearchGraphState)

    # 这里只负责注册角色节点，不实现角色内部的业务逻辑
    builder.add_node(
        "planner",
        tracked_node("planner", planner_node),
    )

    builder.add_node(
        "plan_validator",
        tracked_node(
            "plan_validator",
            plan_validator_node,
        ),
    )
    builder.add_node(
        "query_rewriter",
        tracked_node(
            "query_rewriter",
            query_rewriter_node,
        ),
    )
    builder.add_node(
        "retriever",
        tracked_node("retriever", retriever_node),
    )

    builder.add_node(
        "reader",
        tracked_node("reader", reader_node),
    )

    builder.add_node(
        "reviewer",
        tracked_node("reviewer", reviewer_node),
    )

    builder.add_node(
        "fallback",
        tracked_node("fallback", fallback_node),
    )

    builder.add_node(
        "unsupported",
        tracked_node(
            "unsupported",
            unsupported_node,
        ),
    )

    builder.add_node(
        "direct_answer",
        tracked_node("direct_answer", direct_answer_node),
    )

    builder.add_node(
        "writer",
        tracked_node("writer", writer_node),
    )

    # 工作流从 Planner 开始
    builder.add_edge(START, "planner")

    builder.add_edge("planner", "plan_validator")

    builder.add_conditional_edges(
        "plan_validator",
        route_after_plan_validation,
        {
            "query_rewriter": "query_rewriter",
            "direct_answer": "direct_answer",
            "unsupported": "unsupported",
        },
    )
    builder.add_edge(
        "query_rewriter",
        "retriever",
    )

    # Retriever 根据检索结果选择 Reader 或 Fallback
    builder.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {
            "reader": "reader",
            "fallback": "fallback",
        },
    )

    # Reader 生成回答后交给 Reviewer
    builder.add_edge("reader", "reviewer")

    # Reviewer 通过则保存，不通过则返回 Reader 重试
    builder.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "writer": "writer",
            "reader": "reader",
        },
    )

    # 没有资料或任务类型不支持时，都保存说明性结果
    builder.add_edge("fallback", "writer")
    builder.add_edge("unsupported", "writer")
    builder.add_edge("direct_answer", END)
    builder.add_edge("writer", END)

    return builder.compile()


def save_graph_definition(graph):
    """保存 Mermaid 图结构，方便查看和调试。"""

    graph_path = Path("outputs/langgraph_workflow.mmd")
    graph_path.parent.mkdir(parents=True, exist_ok=True)

    graph_path.write_text(
        graph.get_graph().draw_mermaid(),
        encoding="utf-8",
    )

    return graph_path


def run_langgraph_research_workflow(
    question: str,
    output_path: str = "outputs/langgraph_research_report.md",
    conversation_history: list[dict] | None = None,
    source: str | None = None,
):
    """运行多角色研究工作流。"""

    graph = build_research_graph()
    graph_path = save_graph_definition(graph)

    initial_state: ResearchGraphState = {
        "question": question,
        "source": source,
        "workflow_type": "research",
        "skill_name": "literature_research",
        "output_path": output_path,
        "conversation_history": conversation_history or [],
        "status": "started",
        "planned_tools": [],
        "review_count": 0,
        "review_status": "",
        "review_feedback": "",
        "plan_valid": False,
        "plan_error": "",
        "plan_steps": [],
        "plan_index": 0,
        "current_plan_step": "",
        "completed_plan_steps": [],
        "current_step": "",
        "completed_steps": [],
        "execution_trace": [],
    }

    result = graph.invoke(initial_state)
    result["graph_path"] = str(graph_path)
    state_path = save_final_state(result)
    result["state_path"] = str(state_path)
    return result


def save_final_state(result):
    """保存完整的最终状态。"""

    state_path = Path("outputs/langgraph_final_state.json")

    state_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    state_path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return state_path
