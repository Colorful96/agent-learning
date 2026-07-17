from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDefinition:
    """描述一个可复用的 Agent 能力。"""

    name: str
    description: str
    workflow_type: str
    report_title: str
    system_prompt: str


SKILLS = {
    "literature_research": SkillDefinition(
        name="literature_research",
        description="基于本地论文、笔记和其他资料进行检索式研究。",
        workflow_type="research",
        report_title="科研文献调研报告",
        system_prompt=(
            "你是一名严谨的科研文献阅读助手。"
            "只能根据提供的资料回答问题。"
            "回答必须包含结论、依据和来源。"
            "资料不足时要明确说明，不要编造内容。"
        ),
    ),
    "direct_qa": SkillDefinition(
        name="direct_qa",
        description="回答不需要检索本地资料的常规问题。",
        workflow_type="direct_answer",
        report_title="直接问答",
        system_prompt=(
            "你是一名简洁、准确的智能助手。"
            "当前问题不需要检索本地知识库。"
            "如果缺少必要上下文，请明确说明不确定性。"
        ),
    ),
}


def get_skill(name: str | None) -> SkillDefinition:
    """获取 Skill，不认识的名称统一回退到文献研究 Skill。"""

    return SKILLS.get(name or "literature_research", SKILLS["literature_research"])
