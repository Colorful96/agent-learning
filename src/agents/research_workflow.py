import json
from pathlib import Path

from src.agents.state import AgentState
from src.clients.llm_client import generate_text
from src.config import load_config
from src.rag.prompt_builder import (
    build_context,
    build_rag_prompt,
)
from src.tools.registry import execute_tool


def save_trace(events, trace_path):
    """保存固定研究工作流的运行轨迹。"""

    path = Path(trace_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            events,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def run_step_with_retry(
    step_name,
    action,
    state,
    trace_events,
    max_attempts=2,
):
    """执行一个工作流步骤，失败后进行有限重试。"""

    for attempt in range(1, max_attempts + 1):
        state.current_step = step_name

        trace_events.append(
            {
                "event": "step_started",
                "step": step_name,
                "attempt": attempt,
                "state": state.to_dict(),
            }
        )

        try:
            result = action()

            trace_events.append(
                {
                    "event": "step_succeeded",
                    "step": step_name,
                    "attempt": attempt,
                    "state": state.to_dict(),
                }
            )

            return result

        except Exception as error:
            state.fail()

            trace_events.append(
                {
                    "event": "step_failed",
                    "step": step_name,
                    "attempt": attempt,
                    "error": str(error),
                    "state": state.to_dict(),
                }
            )

            # 还没有达到最大尝试次数，继续重试
            if attempt < max_attempts:
                continue

            # 达到最大次数后，把错误交给外层处理
            raise


def run_research_workflow(
    question,
    output_path="outputs/research_report.md",
    trace_path="outputs/research_workflow_trace.json",
):
    """执行固定式文献调研工作流。"""

    config = load_config()

    # state = AgentState(task=f"完成文献调研：{question}")
    state = AgentState(
        task=f"完成文献调研：{question}",
        workflow_name="research",
    )

    state.plan = [
        "调用工具：search_knowledge_base",
        "生成研究回答",
        "调用工具：save_markdown_report",
    ]

    state.start()

    trace_events = [
        {
            "event": "workflow_started",
            "state": state.to_dict(),
        }
    ]

    try:
        # 第一步：检索知识库
        state.current_step = "调用工具：search_knowledge_base"

        search_result = run_step_with_retry(
            step_name="调用工具：search_knowledge_base",
            action=lambda: execute_tool(
                "search_knowledge_base",
                {
                    "question": question,
                    "top_k": 3,
                },
            ),
            state=state,
            trace_events=trace_events,
        )

        retrieved_items = search_result["items"]

        state.complete_step("调用工具：search_knowledge_base")

        trace_events.append(
            {
                "event": "search_completed",
                "retrieved_count": len(retrieved_items),
                "state": state.to_dict(),
            }
        )

        # 第二步：根据检索资料生成回答
        state.current_step = "生成研究回答"

        if retrieved_items:
            context = build_context(retrieved_items)
            prompt = build_rag_prompt(
                question,
                context,
            )

            answer = run_step_with_retry(
                step_name="生成研究回答",
                action=lambda: generate_text(
                    api_key=config["deepseek_api_key"],
                    model=config["deepseek_model"],
                    api_base=config["deepseek_api_base"],
                    system_prompt=(
                        "你是一个严谨的科研资料助手。"
                        "只能根据提供的资料回答。"
                        "如果资料不足，不要编造。"
                    ),
                    user_input=prompt,
                ),
                state=state,
                trace_events=trace_events,
            )
        else:
            answer = "资料中没有足够信息。"

        state.complete_step("生成研究回答")

        trace_events.append(
            {
                "event": "answer_generated",
                "state": state.to_dict(),
            }
        )

        # 第三步：保存 Markdown 报告
        state.current_step = "调用工具：save_markdown_report"

        report_path = run_step_with_retry(
            step_name="调用工具：save_markdown_report",
            action=lambda: execute_tool(
                "save_markdown_report",
                {
                    "title": "科研文献调研报告",
                    "content": answer,
                    "output_path": output_path,
                },
            ),
            state=state,
            trace_events=trace_events,
        )

        state.complete_step("调用工具：save_markdown_report")

        state.finish(answer)

        trace_events.append(
            {
                "event": "workflow_finished",
                "report_path": report_path,
                "state": state.to_dict(),
            }
        )

        return {
            "answer": answer,
            "report_path": report_path,
        }

    except Exception as error:
        # state.fail()
        state.status = "failed"

        trace_events.append(
            {
                "event": "workflow_failed",
                "error": str(error),
                "state": state.to_dict(),
            }
        )

        raise

    finally:
        save_trace(
            trace_events,
            trace_path,
        )
