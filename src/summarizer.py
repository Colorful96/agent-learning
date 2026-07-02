from pydantic import BaseModel, Field

from openai_client import generate_text, OpenAIClientError


class SummaryResult(BaseModel):
    title: str = Field(description="A short title for the summary")
    summary: str = Field(description="The generated summary")
    source: str = Field(description="Where the summary came from")


def summarize_text_locally(text: str) -> SummaryResult:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Text cannot be empty.")

    sentences = [item.strip() for item in cleaned_text.replace("。", ".").split(".") if item.strip()]
    short_summary = ". ".join(sentences[:3])

    if len(sentences) > 3:
        short_summary += "."

    return SummaryResult(
        title="文本摘要",
        summary=short_summary or cleaned_text,
        source="local_rule",
    )


def summarize_text(text: str, config) -> SummaryResult:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Text cannot be empty.")

    instructions = (
        "你是一个严谨的学习助手。请用中文总结用户输入的文本，"
        "要求：1. 摘要不超过 120 字；2. 保留关键信息；"
        "3. 不添加原文没有的信息。"
    )

    try:
        summary = generate_text(
            api_key=config["openai_api_key"],
            model=config["openai_model"],
            api_base=config["openai_api_base"],
            instructions=instructions,
            user_input=cleaned_text,
        )
    except OpenAIClientError:
        local_result = summarize_text_locally(cleaned_text)
        local_result.title = "文本摘要（本地规则）"
        return local_result

    return SummaryResult(
        title="文本摘要（大模型生成）",
        summary=summary.strip(),
        source="openai_api",
    )
