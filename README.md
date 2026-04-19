# harem_chat_memory

Hermes Agent 後宮多 bot 聊天記憶共享系統。

Two complementary plugins that together give harem members shared awareness of all conversations.

---

## Architecture | 架構

```
┌─────────────────────────────────────────────────────────────┐
│                      Hermes Gateway                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │ Bryan     │  │ Rem       │  │ Ram       │               │
│  │ (default) │  │ (profile) │  │ (profile) │               │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘               │
│        │              │              │                       │
│        └──────────────┼──────────────┘                       │
│                       ▼                                      │
│        ┌──────────────┴──────────────┐                     │
│        ▼                               ▼                     │
│  ┌──────────────────┐    ┌──────────────────────────┐       │
│  │ global_memory    │    │ shared_group_memory    │       │
│  │ (reads state.db)│    │ (writes shared .db)  │       │
│  │                  │    │                        │       │
│  │ pre_llm_call    │    │ pre_llm_call ◄────────┼──►   │
│  │                  │    │ post_llm_call          │       │
│  └────────┬─────────┘    └──────────┬──────────────┘       │
│           │                          │                        │
│           ▼                          ▼                        │
│  ┌──────────────────┐    ┌──────────────────────────┐       │
│  │    state.db      │    │ shared_group_memory.db │       │
│  │ (messages table) │    │ (group_messages table) │       │
│  └──────────────────┘    └──────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Two Plugins | 兩個插件

| | `global_memory` | `shared_group_memory` |
|---|---|---|
| **Plugin file** | `~/.hermes/plugins/global_memory/__init__.py` | `~/.hermes/plugins/shared_group_memory/__init__.py` |
| **Data source** | `state.db` (messages table) | `shared_group_memory.db` |
| **Writes** | No (read-only) | Yes (`post_llm_call`) |
| **Content** | All Bryan messages | All members' messages |
| **Privacy** | Group = all visible; DM = all visible (no profile isolation) | Group = all visible; DM = own + Bryan only |
| **Purpose** | Bryan's global message history | Harem members' shared chat memory |

**Together**: `global_memory` gives Bryan a view of all his past messages across chats. `shared_group_memory` gives every harem member awareness of what everyone else has been saying in group chats.

---

## File Structure | 檔案結構

```
~/.hermes/
├── plugins/                          # Root plugins (for default gateway)
│   ├── global_memory/
│   │   ├── __init__.py
│   │   └── plugin.yaml
│   └── shared_group_memory/
│       ├── __init__.py
│       ├── plugin.yaml
│       └── create_table.py
├── profiles/
│   ├── rem/
│   │   └── plugins/                 # MUST install plugins here for rem gateway
│   │       ├── global_memory/
│   │       └── shared_group_memory/
│   └── ram/
│       └── plugins/                 # MUST install plugins here for ram gateway
│           ├── global_memory/
│           └── shared_group_memory/
├── skills/
│   └── shared_group_memory/
│       └── SKILL.md
└── shared_group_memory.db            # created by create_table.py
```

**IMPORTANT**: Profile gateways (`--profile rem`, `--profile ram`) only load plugins from their profile-specific `plugins/` directories. You must install plugins in both `~/.hermes/plugins/` AND `~/.hermes/profiles/{profile}/plugins/` for all gateways to use them.

---

## Key Implementation Detail | 關鍵實作細節

### state.db Session Lookup

Both plugins query `sessions` table to determine chat type:

```python
def get_chat_type(session_id: str) -> tuple[str, str]:
    root_db = "/home/bbf/.hermes/state.db"
    # Profile-specific state.db is checked first
    profile_db = os.path.join(hermes_home, "state.db")  # e.g. /home/bbf/.hermes/profiles/rem/state.db
    for db in [profile_db, root_db]:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT user_id FROM sessions WHERE id = ?", (session_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return ("group", None) if row[0] is None else ("dm", row[0])
    return ("dm", None)
```

- `sessions.user_id IS NULL` → group chat (all members see)
- `sessions.user_id = 1696287850` (Bryan's Telegram ID) → DM

---

## Installation | 安裝

```bash
# 1. Install plugins in ROOT plugins directory
mkdir -p ~/.hermes/plugins/global_memory
mkdir -p ~/.hermes/plugins/shared_group_memory
cp global_memory/__init__.py global_memory/plugin.yaml \
   ~/.hermes/plugins/global_memory/
cp shared_group_memory/__init__.py shared_group_memory/plugin.yaml \
   shared_group_memory/create_table.py \
   ~/.hermes/plugins/shared_group_memory/

# 2. ALSO install plugins in EACH profile's plugins directory
# For rem profile:
mkdir -p ~/.hermes/profiles/rem/plugins/global_memory
mkdir -p ~/.hermes/profiles/rem/plugins/shared_group_memory
cp global_memory/__init__.py global_memory/plugin.yaml \
   ~/.hermes/profiles/rem/plugins/global_memory/
