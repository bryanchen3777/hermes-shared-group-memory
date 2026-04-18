-- create_table.sql
-- Shared Group Memory Database Initialization Script
-- 可以自定義，但預設已經在 create_table.py 中執行

CREATE TABLE IF NOT EXISTS group_messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    REAL,
    profile_name TEXT,      -- Bryan / Rem / Ram / Yua
    content      TEXT,
    is_from_bryan INTEGER DEFAULT 0,
    chat_type    TEXT DEFAULT 'dm',  -- 'group' or 'dm'
    session_id   TEXT
);

-- 可選：建立索引加速查詢
CREATE INDEX IF NOT EXISTS idx_chat_type ON group_messages(chat_type);
CREATE INDEX IF NOT EXISTS idx_profile ON group_messages(profile_name);
CREATE INDEX IF NOT EXISTS idx_timestamp ON group_messages(timestamp DESC);
