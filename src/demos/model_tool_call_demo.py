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


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="运行一个支持工具调用的简单智能体。")

    parser.add_argument(
        "task",
        help="你希望智能体完成的任务，例如：读取文件并统计文本信息。",
    )

    return parser.parse_args()


def main():
    """程序入口：从命令行读取任务，并交给工具智能体执行。"""

    args = parse_args()
    config = load_config()

    # 根据当前任务检索相关长期记忆
    related_memories = search_memories(args.task, limit=3)
    memory_context = build_memory_context(related_memories)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个会使用工具的助手。"
                "如果用户要求读取文件，必须调用 read_text_file。"
                "如果用户要求统计文本信息，必须调用 count_text_stats。"
                "如果工具返回 error 为 true，说明工具执行失败，你需要根据错误信息调整下一步。"
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
