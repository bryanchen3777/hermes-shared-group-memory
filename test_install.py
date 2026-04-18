#!/usr/bin/env python3
"""
test_install.py
驗證 shared_group_memory 插件是否正確安裝
"""

import os
import sys
import sqlite3


def test_import():
    """測試是否能夠 import 插件"""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import __init__ as sg_memory
        print("[PASS] import __init__")
        return True
    except Exception as e:
        print(f"[FAIL] import __init__: {e}")
        return False


def test_profile_name():
    """測試 get_profile_name() 函數"""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import __init__ as sg_memory
        profile = sg_memory.get_profile_name()
        print(f"[PASS] get_profile_name() = {profile}")
        return True
    except Exception as e:
        print(f"[FAIL] get_profile_name(): {e}")
        return False


def test_db_connection():
    """測試資料庫連接"""
    db_path = "/home/bbf/.hermes/shared_group_memory.db"
    if not os.path.exists(db_path):
        print(f"[WARN] Database not found at {db_path}")
        print("[WARN] 請先執行 create_table.py")
        return True  # 不算失敗，只是还没初始化

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM group_messages")
        count = c.fetchone()[0]
        conn.close()
        print(f"[PASS] Database connection OK, {count} messages stored")
        return True
    except Exception as e:
        print(f"[FAIL] Database connection: {e}")
        return False


def test_read_function():
    """測試讀取函數"""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import __init__ as sg_memory
        result = sg_memory.read_shared_memory("group", "test", limit=5)
        print(f"[PASS] read_shared_memory() returned {len(result)} chars")
        return True
    except Exception as e:
        print(f"[FAIL] read_shared_memory(): {e}")
        return False


def main():
    print("===== Shared Group Memory 安裝測試 =====\n")

    results = []
    results.append(test_import())
    results.append(test_profile_name())
    results.append(test_db_connection())
    results.append(test_read_function())

    print("\n===== 測試結果 =====")
    if all(results):
        print("所有測試通過！插件已正確安裝。")
        return 0
    else:
        print("部分測試失敗，請檢查上述錯誤。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
