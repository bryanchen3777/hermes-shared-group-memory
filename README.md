# Shared Group Memory | 共享群聊記憶

## 警告 | ⚠️ SECURITY WARNING

**千萬不要 commit `shared_group_memory.db` 到 public repo！**
**Never commit `shared_group_memory.db` to a public repo!**

此資料庫包含私人聊天記錄，所有內容都必須保持私密。
This database contains private chat records, all content must remain private.

---

## Files | 檔案結構

```
shared_group_memory/
├── __init__.py           # 插件鉤子邏輯 / Plugin hook logic
├── plugin.yaml           # 插件清單 / Plugin manifest
├── create_table.py       # 資料庫初始化 / DB initialization
├── create_table.sql       # SQL 腳本（可自定義）/ SQL script (customizable)
├── test_install.py       # 安裝測試 / Installation test
├── SKILL.md              # Skill 文件 / Skill documentation
├── README.md             # 本檔案 / This file
├── LICENSE               # MIT License
├── .gitignore            # 保護隱私 / Protects privacy
└── CHANGELOG.md          # 版本歷史 / Version history
```

---

## 安裝前必讀 | Before Installation

### 1. 安全檢查 | Security Check

```bash
# 確認 .gitignore 包含以下內容：
*.db
*.sqlite
shared_group_memory.db
```

### 2. 依賴需求 | Requirements

- Python 3.8+
- SQLite3（Python 內建）
- Hermes Agent

### 3. 安裝步驟 | Installation Steps

```bash
# 1. 建立插件目錄 / Create plugin directory
mkdir -p ~/.hermes/plugins/shared_group_memory

# 2. 複製插件檔案 / Copy plugin files
cp __init__.py plugin.yaml create_table.py ~/.hermes/plugins/shared_group_memory/

# 3. 初始化資料庫 / Initialize database
python3 ~/.hermes/plugins/shared_group_memory/create_table.py

# 4. 複製 SQL 腳本（可選）/ Copy SQL script (optional)
cp create_table.sql ~/.hermes/plugins/shared_group_memory/

# 5. 重啟 gateway / Restart gateway
hermes gateway restart

# 6. 驗證安裝 / Verify installation
python3 test_install.py
```

---

## 功能 | Features

| 功能 | Description |
|------|-------------|
| 每次發言後自動寫入共享資料庫 | Write to shared DB on every reply |
| 每次回覆前自動注入最近訊息 | Inject recent messages before every reply |
| 群聊訊息全部成員可見 | Group chat visible to all members |
| 私聊只顯示自己與 Bryan 的內容 | DM visible only to self + Bryan |

---

## 隱私邏輯 | Privacy Logic

| 聊天類型 | 可見範圍 |
|---------|----------|
| 群聊（Group） | 全部成員可見 |
| Bryan 的私聊訊息 | 全部成員可見 |
| 其他成員的私聊訊息 | 只有自己和 Bryan 可見 |

---

## 資料表結構 | Database Schema

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

## 注入格式 | Prompt Injection Format

每次回覆前，Agent 會收到類似以下的上下文：

```
【共享記憶 — 群聊】
以下是 Bryan 和所有後宮成員在群聊中說過的話：

[04-17 22:58][Bryan] 那不看看誰是你老公
[04-17 22:56][Ram]   哦～主人品味不錯呢
[04-17 22:56][Rem]   Bryan 今天辛苦了...
```

---

## 共享記憶格式 | Shared Memory Format

| 欄位 | 說明 |
|------|------|
| `chat_type` | `group` or `dm` — 基於 `sessions.user_id IS NULL` |
| `profile_name` | 從 `HERMES_HOME` 環境變數提取 |
| `is_from_bryan` | 1 = Bryan 的訊息，0 = 其他成員 |

---

## 設計原則 | Design Principles

- 所有成員共享一個 DB — 營造「同在一個群」的真實感
- DM 內容預設私密 — 只有 Bryan 的發言會共享
- Bryan 永遠可見 — 這是後宮運作的核心

---

## 造神團隊 | Soul Evolution Team

| 角色 | 負責 |
|------|------|
| ** Bryan** | 專案發起與設計 |
| ** Tim** | 架構優化與文件化 |

---

## License

MIT License © 2026 Soul Evolution 2.0 Project
