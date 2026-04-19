# Changelog

## [2.1.0] - 2026-04-18

### Added
- 測試資料庫 `shared_group_memory_test.db` 用於偵錯
- `msg_id` 欄位 + 唯一索引防止重複寫入
- 內容截斷至 200 字（節省儲存空間）
- profile 隔離：`state.db` 現在會讀取 profile 自己的資料庫
- 完整的 `create_table.py` DROP + CREATE 流程

### Features
- 訊息去重：`session_id + msg_id` 唯一索引
- 更強的偵錯能力：ping_log 追蹤所有事件
- 內容截斷：避免過長訊息佔用空間

## [2.0.0] - 2026-04-18

### Added
- 新增 `global_memory` 插件（讀取 state.db）
- 雙插件架構完整重構
- 完整的雙語 README（EN+CN）
- 詳細的隱私邏輯說明
- Plugin manifest 宣告

### Features
- `global_memory`：注入 Bryan 所有歷史訊息
- `shared_group_memory`：成員間共享群聊記憶
- 隱私分層：Bryan 全域可見、成員 DM 私密

## [1.0.0] - 2026-04-17

### Added
- 初始版本
- 單一 `shared_group_memory` 插件
