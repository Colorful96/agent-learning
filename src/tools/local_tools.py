from pathlib import Path


def read_text_file(path: str) -> str:
    file_path = Path(path)

    if not file_path.exists():
        raise ValueError(f"File does not exist: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return file_path.read_text(encoding="utf-8")


def count_text_stats(text: str) -> dict:
    cleaned_text = text.strip()

    return {
        "characters": len(cleaned_text),
        "lines": len(cleaned_text.splitlines()),
        "words": len(cleaned_text.split()),
    }


def save_markdown_report(title: str, content: str, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    markdown = f"# {title}\n\n{content}\n"
    path.write_text(markdown, encoding="utf-8")

    return str(path)
