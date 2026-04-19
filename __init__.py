import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Tuple

SHARED_DB = "/home/bbf/.hermes/shared_group_memory.db"
BRYAN_ID = "1696287850"

STATE_DBS = {
    "default": "/home/bbf/.hermes/state.db",
    "rem":    "/home/bbf/.hermes/profiles/rem/state.db",
    "ram":    "/home/bbf/.hermes/profiles/ram/state.db",
    "mihiru": "/home/bbf/.hermes/profiles/mihiru/state.db",
}


def get_profile_name() -> str:
    hermes_home = os.environ.get("HERMES_HOME", "")
    if "/profiles/" in hermes_home:
        return hermes_home.rstrip("/").split("/")[-1]
    return "default"


def get_chat_type(session_id: str) -> Tuple[str, str | None]:
    """session_id 出現在 2+ profile = 群組聊天"""
    if not session_id:
        return ("dm", None)
    profiles_with_session = []
    user_id = None
    for profile, db_path in STATE_DBS.items():
        if not os.path.exists(db_path):
            continue
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            c = conn.cursor()
            c.execute("SELECT user_id FROM sessions WHERE id = ?", (session_id,))
            row = c.fetchone()
            if row is not None:
                profiles_with_session.append(profile)
                if user_id is None:
                    user_id = row[0]
            conn.close()
        except Exception:
            pass
    if len(profiles_with_session) >= 2:
        return ("group", None)
    if user_id is None:
        return ("dm", None)
    return ("dm", str(user_id) if user_id is not None else None)


def sync_from_state_db() -> None:
    my_profile = get_profile_name()
    dbs_to_scan = [("/home/bbf/.hermes/state.db", "root")]
    if my_profile != "default":
        profile_db_path = f"/home/bbf/.hermes/profiles/{my_profile}/state.db"
        if os.path.exists(profile_db_path):
            dbs_to_scan.append((profile_db_path, my_profile))
    for db_path, source in dbs_to_scan:
        _sync_single_db(db_path, source, my_profile)


def _sync_single_db(db_path: str, source: str, my_profile: str) -> None:
    try:
        src_conn = sqlite3.connect(db_path, timeout=10)
        src_conn.row_factory = sqlite3.Row
    except Exception:
        return
    try:
        shared_conn = sqlite3.connect(SHARED_DB, timeout=10)
        shared_conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        src_conn.close()
        return
    try:
        sessions = {}
        rows = src_conn.execute("SELECT id, user_id FROM sessions").fetchall()
        for row in rows:
            sessions[row["id"]] = row["user_id"]
        if not sessions:
            src_conn.close()
            shared_conn.close()
            return
        session_ids = list(sessions.keys())
        placeholders = ",".join(["?"] * len(session_ids))
        query = f"""
            SELECT m.id, m.session_id, m.role, m.content, m.timestamp
            FROM messages m
            WHERE m.session_id IN ({placeholders})
              AND m.role IN ('user', 'assistant')
              AND m.content IS NOT NULL
              AND LENGTH(m.content) > 1
            ORDER BY m.id DESC
            LIMIT 2000
        """
        messages = src_conn.execute(query, session_ids).fetchall()
        if not messages:
            src_conn.close()
            shared_conn.close()
            return
        shared_c = shared_conn.cursor()
        for msg in messages:
            msg_id = msg["id"]
            session_id = msg["session_id"]
            role = msg["role"]
            content = msg["content"]
            ts = msg["timestamp"] or datetime.now().timestamp()

            chat_type, _ = get_chat_type(session_id)

            # recipient 寫入邏輯：
            # Bryan → 群聊：recipient="all"（所有 Bot 可見）
            # Bryan → 單一 Bot DM：recipient=my_profile（只有該 Bot 可見）
            # Agent → Bryan：recipient="Bryan"
            if role == "user":
                profile_name = "Bryan"
                is_from_bryan = 1
                recipient = "all" if chat_type == "group" else my_profile
            else:
                profile_name = my_profile
                is_from_bryan = 0
                recipient = "Bryan"

            try:
                shared_c.execute("""
                    INSERT OR IGNORE INTO group_messages
                        (timestamp, profile_name, content, is_from_bryan, chat_type, session_id, msg_id, recipient)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (ts, profile_name, content[:500], is_from_bryan, chat_type, session_id, msg_id, recipient))
            except Exception:
                pass
        shared_conn.commit()
        shared_conn.close()
        src_conn.close()
    except Exception:
        try:
            src_conn.close()
            shared_conn.close()
        except Exception:
            pass


def read_shared_memory(chat_type: str, profile_name: str, limit: int = 20) -> str:
    """讀取：群聊全公開，私聊只有自己說的 + Bryan 對自己說的"""
    try:
        conn = sqlite3.connect(SHARED_DB)
        c = conn.cursor()
        if chat_type == "group":
            c.execute("""
                SELECT timestamp, profile_name, content, is_from_bryan
                FROM group_messages
                WHERE chat_type='group'
                ORDER BY id DESC LIMIT ?
            """, (limit,))
        else:
            c.execute("""
                SELECT timestamp, profile_name, content, is_from_bryan
                FROM group_messages
                WHERE chat_type='dm' AND (profile_name=? OR (profile_name='Bryan' AND recipient=?))
                ORDER BY id DESC LIMIT ?
            """, (profile_name, profile_name, limit))
        rows = c.fetchall()
        conn.close()
        if not rows:
            return "（共享記憶目前是空的）"
        result = []
        for ts, profile, content, is_bryan in rows:
            ts_str = datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else ""
            speaker = "Bryan" if is_bryan else profile
            result.append(f"[{ts_str}][{speaker}] {content.strip()[:100]}")
        return "\n".join(result)
    except Exception:
        return "（共享記憶目前是空的）"


def _pre_llm_call(**kwargs: Any) -> Dict[str, str]:
    sync_from_state_db()
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
    sync_from_state_db()


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)
