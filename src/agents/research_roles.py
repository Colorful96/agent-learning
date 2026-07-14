from src.agents.research_state import ResearchGraphState
from src.clients.llm_client import generate_text
from src.config import load_config
from src.demos.semantic_rag_demo import (
    build_context,
    build_rag_prompt,
)
from src.tools.registry import execute_tool
from src.agents.planner import build_plan_with_llm
import json

from pydantic import BaseModel


class ReviewDecision(BaseModel):
    """Reviewer Agent 返回的结构化结果。"""

    approved: bool
    feedback: str = ""


def planner_node(state: ResearchGraphState):
    """Planner：根据用户问题生成结构化任务计划。"""

    config = load_config()

    # 调用大模型生成任务计划
    task_plan = build_plan_with_llm(
        config=config,
        task=(
            f"用户问题：{state['question']}\n"
            "这是一个科研文献研究工作流。"
            "计划必须包含 search_knowledge_base，"
            "并且必须包含 save_markdown_report。"
        ),
        allowed_tools={
            "search_knowledge_base",
            "save_markdown_report",
        },
    )

    plan_text = []

    for step in task_plan.steps:
        tool_name = step.tool_name or "model"

        plan_text.append(
            (
                f"{step.step_id}: "
                f"{step.action} | "
                f"执行者：{tool_name} | "
                f"{step.description}"
            )
        )

    planned_tools = [
        step.tool_name for step in task_plan.steps if step.tool_name is not None
    ]

    plan_steps = [step.model_dump() for step in task_plan.steps]

    return {
        "plan": plan_text,
        "plan_steps": plan_steps,
        "plan_index": 0,
        "current_plan_step": (
            plan_steps[0].get("description", "") if plan_steps else ""
        ),
        "completed_plan_steps": [],
        "planned_tools": planned_tools,
        "status": "planning_completed",
    }


SUPPORTED_RESEARCH_TOOLS = {
    "search_knowledge_base",
    "save_markdown_report",
}

REQUIRED_RESEARCH_TOOLS = {
    "search_knowledge_base",
    "save_markdown_report",
}


def plan_validator_node(state: ResearchGraphState):
    """校验 Planner 生成的计划是否适合当前研究 Workflow。"""

    planned_tools = set(state.get("planned_tools", []))

    unsupported_tools = planned_tools - SUPPORTED_RESEARCH_TOOLS

    errors = []

    if unsupported_tools:
        errors.append(f"当前 Workflow 不支持工具：{unsupported_tools}")

    missing_tools = REQUIRED_RESEARCH_TOOLS - planned_tools

    if missing_tools:
        errors.append(f"研究任务计划中缺少必要工具：{missing_tools}")

    if errors:
        return {
            "plan_valid": False,
            "plan_error": "；".join(errors),
            "status": "plan_validation_failed",
        }

    return {
        "plan_valid": True,
        "plan_error": "",
        "status": "plan_validation_passed",
    }


def route_after_plan_validation(state: ResearchGraphState):
    """根据计划校验结果选择执行分支。"""

    if state.get("plan_valid") is True:
        return "retriever"

    return "unsupported"


def unsupported_node(state: ResearchGraphState):
    """计划无法执行时返回说明。"""

    plan_error = state.get(
        "plan_error",
        "计划不符合当前 Workflow 的执行要求。",
    )

    return {
        "answer": (
            "当前任务计划无法由本研究 Workflow 执行。\n\n" f"原因：{plan_error}"
        ),
        "status": "unsupported_task",
    }


def retriever_node(state: ResearchGraphState):
    """Retriever：从知识库中检索相关资料。"""

    result = execute_tool(
        "search_knowledge_base",
        {
            "question": state["question"],
            "top_k": 3,
        },
    )

    return {
        "retrieved_items": result.get("items", []),
        "status": "retrieval_completed",
    }


def route_after_retriever(state: ResearchGraphState):
    """根据检索结果选择 Reader 或 Fallback。"""

    if state.get("retrieved_items"):
        return "reader"

    return "fallback"


def reader_node(state: ResearchGraphState):
    """Reader：阅读资料并生成研究回答。"""

    config = load_config()
    context = build_context(state["retrieved_items"])

    prompt = build_rag_prompt(
        state["question"],
        context,
    )

    # 如果上一次审核失败，将反馈加入本轮提示词
    review_feedback = state.get("review_feedback", "")

    if review_feedback:
        prompt += (
            "\n\n上一轮审核意见：\n"
            f"{review_feedback}\n"
            "请根据审核意见重新生成回答。"
        )

    answer = generate_text(
        api_key=config["deepseek_api_key"],
        model=config["deepseek_model"],
        api_base=config["deepseek_api_base"],
        system_prompt=(
            "你是一个严谨的科研资料阅读助手。"
            "只能根据提供的资料回答问题。"
            "回答必须包含结论、依据和来源。"
            "如果资料不足，不要编造答案。"
        ),
        user_input=prompt,
    )

    return {
        "answer": answer,
        "status": "reader_completed",
    }


def reviewer_node(state: ResearchGraphState):
    """Reviewer Agent：使用大模型审核回答质量。"""

    config = load_config()

    answer = state.get("answer", "")
    context = build_context(state.get("retrieved_items", []))

    review_prompt = (
        "请审核下面的科研问答结果。\n\n"
        f"用户问题：\n{state['question']}\n\n"
        f"参考资料：\n{context}\n\n"
        f"模型回答：\n{answer}\n\n"
        "请检查以下内容：\n"
        "1. 是否真正回答了用户问题。\n"
        "2. 是否基于参考资料回答。\n"
        "3. 是否包含结论、依据和来源。\n"
        "4. 如果不合格，请给出具体修改意见。\n\n"
        "必须只返回 JSON：\n"
        "{\n"
        '  "approved": true,\n'
        '  "feedback": ""\n'
        "}\n"
    )

    raw_output = generate_text(
        api_key=config["deepseek_api_key"],
        model=config["deepseek_model"],
        api_base=config["deepseek_api_base"],
        system_prompt=("你是一个严格的科研回答审核助手。" "只能返回合法 JSON。"),
        user_input=review_prompt,
        response_format={
            "type": "json_object",
        },
    )

    try:
        decision = ReviewDecision.model_validate(json.loads(raw_output))
    except Exception as error:
        raise ValueError(f"Reviewer 返回格式错误：{error}") from error

    review_count = state.get("review_count", 0) + 1

    if decision.approved:
        review_status = "approved"
        review_feedback = ""
    else:
        review_status = "needs_revision"
        review_feedback = decision.feedback

    return {
        "review_count": review_count,
        "review_status": review_status,
        "review_feedback": review_feedback,
        "status": "review_completed",
    }


def route_after_review(state: ResearchGraphState):
    """根据审核结果选择 Writer 或重新进入 Reader。"""

    if state.get("review_status") == "approved":
        return "writer"

    # 防止 Reader 和 Reviewer 无限循环
    if state.get("review_count", 0) >= 2:
        return "writer"

    return "reader"


def fallback_node(state: ResearchGraphState):
    """资料不足时生成备用回答。"""

    return {
        "answer": ("当前知识库中没有找到足够相关的资料，" "暂时无法给出可靠回答。"),
        "status": "fallback_completed",
    }


def writer_node(state: ResearchGraphState):
    """Writer：把最终回答保存成 Markdown 报告。"""

    report_path = execute_tool(
        "save_markdown_report",
        {
            "title": "科研文献调研报告",
            "content": state["answer"],
            "output_path": state["output_path"],
        },
    )

    return {
        "report_path": report_path,
        "status": "writer_completed",
    }
