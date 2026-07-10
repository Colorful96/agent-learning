from collections import Counter

from src.rag.chroma_store import get_collection


def main():
    """列出 Chroma 知识库中已经入库的资料来源。"""

    collection = get_collection()

    # 获取 collection 中保存的所有 metadata
    result = collection.get(include=["metadatas"])

    metadatas = result.get("metadatas", [])

    source_counter = Counter()

    for metadata in metadatas:
        source = metadata.get("source", "unknown")
        source_counter[source] += 1

    print(f"Total chunks: {len(metadatas)}")
    print("\nSources:")

    if not source_counter:
        print("- No sources found")
        return

    for source, count in source_counter.items():
        print(f"- {source}: {count} chunks")


if __name__ == "__main__":
    main()
