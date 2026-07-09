from src.tools.local_tools import count_text_stats, read_text_file, save_markdown_report


def main():
    # 直接调用本地工具函数，用来验证每个工具本身是否可用。
    text = read_text_file("examples/agent_complex.txt")
    stats = count_text_stats(text)

    # 把统计结果整理成 Markdown，方便检查输出文件。
    content = (
        "## Text Stats\n\n"
        f"- Characters: {stats['characters']}\n"
        f"- Lines: {stats['lines']}\n"
        f"- Words: {stats['words']}\n"
    )

    output_path = save_markdown_report(
        title="Tool Demo Report",
        content=content,
        output_path="outputs/tool_demo_report.md",
    )

    # 在终端打印结果，确认工具执行成功。
    print("Text stats:")
    print(stats)
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
