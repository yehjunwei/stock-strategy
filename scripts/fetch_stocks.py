#!/usr/bin/env python3
"""
臺股歷史資料增量獲取工具 - 主程式
- 先更新到最新日期（今天）
- 再往前補充資料至 2000-01-01
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime
import time
import os

# 添加父目錄到 Python 路徑以導入 core 模組
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stock_fetcher import TaiwanStockFetcher
from core.line_sender import send_line_message


def parse_arguments():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(description='臺股歷史資料增量獲取工具')
    parser.add_argument(
        '--test',
        type=str,
        help='測試模式：只抓取指定股票代號（例如：2330）'
    )
    return parser.parse_args()


def print_header(test_mode=None):
    """列印程式標題"""
    print("\n" + "="*70)
    print("🇹🇼  臺股歷史資料增量獲取工具")
    if test_mode:
        print(f"   [測試模式: 僅抓取 {test_mode}]")
    print("="*70 + "\n")


def check_existing_data(fetcher):
    """檢查現有資料並列印資訊"""
    print("🔍 檢查現有資料...")
    exists, earliest, latest, count = fetcher.get_existing_data_info()

    if exists:
        print(f"✓ 找到現有資料檔案")
        print(f"   記錄數: {count:,} 條")
        print(f"   日期範圍: {earliest} ~ {latest}")
    else:
        print("ℹ️  未找到現有資料，將開始首次獲取")

    return exists, earliest, latest, count


def check_data_complete(fetcher, earliest):
    """檢查資料是否已完整"""
    if earliest and earliest <= fetcher.TARGET_START_DATE:
        print(f"\n🎉 資料已完整！")
        print(f"   涵蓋範圍: {earliest} ~ 今天")
        print(f"   已到達目標日期 {fetcher.TARGET_START_DATE}\n")
        return True
    return False


def print_fetch_plan(fetch_ranges):
    """列印抓取計畫"""
    print(f"\n📌 本次抓取計畫:")
    for idx, (start, end, desc) in enumerate(fetch_ranges, 1):
        print(f"   階段{idx}: {desc}")
        print(f"           {start} ~ {end}")


def prepare_stock_list(fetcher, test_mode):
    """準備股票列表"""
    if test_mode:
        stock_list = [test_mode]
        print(f"\n🧪 測試模式: 僅抓取 {test_mode}")
    else:
        stock_list = fetcher.get_stock_list()
        if not stock_list:
            print("\n❌ 無法獲取股票列表，退出\n")
            return None
    return stock_list


def estimate_time(stock_list, fetch_ranges):
    """估算所需時間"""
    total_ranges = len(fetch_ranges)
    estimated_minutes = len(stock_list) * 0.5 / 60 * total_ranges
    print(f"\n⏱️  預計耗時: {estimated_minutes:.0f}-{estimated_minutes*2:.0f} 分鐘")


def fetch_all_ranges(fetcher, stock_list, fetch_ranges):
    """逐階段獲取所有資料"""
    total_new_records = 0
    for idx, (start_date, end_date, desc) in enumerate(fetch_ranges, 1):
        print(f"\n{'='*70}")
        print(f"開始階段 {idx}/{len(fetch_ranges)}: {desc}")
        print(f"{'='*70}")

        new_df = fetcher.fetch_batch(stock_list, start_date, end_date, delay=0.2)

        if not new_df.empty:
            total_new_records += len(new_df)
            fetcher.merge_and_save(new_df)
            if idx == len(fetch_ranges):
                fetcher.show_preview(new_df, n=5)
        else:
            print("⚠️  本階段未獲取到資料\n")
    return total_new_records


def print_final_summary(fetcher):
    """列印最終摘要"""
    _, new_earliest, new_latest, new_count = fetcher.get_existing_data_info()

    print(f"\n{'='*70}")
    print(f"✅ 所有階段完成！")
    print(f"   最新狀態: {new_earliest} ~ {new_latest}")
    print(f"   總記錄數: {new_count:,} 條")

    if new_earliest and new_earliest > fetcher.TARGET_START_DATE:
        remaining = (
            datetime.strptime(new_earliest, '%Y-%m-%d') -
            datetime.strptime(fetcher.TARGET_START_DATE, '%Y-%m-%d')
        ).days
        print(f"   還需補充: 約 {remaining} 天")
        print(f"💡 提示: 再次執行可繼續補充歷史資料")
    else:
        print(f"🎉 恭喜！已完成所有資料獲取到 {fetcher.TARGET_START_DATE}")

    print(f"{'='*70}\n")


def main():
    """主程式"""
    start_time = time.time()
    status_message = "✅ 執行成功"
    total_new = 0

    # API Token 配置
    api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMS0wNiAwMDo1OTo0MCIsInVzZXJfaWQiOiJ5ZWhqdW53ZWkiLCJlbWFpbCI6InllaGp1bndlaUBnbWFpbC5jb20iLCJpcCI6IjgyLjE0MC4xODcuMjMifQ.cJNVY5xd2VHJHywKUzr89hewHWtZLymLyKzlAK0wPvs"
    fetcher = TaiwanStockFetcher(api_token=api_token)

    try:
        args = parse_arguments()
        print_header(args.test)

        # 檢查現有資料
        exists, earliest, latest, count = check_existing_data(fetcher)

        # 檢查是否已完整
        if exists and check_data_complete(fetcher, earliest):
            status_message = "🎉 資料已完整，無需執行"
            return

        # 計算抓取範圍
        fetch_ranges = fetcher.calculate_fetch_ranges(earliest, latest)
        if not fetch_ranges:
            status_message = "🎉 資料已是最新，無需執行"
            print(f"\n{status_message}\n")
            return

        # 列印計畫
        print_fetch_plan(fetch_ranges)

        # 準備股票列表
        stock_list = prepare_stock_list(fetcher, args.test)
        if not stock_list:
            raise Exception("無法獲取股票列表")

        # 估算時間
        if not args.test:
            estimate_time(stock_list, fetch_ranges)

        print(f"💡 提示: 可隨時按 Ctrl+C 中斷，下次執行會自動續傳\n")

        # 執行抓取
        total_new = fetch_all_ranges(fetcher, stock_list, fetch_ranges)
        print_final_summary(fetcher)

    except KeyboardInterrupt:
        status_message = "⚠️  執行被使用者中斷"
        print(f"\n\n{status_message}")
    except Exception as e:
        status_message = f"❌ 發生錯誤: {e}"
        print(f"\n\n{status_message}\n")
    finally:
        duration = time.time() - start_time
        _, new_earliest, new_latest, new_count = fetcher.get_existing_data_info()

        summary_text = (
            f"\n- 執行狀態: {status_message}"
            f"\n- 新增筆數: {total_new:,} 筆"
            f"\n- 執行耗時: {duration:.2f} 秒"
            f"\n- 資料庫狀態:"
            f"\n  - 總筆數: {new_count:,}"
            f"\n  - 日期範圍: {new_earliest} ~ {new_latest}"
        )
        
        try:
            hostname = os.uname().nodename
        except Exception:
            hostname = "Unknown"
        
        final_message = f"【股市資料獲取報告 - {hostname}】{summary_text}"

        send_line_message(final_message)


if __name__ == "__main__":
    main()
