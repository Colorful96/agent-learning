"""演示 MCP Client 发现并调用项目工具。"""

import json

from src.integrations.mcp_client import call_mcp_tool, list_mcp_tools


def main() -> None:
    """打印 MCP 工具清单，并调用一个无外部依赖的工具。"""

    tools = list_mcp_tools()
    print("MCP tools:")
    print(json.dumps(tools, ensure_ascii=False, indent=2))

    result = call_mcp_tool(
        "count_text_stats",
        {
            "text": "MCP 将工具能力暴露给 Agent。",
        },
    )
    print("Tool result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
