def route_task(task):
    """根据任务内容选择固定工作流。"""

    task_lower = task.lower()

    # 文件统计任务
    if any(
        keyword in task
        for keyword in [
            "统计",
            "字符数",
            "行数",
            "词数",
        ]
    ):
        return "file_stats"

    # 文献研究任务
    if any(
        keyword in task_lower
        for keyword in [
            "rag",
            "fastapi",
            "langchain",
            "langgraph",
            "论文",
            "文献",
            "知识库",
            "资料",
            "研究",
            "报告",
        ]
    ):
        return "research"

    return "unsupported"
