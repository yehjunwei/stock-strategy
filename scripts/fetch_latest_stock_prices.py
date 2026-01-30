#!/usr/bin/env python3
"""
臺股每日資料獲取工具 - 抓取缺失資料並檢查新高
流程：
1. 從 CSV 最新日期抓取到昨天的資料
2. 計算三年新高
3. 發送 LINE 通知
"""

import sys
from pathlib import Path
import time
import os
from datetime import datetime, timedelta
import pandas as pd

# 嘗試載入 python-dotenv（如果有安裝的話）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 手動載入 .env
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

from core.stock_fetcher import TaiwanStockFetcher
from core.line_sender import send_line_message


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

    # 確保 date 欄位是 datetime
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # 計算時間範圍
    latest_date = df['date'].max()
    start_date = latest_date - timedelta(days=years * 365)

    print(f"🔍 最新日期: {latest_date.date()}")
    print(f"📊 比對範圍: {start_date.date()} ~ {(latest_date - timedelta(days=1)).date()} (過去 {years} 年)")

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


def format_new_high_notification(new_highs, years=3):
    """格式化新高通知訊息"""
    if not new_highs:
        return None

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
    """主程式 - 抓取缺失資料並檢查新高"""
    start_time = time.time()
    today = datetime.now()
    yesterday = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    print("\n" + "="*70)
    print(f"🇹🇼  臺股每日資料獲取工具 - {today_str}")
    print("="*70 + "\n")

    # 初始化 fetcher
    api_token = os.getenv('FINMIND_API_TOKEN')
    fetcher = TaiwanStockFetcher(api_token=api_token)

    status_message = "✅ 執行成功"
    total_new = 0
    new_highs = []

    try:
        # 檢查現有資料
        exists, earliest, latest, count = fetcher.get_existing_data_info()

        if exists and latest:
            print(f"📂 現有資料: {earliest} ~ {latest} ({count:,} 筆)")

            # 計算需要抓取的日期範圍
            latest_date = datetime.strptime(latest, '%Y-%m-%d')
            yesterday_date = datetime.strptime(yesterday, '%Y-%m-%d')

            if latest_date >= yesterday_date:
                print(f"✓ 資料已是最新（{latest}），無需抓取\n")
            else:
                # 需要抓取的起始日期 = 最新日期 + 1 天
                fetch_start = (latest_date + timedelta(days=1)).strftime('%Y-%m-%d')
                fetch_end = yesterday

                days_gap = (yesterday_date - latest_date).days
                print(f"📥 需補齊 {days_gap} 天資料: {fetch_start} ~ {fetch_end}\n")

                # 獲取股票列表
                print("📝 獲取股票列表...")
                stock_list = fetcher.get_stock_list()
                if not stock_list:
                    raise Exception("無法獲取股票列表")
                print(f"✓ 共 {len(stock_list)} 檔股票\n")

                # 抓取資料
                new_df = fetcher.fetch_batch(stock_list, fetch_start, fetch_end, delay=0.2)

                if not new_df.empty:
                    total_new = len(new_df)
                    print(f"✓ 獲取到 {total_new} 筆資料\n")

                    # 儲存資料
                    fetcher.merge_and_save(new_df)
                    fetcher.show_preview(new_df, n=5)
                else:
                    print("⚠️  未獲取到資料（可能是休市日）\n")
        else:
            print("📂 無現有資料，抓取最近 30 天...\n")
            fetch_start = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            fetch_end = yesterday

            # 獲取股票列表
            print("📝 獲取股票列表...")
            stock_list = fetcher.get_stock_list()
            if not stock_list:
                raise Exception("無法獲取股票列表")
            print(f"✓ 共 {len(stock_list)} 檔股票\n")

            # 抓取資料
            new_df = fetcher.fetch_batch(stock_list, fetch_start, fetch_end, delay=0.2)

            if not new_df.empty:
                total_new = len(new_df)
                fetcher.merge_and_save(new_df)

        # 檢查三年新高（僅在資料為最新時執行）
        _, _, latest, _ = fetcher.get_existing_data_info()
        if latest != yesterday:
            print(f"\n⚠️  資料不是最新（最新: {latest}，預期: {yesterday}），跳過新高檢查\n")
        else:
            print("\n" + "="*70)
            print("🔍 檢查三年新高...")
            print("="*70 + "\n")

            data_file = fetcher.csv_path
            if data_file.exists():
                df = pd.read_csv(data_file)
                new_highs = check_new_highs(df, years=3)

                if new_highs:
                    print(f"🎉 發現 {len(new_highs)} 支股票創三年新高！\n")
                    for stock in new_highs[:5]:
                        print(f"  • {stock['stock_name']} ({stock['stock_id']})")
                        print(f"    最新高: ${stock['latest_high']:.2f} (前高: ${stock['previous_high']:.2f})")
                        print(f"    突破幅度: +{stock['increase_pct']:.2f}%\n")

                    if len(new_highs) > 5:
                        print(f"  ... 及其他 {len(new_highs) - 5} 支股票\n")
                else:
                    print("ℹ️  今日無股票創三年新高\n")

        # 顯示最終狀態
        _, earliest, latest, count = fetcher.get_existing_data_info()
        print(f"\n{'='*70}")
        print(f"✅ 執行完成！")
        print(f"   總記錄數: {count:,} 條")
        print(f"   日期範圍: {earliest} ~ {latest}")
        print(f"{'='*70}\n")

    except KeyboardInterrupt:
        status_message = "⚠️  執行被使用者中斷"
        print(f"\n\n{status_message}\n")
    except Exception as e:
        status_message = f"❌ 發生錯誤: {e}"
        print(f"\n\n{status_message}\n")
        import traceback
        traceback.print_exc()
    finally:
        # 發送 LINE 通知
        duration = time.time() - start_time
        _, earliest, latest, count = fetcher.get_existing_data_info()

        try:
            hostname = os.uname().nodename
        except Exception:
            hostname = "Unknown"

        # 資料獲取報告
        summary_text = (
            f"\n- 執行狀態: {status_message}"
            f"\n- 新增筆數: {total_new:,} 筆"
            f"\n- 執行耗時: {duration:.2f} 秒"
            f"\n- 資料庫狀態:"
            f"\n  - 總筆數: {count:,}"
            f"\n  - 日期範圍: {earliest} ~ {latest}"
        )

        fetch_message = f"【股市資料獲取報告 - {hostname}】{summary_text}"
        send_line_message(fetch_message)

        # 新高通知（僅在資料為最新時發送）
        if latest == yesterday:
            new_high_message = format_new_high_notification(new_highs, years=3)
            if new_high_message:
                send_line_message(new_high_message)
            else:
                send_line_message(f"📊 {latest} 無股票創 3 年新高")
        else:
            send_line_message(f"⚠️ 資料未更新至 {yesterday}（目前最新: {latest}），跳過新高檢查")


if __name__ == "__main__":
    main()
