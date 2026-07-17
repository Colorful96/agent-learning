from pathlib import Path

from src.ingestion.document_loader import (
    extract_text,
)
from src.rag.chroma_store import (
    build_vector_index,
    delete_vector_index_by_source,
    normalize_source,
)

UPLOAD_DIR = Path("data/uploads")
ALLOWED_SUFFIXES = {".txt", ".docx", ".pdf"}
MAX_FILE_SIZE = 20 * 1024 * 1024


def save_and_index_document(
    filename: str,
    content: bytes,
) -> dict:
    """保存文档，提取文本，并建立向量索引。"""

    if not filename:
        raise ValueError("文件名不能为空。")

    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("只支持 TXT、DOCX 和 PDF 文件。")

    if not content:
        raise ValueError("上传文件不能为空。")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("文件不能超过 20 MB。")

    # 只保留文件名，避免目录穿越
    safe_filename = Path(filename).name
    target_path = UPLOAD_DIR / safe_filename

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    target_path.write_bytes(content)

    # 根据扩展名解析 TXT、DOCX 或 PDF
    text = extract_text(str(target_path))

    # 使用统一的切片、embedding 和 Chroma 入库流程
    index_result = build_vector_index(
        str(target_path),
        text=text,
    )

    return {
        "filename": safe_filename,
        "source": index_result["source"],
        "chunks_count": index_result["chunks_count"],
    }


def list_uploaded_documents() -> list[dict]:
    """返回已经上传的文档列表。"""

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    documents = []

    for path in sorted(UPLOAD_DIR.iterdir()):
        if not path.is_file():
            continue

        documents.append(
            {
                "filename": path.name,
                "source": normalize_source(str(path)),
                "file_type": path.suffix.lower().lstrip("."),
                "size_bytes": path.stat().st_size,
            }
        )

    return documents


def delete_uploaded_document(filename: str) -> dict:
    """删除原始文件以及对应的 Chroma 向量。"""

    if not filename:
        raise ValueError("文件名不能为空。")

    safe_filename = Path(filename).name

    # 防止通过路径访问其他文件
    if safe_filename != filename:
        raise ValueError("非法文件名。")

    target_path = UPLOAD_DIR / safe_filename

    if not target_path.is_file():
        raise ValueError("文件不存在。")

    removed_chunks = delete_vector_index_by_source(str(target_path))

    target_path.unlink()

    return {
        "filename": safe_filename,
        "removed_chunks": removed_chunks,
    }
