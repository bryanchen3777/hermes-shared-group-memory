import os
import sqlite3
from datetime import datetime
from typing import Any, Dict

SHARED_DB = "/home/bbf/.hermes/shared_group_memory.db"
TEST_DB = "/home/bbf/.hermes/shared_group_memory_test.db"

def get_profile_name() -> str:
    hermes_home = os.environ.get("HERMES_HOME", "")
    if "/profiles/" in hermes_home:
        return hermes_home.rstrip("/").split("/")[-1]
    return "default"

# Always write on register to confirm plugin loaded
_conn = sqlite3.connect(TEST_DB)
_c = _conn.cursor()
_c.execute("""
    CREATE TABLE IF NOT EXISTS ping_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event TEXT,
        profile TEXT,
        ts TEXT
    )
""")
_c.execute("INSERT INTO ping_log (event, profile, ts) VALUES (?, ?, ?)",
    ("register_called", get_profile_name(), datetime.now().isoformat()))
_conn.commit()
_conn.close()

def get_chat_type(session_id: str) -> tuple[str, str]:
    root_db = "/home/bbf/.hermes/state.db"
    profile_db = None
    hermes_home = os.environ.get("HERMES_HOME", "")
    if "/profiles/" in hermes_home:
        candidate = os.path.join(hermes_home, "state.db")
        if os.path.exists(candidate):
            profile_db = candidate
    for db in ([profile_db, root_db] if profile_db else [root_db]):
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute("SELECT user_id FROM sessions WHERE id = ?", (session_id,))
            row = c.fetchone()
            conn.close()
            if row:
                return ("group", None) if row[0] is None else ("dm", row[0])
        except Exception:
            pass
    return ("dm", None)

def write_messages(session_id: str, conversation_history: list) -> None:
    profile = get_profile_name()
    chat_type, _ = get_chat_type(session_id)
    try:
        conn = sqlite3.connect(TEST_DB)
        c = conn.cursor()
        c.execute("INSERT INTO ping_log (event, profile, ts) VALUES (?, ?, ?)",
            (f"write_messages session={session_id[:20]} msgs={len(conversation_history)}",
             f"{profile}/{chat_type}", datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        pass
    try:
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
                    (datetime.now().timestamp(), "Bryan", content[:200], 1, chat_type, session_id)
                )
            elif role == "assistant":
                c.execute(
                    "INSERT INTO group_messages (timestamp, profile_name, content, is_from_bryan, chat_type, session_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (datetime.now().timestamp(), profile, content[:200], 0, chat_type, session_id)
                )
        conn.commit()
        conn.close()
    except Exception:
        pass

def read_shared_memory(chat_type: str, profile_name: str, limit: int = 20) -> str:
    try:
        conn = sqlite3.connect(SHARED_DB)
        c = conn.cursor()
        if chat_type == "group":
            c.execute(
                "SELECT timestamp, profile_name, content, is_from_bryan FROM group_messages WHERE chat_type='group' ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        else:
            c.execute(
                "SELECT timestamp, profile_name, content, is_from_bryan FROM group_messages WHERE chat_type='dm' AND (profile_name=? OR profile_name='Bryan') ORDER BY id DESC LIMIT ?",
                (profile_name, limit)
            )
        rows = c.fetchall()
        conn.close()
        if not rows:
            return "（共享記憶目前是空的）"
        result = []
        for ts, profile, content, is_bryan in rows:
            ts_str = datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else ""
            speaker = "Bryan" if is_bryan else profile
            result.append(f"[{ts_str}][{speaker}] {content.strip()}")
        return "\n".join(result)
    except Exception:
        return "（共享記憶目前是空的）"

def _pre_llm_call(**kwargs: Any) -> Dict[str, str]:
    profile = get_profile_name()
    session_id = kwargs.get("session_id", "")
    chat_type, _ = get_chat_type(session_id)
    recent = read_shared_memory(chat_type, profile, limit=20)
    label = "群聊" if chat_type == "group" else "私聊"
    context = (
        f"【共享記憶 — {label}】\n"
        f"以下是 Bryan 和所有後宮成員在{'群聊' if chat_type == 'group' else '私聊'}中說過的話：\n\n"
        f"{recent}"
    )
    return {"context": context}

def _post_llm_call(**kwargs: Any) -> None:
    conversation_history = kwargs.get("conversation_history", [])
    session_id = kwargs.get("session_id", "")
    try:
        conn = sqlite3.connect(TEST_DB)
        c = conn.cursor()
        c.execute("INSERT INTO ping_log (event, profile, ts) VALUES (?, ?, ?)",
            (f"post_llm_called session={session_id[:20] if session_id else 'none'} msgs={len(conversation_history)}",
             get_profile_name(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        pass
    if conversation_history and session_id:
        write_messages(session_id, conversation_history)

def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)
