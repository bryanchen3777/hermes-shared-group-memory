# SKILL.md - Harem Chat Memory Plugins

## Skill Identity

- Name: harem-chat-memory
- Version: 2.0.0
- Purpose: 後宮多 bot 聊天記憶共享系統（雙插件）
- Target: Hermes Agent 多成員群聊系統

## Two Plugins

| Plugin | File | Hooks | Data Source |
|--------|------|-------|-------------|
| `global_memory` | `__init__.py` | `pre_llm_call` | `state.db` (read-only) |
| `shared_group_memory` | `__init__.py` | `pre_llm_call` + `post_llm_call` | `shared_group_memory.db` |

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

# 5. Restart gateway
hermes gateway restart
```

## Usage

自動運作，無需手動操作。

## Privacy

- Bryan 的訊息：全部可見
- 群聊訊息：全部成員可見
- 成員私聊：只有自己可見
