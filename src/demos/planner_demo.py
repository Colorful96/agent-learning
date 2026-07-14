import argparse

from src.agents.planner import build_plan_with_llm
from src.config import load_config


def parse_args():
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="测试大模型任务规划器。")

    parser.add_argument(
        "task",
        help="需要规划的用户任务。",
    )

    return parser.parse_args()


def main():
    """程序入口。"""

    args = parse_args()
    config = load_config()

    plan = build_plan_with_llm(
        config=config,
        task=args.task,
    )

    print(
        plan.model_dump_json(
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
