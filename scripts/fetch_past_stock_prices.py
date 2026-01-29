#!/usr/bin/env python3
"""
臺股歷史資料補齊工具 - 每次往前抓一個月
讀取 data/fetch_past_date_start.txt 的日期，往前抓一個月的資料
"""

import sys
from pathlib import Path
import time
import os
from datetime import datetime, timedelta

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


def read_start_date(file_path):
    """讀取起始日期檔案"""
    if not file_path.exists():
        # 如果檔案不存在，檢查現有資料的最早日期
        return None

    with open(file_path, 'r') as f:
        date_str = f.read().strip()
        return datetime.strptime(date_str, '%Y-%m-%d')


def write_start_date(file_path, date):
    """寫入新的起始日期"""
    with open(file_path, 'w') as f:
        f.write(date.strftime('%Y-%m-%d'))


def calculate_one_month_back(end_date):
    """計算往前一個月的日期範圍"""
    # end_date 是結束日期，往前推一個月
    # 使用較簡單的方式：往前推 30 天
    start_date = end_date - timedelta(days=30)
    return start_date, end_date


def main():
    """主程式 - 往前補齊一個月的歷史資料"""
    start_time = time.time()

    print("\n" + "="*70)
    print("🇹🇼  臺股歷史資料補齊工具 - 往前抓一個月")
    print("="*70 + "\n")

    # 初始化 fetcher
    api_token = os.getenv('FINMIND_API_TOKEN')
    fetcher = TaiwanStockFetcher(api_token=api_token)

    status_message = "✅ 執行成功"
    total_new = 0
    date_file = Path(__file__).parent.parent / 'data' / 'fetch_past_date_start.txt'

    try:
        # 讀取起始日期
        print("📝 讀取起始日期...")
        start_date_obj = read_start_date(date_file)

        if start_date_obj is None:
            # 如果沒有記錄檔，從現有資料的最早日期開始
            exists, earliest, latest, count = fetcher.get_existing_data_info()
            if exists and earliest:
                start_date_obj = datetime.strptime(earliest, '%Y-%m-%d')
                print(f"✓ 從現有資料的最早日期開始: {earliest}")
            else:
                # 如果沒有任何資料，從今天開始
                start_date_obj = datetime.now()
                print(f"✓ 沒有現有資料，從今天開始: {start_date_obj.strftime('%Y-%m-%d')}")
        else:
            print(f"✓ 從記錄檔讀取: {start_date_obj.strftime('%Y-%m-%d')}")

        # 計算要抓取的日期範圍（往前一個月）
        fetch_start, fetch_end = calculate_one_month_back(start_date_obj)

        # 確保不會抓取到未來的日期
        today = datetime.now()
        if fetch_end > today:
            fetch_end = today

        print(f"\n📅 本次抓取範圍:")
        print(f"   {fetch_start.strftime('%Y-%m-%d')} ~ {fetch_end.strftime('%Y-%m-%d')}")

        # 檢查是否已經到達目標日期（2010-01-01）
        target_date = datetime(2010, 1, 1)
        if fetch_start <= target_date:
            fetch_start = target_date
            print(f"\n⚠️  已接近目標日期 {target_date.strftime('%Y-%m-%d')}")

        # 獲取股票列表
        print("\n📝 獲取股票列表...")
        stock_list = fetcher.get_stock_list()
        if not stock_list:
            raise Exception("無法獲取股票列表")
        print(f"✓ 共 {len(stock_list)} 檔股票\n")

        # 抓取資料
        print(f"📥 開始抓取資料...")
        new_df = fetcher.fetch_batch(
            stock_list,
            fetch_start.strftime('%Y-%m-%d'),
            fetch_end.strftime('%Y-%m-%d'),
            delay=0.2
        )

        if not new_df.empty:
            total_new = len(new_df)
            print(f"✓ 獲取到 {total_new} 筆資料\n")

            # 儲存資料
            fetcher.merge_and_save(new_df)
            fetcher.show_preview(new_df, n=5)

            # 更新起始日期記錄（往前推）
            new_start_date = fetch_start - timedelta(days=1)
            write_start_date(date_file, new_start_date)
            print(f"\n✓ 已更新記錄檔，下次從 {new_start_date.strftime('%Y-%m-%d')} 繼續")

            # 檢查是否已完成
            if fetch_start <= target_date:
                status_message = "🎉 已完成所有歷史資料補齊到 2010-01-01"
                print(f"\n{status_message}")
        else:
            print("⚠️  未獲取到資料\n")
            status_message = "⚠️  未獲取到資料"

        # 顯示最終狀態
        _, earliest, latest, count = fetcher.get_existing_data_info()
        print(f"\n{'='*70}")
        print(f"✅ 執行完成！")
        print(f"   總記錄數: {count:,} 條")
        print(f"   日期範圍: {earliest} ~ {latest}")
        if earliest:
            remaining = (datetime.strptime(earliest, '%Y-%m-%d') - target_date).days
            if remaining > 0:
                print(f"   距離目標: 還需約 {remaining} 天")
            else:
                print(f"   🎉 已達成目標日期 2010-01-01！")
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

        summary_text = (
            f"\n- 執行狀態: {status_message}"
            f"\n- 抓取範圍: {fetch_start.strftime('%Y-%m-%d')} ~ {fetch_end.strftime('%Y-%m-%d')}"
            f"\n- 新增筆數: {total_new:,} 筆"
            f"\n- 執行耗時: {duration:.2f} 秒"
            f"\n- 資料庫狀態:"
            f"\n  - 總筆數: {count:,}"
            f"\n  - 日期範圍: {earliest} ~ {latest}"
        )

        final_message = f"【歷史資料補齊報告 - {hostname}】{summary_text}"
        send_line_message(final_message)


if __name__ == "__main__":
    main()
