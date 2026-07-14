import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from src.clients.llm_client import generate_text
from src.config import load_config
from src.demos.semantic_rag_demo import build_context, build_rag_prompt
from src.tools.registry import execute_tool


@dataclass
class ResearchWorkflowState:
    """保存研究工作流中各个节点共享的数据。"""

    question: str
    output_path: str

    # 规划节点产生的任务步骤
    plan: list[str] = field(default_factory=list)

    # 检索节点产生的资料
    retrieved_items: list[dict] = field(default_factory=list)

    # Reader 节点产生的回答
    answer: str = ""

    # Writer 节点产生的报告路径
    report_path: str = ""

    # 工作流当前状态
    status: str = "pending"

    # 保存每个节点的运行记录
    trace: list[dict] = field(default_factory=list)


def planner_node(state: ResearchWorkflowState):
    """规划节点：确定研究任务需要经过哪些步骤。"""

    state.plan = [
        "检索知识库",
        "根据资料生成回答",
        "保存 Markdown 报告",
    ]

    state.trace.append(
        {
            "event": "planner_completed",
            "plan": state.plan,
        }
    )

    return state


def retriever_node(state: ResearchWorkflowState):
    """检索节点：根据问题从知识库中查找相关资料。"""

    search_result = execute_tool(
        "search_knowledge_base",
        {
            "question": state.question,
            "top_k": 3,
        },
    )

    state.retrieved_items = search_result.get("items", [])

    state.trace.append(
        {
            "event": "retriever_completed",
            "retrieved_count": len(state.retrieved_items),
        }
    )

    return state


def route_after_retriever(state: ResearchWorkflowState) -> str:
    """根据检索结果选择下一步节点。"""

    if state.retrieved_items:
        return "reader"

    return "fallback"


def fallback_node(state: ResearchWorkflowState):
    """资料不足时执行的备用节点。"""

    state.answer = "当前知识库中没有找到足够相关的资料，" "暂时无法给出可靠回答。"

    state.trace.append(
        {
            "event": "fallback_completed",
            "reason": "没有检索到相关资料",
        }
    )

    return state


def reader_node(state: ResearchWorkflowState, config: dict):
    """阅读节点：把检索结果加入提示词，再调用大模型生成回答。"""

    if not state.retrieved_items:
        state.answer = "资料中没有找到足够的信息。"

        state.trace.append(
            {
                "event": "reader_skipped",
                "reason": "没有检索到资料",
            }
        )

        return state

    # 把检索到的 chunk 拼接成模型可理解的上下文
    context = build_context(state.retrieved_items)

    # 把问题和上下文组合成 RAG 提示词
    prompt = build_rag_prompt(
        state.question,
        context,
    )

    state.answer = generate_text(
        api_key=config["deepseek_api_key"],
        model=config["deepseek_model"],
        api_base=config["deepseek_api_base"],
        system_prompt=(
            "你是一个严谨的科研资料助手。"
            "只能根据提供的资料回答问题。"
            "如果资料不足，不要编造答案。"
        ),
        user_input=prompt,
    )

    state.trace.append(
        {
            "event": "reader_completed",
            "answer_length": len(state.answer),
        }
    )

    return state


def writer_node(state: ResearchWorkflowState):
    """写作节点：把最终回答保存为 Markdown 文件。"""

    state.report_path = execute_tool(
        "save_markdown_report",
        {
            "title": "科研文献调研报告",
            "content": state.answer,
            "output_path": state.output_path,
        },
    )

    state.trace.append(
        {
            "event": "writer_completed",
            "report_path": state.report_path,
        }
    )

    return state


def save_trace(state: ResearchWorkflowState):
    """保存工作流运行轨迹，便于调试。"""

    trace_path = Path("outputs/manual_workflow_trace.json")
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    trace_path.write_text(
        json.dumps(
            {
                "question": state.question,
                "plan": state.plan,
                "status": state.status,
                "trace": state.trace,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def run_manual_research_workflow(
    question: str,
    output_path: str = "outputs/manual_research_report.md",
):
    """按照节点顺序执行研究工作流。"""

    config = load_config()

    state = ResearchWorkflowState(
        question=question,
        output_path=output_path,
        status="running",
    )

    state.trace.append(
        {
            "event": "workflow_started",
            "question": question,
        }
    )

    try:
        # 每个节点处理同一个 state，并返回更新后的 state
        planner_node(state)
        retriever_node(state)
        # 根据当前 state 决定走哪个分支
        next_node = route_after_retriever(state)
        state.trace.append(
            {
                "event": "route_selected",
                "next_node": next_node,
            }
        )

        if next_node == "reader":
            reader_node(state, config)
        elif next_node == "fallback":
            fallback_node(state)

        reader_node(state, config)
        writer_node(state)

        state.status = "completed"

        state.trace.append(
            {
                "event": "workflow_completed",
                "report_path": state.report_path,
            }
        )

        return state

    except Exception as error:
        state.status = "failed"

        state.trace.append(
            {
                "event": "workflow_failed",
                "error": str(error),
            }
        )

        raise

    finally:
        save_trace(state)
