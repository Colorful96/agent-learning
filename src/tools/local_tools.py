from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = (PROJECT_ROOT / "examples").resolve()
UPLOADS_DIR = (PROJECT_ROOT / "data" / "uploads").resolve()
OUTPUTS_DIR = (PROJECT_ROOT / "outputs").resolve()
MAX_REPORT_CONTENT_SIZE = 500_000


def _resolve_allowed_path(path: str, allowed_root: Path) -> Path:
    """解析路径，并确保它位于指定目录内。"""

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate

    resolved = candidate.resolve()
    if resolved != allowed_root and allowed_root not in resolved.parents:
        raise ValueError(f"路径不在允许的目录内：{path}")

    return resolved


def read_text_file(path: str) -> str:
    file_path = None
    for allowed_root in (EXAMPLES_DIR, UPLOADS_DIR):
        try:
            file_path = _resolve_allowed_path(path, allowed_root)
            break
        except ValueError:
            continue

    if file_path is None:
        raise ValueError("只能读取 examples 或 data/uploads 中的文件")

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
    if len(content) > MAX_REPORT_CONTENT_SIZE:
        raise ValueError("报告内容不能超过 500000 个字符")

    path = _resolve_allowed_path(output_path, OUTPUTS_DIR)
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
