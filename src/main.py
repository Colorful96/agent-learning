import logging
import sys
import argparse
from pathlib import Path
from docx import Document

from config import load_config
from summarizer import summarize_text, analyze_text_structured, StructuredOutputError
import json


def save_structured_summary(output_dir, result, style="default"):
    markdown_path = output_dir / f"structured_summary_{style}.md"
    json_path = output_dir / f"structured_summary_{style}.json"
    markdown_content = (
        f"# Topic\n\n {result.topic}\n\n"
        f"## Summary\n\n{result.summary}\n\n"
        f"## Keywords\n\n"
        + "\n".join(f"- {keyword}" for keyword in result.keywords)
        + "\n\n## Action Items\n\n"
        + "\n".join(f"- {item}" for item in result.action_items)
        + "\n"
    )
    # json_content = json.dumps({"topic": result.topic, "summary": result.summary, "keywords": result.keywords, "action_items": result.action_items}, ensure_ascii=False, indent=2)
    json_content = json.dumps(result.model_dump(), ensure_ascii=False, indent=2)

    markdown_path.write_text(markdown_content, encoding="utf-8")
    json_path.write_text(json_content, encoding="utf-8")
    return markdown_path


def setup_logging(log_file):
    """
    配置日志记录功能
    Args:
        log_file (str): 日志文件的路径
    """
    logging.basicConfig(
        level=logging.INFO,  # 设置日志级别为INFO，记录INFO及以上级别的日志
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",  # 设置日志格式，包含时间、日志级别、名称和消息
        handlers=[  # 配置日志处理器，同时输出到文件和控制台
            logging.FileHandler(
                str(log_file), encoding="utf-8"
            ),  # 输出到文件，使用UTF-8编码
            logging.StreamHandler(),  # 输出到控制台
        ],
    )


def save_summary(output_dir, title: str, summary: str):
    output_path = output_dir / "summary.md"
    content = f"# {title}\n\n{summary}\n"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Summarize text files with optional structured JSON output."
    )

    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to a UTF-8 text, Markdown, or docx file. If omitted, read from terminal input.",
    )

    parser.add_argument(
        "--structured",
        action="store_true",
        help="Generate structured summary output.",
    )

    parser.add_argument(
        "--style",
        choices=["default", "concise", "research", "action", "all"],
        default="default",
        help="Prompt style for structured output.",
    )

    return parser.parse_args()


def read_docx_text(input_path):
    document = Document(input_path)
    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def read_input_text(args):
    if not args:
        print("请输入一段需要摘要的文本，输入完成后按回车：")
        return input("> ")

    input_path = Path(args[0])
    if not input_path.exists():
        raise ValueError(f"文件不存在：{input_path}")

    if not input_path.is_file():
        raise ValueError(f"输入路径不是文件：{input_path}")
    suffix = input_path.suffix.lower()

    if suffix == ".docx":
        return read_docx_text(input_path)

    return input_path.read_text(encoding="utf-8")


def main():
    config = load_config()
    setup_logging(config["log_file"])
    logger = logging.getLogger(__name__)

    try:
        cli_args = parse_cli_args()
        input_args = [cli_args.input_path] if cli_args.input_path else []

        text = read_input_text(input_args)

        if cli_args.structured:
            if cli_args.style == "all":
                styles = ["concise", "research", "action"]
                output_paths = []

                for current_style in styles:
                    result = analyze_text_structured(text, config, style=current_style)
                    output_path = save_structured_summary(
                        config["output_dir"],
                        result,
                        style=current_style,
                    )
                    output_paths.append(output_path)

                output_path = output_paths[-1]
                source = "deepseek_structured_json_all"
            else:
                result = analyze_text_structured(text, config, style=cli_args.style)
                output_path = save_structured_summary(
                    config["output_dir"],
                    result,
                    style=cli_args.style,
                )
                source = "deepseek_structured_json"
        else:
            result = summarize_text(text, config)
            output_path = save_summary(
                config["output_dir"], result.title, result.summary
            )
            source = result.source
        # if structured_mode:
        #     result = analyze_text_structured(text, config, style=style)
        #     output_path = save_structured_summary(
        #         config["output_dir"], result, style=style
        #     )
        #     source = "deepseek_structured_json"
        # else:
        #     result = summarize_text(text, config)
        #     output_path = save_summary(
        #         config["output_dir"], result.title, result.summary
        #     )
        #     source = result.source
    except ValueError as error:
        logger.warning("Invalid input: %s", error)
        print(f"输入错误：{error}")
        return
    except StructuredOutputError as error:
        logger.error("Structured output failed: %s", error)
        print(f"结构化输出失败：{error}")
        return

    logger.info("Summary saved to %s with source=%s", output_path, source)
    print(f"摘要已保存到：{output_path}")
    print(f"摘要来源：{source}")


if __name__ == "__main__":
    main()
