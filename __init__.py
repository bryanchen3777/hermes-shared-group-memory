import os
import sqlite3
from datetime import datetime
from typing import Any, Dict


SHARED_DB = "/home/bbf/.hermes/shared_group_memory.db"
STATE_DB = "/home/bbf/.hermes/state.db"


def get_profile_name() -> str:
    hermes_home = os.environ.get("HERMES_HOME", "")
    if "/profiles/" in hermes_home:
        return hermes_home.rstrip("/").split("/")[-1]
    return "default"


def get_chat_type(session_id: str) -> tuple[str, str]:
    try:
        conn = sqlite3.connect(STATE_DB)
        c = conn.cursor()
        c.execute("SELECT user_id FROM sessions WHERE id = ?", (session_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0] is None:
            return ("group", None)
        return ("dm", row[0] if row else None)
    except Exception:
        return ("dm", None)


def write_messages(session_id: str, conversation_history: list) -> None:
    profile = get_profile_name()
    chat_type, user_id = get_chat_type(session_id)

    conn = sqlite3.connect(SHARED_DB)
    c = conn.cursor()

    for msg in conversation_history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if not content or len(content) < 2:
            continue

        if role == "user":
            c.execute(
                "INSERT INTO group_messages (timestamp, profile_name, content, is_from_bryan, chat_type, session_id) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now().timestamp(), "Bryan", content, 1, chat_type, session_id)
            )
        elif role == "assistant":
            c.execute(
                "INSERT INTO group_messages (timestamp, profile_name, content, is_from_bryan, chat_type, session_id) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now().timestamp(), profile, content, 0, chat_type, session_id)
            )

    conn.commit()
    conn.close()


def read_shared_memory(chat_type: str, profile_name: str, limit: int = 20) -> str:
    try:
        conn = sqlite3.connect(SHARED_DB)
        c = conn.cursor()

        if chat_type == "group":
            c.execute("""
                SELECT timestamp, profile_name, content, is_from_bryan
                FROM group_messages
                WHERE chat_type = 'group'
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
        else:
            c.execute("""
                SELECT timestamp, profile_name, content, is_from_bryan
                FROM group_messages
                WHERE chat_type = 'dm'
                  AND (profile_name = ? OR profile_name = 'Bryan')
                ORDER BY id DESC
                LIMIT ?
            """, (profile_name, limit))

        rows = c.fetchall()
        conn.close()

        if not rows:
            return "（共享記憶目前是空的）"

        result = []
        for ts, profile, content, is_bryan in rows:
            ts_str = datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else ""
            speaker = "Bryan" if is_bryan else profile
            result.append(f"[{ts_str}][{speaker}] {content.strip()}")

        return "
".join(result)
    except Exception as e:
        return f"[shared_memory read error] {e}"


async def _pre_llm_call(**kwargs: Any) -> Dict[str, str]:
    profile = get_profile_name()
    conversation_history = kwargs.get("conversation_history", [])
    session_id = kwargs.get("session_id", "")

    chat_type, _ = get_chat_type(session_id)
    recent = read_shared_memory(chat_type, profile, limit=20)

    label = "群聊" if chat_type == "group" else "私聊"
    context = (
        f"【共享記憶 — {label}】
"
        f"以下是 Bryan 和所有後宮成員在{'群聊' if chat_type == 'group' else '私聊'}中說過的話：

"
        f"{recent}"
    )
    return {"context": context}


async def _post_llm_call(**kwargs: Any) -> None:
    conversation_history = kwargs.get("conversation_history", [])
    session_id = kwargs.get("session_id", "")

    if not conversation_history or not session_id:
        return

    write_messages(session_id, conversation_history)


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)
