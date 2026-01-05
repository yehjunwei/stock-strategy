#!/usr/bin/env python3
"""測試 FinMind API 回應格式"""

import os
from FinMind.data import DataLoader

# 嘗試從 .env 檔案手動載入 token
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('FINMIND_API_TOKEN='):
                api_token = line.split('=', 1)[1].strip()
                break
    print(f"Token loaded: {api_token[:20]}..." if api_token else "Token not found!")
except Exception as e:
    api_token = None
    print(f"Could not load token: {e}")

# 初始化 API
api = DataLoader()

# 嘗試登入
if api_token:
    try:
        api.login_by_token(api_token=api_token)
        print("✓ Token login successful")
    except Exception as e:
        print(f"❌ Token login failed: {e}")

# 測試獲取股票列表
print("\n--- Testing taiwan_stock_info() ---")
try:
    result = api.taiwan_stock_info()
    print(f"Result type: {type(result)}")
    print(f"Result value: {result}")

    if result is not None:
        print(f"\nResult attributes: {dir(result)}")
        if hasattr(result, 'columns'):
            print(f"Columns: {result.columns.tolist()}")
        if hasattr(result, 'head'):
            print(f"\nFirst few rows:\n{result.head()}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
