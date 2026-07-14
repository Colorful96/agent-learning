from functools import lru_cache

from sentence_transformers import CrossEncoder

RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"


@lru_cache(maxsize=1)
def get_reranker():
    """加载并缓存重排序模型。"""

    return CrossEncoder(RERANKER_MODEL_NAME)


def rerank(question, candidates, top_k=3):
    """使用 CrossEncoder 对候选 chunk 重新排序。"""

    if not candidates:
        return []

    model = get_reranker()

    pairs = [
        (
            question,
            item["chunk"]["content"],
        )
        for item in candidates
    ]

    scores = model.predict(pairs)

    reranked_items = []

    for item, score in zip(candidates, scores):
        new_item = dict(item)
        new_item["rerank_score"] = float(score)
        reranked_items.append(new_item)

    reranked_items.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return reranked_items[:top_k]
