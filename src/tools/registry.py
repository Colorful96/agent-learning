from src.tools.local_tools import count_text_stats, read_text_file, save_markdown_report

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_text_file",
            "description": "Read a UTF-8 text file from a local path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the text file.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_text_stats",
            "description": "Count basic statistics of a text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to count.",
                    }
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_markdown_report",
            "description": "Save a Markdown report to a local path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Report title.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Report content in Markdown.",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save the Markdown report.",
                    },
                },
                "required": ["title", "content", "output_path"],
            },
        },
    },
]


TOOL_FUNCTIONS = {
    "read_text_file": read_text_file,
    "count_text_stats": count_text_stats,
    "save_markdown_report": save_markdown_report,
}


def execute_tool(name: str, arguments: dict):
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {name}")

    tool_function = TOOL_FUNCTIONS[name]
    return tool_function(**arguments)
