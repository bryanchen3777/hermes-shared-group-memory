import os
import sqlite3
from datetime import datetime
from typing import Any, Dict


def get_profile_name() -> str:
    hermes_home = os.environ.get("HERMES_HOME", "")
    if "/profiles/" in hermes_home:
        return hermes_home.rstrip("/").split("/")[-1]
    return "default"


def get_state_db() -> str:
    """Resolve state.db path: prefer profile-specific, fallback to root."""
    hermes_home = os.environ.get("HERMES_HOME", "")
    if "/profiles/" in hermes_home:
        profile_db = os.path.join(hermes_home, "state.db")
        if os.path.exists(profile_db):
            return profile_db
    return "/home/bbf/.hermes/state.db"


def get_global_memory(limit: int = 20, profile_name: str = None) -> str:
    db_path = get_state_db()
    profile_name = profile_name or get_profile_name()

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        c.execute("""
            SELECT
                substr(m.content, 1, 350) as msg,
                m.timestamp,
                s.user_id
            FROM messages m
            JOIN sessions s ON m.session_id = s.id
            WHERE m.role = 'user'
            ORDER BY m.id DESC
            LIMIT ?
        """, (limit * 2,))

        rows = c.fetchall()
        conn.close()

        if not rows:
            return "目前沒有新訊息。"

        result = []
        for content, ts, user_id in rows:
            if not content or not content.strip():
                continue

            time_str = datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else ""

            if user_id is None:
                result.append(f"[{time_str}][群聊] {content.strip()}")
            else:
                result.append(f"[{time_str}][私聊] {content.strip()}")

        output = "\n".join(result[:limit]) if result else "目前沒有新訊息。"
        return f"[全域記憶 - Bryan 最近發言]\n{output}"

    except Exception as e:
        return f"[Global Memory 錯誤] {str(e)}"


def _inject_global_memory(**kwargs: Any) -> Dict[str, str]:
    profile_name = get_profile_name()
    try:
        memory_text = get_global_memory(limit=20, profile_name=profile_name)
        context = (
            f"【全域記憶同步 — Bryan 最近的發言】\n"
            f"（目前 profile 名稱尚無法寫入 sessions，私聊暫且全部顯示）\n\n"
            f"{memory_text}"
        )
        return {"context": context}
    except Exception as e:
        return {"context": f"[global_memory plugin 錯誤] {e}"}


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _inject_global_memory)
