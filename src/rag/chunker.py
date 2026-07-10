def split_long_text(text, chunk_size=300, overlap=50):
    """当单个段落太长时，按字符切分，并保留一定重叠。"""

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append(chunk_text)

        # 下一个片段保留 overlap 个字符，减少上下文断裂
        start = end - overlap

        # 防止 overlap 设置不合理导致死循环
        if start <= 0:
            start = end

    return chunks


def split_text(text, chunk_size=300, overlap=50):
    """优先按段落切分文本，必要时再按字符切分长段落。"""

    chunks = []
    current_text = ""
    current_start = 0
    search_start = 0

    # 按空行切分段落
    paragraphs = [
        paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()
    ]

    for paragraph in paragraphs:
        paragraph_start = text.find(paragraph, search_start)
        paragraph_end = paragraph_start + len(paragraph)
        search_start = paragraph_end

        # 如果单个段落已经超过 chunk_size，就单独切分
        if len(paragraph) > chunk_size:
            if current_text:
                chunks.append(
                    {
                        "content": current_text.strip(),
                        "start": current_start,
                        "end": current_start + len(current_text),
                    }
                )
                current_text = ""

            long_chunks = split_long_text(
                paragraph,
                chunk_size=chunk_size,
                overlap=overlap,
            )

            local_start = paragraph_start

            for long_chunk in long_chunks:
                chunks.append(
                    {
                        "content": long_chunk,
                        "start": local_start,
                        "end": local_start + len(long_chunk),
                    }
                )

                # 这里用 len(long_chunk) - overlap 估算下一个片段起点
                local_start = local_start + len(long_chunk) - overlap

            continue

        # 如果当前 chunk 加上这个段落不会太长，就合并
        candidate = paragraph if not current_text else current_text + "\n\n" + paragraph

        if len(candidate) <= chunk_size:
            if not current_text:
                current_start = paragraph_start

            current_text = candidate
        else:
            # 当前 chunk 已经装不下新段落，先保存当前 chunk
            chunks.append(
                {
                    "content": current_text.strip(),
                    "start": current_start,
                    "end": current_start + len(current_text),
                }
            )

            # 开启一个新的 chunk
            current_text = paragraph
            current_start = paragraph_start

    # 保存最后一个 chunk
    if current_text:
        chunks.append(
            {
                "content": current_text.strip(),
                "start": current_start,
                "end": current_start + len(current_text),
            }
        )

    return chunks


def add_chunk_metadata(chunks, source):
    """给 chunk 增加编号和来源信息。"""

    enriched_chunks = []

    for index, chunk in enumerate(chunks, start=1):
        enriched_chunk = {
            "id": f"chunk-{index}",
            "source": source,
            "content": chunk["content"],
            "start": chunk["start"],
            "end": chunk["end"],
        }

        enriched_chunks.append(enriched_chunk)

    return enriched_chunks
