from config import load_config
from summarizer import summarize_text


def save_summary(output_dir, title: str, summary: str):
    output_path = output_dir / "summary.md"
    content = f"# {title}\n\n{summary}\n"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main():
    config = load_config()

    print("请输入一段需要摘要的文本，输入完成后按回车：")
    text = input("> ")

    try:
        result = summarize_text(text)
        output_path = save_summary(config["output_dir"], result.title, result.summary)
    except ValueError as error:
        print(f"输入错误：{error}")
        return

    print(f"摘要已保存到：{output_path}")


if __name__ == "__main__":
    main()