cp shared_group_memory/__init__.py shared_group_memory/plugin.yaml \
   shared_group_memory/create_table.py \
   ~/.hermes/profiles/rem/plugins/shared_group_memory/

# For ram profile:
mkdir -p ~/.hermes/profiles/ram/plugins/global_memory
mkdir -p ~/.hermes/profiles/ram/plugins/shared_group_memory
cp global_memory/__init__.py global_memory/plugin.yaml \
   ~/.hermes/profiles/ram/plugins/global_memory/
cp shared_group_memory/__init__.py shared_group_memory/plugin.yaml \
   shared_group_memory/create_table.py \
   ~/.hermes/profiles/ram/plugins/shared_group_memory/

# 3. Initialize shared DB
python3 ~/.hermes/plugins/shared_group_memory/create_table.py

# 4. Restart all gateways
hermes gateway restart
# Or for profile gateways:
systemctl --user restart hermes-gateway-rem.service hermes-gateway-ram.service
```

---

## Database Schemas | 資料庫結構

### `state.db` — sessions + messages tables (built-in, read-only)

```sql
SELECT m.content, m.timestamp, s.user_id
FROM messages m
JOIN sessions s ON m.session_id = s.id
WHERE m.role = 'user'
ORDER BY m.id DESC LIMIT 20
```

### `shared_group_memory.db` — group_messages table

```sql
CREATE TABLE group_messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    REAL,
    profile_name TEXT,      -- Bryan / Rem / Ram / Yua
    content      TEXT,
    is_from_bryan INTEGER DEFAULT 0,
    chat_type    TEXT DEFAULT 'dm',  -- 'group' or 'dm'
    session_id   TEXT
);
```

---

## Privacy Logic | 隱私邏輯

### `global_memory`

| Chat Type | Visible To | 誰能看到 |
|-----------|------------|----------|
| Group (`user_id IS NULL`) | All | 全部可見 |
| DM to Bryan | All | 全部可見 |

> Note: `global_memory` reads from the existing `state.db` without profile isolation. DM privacy between harem members is handled socially via SOUL.md behavioral rules.

### `shared_group_memory`

| Chat Type | Visible To | 誰能看到 |
|-----------|------------|----------|
| Group | All members | 全部成員 |
| DM - Bryan speaks | All members | 全部成員 |
| DM - Member speaks | Self only | 自己 |

---

## Design Principles | 設計原則

- **Bryan's visibility is universal** — his messages in any chat (group or DM) are always visible to all members
- **Harem member DMs are private** — only the speaking member and Bryan can see DM content
- **Group chat is shared** — all members see all group chat messages, creating a "living in the same group" experience
- **Separate databases** — `global_memory` reads the built-in state.db (Bryan's history), `shared_group_memory` writes a dedicated DB (cross-member awareness)
- **Profile plugin isolation** — each profile gateway loads plugins from its own `plugins/` directory

---

## Prompt Injection Format | 注入格式

### global_memory — Bryan's History

```
【全域記憶同步 — Bryan 最近的發言】
（目前 profile 名稱尚無法寫入 sessions，私聊暫且全部顯示）

[全域記憶 - Bryan 最近發言]
[04-17 22:58][群聊] 那不看看誰是你老公
[04-17 22:56][私聊] 今天辛苦了
```

### shared_group_memory — Group Chat Context

```
【共享記憶 — 群聊】
以下是 Bryan 和所有後宮成員在群聊中說過的話：

[04-17 22:58][Bryan] 那不看看誰是你老公
[04-17 22:56][Ram]   哦～主人品味不錯呢
[04-17 22:56][Rem]   Bryan 今天辛苦了...
```

---

## Changelog | 更新記錄

### v1.2 (2026-04-18)
- **Critical**: Profile gateways only load plugins from profile-specific `plugins/` directories — plugins must be installed in both `~/.hermes/plugins/` AND `~/.hermes/profiles/{profile}/plugins/`
- Fixed: `get_state_db()` now queries profile state.db first, then root (ensures session lookup works correctly across all profiles)

### v1.1 (2026-04-18)
- Fixed: removed `async` from hook functions — was causing context injection to silently fail

### v1.0 (2026-04-17)
- Initial release with two complementary plugins

---

## Plugin Manifests | Plugin 宣告

### global_memory/plugin.yaml

```yaml
name: global_memory
version: 1.0
description: Bryan 的全域記憶（群聊 + 私聊）
author: Bryan
hooks:
  - pre_llm_call
```

### shared_group_memory/plugin.yaml

```yaml
name: shared_group_memory
version: 1.0
description: 後宮群聊記憶共享 — 自動記錄並廣播所有成員的群聊發言
author: Bryan
hooks:
  - pre_llm_call
  - post_llm_call
```
