import json
from pathlib import Path

from src.agents.state import AgentState
from src.tools.registry import execute_tool


def save_workflow_trace(events, trace_path):
    """保存固定工作流的运行轨迹。"""

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


def run_file_stats_workflow(
    file_path,
    trace_path="outputs/fixed_workflow_trace.json",
):
    """按固定顺序读取文件并统计文本信息。"""

    # state = AgentState(task=f"读取并统计文件：{file_path}")
    state = AgentState(
        task=f"读取并统计文件：{file_path}",
        workflow_name="file_stats",
    )

    state.plan = [
        "调用工具：read_text_file",
        "调用工具：count_text_stats",
        "生成最终结果",
    ]

    state.start()

    trace_events = [
        {
            "event": "workflow_started",
            "state": state.to_dict(),
        }
    ]

    try:
        # 第一步：固定调用文件读取工具
        state.current_step = "调用工具：read_text_file"

        trace_events.append(
            {
                "event": "step_started",
                "step": state.current_step,
                "state": state.to_dict(),
            }
        )

        text = execute_tool(
            "read_text_file",
            {"path": file_path},
        )

        state.complete_step("调用工具：read_text_file")

        trace_events.append(
            {
                "event": "step_completed",
                "step": "调用工具：read_text_file",
                "state": state.to_dict(),
            }
        )

        # 第二步：固定调用文本统计工具
        state.current_step = "调用工具：count_text_stats"

        trace_events.append(
            {
                "event": "step_started",
                "step": state.current_step,
                "state": state.to_dict(),
            }
        )

        stats = execute_tool(
            "count_text_stats",
            {"text": text},
        )

        state.complete_step("调用工具：count_text_stats")

        trace_events.append(
            {
                "event": "step_completed",
                "step": "调用工具：count_text_stats",
                "state": state.to_dict(),
            }
        )

        # 第三步：固定生成最终结果
        final_answer = (
            f"文件：{file_path}\n"
            f"字符数：{stats['characters']}\n"
            f"行数：{stats['lines']}\n"
            f"词数：{stats['words']}"
        )

        state.complete_step("生成最终结果")
        state.finish(final_answer)

        trace_events.append(
            {
                "event": "workflow_finished",
                "result": stats,
                "state": state.to_dict(),
            }
        )

        return stats

    except Exception as error:
        state.fail()
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
        save_workflow_trace(
            trace_events,
            trace_path,
        )
