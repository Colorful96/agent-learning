import hashlib
from pathlib import Path

import chromadb

from src.rag.chunker import split_text
from src.rag.embedding import embed_texts


def normalize_source(file_path):
    """把文件路径统一成适合保存和检索的格式。"""

    return Path(file_path).as_posix()


def make_chunk_id(source, start, end):
    """根据来源和位置生成稳定的 chunk id。"""

    raw_text = f"{source}:{start}:{end}"
    digest = hashlib.md5(raw_text.encode("utf-8")).hexdigest()[:8]
    return f"{Path(source).stem}-{start}-{end}-{digest}"


def get_collection(persist_dir="data/chroma", collection_name="agent-rag-notes"):
    """获取 Chroma collection；不存在就创建。"""

    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_or_create_collection(name=collection_name)


def build_vector_index(
    file_path,
    chunk_size=300,
    overlap=50,
    text=None,
):
    """读取文件，切片，向量化，并写入 Chroma。"""

    source = normalize_source(file_path)
    # TXT 可以直接读取，DOCX 和 PDF 使用外部解析结果
    if text is None:
        text = Path(file_path).read_text(
            encoding="utf-8",
        )

    chunks = split_text(text, chunk_size=chunk_size, overlap=overlap)

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        chunk_id = make_chunk_id(source, chunk["start"], chunk["end"])

        ids.append(chunk_id)
        documents.append(chunk["content"])
        metadatas.append(
            {
                "source": source,
                "start": chunk["start"],
                "end": chunk["end"],
            }
        )

    embeddings = embed_texts(documents)

    collection = get_collection()

    # upsert 表示：id 不存在就新增，id 已存在就更新
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return {
        "source": source,
        "chunks_count": len(chunks),
    }


def query_vector_index(question, source=None, top_k=3, max_distance=None):
    """把问题向量化，然后从 Chroma 中检索最相关的 chunk。"""

    collection = get_collection()
    query_embedding = embed_texts([question])

    where_filter = None
    if source:
        where_filter = {"source": normalize_source(source)}

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    retrieved_items = []

    for index, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][index]
        distance = results["distances"][0][index]
        chunk_id = results["ids"][0][index]
        # distance 越小，说明问题和 chunk 越相似；超过阈值就丢弃
        if max_distance is not None and distance > max_distance:
            continue

        retrieved_items.append(
            {
                "distance": distance,
                "chunk": {
                    "id": chunk_id,
                    "source": metadata["source"],
                    "start": metadata["start"],
                    "end": metadata["end"],
                    "content": document,
                },
            }
        )

    return retrieved_items


def delete_vector_index_by_source(source: str) -> int:
    """删除指定来源对应的所有向量切片。"""

    collection = get_collection()
    normalized_source = normalize_source(source)

    result = collection.get(
        where={
            "source": normalized_source,
        }
    )

    ids = result.get("ids", [])

    if ids:
        collection.delete(ids=ids)

    return len(ids)
