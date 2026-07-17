"""MCP Client 适配器，把异步 MCP 调用转换为同步工具接口。"""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


DEFAULT_SERVER_SCRIPT = Path("src/integrations/mcp_server.py")


def _server_parameters() -> StdioServerParameters:
    """构造启动本地 MCP Server 所需的参数。"""

    project_root = Path(__file__).resolve().parents[2]
    script = Path(
        os.getenv(
            "AGENT_MCP_SERVER_SCRIPT",
            str(project_root / DEFAULT_SERVER_SCRIPT),
        )
    ).resolve()

    environment = os.environ.copy()
    existing_python_path = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        value
        for value in [str(project_root), existing_python_path]
        if value
    )

    return StdioServerParameters(
        command=sys.executable,
        args=[str(script)],
        env=environment,
        cwd=project_root,
    )


async def _list_tools() -> list[dict]:
    """通过 MCP 获取服务端工具清单。"""

    async with stdio_client(_server_parameters()) as streams:
        read_stream, write_stream = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.model_dump() for tool in result.tools]


async def _call_tool(name: str, arguments: dict) -> object:
    """通过 MCP 调用指定工具。"""

    async with stdio_client(_server_parameters()) as streams:
        read_stream, write_stream = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)

            structured_content = getattr(
                result,
                "structured_content",
                None,
            )
            if structured_content is not None:
                return structured_content

            text_parts = [
                item.text
                for item in result.content
                if getattr(item, "text", None) is not None
            ]
            text = "\n".join(text_parts)

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text


def list_mcp_tools() -> list[dict]:
    """同步获取 MCP 工具列表。"""

    return asyncio.run(_list_tools())


def call_mcp_tool(name: str, arguments: dict) -> object:
    """同步调用 MCP 工具。"""

    return asyncio.run(_call_tool(name, arguments))
