# SKILL.md - Shared Group Memory Plugin

## Skill Identity

- Name: shared-group-memory
- Version: 1.0.0
- Purpose: 後宮多 bot 群聊記憶共享系統
- Target: Hermes Agent 多成員群聊系統

## Pre-installation

1. 確認 `.gitignore` 包含 `*.db`
2. 確認有 Python 3.8+

## Installation

```bash
# 1. Create plugin directory
mkdir -p ~/.hermes/plugins/shared_group_memory

# 2. Copy plugin files
cp __init__.py plugin.yaml create_table.py ~/.hermes/plugins/shared_group_memory/

# 3. Initialize database
python3 ~/.hermes/plugins/shared_group_memory/create_table.py

# 4. Restart gateway
hermes gateway restart
```

## Usage

自動運作，無需手動操作。每次發言/回覆都會自動寫入/讀取共享記憶。

## Integration

- `pre_llm_call`: 讀取共享記憶並注入 prompt
- `post_llm_call`: 寫入新訊息到共享資料庫
