import logging

from config import load_config
from summarizer import summarize_text


def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def save_summary(output_dir, title: str, summary: str):
    output_path = output_dir / "summary.md"
    content = f"# {title}\n\n{summary}\n"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main():
    config = load_config()
    setup_logging(config["log_file"])
    logger = logging.getLogger(__name__)

    print("请输入一段需要摘要的文本，输入完成后按回车：")
    text = input("> ")

    try:
        result = summarize_text(text, config)
        output_path = save_summary(config["output_dir"], result.title, result.summary)
    except ValueError as error:
        logger.warning("Invalid input: %s", error)
        print(f"输入错误：{error}")
        return

    logger.info("Summary saved to %s with source=%s", output_path, result.source)
    print(f"摘要已保存到：{output_path}")
    print(f"摘要来源：{result.source}")


if __name__ == "__main__":
    main()
