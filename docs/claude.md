# Stock Strategy - 專案記錄

## 專案簡介
台股歷史數據獲取與策略回測系統

## 執行指令記錄

### 2026-01-05

#### 台股數據抓取
```bash
# 執行台股數據抓取（增量更新）
python3 scripts/fetch_stocks.py

# 測試單一股票（例如：2330 台積電）
python3 scripts/fetch_stocks.py --test 2330

# 測試另一支股票（例如：2317 鴻海）
python3 scripts/fetch_stocks.py --test 2317
```

**數據更新策略：**
1. 檢查 CSV 中最新的日期
2. 先從今天往回抓到最新日期（補齊最新數據）
3. 再從最早日期往回抓到 2000-01-01（補齊歷史數據）
4. 自動去重，避免重複記錄

## 技術架構

### 數據來源
- **FinMind API**: 台股歷史數據
- **API Token**: 已配置（600 次/小時）

### 數據格式
```
date | stock_id | stock_name | open | high | low | close | volume
```

**範例：**
```csv
date,stock_id,stock_name,open,high,low,close,volume
2026-01-05,2330,台積電,1630.0,1695.0,1625.0,1670.0,76182999
2026-01-05,2317,鴻海,114.0,114.5,113.5,114.0,50123456
```

### 目錄結構
```
stock-strategy/
├── core/                     # 核心邏輯
│   ├── __init__.py
│   └── stock_fetcher.py      # TaiwanStockFetcher 類
├── scripts/                  # 執行腳本
│   └── fetch_stocks.py       # 主入口腳本
├── services/                 # 系統服務配置
│   ├── stock-fetcher.service
│   ├── stock-fetcher.timer
│   ├── install_service.sh
│   ├── uninstall_service.sh
│   └── manage.sh
├── data/                     # 數據目錄
│   ├── taiwan_stocks.csv     # 台股歷史數據（支持多股票）
│   ├── stock_list.txt        # 股票代號列表（每天更新）
│   └── stock_list.json       # 股票列表詳細信息（含更新時間）
├── docs/                     # 文檔
│   ├── claude.md             # 專案記錄（本文件）
│   ├── DEPLOY.md             # 部署說明
│   └── QUICKSTART.md         # 快速開始
├── requirements.txt          # Python 依賴
└── README.md                 # 專案說明
```

## 重要設定

### 目標日期範圍
- 開始日期：2000-01-01
- 結束日期：今天

### API 配置
- 延遲設定：0.2 秒/請求（避免超出 API 限制）
- 速率限制：600 次/小時

### 股票列表文件

**`data/stock_list.txt`** - 純文本格式
```
0050
0051
0052
...
2330
2317
...
9958
Food
```

**`data/stock_list.json`** - JSON 格式
```json
{
  "update_time": "2026-01-05 09:30:32",
  "total_count": 1215,
  "filter_criteria": {
    "type": "twse",
    "stock_id_length": 4
  },
  "stocks": ["0050", "0051", ...]
}
```

**更新機制：**
- 每次執行抓取腳本時自動更新
- 追蹤新上市/下市股票
- 可用於策略分析、股票篩選等

## 開發歷程

### 2026-01-05

#### 第一階段：功能實現
- 實現增量更新邏輯：先更新到最新，再補齊歷史
- 新增測試模式：支援單一股票測試（--test 參數）
- 創建專案記錄文件

#### 第二階段：代碼重構與整理
- **代碼重構**：
  - 拆分長函數：確保所有函數不超過 100 行
  - 將 `main()` 函數拆分成 10+ 個職責單一的小函數
  - 創建核心類 `TaiwanStockFetcher`，職責清晰
  - 添加私有方法 `_print_batch_summary` 和 `_print_save_summary`

- **項目結構優化**：
  - 創建 `core/` 目錄存放核心邏輯類
  - 創建 `scripts/` 目錄存放可執行腳本
  - 創建 `services/` 目錄存放系統服務配置
  - 創建 `docs/` 目錄存放文檔
  - 移除不需要的文件（`__pycache__`）

- **多股票支持驗證**：
  - 測試 2330（台積電）：成功抓取並存入 CSV
  - 測試 2317（鴻海）：成功追加到同一 CSV
  - 驗證 CSV 可無限擴展，支持多股票數據
  - 數據按 `date` 和 `stock_id` 正確排序

- **代碼質量提升**：
  - 所有函數職責單一，易於理解和維護
  - 模塊化設計，核心邏輯與入口分離
  - 清晰的文件組織結構

#### 第三階段：股票列表管理
- **自動保存股票列表**：
  - 新增 `_save_stock_list()` 方法
  - 每次獲取股票列表時自動保存到 `data/` 目錄
  - 生成三種格式：
    - `stock_list.txt`：制表符分隔，包含股票代號和中文名稱
    - `stock_list.csv`：CSV 格式，包含 stock_id 和 stock_name 欄位
    - `stock_list.json`：JSON 格式，包含更新時間、總數量、篩選條件等詳細信息
  - 每天執行服務時自動更新（追蹤新上市/下市股票）

#### 第四階段：股票中文名稱支持
- **CSV 數據結構升級**：
  - 在 `taiwan_stocks.csv` 中加入 `stock_name` 欄位（位於 stock_id 後面）
  - 新增 `_load_stock_name_map()` 方法：啟動時自動從 `stock_list.json` 加載股票名稱映射
  - 修改 `fetch_stock_data()` 方法：抓取數據時自動填充股票名稱
  - 修改 `merge_and_save()` 方法：合併時自動填充舊數據的缺失名稱
  - 修復類型不匹配問題：確保 stock_id 在整個流程中保持字符串類型

- **數據格式更新**：
  - 舊格式：`date, stock_id, open, high, low, close, volume`
  - 新格式：`date, stock_id, stock_name, open, high, low, close, volume`
  - 所有歷史數據已自動回填股票名稱

## TODO
- [ ] 實現策略回測框架
- [ ] 整合技術指標計算
- [ ] 建立績效評估系統
