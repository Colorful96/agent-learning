import argparse

from src.agents.tool_agent import run_tool_agent
from src.config import load_config
from src.memory.long_term_memory import (
    save_memory,
    load_recent_memories,
    build_memory_context,
    search_memories,
    score_memory,
)
from src.agents.planner import build_plan_with_llm


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="运行一个支持工具调用的简单智能体。")

    parser.add_argument(
        "task",
        help="你希望智能体完成的任务，例如：读取文件并统计文本信息。",
    )

    return parser.parse_args()


def format_plan_steps(task_plan):
    """把结构化计划转换成 AgentState 可保存的文本列表。"""

    return [
        (
            f"{step.step_id}: "
            f"{step.tool_name or 'no_tool'} - "
            f"{step.action} - "
            f"{step.description}"
        )
        for step in task_plan.steps
    ]


def main():
    """程序入口：从命令行读取任务，并交给工具智能体执行。"""

    args = parse_args()
    config = load_config()
    # 第一步：让大模型生成结构化任务计划
    task_plan = build_plan_with_llm(
        config=config,
        task=args.task,
    )

    # 保存给 AgentState 的简化计划
    plan_steps = format_plan_steps(task_plan)

    print("Generated plan:")
    print(
        task_plan.model_dump_json(
            ensure_ascii=False,
            indent=2,
        )
    )

    def replan_after_error(error_message):
        """根据工具错误重新生成任务计划。"""

        replanning_task = (
            f"原始任务：{args.task}\n"
            f"上一轮工具执行失败：{error_message}\n"
            "请重新生成计划，避免重复相同的失败操作。"
        )

        new_plan = build_plan_with_llm(
            config=config,
            task=replanning_task,
        )

        print("Replanned plan:")
        print(
            new_plan.model_dump_json(
                ensure_ascii=False,
                indent=2,
            )
        )

        return format_plan_steps(new_plan)
    # 根据当前任务检索相关长期记忆
    related_memories = search_memories(args.task, limit=3)
    memory_context = build_memory_context(related_memories)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个会按照任务计划执行工作的助手。"
                "请参考下面经过程序校验的任务计划。"
                "如果某一步需要工具，必须调用对应工具。"
                "不要跳过必要步骤。"
                "如果工具返回 error 为 true，"
                "需要根据错误信息调整后续操作。"
                "\n\n任务计划：\n"
                f"{task_plan.model_dump_json(ensure_ascii=False, indent=2)}\n"
                "\n你是一个会使用工具的助手。"
                "如果用户要求读取文件，必须调用 read_text_file。"
                "如果用户要求统计文本信息，必须调用 count_text_stats。"
                "如果用户要求根据本地资料回答问题，"
                "必须调用 search_knowledge_base。"
                "如果用户要求保存报告，"
                "必须调用 save_markdown_report。"
                "在需要工具结果时，不要凭空编造。"
                "以下是你可以参考的长期记忆：\n"
                f"{memory_context}"
            ),
        },
        {
            "role": "user",
            "content": args.task,
        },
    ]

    final_answer = run_tool_agent(
        config=config,
        messages=messages,
        plan=plan_steps,
        replan_callback=replan_after_error,
        max_replans=1,
        trace_path="outputs/tool_agent_trace.json",
        messages_path="outputs/tool_agent_messages.json",
    )

    # 把本次任务和最终回答保存到长期记忆
    save_memory(
        task=args.task,
        final_answer=final_answer,
        memory_type="task",
        metadata={
            "source": "model_tool_call_demo",
        },
    )

    print("\nFinal answer:")
    print(final_answer)


if __name__ == "__main__":
    main()
