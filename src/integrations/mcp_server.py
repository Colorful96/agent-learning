"""把项目本地工具暴露为 MCP Server。"""

from mcp.server.fastmcp import FastMCP

from src.tools.local_tools import (
    count_text_stats as local_count_text_stats,
    read_text_file as local_read_text_file,
    save_markdown_report as local_save_markdown_report,
    search_knowledge_base as local_search_knowledge_base,
)


mcp = FastMCP(
    "agent-learning-tools",
    json_response=True,
)


@mcp.tool()
def read_text_file(path: str) -> str:
    """读取项目允许范围内的文本文件。"""

    return local_read_text_file(path)


@mcp.tool()
def count_text_stats(text: str) -> dict:
    """统计文本的字符数、行数和词数。"""

    return local_count_text_stats(text)


@mcp.tool()
def search_knowledge_base(
    question: str,
    top_k: int = 3,
    source: str | None = None,
) -> dict:
    """检索本地知识库并返回引用来源。"""

    return local_search_knowledge_base(
        question=question,
        top_k=top_k,
        source=source,
    )


@mcp.tool()
def save_markdown_report(
    title: str,
    content: str,
    output_path: str,
) -> str:
    """保存 Markdown 报告。"""

    return local_save_markdown_report(
        title=title,
        content=content,
        output_path=output_path,
    )


def main() -> None:
    """使用 stdio 启动本地 MCP Server。"""

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
