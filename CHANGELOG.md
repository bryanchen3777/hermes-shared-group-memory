# Changelog

## [1.0.0] - 2026-04-18

### Added
- 初始版本 / Initial release
- `__init__.py`: 插件鉤子邏輯
- `plugin.yaml`: 插件清單
- `create_table.py`: 資料庫初始化
- `create_table.sql`: SQL 腳本（可自定義）
- `test_install.py`: 安裝測試腳本
- 雙語 README（EN+CN）
- `.gitignore`: 保護隱私

### Features
- 每次發言後自動寫入共享資料庫
- 每次回覆前自動注入最近訊息
- 群聊訊息全部成員可見
- DM 內容預設私密
