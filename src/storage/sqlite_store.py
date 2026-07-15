import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/agent.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id)
        REFERENCES sessions(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id
ON messages(session_id);
"""


def current_time() -> str:
    """返回当前 UTC 时间。"""

    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    """创建 SQLite 数据库连接。"""

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    # 开启外键约束
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database() -> None:
    """创建会话表和消息表。"""

    connection = get_connection()

    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()


def create_session(
    title: str = "科研文献会话",
) -> str:
    """创建一个新会话并返回 session_id。"""

    initialize_database()

    session_id = uuid.uuid4().hex
    now = current_time()

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO sessions (
                id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                title,
                now,
                now,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return session_id


def get_or_create_session(
    session_id: str | None = None,
) -> str:
    """获取已有会话，不存在时创建新会话。"""

    if not session_id:
        return create_session()

    initialize_database()

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT id
            FROM sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
    finally:
        connection.close()

    if row:
        return session_id

    return create_session()


def add_message(
    session_id: str,
    role: str,
    content: str,
) -> None:
    """向指定会话保存一条消息。"""

    if role not in {"user", "assistant"}:
        raise ValueError("role 只能是 user 或 assistant。")

    if not content.strip():
        raise ValueError("消息内容不能为空。")

    initialize_database()
    now = current_time()

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO messages (
                session_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                now,
            ),
        )

        connection.execute(
            """
            UPDATE sessions
            SET updated_at = ?
            WHERE id = ?
            """,
            (
                now,
                session_id,
            ),
        )

        connection.commit()
    finally:
        connection.close()


def get_recent_messages(
    session_id: str,
    limit: int = 10,
) -> list[dict]:
    """读取指定会话最近的消息。"""

    initialize_database()

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT role, content
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                session_id,
                limit,
            ),
        ).fetchall()
    finally:
        connection.close()

    # 查询结果是倒序，需要恢复成正常对话顺序
    rows.reverse()

    return [
        {
            "role": row["role"],
            "content": row["content"],
        }
        for row in rows
    ]
