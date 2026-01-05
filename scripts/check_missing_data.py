#!/usr/bin/env python3
"""
檢查並補齊臺股資料中缺失的資料
- 分析現有CSV檔案，找出缺失的日期和股票
- 提供補齊缺失資料的功能
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import argparse
import os

# 嘗試載入 python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)

# 添加父目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stock_fetcher import TaiwanStockFetcher
from core.line_sender import send_line_message


def get_trading_days(start_date, end_date):
    """
    獲取台股交易日（排除週末）
    注意：這裡只排除週末，不包含國定假日

    Args:
        start_date: 開始日期 (datetime)
        end_date: 結束日期 (datetime)

    Returns:
        list: 交易日列表
    """
    trading_days = []
    current = start_date

    while current <= end_date:
        # 排除週六(5)和週日(6)
        if current.weekday() < 5:
            trading_days.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    return trading_days


def analyze_missing_data(csv_path, output_dir):
    """
    分析CSV中缺失的資料

    Args:
        csv_path: CSV檔案路徑
        output_dir: 輸出目錄

    Returns:
        tuple: (缺失資料字典, 統計資訊)
    """
    print(f"\n{'='*70}")
    print("📊 分析資料完整性")
    print(f"{'='*70}\n")

    if not csv_path.exists():
        print("❌ CSV檔案不存在")
        return {}, {}

    print("📂 讀取資料...")
    df = pd.read_csv(csv_path, dtype={'stock_id': str})

    if df.empty:
        print("❌ CSV檔案為空")
        return {}, {}

    # 基本統計
    total_records = len(df)
    unique_stocks = df['stock_id'].nunique()
    date_range_start = df['date'].min()
    date_range_end = df['date'].max()

    print(f"✓ 資料載入完成")
    print(f"   總記錄數: {total_records:,}")
    print(f"   股票數量: {unique_stocks}")
    print(f"   日期範圍: {date_range_start} ~ {date_range_end}")

    # 計算交易日
    start_dt = datetime.strptime(date_range_start, '%Y-%m-%d')
    end_dt = datetime.strptime(date_range_end, '%Y-%m-%d')
    all_trading_days = get_trading_days(start_dt, end_dt)
    total_trading_days = len(all_trading_days)

    print(f"\n📅 預期交易日數（排除週末）: {total_trading_days} 天")
    print(f"🔍 開始檢查每支股票的資料完整性...\n")

    # 分析每支股票的缺失日期
    missing_data = {}
    stock_stats = []

    all_stocks = sorted(df['stock_id'].unique())

    for idx, stock_id in enumerate(all_stocks, 1):
        stock_df = df[df['stock_id'] == stock_id]
        stock_dates = set(stock_df['date'].tolist())

        # 找出缺失的日期
        missing_dates = [d for d in all_trading_days if d not in stock_dates]

        if missing_dates:
            missing_data[stock_id] = missing_dates

        # 統計
        actual_days = len(stock_dates)
        missing_count = len(missing_dates)
        completeness = (actual_days / total_trading_days) * 100 if total_trading_days > 0 else 0

        stock_stats.append({
            'stock_id': stock_id,
            'actual_days': actual_days,
            'missing_days': missing_count,
            'completeness': completeness
        })

        # 每100支股票顯示一次進度
        if idx % 100 == 0:
            print(f"   處理進度: {idx}/{unique_stocks}")

    print(f"\n✓ 分析完成\n")

    # 顯示統計結果
    stats_df = pd.DataFrame(stock_stats)

    # 完整度統計
    complete_stocks = len(stats_df[stats_df['missing_days'] == 0])
    incomplete_stocks = len(stats_df[stats_df['missing_days'] > 0])

    print(f"{'='*70}")
    print(f"📈 統計摘要")
    print(f"{'='*70}")
    print(f"完整股票數量: {complete_stocks} ({complete_stocks/unique_stocks*100:.1f}%)")
    print(f"缺失股票數量: {incomplete_stocks} ({incomplete_stocks/unique_stocks*100:.1f}%)")

    if incomplete_stocks > 0:
        total_missing = stats_df['missing_days'].sum()
        avg_missing = stats_df[stats_df['missing_days'] > 0]['missing_days'].mean()
        max_missing = stats_df['missing_days'].max()
        max_missing_stock = stats_df[stats_df['missing_days'] == max_missing].iloc[0]['stock_id']

        print(f"\n缺失資料統計:")
        print(f"   總缺失筆數: {total_missing:,} 筆")
        print(f"   平均缺失天數: {avg_missing:.1f} 天")
        print(f"   最多缺失天數: {max_missing} 天 (股票代號: {max_missing_stock})")

        # 顯示缺失最嚴重的前10支股票
        print(f"\n缺失最嚴重的前10支股票:")
        top_10 = stats_df.nlargest(10, 'missing_days')[['stock_id', 'missing_days', 'completeness']]
        for _, row in top_10.iterrows():
            print(f"   {row['stock_id']}: 缺 {row['missing_days']} 天 (完整度: {row['completeness']:.1f}%)")

    print(f"{'='*70}\n")

    # 儲存詳細報告
    report_path = output_dir / "missing_data_report.csv"
    stats_df.to_csv(report_path, index=False, encoding='utf-8-sig')
    print(f"✓ 詳細報告已儲存至: {report_path}\n")

    # 儲存缺失明細
    if missing_data:
        detail_path = output_dir / "missing_data_detail.txt"
        with open(detail_path, 'w', encoding='utf-8') as f:
            f.write(f"缺失資料明細報告\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n\n")

            for stock_id in sorted(missing_data.keys()):
                dates = missing_data[stock_id]
                f.write(f"{stock_id}: 缺 {len(dates)} 天\n")
                # 顯示前5個缺失日期
                sample_dates = dates[:5]
                f.write(f"   範例: {', '.join(sample_dates)}")
                if len(dates) > 5:
                    f.write(f" ... (還有 {len(dates)-5} 天)")
                f.write("\n\n")

        print(f"✓ 缺失明細已儲存至: {detail_path}\n")

    return missing_data, {
        'total_missing': total_missing if incomplete_stocks > 0 else 0,
        'incomplete_stocks': incomplete_stocks
    }


def fill_missing_data(missing_data, fetcher, max_stocks=None):
    """
    補齊缺失的資料

    Args:
        missing_data: 缺失資料字典 {stock_id: [missing_dates]}
        fetcher: TaiwanStockFetcher 實例
        max_stocks: 最多補齊幾支股票（None 表示全部）
    """
    if not missing_data:
        print("✓ 沒有缺失的資料需要補齊")
        return 0

    print(f"\n{'='*70}")
    print(f"🔧 開始補齊缺失資料")
    print(f"{'='*70}\n")

    total_stocks = len(missing_data)
    if max_stocks:
        print(f"⚠️  限制補齊數量: 最多 {max_stocks} 支股票\n")
        stocks_to_fill = list(missing_data.keys())[:max_stocks]
    else:
        stocks_to_fill = list(missing_data.keys())

    all_new_data = []
    success_count = 0
    fail_count = 0

    for idx, stock_id in enumerate(stocks_to_fill, 1):
        missing_dates = missing_data[stock_id]

        print(f"[{idx}/{len(stocks_to_fill)}] {stock_id} (缺 {len(missing_dates)} 天)", end=' ')

        # 將連續的日期合併成區間來減少API請求
        date_ranges = _merge_date_ranges(missing_dates)

        stock_data = []
        for start_date, end_date in date_ranges:
            df = fetcher.fetch_stock_data(stock_id, start_date, end_date)
            if df is not None and not df.empty:
                stock_data.append(df)

        if stock_data:
            combined = pd.concat(stock_data, ignore_index=True)
            all_new_data.append(combined)
            success_count += 1
            print(f"✓ 補齊 {len(combined)} 筆")
        else:
            fail_count += 1
            print("✗ 失敗")

    print(f"\n{'='*70}")
    print(f"補齊結果:")
    print(f"   成功: {success_count}/{len(stocks_to_fill)}")
    print(f"   失敗: {fail_count}/{len(stocks_to_fill)}")
    print(f"{'='*70}\n")

    # 合併並儲存
    if all_new_data:
        final_df = pd.concat(all_new_data, ignore_index=True)
        print(f"💾 儲存補齊的資料...")
        fetcher.merge_and_save(final_df)
        return len(final_df)
    else:
        print("⚠️  沒有成功補齊任何資料")
        return 0


def _merge_date_ranges(dates):
    """
    將日期列表合併成連續的日期區間

    Args:
        dates: 日期字串列表 ['2024-01-01', '2024-01-02', ...]

    Returns:
        list: [(start_date, end_date), ...]
    """
    if not dates:
        return []

    # 轉換為 datetime 並排序
    date_objs = sorted([datetime.strptime(d, '%Y-%m-%d') for d in dates])

    ranges = []
    start = date_objs[0]
    end = date_objs[0]

    for i in range(1, len(date_objs)):
        if (date_objs[i] - end).days <= 3:  # 允許3天內的間隔（考慮週末）
            end = date_objs[i]
        else:
            ranges.append((start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))
            start = date_objs[i]
            end = date_objs[i]

    ranges.append((start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))
    return ranges


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='檢查並補齊臺股資料中缺失的資料')
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='僅檢查，不補齊資料'
    )
    parser.add_argument(
        '--max-stocks',
        type=int,
        help='最多補齊幾支股票（用於測試）'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='資料目錄（預設: data）'
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("🔍 臺股資料完整性檢查工具")
    print("="*70)

    # 初始化
    output_dir = Path(args.output_dir)
    csv_path = output_dir / "taiwan_stocks.csv"

    # 分析缺失資料
    missing_data, stats = analyze_missing_data(csv_path, output_dir)

    # 如果只是檢查，就結束
    if args.check_only:
        print("✓ 檢查完成（僅檢查模式，未補齊資料）\n")
        return

    # 補齊缺失資料
    if missing_data:
        api_token = os.getenv('FINMIND_API_TOKEN')
        fetcher = TaiwanStockFetcher(api_token=api_token, output_dir=args.output_dir)

        filled_count = fill_missing_data(missing_data, fetcher, max_stocks=args.max_stocks)

        print(f"\n✅ 任務完成！共補齊 {filled_count:,} 筆資料\n")

        # 發送通知
        message = (
            f"【資料補齊報告】\n"
            f"- 缺失股票數: {stats['incomplete_stocks']}\n"
            f"- 總缺失筆數: {stats['total_missing']:,}\n"
            f"- 已補齊筆數: {filled_count:,}"
        )
        send_line_message(message)
    else:
        print("✅ 資料完整，無需補齊\n")


if __name__ == "__main__":
    main()
