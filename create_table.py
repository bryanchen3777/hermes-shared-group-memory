import sqlite3

db_path = "/home/bbf/.hermes/shared_group_memory.db"

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS group_messages")

c.execute("""
    CREATE TABLE IF NOT EXISTS group_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL,
        profile_name TEXT,
        content TEXT,
        is_from_bryan INTEGER DEFAULT 0,
        chat_type TEXT DEFAULT 'dm',
        session_id TEXT
    )
""")

conn.commit()
conn.close()
print("done")
