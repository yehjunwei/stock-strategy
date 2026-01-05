#!/usr/bin/env python3
"""
台股歷史數據增量獲取工具 - 主程序
- 先更新到最新日期（今天）
- 再往前補充數據至 2000-01-01
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime

# 添加父目錄到 Python 路徑以導入 core 模組
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stock_fetcher import TaiwanStockFetcher


def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='台股历史数据增量获取工具')
    parser.add_argument(
        '--test',
        type=str,
        help='测试模式：只抓取指定股票代号（例如：2330）'
    )
    return parser.parse_args()


def print_header(test_mode=None):
    """打印程序標題"""
    print("\n" + "="*70)
    print("🇹🇼  台股历史数据增量获取工具")
    if test_mode:
        print(f"   [测试模式: 仅抓取 {test_mode}]")
    print("="*70 + "\n")


def check_existing_data(fetcher):
    """檢查現有數據並打印信息"""
    print("🔍 检查现有数据...")
    exists, earliest, latest, count = fetcher.get_existing_data_info()

    if exists:
        print(f"✓ 找到现有数据文件")
        print(f"   记录数: {count:,} 条")
        print(f"   日期范围: {earliest} ~ {latest}")
    else:
        print("ℹ️  未找到现有数据，将开始首次获取")

    return exists, earliest, latest, count


def check_data_complete(fetcher, earliest):
    """檢查數據是否已完整"""
    if earliest and earliest <= fetcher.TARGET_START_DATE:
        print(f"\n🎉 数据已完整！")
        print(f"   涵盖范围: {earliest} ~ 今天")
        print(f"   已到达目标日期 {fetcher.TARGET_START_DATE}\n")
        return True
    return False


def print_fetch_plan(fetch_ranges):
    """打印抓取計劃"""
    print(f"\n📌 本次抓取计划:")
    for idx, (start, end, desc) in enumerate(fetch_ranges, 1):
        print(f"   阶段{idx}: {desc}")
        print(f"           {start} ~ {end}")


def prepare_stock_list(fetcher, test_mode):
    """準備股票列表"""
    if test_mode:
        stock_list = [test_mode]
        print(f"\n🧪 测试模式: 仅抓取 {test_mode}")
    else:
        stock_list = fetcher.get_stock_list()
        if not stock_list:
            print("\n❌ 无法获取股票列表，退出\n")
            return None
    return stock_list


def estimate_time(stock_list, fetch_ranges):
    """估算所需時間"""
    total_ranges = len(fetch_ranges)
    estimated_minutes = len(stock_list) * 0.5 / 60 * total_ranges
    print(f"\n⏱️  预计耗时: {estimated_minutes:.0f}-{estimated_minutes*2:.0f} 分钟")


def fetch_all_ranges(fetcher, stock_list, fetch_ranges):
    """逐階段獲取所有數據"""
    for idx, (start_date, end_date, desc) in enumerate(fetch_ranges, 1):
        print(f"\n{'='*70}")
        print(f"开始阶段 {idx}/{len(fetch_ranges)}: {desc}")
        print(f"{'='*70}")

        new_df = fetcher.fetch_batch(stock_list, start_date, end_date, delay=0.2)

        if not new_df.empty:
            fetcher.merge_and_save(new_df)
            if idx == len(fetch_ranges):
                fetcher.show_preview(new_df, n=5)
        else:
            print("⚠️  本阶段未获取到数据\n")


def print_final_summary(fetcher):
    """打印最終摘要"""
    _, new_earliest, new_latest, new_count = fetcher.get_existing_data_info()

    print(f"\n{'='*70}")
    print(f"✅ 所有阶段完成！")
    print(f"   最新状态: {new_earliest} ~ {new_latest}")
    print(f"   总记录数: {new_count:,} 条")

    if new_earliest and new_earliest > fetcher.TARGET_START_DATE:
        remaining = (
            datetime.strptime(new_earliest, '%Y-%m-%d') -
            datetime.strptime(fetcher.TARGET_START_DATE, '%Y-%m-%d')
        ).days
        print(f"   还需补充: 约 {remaining} 天")
        print(f"💡 提示: 再次执行可继续补充历史数据")
    else:
        print(f"🎉 恭喜！已完成所有数据获取到 {fetcher.TARGET_START_DATE}")

    print(f"{'='*70}\n")


def main():
    """主程序"""
    args = parse_arguments()
    print_header(args.test)

    # API Token 配置
    api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMS0wNiAwMDo1OTo0MCIsInVzZXJfaWQiOiJ5ZWhqdW53ZWkiLCJlbWFpbCI6InllaGp1bndlaUBnbWFpbC5jb20iLCJpcCI6IjgyLjE0MC4xODcuMjMifQ.cJNVY5xd2VHJHywKUzr89hewHWtZLymLyKzlAK0wPvs"

    # 創建獲取器
    fetcher = TaiwanStockFetcher(api_token=api_token)

    # 檢查現有數據
    exists, earliest, latest, count = check_existing_data(fetcher)

    # 檢查是否已完整
    if exists and check_data_complete(fetcher, earliest):
        return

    # 計算抓取範圍
    fetch_ranges = fetcher.calculate_fetch_ranges(earliest, latest)

    if not fetch_ranges:
        print(f"\n🎉 数据已完整！")
        print(f"   涵盖范围: {earliest} ~ {latest}")
        print(f"   已到达目标日期 {fetcher.TARGET_START_DATE}\n")
        return

    # 打印計劃
    print_fetch_plan(fetch_ranges)

    # 準備股票列表
    stock_list = prepare_stock_list(fetcher, args.test)
    if not stock_list:
        return

    # 估算時間
    if not args.test:
        estimate_time(stock_list, fetch_ranges)

    print(f"💡 提示: 可随时按 Ctrl+C 中断，下次执行会自动续传\n")

    # 執行抓取
    try:
        fetch_all_ranges(fetcher, stock_list, fetch_ranges)
        print_final_summary(fetcher)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        print("💡 提示: 下次执行会从中断处继续\n")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}\n")


if __name__ == "__main__":
    main()
