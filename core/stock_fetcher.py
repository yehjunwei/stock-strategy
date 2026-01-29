"""
臺股資料獲取器核心類
提供臺股歷史資料的增量獲取功能
"""

import pandas as pd
from datetime import datetime, timedelta
import time
from pathlib import Path
import json

try:
    from FinMind.data import DataLoader
except ImportError:
    print("❌ 請先安裝依賴: pip install -r requirements.txt")
    exit(1)


class TaiwanStockFetcher:
    """臺股資料增量獲取器"""

    TARGET_START_DATE = "2010-01-01"
    CSV_FILENAME = "taiwan_stocks.csv"

    def __init__(self, api_token=None, output_dir="data"):
        """初始化獲取器"""
        self.api = DataLoader()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.csv_path = self.output_dir / self.CSV_FILENAME
        self.stock_name_map = {}  # 股票代號 -> 中文名稱對應

        if api_token:
            self.api.login_by_token(api_token=api_token)
            print("✓ 已使用 API Token 登入")
        else:
            print("ℹ️  未使用 API Token（請求頻率受限）")

        # 嘗試從現有檔案載入股票名稱對應
        self._load_stock_name_map()

    def _load_stock_name_map(self):
        """從現有的 stock_list.json 載入股票名稱對應"""
        json_path = self.output_dir / "stock_list.json"
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for stock in data.get('stocks', []):
                        self.stock_name_map[stock['stock_id']] = stock['stock_name']
                print(f"✓ 已載入 {len(self.stock_name_map)} 個股票名稱對應")
            except Exception as e:
                print(f"⚠️  載入股票名稱對應失敗: {e}")

    def get_existing_data_info(self):
        """
        獲取現有資料資訊
        返回: (是否存在, 最早日期, 最晚日期, 記錄數)
        """
        if not self.csv_path.exists():
            return False, None, None, 0

        try:
            df = pd.read_csv(self.csv_path, usecols=['date'])
            if df.empty:
                return False, None, None, 0

            dates = pd.to_datetime(df['date']).sort_values()
            earliest = dates.min().strftime('%Y-%m-%d')
            latest = dates.max().strftime('%Y-%m-%d')
            count = len(df)
            return True, earliest, latest, count

        except Exception as e:
            print(f"⚠️  讀取現有資料失敗: {e}")
            return False, None, None, 0

    def calculate_fetch_ranges(self, existing_earliest_date, existing_latest_date):
        """
        計算需要獲取的日期範圍（兩階段）

        策略:
        1. 第一階段：從最新日期到今天（補齊最新資料）
        2. 第二階段：從最早日期往回抓到 2010-01-01（補齊歷史資料）

        返回: [(start_date, end_date, description), ...]
        """
        ranges = []
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_start_date = datetime.strptime(self.TARGET_START_DATE, "%Y-%m-%d")

        if existing_latest_date is None:
            start_date = today - timedelta(days=30)
            ranges.append((
                start_date.strftime('%Y-%m-%d'),
                today.strftime('%Y-%m-%d'),
                "首次執行（最近30天）"
            ))
        else:
            latest_date = datetime.strptime(existing_latest_date, "%Y-%m-%d")
            days_gap = (today - latest_date).days

            if days_gap > 1:
                ranges.append((
                    (latest_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                    today.strftime('%Y-%m-%d'),
                    f"更新最新資料（補齊 {days_gap} 天）"
                ))

            if existing_earliest_date:
                earliest_date = datetime.strptime(existing_earliest_date, "%Y-%m-%d")

                if earliest_date > target_start_date:
                    end_date = earliest_date - timedelta(days=1)
                    start_date = end_date - timedelta(days=30)

                    if start_date < target_start_date:
                        start_date = target_start_date

                    days_to_fetch = (end_date - start_date).days
                    ranges.append((
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d'),
                        f"補充歷史資料（往前 {days_to_fetch} 天）"
                    ))

        return ranges

    def get_stock_list(self, force_update=False):
        """
        獲取所有上市股票列表

        Args:
            force_update: 是否強制從 API 更新（預設 False，會先檢查快取）
        """
        print("\n📋 正在獲取臺股列表...")

        # 檢查是否有當天的快取
        if not force_update:
            cached_stocks = self._load_cached_stock_list()
            if cached_stocks:
                return cached_stocks

        # 快取不存在或已過期，從 API 獲取
        print("🌐 從 API 獲取最新股票列表...")
        try:
            stock_info = self.api.taiwan_stock_info()

            # 除錯資訊
            print(f"🔍 API 回應類型: {type(stock_info)}")
            if stock_info is None:
                print("⚠️  API 回應為 None")
                return []

            # 檢查是否為 DataFrame
            if hasattr(stock_info, 'empty'):
                print(f"🔍 DataFrame 是否為空: {stock_info.empty}")
                if not stock_info.empty:
                    print(f"🔍 DataFrame 欄位: {stock_info.columns.tolist()}")
                    print(f"🔍 DataFrame 行數: {len(stock_info)}")

            if stock_info is not None and not stock_info.empty:
                # 篩選上市股票（4位數代碼）
                filtered = stock_info[
                    (stock_info['type'] == 'twse') &
                    (stock_info['stock_id'].str.len() == 4)
                ]

                # 建立股票代號到名稱的對應
                self.stock_name_map = dict(
                    zip(filtered['stock_id'], filtered['stock_name'])
                )

                sorted_stocks = sorted(filtered['stock_id'].unique().tolist())
                print(f"✓ 獲取到 {len(sorted_stocks)} 支上市股票")

                # 儲存股票列表到檔案
                self._save_stock_list(sorted_stocks)

                return sorted_stocks
            else:
                print("❌ 無法獲取股票列表（回應為空）")
                return []

        except KeyError as e:
            print(f"❌ KeyError: {e}")
            print(f"🔍 這可能是 FinMind API 回應格式問題")
            import traceback
            traceback.print_exc()
            return []
        except Exception as e:
            print(f"❌ 獲取股票列表失敗: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _load_cached_stock_list(self):
        """
        從快取檔案載入股票列表（如果是當天更新的）

        Returns:
            list: 股票代號列表，如果快取不存在或已過期則返回 None
        """
        json_path = self.output_dir / "stock_list.json"

        if not json_path.exists():
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 檢查更新時間
            update_time_str = data.get('update_time')
            if not update_time_str:
                print("⚠️  快取檔案缺少更新時間，將重新獲取")
                return None

            # 解析更新時間
            update_time = datetime.strptime(update_time_str, '%Y-%m-%d %H:%M:%S')
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # 檢查是否為當天更新
            if update_time >= today:
                stocks = [stock['stock_id'] for stock in data.get('stocks', [])]

                # 同時載入股票名稱對應
                self.stock_name_map = {
                    stock['stock_id']: stock['stock_name']
                    for stock in data.get('stocks', [])
                }

                print(f"✓ 使用快取的股票列表（更新時間: {update_time_str}）")
                print(f"✓ 共 {len(stocks)} 支股票")
                return stocks
            else:
                print(f"ℹ️  快取已過期（更新時間: {update_time_str}），將重新獲取")
                return None

        except Exception as e:
            print(f"⚠️  讀取快取失敗: {e}")
            return None

    def _save_stock_list(self, stocks):
        """儲存股票列表到檔案"""
        if not stocks:
            return

        # 儲存為 JSON 檔案（包含詳細資訊）
        json_path = self.output_dir / "stock_list.json"
        stock_list_with_names = [
            {"stock_id": stock_id, "stock_name": self.stock_name_map.get(stock_id, '')}
            for stock_id in stocks
        ]
        stock_info = {
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_count": len(stocks),
            "filter_criteria": {
                "type": "twse",
                "stock_id_length": 4
            },
            "stocks": stock_list_with_names
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(stock_info, f, ensure_ascii=False, indent=2)

        print(f"✓ 股票列表已儲存到: {json_path}")

    def fetch_stock_data(self, stock_id, start_date, end_date):
        """獲取單一股票的歷史資料"""
        try:
            df = self.api.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                # 獲取股票名稱
                stock_name = self.stock_name_map.get(stock_id, '')

                df_clean = pd.DataFrame({
                    'date': pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d'),
                    'stock_id': df['stock_id'],
                    'stock_name': stock_name,
                    'open': df['open'],
                    'high': df['max'],
                    'low': df['min'],
                    'close': df['close'],
                    'volume': df['Trading_Volume']
                })
                return df_clean
            else:
                return None

        except Exception:
            return None

    def fetch_batch(self, stock_list, start_date, end_date, delay=0.5):
        """批次獲取股票資料"""
        print(f"\n{'='*70}")
        print(f"📥 開始獲取資料: {start_date} 至 {end_date}")
        print(f"{'='*70}\n")

        all_data = []
        total = len(stock_list)
        success_count = 0
        fail_count = 0

        for idx, stock_id in enumerate(stock_list, 1):
            percentage = (idx / total) * 100
            print(f"[{idx}/{total}] ({percentage:.1f}%) {stock_id} ", end='', flush=True)

            df = self.fetch_stock_data(stock_id, start_date, end_date)

            if df is not None and not df.empty:
                all_data.append(df)
                success_count += 1
                print(f"✓ {len(df)} 條")
            else:
                fail_count += 1
                print("✗")

            if idx < total:
                time.sleep(delay)

            if idx % 50 == 0:
                print(f"\n   進度統計: 成功 {success_count} | 失敗 {fail_count}\n")

        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            self._print_batch_summary(final_df, success_count, fail_count, total)
            return final_df
        else:
            print("\n❌ 未獲取到任何資料")
            return pd.DataFrame()

    def _print_batch_summary(self, df, success_count, fail_count, total):
        """列印批次獲取摘要"""
        print(f"\n{'='*70}")
        print(f"✓ 本次獲取完成")
        print(f"  新增記錄: {len(df):,} 條")
        print(f"  成功股票: {success_count}/{total}")
        print(f"  失敗股票: {fail_count}/{total}")
        print(f"{'='*70}\n")

    def merge_and_save(self, new_df):
        """合併新舊資料並儲存"""
        if new_df.empty:
            print("⚠️  沒有新資料需要儲存")
            return

        if self.csv_path.exists():
            print("📂 正在讀取現有資料...")
            existing_df = pd.read_csv(self.csv_path, dtype={'stock_id': str})
            print(f"   現有記錄: {len(existing_df):,} 條")

            # 為舊資料填充缺失的 stock_name
            if 'stock_name' not in existing_df.columns:
                existing_df['stock_name'] = ''

            # 填充空的 stock_name
            mask = existing_df['stock_name'].isna() | (existing_df['stock_name'] == '')
            if mask.any():
                existing_df.loc[mask, 'stock_name'] = existing_df.loc[mask, 'stock_id'].map(
                    self.stock_name_map
                ).fillna('')

            print("🔄 合併新舊資料...")
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)

            # 填充所有空的 stock_name
            mask = combined_df['stock_name'].isna() | (combined_df['stock_name'] == '')
            if mask.any():
                combined_df.loc[mask, 'stock_name'] = combined_df.loc[mask, 'stock_id'].map(
                    self.stock_name_map
                ).fillna('')

            print("🧹 去除重複記錄...")
            combined_df = combined_df.drop_duplicates(
                subset=['date', 'stock_id'],
                keep='last'
            )
        else:
            print("📝 建立新資料檔案...")
            combined_df = new_df

        print("📊 排序資料...")
        combined_df = combined_df.sort_values(['date', 'stock_id']).reset_index(drop=True)

        # 確保欄位順序正確
        desired_columns = ['date', 'stock_id', 'stock_name', 'open', 'high', 'low', 'close', 'volume']
        combined_df = combined_df[desired_columns]

        print(f"💾 儲存到 {self.csv_path}...")
        combined_df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')

        self._print_save_summary(combined_df)

    def _print_save_summary(self, df):
        """列印儲存摘要"""
        file_size_mb = self.csv_path.stat().st_size / 1024 / 1024
        date_range = f"{df['date'].min()} ~ {df['date'].max()}"
        stock_count = df['stock_id'].nunique()

        print(f"\n{'='*70}")
        print(f"✅ 資料已儲存")
        print(f"   檔案路徑: {self.csv_path}")
        print(f"   檔案大小: {file_size_mb:.2f} MB")
        print(f"   總記錄數: {len(df):,} 條")
        print(f"   股票數量: {stock_count} 支")
        print(f"   日期範圍: {date_range}")
        print(f"{'='*70}\n")

    def show_preview(self, df, n=5):
        """顯示資料預覽"""
        if df.empty:
            return

        print(f"資料預覽（前 {n} 條）:")
        print(df.head(n).to_string(index=False))
        print()
