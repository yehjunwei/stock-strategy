#!/usr/bin/env python3
"""
檢查股票是否創三年新高並發送 Line 通知
功能：
- 檢查每支股票的最新 high 價格是否為近三年的新高點
- 如果是新高點，發送 Line 通知
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import os

# 嘗試載入 python-dotenv（如果有安裝的話）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 手動載入 .env 檔案
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)

# 添加父目錄到 Python 路徑以導入 core 模組
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.line_sender import send_line_message


def load_stock_data(data_file):
    """載入股票資料"""
    if not data_file.exists():
        print(f"❌ 找不到資料檔案: {data_file}")
        return None

    try:
        df = pd.read_csv(data_file)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"❌ 讀取資料檔案失敗: {e}")
        return None


def check_new_highs(df, years=3):
    """
    檢查哪些股票創下近期新高

    Args:
        df: 股票資料 DataFrame
        years: 檢查幾年內的新高（預設 3 年）

    Returns:
        list: 創新高的股票資訊列表
    """
    if df is None or df.empty:
        return []

    # 計算時間範圍
    latest_date = df['date'].max()
    start_date = latest_date - timedelta(days=years * 365)

    print(f"🔍 最新日期: {latest_date.date()}")
    print(f"📊 比對範圍: {start_date.date()} ~ {(latest_date - timedelta(days=1)).date()} (過去 {years} 年)")
    print(f"📌 邏輯: 檢查最新日期的 high 是否 > 過去 {years} 年內的所有 high\n")

    # 篩選近 N 年的資料（用於比對）
    df_recent = df[df['date'] >= start_date].copy()

    new_highs = []

    # 取得最新日期有交易的股票
    latest_df = df_recent[df_recent['date'] == latest_date]
    print(f"💼 最新日期有交易的股票數: {latest_df['stock_id'].nunique()} 支\n")

    # 對每支股票進行檢查
    for stock_id in latest_df['stock_id'].unique():
        # 該股票在近 N 年的所有歷史資料
        stock_data = df_recent[df_recent['stock_id'] == stock_id]

        if len(stock_data) < 2:
            continue

        # 【比對點1】最新日期的 high
        latest_record = stock_data[stock_data['date'] == latest_date].iloc[0]
        latest_high = latest_record['high']

        # 【比對點2】過去 N 年的最高價（不含最新日期）
        historical_data = stock_data[stock_data['date'] < latest_date]
        if historical_data.empty:
            continue

        historical_max = historical_data['high'].max()

        # 找出前高的日期
        previous_high_date = historical_data[historical_data['high'] == historical_max]['date'].max()

        # 檢查是否創新高
        if latest_high > historical_max:
            new_highs.append({
                'stock_id': stock_id,
                'stock_name': latest_record['stock_name'],
                'date': latest_date.date(),
                'latest_high': latest_high,
                'previous_high': historical_max,
                'previous_high_date': previous_high_date.date(),
                'increase': latest_high - historical_max,
                'increase_pct': ((latest_high - historical_max) / historical_max) * 100
            })

    return new_highs


def format_notification(new_highs, years=3):
    """格式化通知訊息"""
    if not new_highs:
        return f"📊 今日無股票創 {years} 年新高"

    message_lines = [
        f"🚀 創 {years} 年新高通知",
        f"📅 {new_highs[0]['date']} (共 {len(new_highs)} 支)",
        ""
    ]

    # 依照股票代號排序
    sorted_highs = sorted(new_highs, key=lambda x: x['stock_id'])

    for stock in sorted_highs:
        message_lines.append(
            f"{stock['stock_id']} ({stock['stock_name']}): "
            f"新高 ${stock['latest_high']:.2f} | "
            f"前高 ${stock['previous_high']:.2f} ({stock['previous_high_date']})"
        )

    return "\n".join(message_lines)


def main():
    """主程式"""
    print("\n" + "="*70)
    print("🔍 股票三年新高檢查工具")
    print("="*70 + "\n")

    # 資料檔案路徑
    project_root = Path(__file__).parent.parent
    data_file = project_root / 'data' / 'taiwan_stocks.csv'

    # 載入資料
    print("📂 載入股票資料...")
    df = load_stock_data(data_file)

    if df is None:
        print("\n❌ 無法載入資料，程式結束\n")
        return

    print(f"✓ 已載入 {len(df):,} 筆資料")
    print(f"✓ 股票數量: {df['stock_id'].nunique()} 支\n")

    # 檢查新高
    new_highs = check_new_highs(df, years=3)

    # 顯示結果
    if new_highs:
        print(f"🎉 發現 {len(new_highs)} 支股票創三年新高！\n")
        for stock in new_highs[:5]:  # 在終端只顯示前 5 支
            print(f"  • {stock['stock_name']} ({stock['stock_id']})")
            print(f"    最新高: ${stock['latest_high']:.2f} (前高: ${stock['previous_high']:.2f})")
            print(f"    突破幅度: +{stock['increase_pct']:.2f}%\n")

        if len(new_highs) > 5:
            print(f"  ... 及其他 {len(new_highs) - 5} 支股票\n")
    else:
        print("ℹ️  今日無股票創三年新高\n")

    # 發送 Line 通知
    message = format_notification(new_highs, years=3)
    print("📤 發送 Line 通知...")
    send_line_message(message)

    print("\n" + "="*70)
    print("✅ 檢查完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
