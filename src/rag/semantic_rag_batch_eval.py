import json
import re
from pathlib import Path

from src.clients.llm_client import LLMClientError, generate_text
from src.config import load_config
from src.demos.semantic_rag_demo import build_context, build_rag_prompt
from src.rag.hybrid_retriever import retrieve_hybrid
from src.rag.reranker import rerank


def normalize_for_match(text):
    """统一关键词匹配格式，忽略空格和常见标点差异。"""

    if not text:
        return ""

    # 评测关键词时，HTTP 接口和 HTTP接口应该被视为同一种表达。
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？、：；（）()【】\[\]“”‘’'\",.!?:;]", "", text)
    return text.lower()


def has_valid_citation(answer, retrieved_items):
    """检查回答是否同时引用了实际的 chunk ID 和 source。"""

    normalized_answer = normalize_for_match(answer)

    for item in retrieved_items:
        chunk = item["chunk"]
        chunk_id = normalize_for_match(chunk.get("id", ""))
        source = normalize_for_match(chunk.get("source", ""))

        if (
            chunk_id
            and source
            and chunk_id in normalized_answer
            and source in normalized_answer
        ):
            return True

    return False


def load_cases(cases_path="eval_cases/semantic_rag_cases.json"):
    """读取批量评测用例。"""

    path = Path(cases_path)

    if not path.exists():
        raise FileNotFoundError(f"Eval cases file not found: {cases_path}")

    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_answer(answer, retrieved_items, case):
    """根据期望关键词、来源和拒答要求评测单条回答。"""

    score = 10
    notes = []

    expected_keywords = case.get("expected_keywords", [])
    expected_sources = case.get("expected_sources", [])
    should_refuse = case.get("should_refuse", False)

    # 检查回答是否为空
    if not answer:
        score -= 4
        notes.append("Answer is empty")

    normalized_answer = normalize_for_match(answer)

    # 检查期望关键词是否出现在回答中，同时忽略空格和常见标点差异
    for keyword in expected_keywords:
        if normalize_for_match(keyword) not in normalized_answer:
            score -= 1
            notes.append(f"Missing expected keyword: {keyword}")

    # 检查期望来源是否出现在检索结果中
    for expected_source in expected_sources:
        found_source = False

        for item in retrieved_items:
            chunk = item["chunk"]
            source_text = chunk.get("source", "") + " " + chunk.get("id", "")

            if expected_source in source_text:
                found_source = True
                break

        if not found_source:
            score -= 2
            notes.append(f"Missing expected source: {expected_source}")

    # 不应该拒答的问题，如果没有检索到资料，扣分
    if not should_refuse and not retrieved_items:
        score -= 3
        notes.append("This case should answer, but no chunks were retrieved")

    # 可回答问题的回答应该同时包含实际的 chunk ID 和 source。
    # 拒答问题不要求引用，因为拒答可能正是由于资料不足。
    if (
        retrieved_items
        and not should_refuse
        and not has_valid_citation(answer, retrieved_items)
    ):
        score -= 2
        notes.append("Answer does not cite a valid chunk_id and source")

    # 分数不能低于 0
    score = max(score, 0)

    return {
        "score": score,
        "notes": notes,
    }


def run_case(case, config, top_k=3, max_distance=0.9):
    """运行单条语义 RAG 评测用例。"""

    question = case["question"]
    file_path = case.get("file")

    # 第一步：使用混合检索获取更多候选资料
    candidate_items = retrieve_hybrid(
        question=question,
        source=file_path,
        top_k=max(top_k * 3, 10),
        max_distance=max_distance,
    )

    # 第二步：使用 CrossEncoder 对候选资料重新排序
    retrieved_items = rerank(
        question=question,
        candidates=candidate_items,
        top_k=top_k,
    )

    if not retrieved_items:
        answer = "没有检索到足够相关资料。"
    else:
        context = build_context(retrieved_items)
        prompt = build_rag_prompt(question, context)

        try:
            answer = generate_text(
                api_key=config["deepseek_api_key"],
                model=config["deepseek_model"],
                api_base=config["deepseek_api_base"],
                system_prompt=(
                    "你是一个严谨的 RAG 资料问答助手。"
                    "你只能根据用户提供的资料回答问题。"
                    "如果资料不足，不要编造答案。"
                ),
                user_input=prompt,
            )
        except LLMClientError as error:
            answer = "模型调用失败：" + str(error)

    evaluation = evaluate_answer(answer, retrieved_items, case)

    return {
        "id": case.get("id"),
        "question": question,
        "file": file_path,
        "retrieved_count": len(retrieved_items),
        "retrieved_items": retrieved_items,
        "answer": answer,
        "evaluation": evaluation,
    }


def save_report(report, output_path="outputs/semantic_rag_hybrid_rerank_eval.json"):
    """保存批量评测报告。"""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    """程序入口：批量运行语义 RAG 评测用例。"""

    config = load_config()
    cases = load_cases()

    results = []

    for case in cases:
        result = run_case(case, config)
        results.append(result)

        print("Case:", result["id"])
        print("Question:", result["question"])
        print("Score:", result["evaluation"]["score"])
        print("Notes:", result["evaluation"]["notes"])
        print("-" * 40)

    average_score = sum(result["evaluation"]["score"] for result in results) / len(
        results
    )

    report = {
        "average_score": average_score,
        "results": results,
    }

    save_report(report)

    print("Average score:", average_score)
    print("Report saved to: outputs/semantic_rag_hybrid_rerank_eval.json")


if __name__ == "__main__":
    main()
