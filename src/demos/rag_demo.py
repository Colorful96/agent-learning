import argparse

from src.clients.llm_client import generate_text, LLMClientError
from src.config import load_config
from src.rag.chunker import split_text, add_chunk_metadata
from src.rag.keyword_retriever import retrieve_chunks
import json
from pathlib import Path


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="运行一个关键词检索版 RAG demo。")

    parser.add_argument(
        "question",
        help="你想基于资料提出的问题。",
    )

    parser.add_argument(
        "--file",
        default="examples/agent_complex.txt",
        help="要检索的资料文件路径。",
    )

    return parser.parse_args()


def build_context(retrieved_items):
    """把检索到的 chunk 整理成 prompt 上下文。"""

    context_parts = []

    for index, item in enumerate(retrieved_items, start=1):
        chunk = item["chunk"]
        score = item["score"]

        context_parts.append(
            (
                f"[资料 {index}]\n"
                f"chunk_id：{chunk['id']}\n"
                f"source：{chunk['source']}\n"
                f"相关分数：{score}\n"
                f"位置：{chunk['start']} - {chunk['end']}\n"
                f"内容：\n{chunk['content']}"
            )
        )

    return "\n\n".join(context_parts)


def build_rag_prompt(question, context):
    """构造 RAG 用户提示词，把检索资料和问题一起交给模型。"""

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
        "4. 如果资料中没有答案，请只回答：资料中没有足够信息。"
    )


def save_rag_trace(question, file_path, chunks, retrieved_items, answer):
    """保存 RAG 运行过程，方便调试检索质量和回答来源。"""

    trace = {
        "question": question,
        "file": file_path,
        "chunks_count": len(chunks),
        "retrieved_items": retrieved_items,
        "answer": answer,
    }

    output_path = Path("outputs/rag_debug_trace.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(trace, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    """程序入口：读取资料、检索相关片段，并调用模型生成答案。"""

    args = parse_args()
    config = load_config()

    # 读取资料文件
    with open(args.file, "r", encoding="utf-8") as file:
        text = file.read()

    # 把长文本切成多个 chunk
    chunks = split_text(text, chunk_size=300, overlap=50)
    chunks = add_chunk_metadata(chunks, source=args.file)

    # 根据用户问题检索最相关的 chunk
    retrieved_items = retrieve_chunks(args.question, chunks, top_k=3)

    if not retrieved_items:
        print("没有检索到相关资料。")
        return

    # 把检索结果整理成上下文
    context = build_context(retrieved_items)

    print("Retrieved chunks:")
    print(context)
    print("\nAnswer:")

    # 构造 RAG prompt
    prompt = build_rag_prompt(args.question, context)

    # 调用模型生成最终回答
    try:
        # 调用大模型生成最终回答
        answer = generate_text(
            api_key=config["deepseek_api_key"],
            model=config["deepseek_model"],
            api_base=config["deepseek_api_base"],
            system_prompt=(
                "你是一个严谨的资料问答助手。"
                "请只根据给定资料回答问题。"
                "如果资料中没有答案，请直接说：资料中没有足够信息。"
            ),
            user_input=prompt,
        )
    except LLMClientError as error:
        # 模型调用失败时，不让程序崩溃，保留检索结果方便调试
        answer = "模型调用失败：" + str(error)

    save_rag_trace(
        question=args.question,
        file_path=args.file,
        chunks=chunks,
        retrieved_items=retrieved_items,
        answer=answer,
    )

    print(answer)


if __name__ == "__main__":
    main()
