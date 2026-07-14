import json
from pathlib import Path

from src.clients.llm_client import create_chat_completion, get_first_message
from src.tools.registry import TOOL_SCHEMAS, execute_tool
from src.agents.state import AgentState
from src.agents.error_policy import (
    classify_tool_error,
)


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


def is_tool_allowed_by_plan(tool_name, plan):
    """检查工具是否出现在当前任务计划中。"""

    if not plan:
        return True

    return any(tool_name in plan_step for plan_step in plan)


def run_tool_agent(
    config,
    messages,
    max_rounds=5,
    trace_path=None,
    messages_path=None,
    plan=None,
    replan_callback=None,
    max_replans=1,
):
    """运行一个支持工具调用的简单智能体循环。"""

    trace_events = []

    task = ""

    for message in reversed(messages):
        if message.get("role") == "user":
            task = message.get("content", "")
            break

    state = AgentState(
        task=task,
        plan=plan or [],
    )
    state.start()

    trace_events.append(
        {
            "event": "state_initialized",
            "state": state.to_dict(),
        }
    )

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
            # 模型不再请求工具，说明任务已经完成
            # 模型不再请求工具，说明进入最终回答步骤
            if plan:
                for plan_step in plan:
                    if "no_tool" in plan_step:
                        state.complete_step(plan_step)
                        break
            state.finish(final_answer)

            trace_events.append(
                {
                    "round": round_index + 1,
                    "event": "final_answer",
                    "content": final_answer,
                    "state": state.to_dict(),
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

            if not is_tool_allowed_by_plan(
                tool_name,
                plan,
            ):
                tool_result = build_tool_error_result(
                    f"工具 {tool_name} 不在当前任务计划中。"
                )

                state.fail()

                trace_events.append(
                    {
                        "round": round_index + 1,
                        "event": "plan_violation",
                        "tool_name": tool_name,
                        "message": tool_result["message"],
                        "state": state.to_dict(),
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(
                            tool_result,
                            ensure_ascii=False,
                        ),
                    }
                )

                continue

            # 记录当前正在执行的步骤
            state.current_step = f"调用工具：{tool_name}"
            current_step = state.current_step

            arguments = {}
            tool_succeeded = False

            try:
                # 模型传来的 arguments 是 JSON 字符串
                arguments = json.loads(function_info["arguments"])

                print(f"Calling tool: {tool_name}")
                print("Arguments:", arguments)

                # 执行工具
                tool_result = execute_tool(tool_name, arguments)

                # 工具返回 error=True 时，认为本次执行失败
                tool_succeeded = not (
                    isinstance(tool_result, dict) and tool_result.get("error") is True
                )

            except json.JSONDecodeError as error:
                tool_result = build_tool_error_result(
                    "工具参数不是合法 JSON：" + str(error)
                )

            except Exception as error:
                tool_result = build_tool_error_result("工具执行失败：" + str(error))

            # 根据工具执行结果更新 Agent 状态
            if tool_succeeded:
                state.complete_step(current_step)
            else:
                state.fail()

            print("Tool result:", tool_result)
            error_type = classify_tool_error(tool_result)

            if error_type != "none":
                trace_events.append(
                    {
                        "round": round_index + 1,
                        "event": "error_classified",
                        "error_type": error_type,
                        "message": tool_result.get(
                            "message",
                            "",
                        ),
                        "state": state.to_dict(),
                    }
                )

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

            # 记录状态变化
            trace_events.append(
                {
                    "round": round_index + 1,
                    "event": "state_update",
                    "state": state.to_dict(),
                }
            )

            # 把工具结果返回给模型
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    ),
                }
            )

            # 永久错误不再继续请求模型
            if error_type == "permanent":
                final_answer = "任务无法继续，工具报告了永久错误：" + tool_result.get(
                    "message", ""
                )

                state.status = "failed"

                trace_events.append(
                    {
                        "round": round_index + 1,
                        "event": "permanent_error_stop",
                        "content": final_answer,
                        "state": state.to_dict(),
                    }
                )

                if trace_path:
                    save_trace(
                        trace_events,
                        trace_path,
                    )

                if messages_path:
                    save_messages(
                        messages,
                        messages_path,
                    )

                return final_answer

    final_answer = "智能体达到最大轮数限制，未得到最终答案。"
    state.status = "failed"
    trace_events.append(
        {
            "round": max_rounds,
            "event": "max_round_limit",
            "content": final_answer,
            "state": state.to_dict(),
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
