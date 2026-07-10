def score_chunk(query, chunk):
    """根据问题和 chunk 的字符重合程度计算相关性分数。"""

    query_text = query.lower()
    chunk_text = chunk["content"].lower()

    # 忽略常见标点和空白字符
    ignored_chars = set(" \n\t，。！？；：,.!?;:()（）[]【】\"'")

    query_chars = {char for char in query_text if char not in ignored_chars}

    chunk_chars = set(chunk_text)

    return len(query_chars & chunk_chars)


def retrieve_chunks(query, chunks, top_k=3):
    """从 chunks 中检索和问题最相关的片段。"""

    scored_chunks = []

    for chunk in chunks:
        score = score_chunk(query, chunk)

        if score > 0:
            scored_chunks.append(
                {
                    "score": score,
                    "chunk": chunk,
                }
            )

    # 分数越高，说明越相关
    scored_chunks.sort(key=lambda item: item["score"], reverse=True)

    return scored_chunks[:top_k]
