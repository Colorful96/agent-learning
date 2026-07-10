import json
from pathlib import Path


def load_trace(trace_path="outputs/semantic_rag_debug_trace.json"):
    """读取语义 RAG 调试轨迹文件。"""

    path = Path(trace_path)

    if not path.exists():
        raise FileNotFoundError(f"Semantic RAG trace file not found: {trace_path}")

    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_semantic_rag_trace(trace):
    """根据简单规则评测一次语义 RAG 运行结果。"""

    score = 10
    notes = []

    question = trace.get("question", "")
    settings = trace.get("settings", {})
    retrieved_items = trace.get("retrieved_items", [])
    answer = trace.get("answer", "")

    max_distance = settings.get("max_distance")

    # 检查问题是否存在
    if not question:
        score -= 2
        notes.append("Question is empty")

    # 检查 settings 是否保存
    if not settings:
        score -= 2
        notes.append("Settings are missing")

    # 检查回答是否为空
    if not answer:
        score -= 4
        notes.append("Answer is empty")

    # 如果检索到了资料，回答应该包含 chunk_id
    if retrieved_items and "chunk" not in answer:
        score -= 2
        notes.append("Answer does not cite chunk_id")

    # 如果检索到了资料，回答应该包含 source
    if retrieved_items and "source" not in answer and "examples" not in answer:
        score -= 1
        notes.append("Answer does not cite source")

    # 如果设置了 max_distance，检查返回结果是否都在阈值内
    if max_distance is not None:
        for item in retrieved_items:
            distance = item.get("distance")

            if distance is not None and distance > max_distance:
                score -= 2
                notes.append("A retrieved chunk is over max_distance")
                break

    # 如果没有检索到资料，回答应该明确说明没有足够相关资料
    if not retrieved_items and "没有检索到足够相关资料" not in answer:
        score -= 2
        notes.append("Empty retrieval should return a clear no-context answer")

    # 分数不能低于 0
    score = max(score, 0)

    return {
        "score": score,
        "notes": notes,
    }


def main():
    """程序入口：读取语义 RAG trace 并输出评测结果。"""

    trace = load_trace()
    result = evaluate_semantic_rag_trace(trace)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
