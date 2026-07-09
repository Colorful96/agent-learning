import json
from pathlib import Path

from src.clients.llm_client import create_chat_completion, get_first_message
from src.tools.registry import TOOL_SCHEMAS, execute_tool


def save_trace(trace_events, trace_path):
    """把智能体运行轨迹保存为 JSON 文件。"""

    # 确保 outputs 目录存在
    output_path = Path(trace_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存轨迹，ensure_ascii=False 可以让中文正常显示
    output_path.write_text(
        json.dumps(trace_events, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_tool_agent(config, messages, max_rounds=5, trace_path=None, messages_path=None):
    """运行一个支持工具调用的简单智能体循环。"""

    trace_events = []

    for round_index in range(max_rounds):
        print(f"\nRound {round_index + 1}")

        # 把当前对话历史和工具描述发送给模型
        response_json = create_chat_completion(
            api_key=config["deepseek_api_key"],
            model=config["deepseek_model"],
            api_base=config["deepseek_api_base"],
            messages=messages,
            tools=TOOL_SCHEMAS,
        )

        # 获取模型返回的 assistant 消息
        assistant_message = get_first_message(response_json)
        messages.append(assistant_message)

        # 记录本轮模型返回内容
        trace_events.append(
            {
                "round": round_index + 1,
                "event": "assistant_message",
                "content": assistant_message.get("content"),
                "tool_calls": assistant_message.get("tool_calls", []),
            }
        )

        tool_calls = assistant_message.get("tool_calls", [])

        # 如果没有工具调用，说明模型已经给出最终答案
        if not tool_calls:
            final_answer = assistant_message.get("content", "")

            trace_events.append(
                {
                    "round": round_index + 1,
                    "event": "final_answer",
                    "content": final_answer,
                }
            )

            if trace_path:
                save_trace(trace_events, trace_path)

            if messages_path:
                save_messages(messages, messages_path)

            return final_answer

        print(f"Model requested {len(tool_calls)} tool call(s).")

        for tool_call in tool_calls:
            function_info = tool_call["function"]
            tool_name = function_info["name"]

            try:
                # 模型传来的 arguments 是 JSON 字符串，需要转成 Python 字典
                arguments = json.loads(function_info["arguments"])

                print(f"Calling tool: {tool_name}")
                print("Arguments:", arguments)

                # 执行本地工具，如果工具内部报错，会进入 except
                tool_result = execute_tool(tool_name, arguments)

            except json.JSONDecodeError as error:
                arguments = {}
                tool_result = build_tool_error_result(
                    "工具参数不是合法 JSON：" + str(error)
                )

            except Exception as error:
                tool_result = build_tool_error_result("工具执行失败：" + str(error))

            print("Tool result:", tool_result)

            # 记录工具调用过程
            trace_events.append(
                {
                    "round": round_index + 1,
                    "event": "tool_call",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": tool_result,
                }
            )

            # 把工具结果放回对话历史，让模型继续推理
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    final_answer = "智能体达到最大轮数限制，未得到最终答案。"

    trace_events.append(
        {
            "round": max_rounds,
            "event": "max_round_limit",
            "content": final_answer,
        }
    )

    if trace_path:
        save_trace(trace_events, trace_path)

    if messages_path:
        save_messages(messages, messages_path)

    return final_answer


def build_tool_error_result(error_message):
    """把工具执行错误包装成统一的返回格式。"""

    return {
        "error": True,
        "message": error_message,
    }


def save_messages(messages, messages_path):
    """把当前短期记忆 messages 保存为 JSON 文件。"""

    # 确保输出目录存在
    output_path = Path(messages_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存 messages，方便观察智能体每一步的上下文
    output_path.write_text(
        json.dumps(messages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
