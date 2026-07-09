import json
from datetime import datetime
from pathlib import Path


def save_memory(
    task,
    final_answer,
    memory_path="outputs/long_term_memory.jsonl",
    memory_type="task",
    metadata=None,
):
    """把一次智能体任务保存到长期记忆文件中。"""

    # 如果没有传入元数据，就使用空字典
    if metadata is None:
        metadata = {}

    # 构造一条长期记忆记录
    memory_item = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "type": memory_type,
        "task": task,
        "final_answer": final_answer,
        "metadata": metadata,
    }

    # 确保 outputs 目录存在
    output_path = Path(memory_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 使用 JSONL 格式保存：一行就是一条 JSON 记录
    with output_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(memory_item, ensure_ascii=False) + "\n")


def load_recent_memories(memory_path="outputs/long_term_memory.jsonl", limit=5):
    """读取最近的长期记忆记录。"""

    path = Path(memory_path)

    # 如果记忆文件不存在，说明还没有历史记录
    if not path.exists():
        return []

    memories = []

    # JSONL 文件是一行一条 JSON，所以需要逐行读取
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            memories.append(json.loads(line))

    # 只返回最近 limit 条记录
    return memories[-limit:]


def build_memory_context(memories):
    """把长期记忆记录整理成可以放进 prompt 的文本。"""

    if not memories:
        return "暂无长期记忆。"

    memory_lines = []

    for index, memory in enumerate(memories, start=1):
        memory_lines.append(
            (
                f"{index}. 时间：{memory.get('created_at')}\n"
                f"任务：{memory.get('task')}\n"
                f"回答：{memory.get('final_answer')}"
            )
        )

    return "\n\n".join(memory_lines)


def score_memory(query, memory):
    """根据当前任务和记忆内容的重合程度，计算一条记忆的相关性分数。"""

    query_text = query.lower()
    memory_text = (
        str(memory.get("task", "")) + "\n" + str(memory.get("final_answer", ""))
    ).lower()

    if not query_text or not memory_text:
        return 0

    score = 0

    # 英文或带空格的内容，用简单词匹配
    for word in query_text.split():
        if word in memory_text:
            score += 2

    # 中文没有天然空格，这里用字符重合做一个入门版匹配
    ignored_chars = set(" \n\t，。！？；：,.!?;:()（）[]【】\"'")
    query_chars = {char for char in query_text if char not in ignored_chars}
    memory_chars = set(memory_text)

    score += len(query_chars & memory_chars)

    return score


def search_memories(
    query,
    memory_path="outputs/long_term_memory.jsonl",
    limit=3,
    memory_type=None,
):
    """从长期记忆中检索和当前任务最相关的记忆。"""

    memories = load_recent_memories(memory_path=memory_path, limit=100)

    scored_memories = []

    for memory in memories:
        # 如果指定了记忆类型，就只检索这一类记忆
        if memory_type and memory.get("type") != memory_type:
            continue

        score = score_memory(query, memory)

        if score > 0:
            scored_memories.append(
                {
                    "score": score,
                    "memory": memory,
                }
            )

    # 分数越高，说明越相关
    scored_memories.sort(key=lambda item: item["score"], reverse=True)

    return [item["memory"] for item in scored_memories[:limit]]
