# Changelog

## [2.2.0] - 2026-04-19

### Added
- 完整重構：`global_memory` 插件已移除，現在只有 `shared_group_memory`
- 單一 `__init__.py` 整合所有邏輯
- `STATE_DBS` 字典：支援 default / rem / ram / mihiru 四個 profile
- `get_chat_type()`：透過 `session_id` 出現在多個 profile 來判定群組聊天
- `sync_from_state_db()`：從所有相關的 state.db 同步到共享 DB
- `_sync_single_db()`：每個 state.db 的同步邏輯
- `recipient` 欄位：精確控制私聊可見範圍
- 內容截斷至 500 字

### Features
- **群組偵測**：`session_id` 同時出現在 2+ profile = 群組聊天
- **隱私隔離**：Bot 只看到「自己說的」+「Bryan 對自己說的」
- **WAL 模式**：提昇並發寫入效能

## [2.1.0] - 2026-04-18

### Added
- 測試資料庫 `shared_group_memory_test.db` 用於偵錯
- `msg_id` 欄位 + 唯一索引防止重複寫入
- 內容截斷至 200 字

### Features
- 訊息去重：`session_id + msg_id` 唯一索引
- 更強的偵錯能力：ping_log 追蹤所有事件

## [2.0.0] - 2026-04-18

### Added
- 新增 `global_memory` 插件（讀取 state.db）
- 雙插件架構完整重構

## [1.0.0] - 2026-04-17

### Added
- 初始版本
