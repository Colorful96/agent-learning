from typing import TypedDict


class ResearchGraphState(TypedDict, total=False):
    """研究工作流中所有角色共享的状态。"""

    question: str
    source: str | None
    workflow_type: str
    skill_name: str
    conversation_history: list[dict]
    output_path: str
    plan: list[str]
    retrieved_items: list[dict]
    answer: str
    report_path: str
    status: str

    # 审核相关状态
    review_count: int
    review_status: str
    review_feedback: str

    plan_valid: bool
    plan_error: str

    planned_tools: list[str]
    current_step: str
    completed_steps: list[str]
    execution_trace: list[dict]

    plan_steps: list[dict]
    plan_index: int
    current_plan_step: str
    completed_plan_steps: list[str]

    retrieval_question: str
