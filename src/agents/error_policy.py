def classify_tool_error(tool_result):
    """判断工具错误属于哪种类型。"""

    if not isinstance(tool_result, dict):
        return "none"

    if tool_result.get("error") is not True:
        return "none"

    message = str(tool_result.get("message", "")).lower()

    # 这些错误通常重试也没有意义
    permanent_markers = [
        "does not exist",
        "not a file",
        "unknown tool",
        "不存在",
        "不是一个文件",
        "未知工具",
        "不在当前任务计划",
    ]

    if any(marker in message for marker in permanent_markers):
        return "permanent"

    # 这些错误可能通过重试恢复
    retryable_markers = [
        "timeout",
        "timed out",
        "connection",
        "network",
        "超时",
        "网络",
        "连接",
    ]

    if any(marker in message for marker in retryable_markers):
        return "retryable"

    return "unknown"
