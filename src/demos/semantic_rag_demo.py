import argparse
import json
from pathlib import Path

from src.clients.llm_client import LLMClientError, generate_text
from src.config import load_config

# from src.rag.chroma_store import query_vector_index
from src.rag.hybrid_retriever import retrieve_hybrid
from src.rag.reranker import rerank


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="运行语义检索版 RAG demo。")

    parser.add_argument(
        "question",
        help="你想基于资料提出的问题。",
    )

    parser.add_argument(
        "--file",
        default=None,
        help="可选：只在指定资料文件中检索；不传则检索整个知识库。",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="检索最相关的 chunk 数量。",
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=0.9,
        help="最大距离阈值；distance 越小越相关，超过阈值的 chunk 会被过滤。",
    )
    return parser.parse_args()


def build_context(retrieved_items):
    """把向量检索结果整理成模型可读的上下文。"""

    context_parts = []

    for index, item in enumerate(retrieved_items, start=1):
        chunk = item["chunk"]
        distance = item["distance"]

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


def build_rag_prompt(question, context):
    """构造 RAG 提示词，让模型基于检索资料回答。"""

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


def save_semantic_rag_trace(
    question,
    file_path,
    settings,
    index_result,
    retrieved_items,
    answer,
):
    """保存语义 RAG 的运行记录，方便后续调试。"""

    trace = {
        "question": question,
        "file": file_path,
        "index_result": index_result,
        "retrieved_items": retrieved_items,
        "answer": answer,
        "settings": settings,
    }

    output_path = Path("outputs/semantic_rag_debug_trace.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(trace, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    """程序入口：从已有向量索引中检索资料，并生成答案。"""

    args = parse_args()
    config = load_config()

    # 这里属于在线问答阶段：直接使用已经构建好的 Chroma 索引。
    candidate_items = retrieve_hybrid(
        question=args.question,
        source=args.file,
        top_k=max(args.top_k * 3, 10),
        max_distance=args.max_distance,
    )

    retrieved_items = rerank(
        question=args.question,
        candidates=candidate_items,
        top_k=args.top_k,
    )

    if not retrieved_items:
        answer = "没有检索到足够相关资料。"

        save_semantic_rag_trace(
            question=args.question,
            file_path=args.file,
            settings={
                "top_k": args.top_k,
                "max_distance": args.max_distance,
            },
            index_result=None,
            retrieved_items=[],
            answer=answer,
        )

        print(answer)
        return

    context = build_context(retrieved_items)

    print("\nRetrieved chunks:")
    print(context)
    print("\nAnswer:")

    # 第三步：把检索结果交给大模型生成答案
    prompt = build_rag_prompt(args.question, context)

    try:
        # 检索已经完成，这一步只负责让大模型基于检索资料生成回答。
        answer = generate_text(
            api_key=config["deepseek_api_key"],
            model=config["deepseek_model"],
            api_base=config["deepseek_api_base"],
            system_prompt=(
                "你是一个严谨的 RAG 资料问答助手。"
                "你只能根据用户提供的资料回答问题。"
                "如果资料不足，不要编造答案。"
            ),
            user_input=prompt,
        )
    except LLMClientError as error:
        # 模型调用失败时保留检索结果，方便判断问题出在检索还是生成阶段。
        answer = "模型调用失败：" + str(error)

    save_semantic_rag_trace(
        question=args.question,
        file_path=args.file,
        settings={
            "top_k": args.top_k,
            "max_distance": args.max_distance,
        },
        index_result=None,
        retrieved_items=retrieved_items,
        answer=answer,
    )

    print(answer)


if __name__ == "__main__":
    main()
