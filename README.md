# 臺股歷史數據獲取工具

一個簡單高效的臺股歷史數據獲取工具，支持**增量更新**，自動補充數據至 2000 年。

## 功能特色

- ✅ **增量更新**: 每次執行自動往前補充歷史數據
- ✅ **智能續傳**: 中斷後再次執行會從上次進度繼續
- ✅ **數據完整**: 涵蓋所有上市股票（約 1200+ 支）
- ✅ **格式標準**: CSV 格式，包含 OHLCV 數據
- ✅ **自動去重**: 合併數據時自動去除重複記錄

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 執行程序

```bash
python fetch_taiwan_stocks.py
```

**首次執行**: 獲取最近 1 年的數據
**後續執行**: 每次往前補充 1 年，直到 2000-01-01

### 3. 等待完成

- 預計每次執行 10-30 分鐘（取決於網絡速度）
- 可隨時按 `Ctrl+C` 中斷，下次會自動續傳
- 數據保存在 `data/taiwan_stocks.csv`

## Linux 自動化部署（推薦）

在 Linux 服務器上設置自動定時任務，每小時自動獲取數據。

### 一鍵安裝

```bash
# 下載項目
git clone <your-repo-url>
cd stock-strategy

# 運行安裝腳本（需要 root 權限）
sudo bash install_service.sh
```

安裝完成後，服務會：
- ✅ 每小時自動運行一次
- ✅ 開機自動啓動
- ✅ 自動補齊數據到 2000 年
- ✅ 日誌記錄所有操作

### 管理命令

```bash
# 查看服務狀態
bash manage.sh status

# 查看實時日誌
bash manage.sh logs

# 手動運行一次
bash manage.sh run

# 查看數據信息
bash manage.sh data

# 查看所有命令
bash manage.sh help
```

### 卸載服務

```bash
sudo bash uninstall_service.sh
```

## 數據格式

### CSV 欄位說明

| 欄位 | 說明 | 類型 | 示例 |
|------|------|------|------|
| `date` | 交易日期 | String | 2025-12-08 |
| `stock_id` | 股票代碼 | String | 2330 |
| `open` | 開盤價 | Float | 1035.0 |
| `high` | 最高價 | Float | 1050.0 |
| `low` | 最低價 | Float | 1032.0 |
| `close` | 收盤價 | Float | 1048.0 |
| `volume` | 成交量 | Integer | 58234567 |

### 示例數據

```csv
date,stock_id,open,high,low,close,volume
2025-12-08,2330,1035.0,1050.0,1032.0,1048.0,58234567
2025-12-08,2317,135.5,138.0,134.0,137.5,12345678
2025-12-09,2330,1050.0,1055.0,1045.0,1052.0,45678901
```

## 工作原理

```
首次執行
├─ 檢查數據文件 → 不存在
├─ 獲取最近 1 年數據 (2025-01-01 ~ 2026-01-05)
└─ 保存到 data/taiwan_stocks.csv

第二次執行
├─ 檢查數據文件 → 存在 (最早: 2025-01-01)
├─ 往前補充 1 年 (2024-01-01 ~ 2024-12-31)
└─ 合併並去重

第三次執行
├─ 檢查數據文件 → 存在 (最早: 2024-01-01)
├─ 繼續往前補充 1 年
└─ ...直到 2000-01-01
```

## 預期數據量

完整獲取 2000-2026 年的數據：

- **時間跨度**: 26 年 ≈ 6,500 交易日
- **股票數量**: 約 1,200 支（僅上市，不含 ETF）
- **總記錄數**: 約 500 萬 - 800 萬條
- **文件大小**: 約 200-300 MB

## 使用 API Token（推薦）

使用 FinMind API Token 可提升 6 倍速度。

### 獲取 Token

