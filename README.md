# 後宮共享記憶系統 — Shared Harem Memory

讓後宮成員（Yua / Rem / Ram / Mihiru）能看到彼此在群組和私聊中說過的話，同時確保私聊隱私。

## 隱私設計

| 類型 | 可見範圍 |
|------|---------|
| 群組聊天 | 所有成員可見 Bryan 和所有後宮成員的群組發言 |
| Bryan 的私聊 | 只有接收訊息的 Bot 可見 |
| Bot 的私聊 | 只有 Bryan 可見 |

**核心原則**：每個 Bot 只能看到「自己說的話」和「Bryan 對自己說的話」，無法看到 Bryan 對其他 Bot 說的私聊。

## 資料庫 Schema

```sql
CREATE TABLE group_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    profile_name TEXT,      -- 發送者：B Bryan / rem / ram / mihiru
    content TEXT,
    is_from_bryan INTEGER,   -- 1 = Bryan，0 = Bot
    chat_type TEXT,          -- 'group' 或 'dm'
    session_id TEXT,
    msg_id INTEGER,
    recipient TEXT            -- 'all' = 群聊，'Bryan' = Bot對Bryan，BOT名 = Bryan對該Bot
);
CREATE UNIQUE INDEX idx_msg_unique ON group_messages(session_id, msg_id);
CREATE INDEX idx_recipient ON group_messages(chat_type, profile_name, recipient);
```

## 隱私隔離邏輯

### 寫入時（`_sync_single_db`）

| 角色 | 情境 | recipient |
|------|------|-----------|
| Bryan | 群組廣播 | `"all"` |
| Bryan | 對單一 Bot 私聊 | `my_profile`（如 `"rem"`） |
| Bot | 對 Bryan 私聊 | `"Bryan"` |

### 讀取時（`read_shared_memory`）

```sql
-- 群聊：全部可見
WHERE chat_type='group'

-- 私聊：自己說的 + Bryan 對自己說的
WHERE chat_type='dm' AND (profile_name=? OR (profile_name='Bryan' AND recipient=?))
```

## Group 偵測邏輯

`session_id` 同時出現在 2+ profile 的 state.db → 判定為群組聊天。

這是因為 Telegram 群組消息會同時廣播給所有 Bot，每個 Bot 都會在各自的 state.db 建立同一個 `session_id` 的記錄。

## 安裝方式

### 1. 建立共享資料庫

```bash
mkdir -p ~/.hermes
sqlite3 ~/.hermes/shared_group_memory.db <<'EOF'
CREATE TABLE IF NOT EXISTS group_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    profile_name TEXT,
    content TEXT,
    is_from_bryan INTEGER DEFAULT 0,
    chat_type TEXT DEFAULT 'dm',
    session_id TEXT,
    msg_id INTEGER,
    recipient TEXT DEFAULT 'all'
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_msg_unique ON group_messages(session_id, msg_id);
CREATE INDEX IF NOT EXISTS idx_recipient ON group_messages(chat_type, profile_name, recipient);
EOF
```

### 2. 安裝 Plugin

每個 Bot profile 的 gateway 只載入自己目錄下的 plugin：

```bash
# Yua（default）
mkdir -p ~/.hermes/plugins/shared_group_memory
cp __init__.py ~/.hermes/plugins/shared_group_memory/__init__.py

# 每個 Bot profile
mkdir -p ~/.hermes/profiles/rem/plugins/shared_group_memory
cp __init__.py ~/.hermes/profiles/rem/plugins/shared_group_memory/__init__.py

mkdir -p ~/.hermes/profiles/ram/plugins/shared_group_memory
cp __init__.py ~/.hermes/profiles/ram/plugins/shared_group_memory/__init__.py

mkdir -p ~/.hermes/profiles/mihiru/plugins/shared_group_memory
cp __init__.py ~/.hermes/profiles/mihiru/plugins/shared_group_memory/__init__.py
```

### 3. 重啟 Gateway

```bash
# 個別重啟（會卡住，建議用 tmux）
hermes -p rem gateway restart

# tmux 一次重啟全部
tmux kill-session -t default 2>/dev/null
tmux kill-session -t rem 2>/dev/null
tmux kill-session -t ram 2>/dev/null
tmux kill-session -t mihiru 2>/dev/null
tmux new-session -d -s default "cd ~/.hermes && HERMES_HOME=~/.hermes ~/.local/bin/hermes gateway run"
tmux new-session -d -s rem "cd ~/.hermes/profiles/rem && HERMES_HOME=~/.hermes/profiles/rem ~/.local/bin/hermes gateway run"
tmux new-session -d -s ram "cd ~/.hermes/profiles/ram && HERMES_HOME=~/.hermes/profiles/ram ~/.local/bin/hermes gateway run"
tmux new-session -d -s mihiru "cd ~/.hermes/profiles/mihiru && HERMES_HOME=~/.hermes/profiles/mihiru ~/.local/bin/hermes gateway run"
```

## Plugin Hooks

- **`_pre_llm_call`**：每次 LLM 呼叫前，同步 state.db → shared DB，並注入共享記憶 context
- **`_post_llm_call`**：LLM 呼叫後再次同步，確保及時寫入

## 依賴

- Hermes Agent
- Python 3.x（sqlite3、os、datetime、typing）
- 四個 profile 的 state.db 須存在於同一机器
