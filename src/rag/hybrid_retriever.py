from src.rag.chroma_store import get_collection, normalize_source
from src.rag.embedding import embed_texts
from src.rag.keyword_retriever import score_chunk


def get_vector_candidates(
    question,
    source=None,
    candidate_k=10,
    max_distance=None,
):
    """获取向量检索候选结果。"""

    collection = get_collection()

    where_filter = None

    if source:
        where_filter = {"source": normalize_source(source)}

    results = collection.query(
        query_embeddings=embed_texts([question]),
        n_results=candidate_k,
        where=where_filter,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    items = []

    for index, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][index]
        distance = results["distances"][0][index]

        if max_distance is not None and distance > max_distance:
            continue

        items.append(
            {
                "chunk": {
                    "id": results["ids"][0][index],
                    "source": metadata["source"],
                    "start": metadata["start"],
                    "end": metadata["end"],
                    "content": document,
                },
                "distance": distance,
            }
        )

    return items


def get_keyword_candidates(
    question,
    source=None,
    candidate_k=10,
):
    """获取关键词检索候选结果。"""

    collection = get_collection()

    where_filter = None

    if source:
        where_filter = {"source": normalize_source(source)}

    results = collection.get(
        where=where_filter,
        include=[
            "documents",
            "metadatas",
        ],
    )

    items = []

    for index, document in enumerate(results["documents"]):
        metadata = results["metadatas"][index]

        chunk = {
            "id": results["ids"][index],
            "source": metadata["source"],
            "start": metadata["start"],
            "end": metadata["end"],
            "content": document,
        }

        keyword_score = score_chunk(
            question,
            chunk,
        )

        if keyword_score > 0:
            items.append(
                {
                    "chunk": chunk,
                    "keyword_score": keyword_score,
                    "distance": None,
                }
            )

    items.sort(
        key=lambda item: item["keyword_score"],
        reverse=True,
    )

    return items[:candidate_k]


def retrieve_hybrid(
    question,
    source=None,
    top_k=3,
    max_distance=None,
):
    """使用 RRF 算法融合向量检索和关键词检索。"""

    candidate_k = max(top_k * 3, 10)

    vector_items = get_vector_candidates(
        question=question,
        source=source,
        candidate_k=candidate_k,
        max_distance=max_distance,
    )

    keyword_items = get_keyword_candidates(
        question=question,
        source=source,
        candidate_k=candidate_k,
    )

    fused_items = {}

    def add_results(items, result_type):
        """把一种检索结果加入融合结果。"""

        for rank, item in enumerate(items, start=1):
            chunk_id = item["chunk"]["id"]

            if chunk_id not in fused_items:
                fused_items[chunk_id] = {
                    "chunk": item["chunk"],
                    "distance": item.get("distance"),
                    "hybrid_score": 0.0,
                    "vector_rank": None,
                    "keyword_rank": None,
                }

            # Reciprocal Rank Fusion：
            # 排名越靠前，贡献的分数越高。
            fused_items[chunk_id]["hybrid_score"] += 1 / (60 + rank)

            if result_type == "vector":
                fused_items[chunk_id]["vector_rank"] = rank

            if result_type == "keyword":
                fused_items[chunk_id]["keyword_rank"] = rank

    add_results(vector_items, "vector")
    add_results(keyword_items, "keyword")

    results = list(fused_items.values())

    results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )

    return results[:top_k]
