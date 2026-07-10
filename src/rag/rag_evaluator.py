import json
from pathlib import Path


def load_trace(trace_path="outputs/rag_debug_trace.json"):
    """读取 RAG 调试轨迹文件。"""

    path = Path(trace_path)

    if not path.exists():
        raise FileNotFoundError(f"RAG trace file not found: {trace_path}")

    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_rag_trace(trace):
    """根据简单规则评测一次 RAG 运行结果。"""

    score = 10
    notes = []

    question = trace.get("question", "")
    retrieved_items = trace.get("retrieved_items", [])
    answer = trace.get("answer", "")

    # 检查是否有用户问题
    if not question:
        score -= 2
        notes.append("Question is empty")

    # 检查是否检索到资料
    if not retrieved_items:
        score -= 4
        notes.append("No chunks were retrieved")

    # 检查回答是否为空
    if not answer:
        score -= 4
        notes.append("Answer is empty")

    # 如果检索到了资料，回答中应该包含来源引用
    if retrieved_items and "chunk-" not in answer:
        score -= 2
        notes.append("Answer does not cite chunk_id")

    # 如果检索到了资料，回答中应该包含 source
    if retrieved_items and "source" not in answer and "examples" not in answer:
        score -= 1
        notes.append("Answer does not cite source")

    # 如果回答说资料不足，但实际检索到了资料，给一个提醒
    if retrieved_items and "资料中没有足够信息" in answer:
        notes.append(
            "Answer refused despite retrieved chunks; check retrieval relevance"
        )

    # 分数不能低于 0
    score = max(score, 0)

    return {
        "score": score,
        "notes": notes,
    }


def main():
    """程序入口：读取 RAG trace 并输出评测结果。"""

    trace = load_trace()
    result = evaluate_rag_trace(trace)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
