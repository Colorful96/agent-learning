from src.tools.registry import TOOL_SCHEMAS, execute_tool


def main():
    # 1. 打印当前注册过的工具名称。
    # 这一步是为了确认 TOOL_SCHEMAS 中有哪些工具可以给模型使用。
    print("Available tools:")
    for tool in TOOL_SCHEMAS:
        print("-", tool["function"]["name"])

    # 2. 通过工具注册表读取本地文本文件。
    # 注意：这里不是直接调用 read_text_file()，
    # 而是通过 execute_tool() + 工具名 + 参数字典来调用。
    text = execute_tool(
        "read_text_file",
        {"path": "examples/agent_complex.txt"},
    )

    # 3. 通过工具注册表统计文本信息。
    # execute_tool 会根据 "count_text_stats" 找到对应的 Python 函数，
    # 然后把 {"text": text} 展开成函数参数。
    stats = execute_tool(
        "count_text_stats",
        {"text": text},
    )

    # 4. 通过工具注册表保存 Markdown 报告。
    # 这里把统计结果整理成 Markdown 内容，再写入 outputs 目录。
    report_path = execute_tool(
        "save_markdown_report",
        {
            "title": "Tool Registry Demo",
            "content": (
                "## Text Stats\n\n"
                f"- Characters: {stats['characters']}\n"
                f"- Lines: {stats['lines']}\n"
                f"- Words: {stats['words']}\n"
            ),
            "output_path": "outputs/tool_registry_demo.md",
        },
    )

    # 5. 打印执行结果，方便在终端确认工具调用成功。
    print("Stats:", stats)
    print("Report saved to:", report_path)


if __name__ == "__main__":
    main()
