import argparse

from src.rag.chroma_store import build_vector_index


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="把资料文件构建为 Chroma 向量索引。")

    parser.add_argument(
        "--file",
        required=True,
        help="要构建索引的资料文件路径。",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=300,
        help="每个 chunk 的最大字符数。",
    )

    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="长文本切片时相邻 chunk 的重叠字符数。",
    )

    return parser.parse_args()


def main():
    """程序入口：读取文件，切片，生成 embedding，并写入 Chroma。"""

    args = parse_args()

    # 这一步属于离线索引阶段：资料变化时才需要重新执行。
    result = build_vector_index(
        file_path=args.file,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )

    print("Index built:")
    print(result)


if __name__ == "__main__":
    main()
