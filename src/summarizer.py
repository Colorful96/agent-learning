from pydantic import BaseModel, Field

from llm_client import generate_text, LLMClientError


class SummaryResult(BaseModel):
    title: str = Field(description="A short title for the summary")
    summary: str = Field(description="The generated summary")
    source: str = Field(description="Where the summary came from")


def summarize_text_locally(text: str) -> SummaryResult:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Text cannot be empty.")

    normalized_text = cleaned_text.replace("\u3002", ".")
    sentences = [item.strip() for item in normalized_text.split(".") if item.strip()]
    short_summary = ". ".join(sentences[:3])

    if len(sentences) > 3:
        short_summary += "."

    return SummaryResult(
        title="Text Summary (Local Rule)",
        summary=short_summary or cleaned_text,
        source="local_rule",
    )


def summarize_text(text: str, config) -> SummaryResult:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Text cannot be empty.")

    system_prompt = (
        "You are a careful study assistant. Summarize the user's text in Chinese. "
        "Requirements: keep the summary within 120 Chinese characters, keep key "
        "information, and do not add information that is not in the original text."
    )

    try:
        summary = generate_text(
            api_key=config["deepseek_api_key"],
            model=config["deepseek_model"],
            api_base=config["deepseek_api_base"],
            system_prompt=system_prompt,
            user_input=cleaned_text,
        )
    except LLMClientError:
        return summarize_text_locally(cleaned_text)

    return SummaryResult(
        title="Text Summary (DeepSeek)",
        summary=summary.strip(),
        source="deepseek_api",
    )
