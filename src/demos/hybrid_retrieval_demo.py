import argparse

from src.rag.hybrid_retriever import retrieve_hybrid


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="测试混合检索。")

    parser.add_argument(
        "question",
        help="要检索的问题。",
    )

    parser.add_argument(
        "--file",
        default=None,
        help="可选：只检索指定文件。",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="返回的 chunk 数量。",
    )

    return parser.parse_args()


def main():
    """程序入口。"""

    args = parse_args()

    results = retrieve_hybrid(
        question=args.question,
        source=args.file,
        top_k=args.top_k,
    )

    for index, item in enumerate(results, start=1):
        chunk = item["chunk"]

        print(f"[结果 {index}]")
        print("chunk_id:", chunk["id"])
        print("source:", chunk["source"])
        print("hybrid_score:", item["hybrid_score"])
        print("vector_rank:", item["vector_rank"])
        print("keyword_rank:", item["keyword_rank"])
        print("content:")
        print(chunk["content"])
        print("-" * 60)


if __name__ == "__main__":
    main()
