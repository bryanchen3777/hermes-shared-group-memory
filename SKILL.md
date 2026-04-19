# SKILL.md - Shared Harem Memory v2.0

## Skill Identity

- Name: shared-harem-memory
- Version: 2.0.0
- Purpose: 後宮共享記憶系統，讓後宮成員能看到彼此的發言，同時確保私聊隱私
- Target: Hermes Agent 四個 profile（Yua / Rem / Ram / Mihiru）

## Core Concept

| 類型 | 可見範圍 |
|------|---------|
| 群組聊天 | 所有成員可見 Bryan 和所有後宮成員的群組發言 |
| Bryan 的私聊 | 只有接收訊息的 Bot 可見 |
| Bot 的私聊 | 只有 Bryan 可見 |

**核心原則**：每個 Bot 只能看到「自己說的話」和「Bryan 對自己說的話」，無法看到 Bryan 對其他 Bot 說的私聊。

## Group Detection Logic

`session_id` 同時出現在 2+ profile 的 `state.db` → 判定為群組聊天。

這是因為 Telegram 群組消息會同時廣播給所有 Bot，每個 Bot 都會在各自的 `state.db` 建立同一個 `session_id` 的記錄。

## Database Schema

```sql
CREATE TABLE group_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    profile_name TEXT,      -- Bryan / rem / ram / mihiru
    content TEXT,
    is_from_bryan INTEGER DEFAULT 0,
    chat_type TEXT DEFAULT 'dm',
    session_id TEXT,
    msg_id INTEGER,
    recipient TEXT DEFAULT 'all'
);
CREATE UNIQUE INDEX idx_msg_unique ON group_messages(session_id, msg_id);
CREATE INDEX idx_recipient ON group_messages(chat_type, profile_name, recipient);
```

## Privacy Logic

### Write Logic (`_sync_single_db`)

| 角色 | 情境 | recipient |
|------|------|-----------|
| Bryan | 群組廣播 | `"all"` |
| Bryan | 對單一 Bot 私聊 | `my_profile`（如 `"rem"`） |
| Bot | 對 Bryan 私聊 | `"Bryan"` |

### Read Logic (`read_shared_memory`)

```sql
-- 群聊：全部可見
WHERE chat_type='group'

-- 私聊：自己說的 + Bryan 對自己說的
WHERE chat_type='dm' AND (profile_name=? OR (profile_name='Bryan' AND recipient=?))
```

## Installation

### 1. Create shared database

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

### 2. Install Plugin per profile

```bash
# Yua（default）
mkdir -p ~/.hermes/plugins/shared_group_memory
cp __init__.py ~/.hermes/plugins/shared_group_memory/__init__.py

# 每個 Bot profile
mkdir -p ~/.hermes/profiles/rem/plugins/shared_group_memory
cp __init__.py ~/.hermes/profiles/rem/plugins/shared_group_memory/__init__.py

# ... ram, mihiru 同樣複製
```

### 3. Restart gateways

```bash
tmux new-session -d -s default "cd ~/.hermes && HERMES_HOME=~/.hermes ~/.local/bin/hermes gateway run"
tmux new-session -d -s rem "cd ~/.hermes/profiles/rem && HERMES_HOME=~/.hermes/profiles/rem ~/.local/bin/hermes gateway run"
```

## Plugin Hooks

- `_pre_llm_call`：同步 state.db → shared DB，並注入共享記憶 context
- `_post_llm_call`：LLM 呼叫後再次同步，確保及時寫入
