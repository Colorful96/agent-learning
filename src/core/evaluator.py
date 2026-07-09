import json
from pathlib import Path

REQUIRED_FIELDS = ["topic", "summary", "keywords", "action_items"]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def get_style_from_path(path: Path):
    name = path.stem

    if name.endswith("_concise"):
        return "concise"

    if name.endswith("_research"):
        return "research"

    if name.endswith("_action"):
        return "action"

    return "default"


def get_rules(style):
    if style == "concise":
        return {
            "summary_min": 20,
            "summary_max": 100,
            "keywords_min": 3,
            "keywords_max": 5,
            "action_items_min": 1,
            "action_items_max": 3,
        }

    if style == "research":
        return {
            "summary_min": 50,
            "summary_max": 260,
            "keywords_min": 4,
            "keywords_max": 12,
            "action_items_min": 2,
            "action_items_max": 8,
        }

    if style == "action":
        return {
            "summary_min": 30,
            "summary_max": 180,
            "keywords_min": 3,
            "keywords_max": 8,
            "action_items_min": 3,
            "action_items_max": 10,
        }

    return {
        "summary_min": 20,
        "summary_max": 180,
        "keywords_min": 3,
        "keywords_max": 8,
        "action_items_min": 1,
        "action_items_max": 8,
    }


def evaluate_summary(data, style="default"):
    rules = get_rules(style)

    score = 0
    notes = []

    missing_fields = [field for field in REQUIRED_FIELDS if field not in data]
    if not missing_fields:
        score += 2
    else:
        notes.append("Missing fields: " + ", ".join(missing_fields))

    summary = data.get("summary", "")
    if rules["summary_min"] <= len(summary) <= rules["summary_max"]:
        score += 2
    else:
        notes.append(
            "Summary length should be between "
            f"{rules['summary_min']} and {rules['summary_max']}"
        )

    keywords = data.get("keywords", [])
    if (
        isinstance(keywords, list)
        and rules["keywords_min"] <= len(keywords) <= rules["keywords_max"]
    ):
        score += 2
    else:
        notes.append(
            "Keywords count should be between "
            f"{rules['keywords_min']} and {rules['keywords_max']}"
        )

    action_items = data.get("action_items", [])
    if (
        isinstance(action_items, list)
        and rules["action_items_min"] <= len(action_items) <= rules["action_items_max"]
    ):
        score += 2
    else:
        notes.append(
            "Action items count should be between "
            f"{rules['action_items_min']} and {rules['action_items_max']}"
        )

    if all(isinstance(item, str) and item.strip() for item in keywords + action_items):
        score += 2
    else:
        notes.append("Keywords and action items should be non-empty strings")

    return {
        "score": score,
        "notes": notes,
    }


def evaluate_file(path: Path):
    style = get_style_from_path(path)
    data = load_json(path)
    result = evaluate_summary(data, style=style)

    return {
        "file": str(path),
        "style": style,
        "score": result["score"],
        "notes": result["notes"],
    }


def main():
    output_dir = Path("outputs")
    files = [
        output_dir / "structured_summary_concise.json",
        output_dir / "structured_summary_research.json",
        output_dir / "structured_summary_action.json",
    ]

    results = []
    for path in files:
        if path.exists():
            results.append(evaluate_file(path))

    report_path = output_dir / "evaluation_report.json"
    report_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Evaluation report saved to: {report_path}")


if __name__ == "__main__":
    main()
