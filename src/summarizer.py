import logging

from pydantic import BaseModel, Field, ValidationError

from llm_client import generate_text, LLMClientError
import json

logger = logging.getLogger(__name__)


class SummaryResult(BaseModel):
    title: str = Field(description="A short title for the summary")
    summary: str = Field(description="The generated summary")
    source: str = Field(description="Where the summary came from")


class StructuredSummary(BaseModel):
    topic: str = Field(description="The main topic of the text")
    summary: str = Field(description="A concise summary")
    keywords: list[str] = Field(description="Important keywords")
    action_items: list[str] = Field(description="Suggested next actions")


class StructuredOutputError(Exception):
    pass


def analyze_text_structured(
    text: str, config, style: str = "default"
) -> StructuredSummary:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Text cannot be empty.")

    system_prompt = build_structured_prompt(style)
    # system_prompt = (
    #     "You are a careful study assistant. Analyze the user's text and return JSON only. "
    #     "The JSON object must contain exactly these fields: "
    #     "topic, summary, keywords, action_items. "
    #     "topic must be a Chinese string. "
    #     "summary must be a Chinese string within 150 Chinese characters. "
    #     "keywords must be a list of strings. "
    #     "action_items must be a list of strings. "
    #     "Do not output markdown. Do not output explanations. Output valid JSON only."
    # )

    raw_output = generate_text(
        api_key=config["deepseek_api_key"],
        model=config["deepseek_model"],
        api_base=config["deepseek_api_base"],
        system_prompt=system_prompt,
        user_input=cleaned_text,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as error:
        logger.error("Invalid JSON from model: %s", raw_output)
        raise StructuredOutputError("Model returned invalid JSON.") from error

    try:
        return StructuredSummary(**data)
    except ValidationError as error:
        logger.error("JSON did not match StructuredSummary: %s", data)
        raise StructuredOutputError(
            "Model returned JSON that does not match StructuredSummary."
        ) from error


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
    except LLMClientError as error:
        logger.warning("DeepSeek API failed, falling back to local rule: %s", error)
        return summarize_text_locally(cleaned_text)

    return SummaryResult(
        title="Text Summary (DeepSeek)",
        summary=summary.strip(),
        source="deepseek_api",
    )


def build_structured_prompt(style: str) -> str:
    """
    根据指定的风格构建结构化的提示词。

    该函数基于一个基础提示词，要求AI助手分析文本并以纯JSON格式返回
    包含主题、摘要、关键词和行动项的结果。根据传入的style参数，
    函数会追加不同的风格指令，以控制输出内容的具体倾向和长度要求。

    Args:
        style (str): 提示词的风格。可选值包括 "concise"（简洁）、
                     "research"（研究导向）、"action"（行动导向）。
                     如果不匹配上述任何值，则返回基础提示词。

    Returns:
        str: 构建完成的完整提示词字符串。
    """
    base_prompt = (
        "You are a careful study assistant. Analyze the user's text and return JSON only. "
        "The JSON object must contain exactly these fields: "
        "topic, summary, keywords, action_items. "
        "topic must be a Chinese string. "
        "summary must be a Chinese string. "
        "keywords must be a list of strings. "
        "action_items must be a list of strings. "
        "Do not output markdown. Do not output explanations. Output valid JSON only. "
    )
    example_json = """
        Example output:

        {
        "topic": "智能体开发基础",
        "summary": "这段文本说明智能体开发不仅是调用大模型，还需要掌握工程结构、工具调用、检索、评测和部署。",
        "keywords": ["智能体开发", "工程结构", "工具调用", "检索", "评测"],
        "action_items": ["整理项目结构", "练习工具调用", "设计简单评测集"]
        }
        """

    if style == "concise":
        return (
            base_prompt
            + "Use a concise style. Summary must be within 80 Chinese characters. "
            + "Keywords should contain 3 to 5 items. "
            + "Action items should contain 1 to 3 short items."
        )

    if style == "research":
        return (
            base_prompt
            + example_json
            + "Use a research-oriented style. Focus on concepts, methods, limitations, "
            + "and possible study directions. Keywords should be academic and precise. "
            + "Action items should help a graduate student continue studying this topic."
        )

    if style == "action":
        return (
            base_prompt
            + "Use an action-oriented style. Focus on what the learner should do next. "
            + "The summary should be practical. Action items should be specific, executable, "
            + "and ordered from easy to hard."
        )

    return base_prompt