1. 前往 [FinMind 官網](https://finmindtrade.com/) 註冊
2. 登錄後在個人中心獲取 API Token

### 設置 Token

編輯 `fetch_taiwan_stocks.py` 的第 261 行：

```python
api_token = "YOUR_API_TOKEN_HERE"  # 替換成你的 token
```

## 常見問題

### Q1: 需要執行多少次才能完成？

約 25-26 次（每次補充 1 年，從現在到 2000 年）

### Q2: 可以一次獲取全部數據嗎？

可以，但不推薦。理由：
- 需要 5+ 小時連續運行
- 容易因網絡問題中斷
- 增量更新更穩定可靠

### Q3: 如何修改目標年份？

編輯 `fetch_taiwan_stocks.py` 的第 25 行：

```python
TARGET_START_DATE = "2000-01-01"  # 改成你想要的日期
```

### Q4: 數據會自動更新嗎？

目前只支持往前補充歷史數據。如需更新最新數據，需要手動修改邏輯。

### Q5: 爲什麼有些股票沒有完整數據？

- 新上市股票：上市時間晚於 2000 年
- 已下市股票：FinMind 可能無數據
- 暫停交易：某些日期可能停牌

## 進階使用

### 只獲取特定股票

修改 `get_stock_list()` 函數返回值：

```python
def get_stock_list(self):
    return ['2330', '2317', '2454']  # 臺積電、鴻海、聯發科
```

### 修改每次獲取的時間跨度

修改 `calculate_fetch_range()` 函數：

```python
# 第 80 行和 85 行
start_date = end_date - timedelta(days=365*2)  # 改爲 2 年
```

### 調整請求延遲

修改 `main()` 函數：

```python
# 第 315 行
new_df = fetcher.fetch_batch(stock_list, start_date, end_date, delay=1.0)
```

## 項目結構

```
stock-strategy/
├── fetch_taiwan_stocks.py   # 主程序
├── requirements.txt          # 依賴列表
├── README.md                 # 本文檔
├── install_service.sh        # Linux 服務安裝腳本
├── uninstall_service.sh      # Linux 服務卸載腳本
├── manage.sh                 # 服務管理腳本
├── stock-fetcher.service     # Systemd service 文件
├── stock-fetcher.timer       # Systemd timer 文件
└── data/
    └── taiwan_stocks.csv     # 數據文件（自動生成）
```

## 數據來源

本工具使用 [FinMind](https://finmindtrade.com/) API 獲取數據：

- 官方文檔: https://finmind.github.io/
- 數據來源: 臺灣證券交易所（TWSE）
- 數據質量: 專業級，廣泛用於量化交易

## 授權聲明

- 本工具僅供學習和研究使用
- 數據版權歸臺灣證券交易所及 FinMind 所有
- 請遵守 FinMind 使用條款
- 使用數據進行交易需自行承擔風險

## 後續應用

獲取數據後，可以進行：

1. **回測交易策略**: 驗證技術分析指標的有效性
2. **統計分析**: 研究股票走勢、波動率、相關性等
3. **機器學習**: 訓練股價預測模型
4. **數據可視化**: 繪製K線圖、趨勢圖等

## 學習資源

- Pandas 教學: https://leemeng.tw/practical-pandas-tutorial-for-aspiring-data-scientists.html
- Pandas_ta 教學: https://blog.csdn.net/ndhtou222/article/details/132157873
- 用 Python 實作買賣指標: https://python.plainenglish.io/generating-buy-sell-trade-signals-in-python-1153b1a543c4
- FinMind 官方文檔: https://finmind.github.io/
- FinMind 策略分析: https://finmindtrade.com/analysis/#/dashboards/strategy-analysis

## 技術支持

- **問題回報**: [GitHub Issues](https://github.com/finmind/FinMind/issues)
- **FinMind 文檔**: https://finmind.github.io/
- **API 使用**: https://finmindtrade.com/

## 更新日誌

### v2.0 (2026-01-05)

- ✨ 實現增量更新功能
- ✨ 自動檢測現有數據並續傳
- ✨ 智能去重和數據合併
- 🔄 重構代碼結構
- 📝 完善文檔說明

### v1.0

- 初始版本
- 基本數據獲取功能

---

**Made with ❤️ for Taiwan Stock Traders**
