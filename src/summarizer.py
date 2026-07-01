from pydantic import BaseModel, Field


class SummaryResult(BaseModel):
    title: str = Field(description="A short title for the summary")
    summary: str = Field(description="The generated summary")


def summarize_text(text: str) -> SummaryResult:
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
    )
