"""RAG 上下文和提示词构建。"""


def build_context(retrieved_items: list[dict]) -> str:
    """把检索结果整理成模型可以阅读的上下文。"""

    context_parts = []

    for index, item in enumerate(retrieved_items, start=1):
        chunk = item["chunk"]
        distance = item.get("distance")

        context_parts.append(
            (
                f"[资料 {index}]\n"
                f"chunk_id：{chunk['id']}\n"
                f"source：{chunk['source']}\n"
                f"distance：{distance}\n"
                f"位置：{chunk['start']} - {chunk['end']}\n"
                f"内容：\n{chunk['content']}"
            )
        )

    return "\n\n".join(context_parts)


def build_rag_prompt(question: str, context: str) -> str:
    """构建要求模型基于检索资料回答的 RAG Prompt。"""

    return (
        "资料如下：\n"
        f"{context}\n\n"
        "问题：\n"
        f"{question}\n\n"
        "请用中文回答。\n"
        "回答要求：\n"
        "1. 先直接给出结论。\n"
        "2. 再用自己的话简要说明依据，不要大段复制原文。\n"
        "3. 最后用“来源：chunk_id, source”的格式列出依据来源。\n"
        "4. 如果资料中没有答案，只回答：资料中没有足够信息。"
    )
