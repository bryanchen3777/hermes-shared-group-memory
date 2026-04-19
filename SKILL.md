# SKILL.md - Harem Chat Memory Plugins v2.1

## Skill Identity

- Name: harem-chat-memory
- Version: 2.1.0
- Purpose: 後宮多 bot 聊天記憶共享系統（雙插件）
- Target: Hermes Agent 多成員群聊系統

## Two Plugins

| Plugin | File | Hooks | Data Source |
|--------|------|-------|-------------|
| `global_memory` | `__init__.py` | `pre_llm_call` | `state.db` (read-only) |
| `shared_group_memory` | `__init__.py` | `pre_llm_call` + `post_llm_call` | `shared_group_memory.db` |

## What's New in v2.1

- **測試資料庫**：`shared_group_memory_test.db` 用於偵錯所有事件
- **訊息去重**：`msg_id` + `session_id` 唯一索引，防止重複寫入
- **內容截斷**：200 字上限，節省儲存空間
- **Profile 隔離**：現在會讀取 profile 自己的 `state.db`

## Installation

```bash
# 1. Create plugin directories
mkdir -p ~/.hermes/plugins/global_memory
mkdir -p ~/.hermes/plugins/shared_group_memory

# 2. Copy global_memory plugin
cp global_memory/__init__.py global_memory/plugin.yaml \
   ~/.hermes/plugins/global_memory/

# 3. Copy shared_group_memory plugin
cp shared_group_memory/__init__.py shared_group_memory/plugin.yaml \
   shared_group_memory/create_table.py \
   ~/.hermes/plugins/shared_group_memory/

# 4. Initialize shared DB
python3 ~/.hermes/plugins/shared_group_memory/create_table.py

# 5. For each profile, also install plugins
mkdir -p ~/.hermes/profiles/rem/plugins
mkdir -p ~/.hermes/profiles/ram/plugins
# Copy both plugins to each profile's plugins/ directory

# 6. Restart gateway
hermes gateway restart
```

## Usage

自動運作，無需手動操作。

## Privacy

- Bryan 的訊息：全部可見
- 群聊訊息：全部成員可見
- 成員私聊：只有自己可見
