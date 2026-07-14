from pathlib import Path


def read_text_file(path: str) -> str:
    file_path = Path(path)

    if not file_path.exists():
        raise ValueError(f"File does not exist: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return file_path.read_text(encoding="utf-8")


def count_text_stats(text: str) -> dict:
    cleaned_text = text.strip()

    return {
        "characters": len(cleaned_text),
        "lines": len(cleaned_text.splitlines()),
        "words": len(cleaned_text.split()),
    }


def save_markdown_report(title: str, content: str, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    markdown = f"# {title}\n\n{content}\n"
    path.write_text(markdown, encoding="utf-8")

    return str(path)


def search_knowledge_base(
    question: str,
    top_k: int = 3,
    source: str | None = None,
) -> dict:
    """从本地知识库检索和问题相关的资料。"""

    # 延迟导入，避免程序启动时立即加载重排序模型
    from src.rag.hybrid_retriever import retrieve_hybrid
    from src.rag.reranker import rerank

    # 先使用混合检索获取较多候选资料
    candidates = retrieve_hybrid(
        question=question,
        source=source,
        top_k=max(top_k * 3, 10),
        max_distance=0.9,
    )

    # 再使用重排序模型选出最相关的资料
    retrieved_items = rerank(
        question=question,
        candidates=candidates,
        top_k=top_k,
    )

    return {
        "question": question,
        "count": len(retrieved_items),
        "items": retrieved_items,
    }
