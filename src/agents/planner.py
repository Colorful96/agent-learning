import json
from typing import Literal

from pydantic import BaseModel

from src.clients.llm_client import generate_text

# 只允许模型规划使用这些工具
ALLOWED_TOOLS = {
    "read_text_file",
    "count_text_stats",
    "search_knowledge_base",
    "save_markdown_report",
}
TOOL_DESCRIPTIONS = {
    "read_text_file": "读取本地文本文件",
    "count_text_stats": "统计文本信息",
    "search_knowledge_base": "检索本地知识库",
    "save_markdown_report": "保存 Markdown 报告",
}


class PlanStep(BaseModel):
    """表示计划中的一个步骤。"""

    step_id: str
    action: str
    tool_name: str | None = None
    description: str


class TaskPlan(BaseModel):
    """表示大模型生成的完整任务计划。"""

    goal: str
    workflow_type: Literal["research", "direct_answer"] = "research"
    skill_name: Literal["literature_research", "direct_qa"] = "literature_research"
    steps: list[PlanStep]


def validate_plan(plan):
    """校验计划长度和工具名称。"""

    if not plan.steps:
        raise ValueError("计划至少需要包含一个步骤。")

    if len(plan.steps) > 5:
        raise ValueError("计划步骤不能超过 5 步。")

    if plan.workflow_type == "direct_answer":
        if any(step.tool_name for step in plan.steps):
            raise ValueError("direct_answer 不应该包含工具调用。")

    for step in plan.steps:
        if step.tool_name is not None:
            if step.tool_name not in ALLOWED_TOOLS:
                raise ValueError(f"计划使用了未注册的工具：{step.tool_name}")

    return plan


def build_plan_with_llm(
    config,
    task,
    allowed_tools=None,
):
    """让大模型根据用户任务生成结构化计划。"""

    if allowed_tools is None:
        allowed_tools = ALLOWED_TOOLS

    unknown_tools = set(allowed_tools) - ALLOWED_TOOLS

    if unknown_tools:
        raise ValueError(f"发现未注册的工具：{unknown_tools}")

    tool_descriptions = "\n".join(
        f"- {name}：{TOOL_DESCRIPTIONS[name]}" for name in sorted(allowed_tools)
    )

    system_prompt = "".join(
        [
            "你是一个任务规划器。",
            "你的工作是把用户任务拆分成清晰、可执行的步骤。",
            "只能使用允许的工具。",
            "不要执行工具，只生成计划。",
            "必须返回 JSON，不要返回 Markdown。",
            "\n\n允许使用的工具：\n",
            tool_descriptions,
            "\n\nJSON 格式必须是：",
            "\n{",
            '\n  "goal": "任务目标",',
            '\n  "workflow_type": "research 或 direct_answer",',
            '\n  "skill_name": "literature_research 或 direct_qa",',
            '\n  "steps": [',
            "\n    {",
            '\n      "step_id": "step-1",',
            '\n      "action": "工具调用或生成回答",',
            '\n      "tool_name": "工具名称或 null",',
            '\n      "description": "这一步要做什么"',
            "\n    }",
            "\n  ]",
            "\n}",
        ]
    )

    raw_output = generate_text(
        api_key=config["deepseek_api_key"],
        model=config["deepseek_model"],
        api_base=config["deepseek_api_base"],
        system_prompt=system_prompt,
        user_input=task,
        response_format={
            "type": "json_object",
        },
    )

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as error:
        raise ValueError("规划器返回的内容不是合法 JSON。") from error

    plan = TaskPlan.model_validate(data)
    for step in plan.steps:
        if step.tool_name is not None:
            if step.tool_name not in allowed_tools:
                raise ValueError(f"当前 Workflow 不允许使用工具：" f"{step.tool_name}")

    return validate_plan(plan)
