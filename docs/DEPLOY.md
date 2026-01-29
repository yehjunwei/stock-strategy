# Linux 伺服器部署指南

快速在 Linux 伺服器上部署臺股資料自動獲取服務。

## 系統要求

- **作業系統**: Ubuntu 18.04+ / Debian 10+ / CentOS 7+
- **Python**: 3.7+
- **權限**: root 或 sudo
- **網路**: 可存取 FinMind API

## 快速部署

### 1. 上傳專案到伺服器

```bash
# 方式 1: 使用 git
git clone <your-repo-url>
cd stock-strategy

# 方式 2: 使用 scp 上傳
scp -r /path/to/stock-strategy user@server:/home/user/
ssh user@server
cd ~/stock-strategy
```

### 2. 一鍵安裝服務

```bash
sudo bash services/install_service.sh
```

安裝腳本會自動：
- ✅ 檢查 Python 3 和 pip3
- ✅ 安裝依賴 (FinMind, pandas, requests)
- ✅ 建立日誌檔案 `/var/log/stock-fetcher.log`
- ✅ 建立資料目錄 `data/`
- ✅ 設定 systemd service 和 timer
- ✅ 啟動定時任務

### 3. 驗證安裝

```bash
# 查看服務狀態
bash services/manage.sh status

# 手動執行一次測試
bash services/manage.sh run

# 查看即時日誌
bash services/manage.sh logs
```

## 服務說明

### 執行頻率

- **定時**: 每小時執行一次
- **隨機延遲**: 0-5 分鐘（避免同時大量請求）
- **開機啟動**: 系統重啟後自動啟動
- **斷點續傳**: 每次從上次中斷處繼續

### 日誌位置

```bash
# 系統日誌（systemd）
sudo journalctl -u stock-fetcher.service -f

# 應用程式日誌（程式輸出）
sudo tail -f /var/log/stock-fetcher.log
```

### 資料位置

```
/path/to/stock-strategy/data/taiwan_stocks.csv
```

## 管理命令

### 查看狀態

```bash
# Timer 和 Service 狀態
bash services/manage.sh status

# 下次執行時間
systemctl list-timers stock-fetcher.timer
```

### 控制服務

```bash
# 啟動定時任務
bash services/manage.sh start

# 停止定時任務
bash services/manage.sh stop

# 重啟定時任務
bash services/manage.sh restart

# 手動執行一次（不影響定時）
bash services/manage.sh run
```

### 查看日誌

```bash
# 即時日誌
bash services/manage.sh logs

# 歷史記錄
bash services/manage.sh history

# 系統日誌（最近 50 條）
sudo journalctl -u stock-fetcher.service -n 50
```

### 資料管理

```bash
# 查看資料統計
bash services/manage.sh data

# 手動查看 CSV
head -20 data/taiwan_stocks.csv
```

## 設定調整

### 修改執行頻率

編輯 `/etc/systemd/system/stock-fetcher.timer`:

```ini
[Timer]
# 每小時 → 每 30 分鐘
OnCalendar=*:0/30

# 每小時 → 每天凌晨 2 點
OnCalendar=02:00
```

然後重載：

```bash
sudo systemctl daemon-reload
sudo systemctl restart stock-fetcher.timer
```

### 修改 API Token

編輯 `scripts/fetch_latest_stock_prices.py` 主程式，修改 `api_token` 變數。

### 修改請求延遲

編輯 `scripts/fetch_latest_stock_prices.py` 中的 `fetch_all_ranges` 函式呼叫：

```python
# 600次/小時 = 0.2秒/次（當前）
# 改為更保守的 0.5 秒
total_new = fetch_all_ranges(fetcher, stock_list, fetch_ranges, delay=0.5)
```

## 故障排除

### 服務未啟動

```bash
# 檢查狀態
sudo systemctl status stock-fetcher.timer
sudo systemctl status stock-fetcher.service

# 查看錯誤日誌
sudo journalctl -u stock-fetcher.service -xe

# 手動啟動
sudo systemctl start stock-fetcher.timer
```

### API 限流錯誤

如果日誌顯示 API 請求過多：

1. 檢查是否設定了 API Token
2. 增加請求延遲（修改 `delay` 參數）
3. 減少執行頻率（修改 timer）

### 資料未更新

```bash
# 檢查上次執行時間
sudo journalctl -u stock-fetcher.service | tail -20

# 檢查資料檔案
ls -lh data/taiwan_stocks.csv
tail -20 data/taiwan_stocks.csv

# 手動執行測試
sudo systemctl start stock-fetcher.service
sudo tail -f /var/log/stock-fetcher.log
```

### Python 依賴問題

```bash
# 重新安裝依賴
pip3 install -r requirements.txt --upgrade

# 檢查版本
pip3 list | grep -E "FinMind|pandas|requests"
```

## 效能優化

### API Token（必須）

已設定 API Token:
- 每小時限制: 600 次
- 約 1200 支股票
- 需要約 2 小時完成一次全量獲取

### 調整批次大小

如果想更快完成，可以修改每次獲取的時間跨度：

編輯 `core/stock_fetcher.py` 中的 `calculate_fetch_ranges` 函式。

注意：增加批次會增加單次執行時間。

## 卸載服務

```bash
# 停止並刪除服務
sudo bash services/uninstall_service.sh

# 刪除專案（可選）
cd ..
rm -rf stock-strategy
```

## 監控建議

### 設定告警

建立監控腳本 `/usr/local/bin/check-stock-fetcher.sh`:

```bash
#!/bin/bash
if ! systemctl is-active --quiet stock-fetcher.timer; then
    echo "Stock fetcher timer is not running!" | mail -s "Alert" admin@example.com
fi
```

新增到 crontab:

```bash
# 每天檢查一次
0 9 * * * /usr/local/bin/check-stock-fetcher.sh
```

### 磁碟空間監控

```bash
# 查看資料檔案大小
du -h data/taiwan_stocks.csv

# 預期: 完整 26 年資料約 200-300 MB
```

## 備份建議

### 自動備份腳本

建立 `/usr/local/bin/backup-stock-data.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/stock-data"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR
cp /path/to/stock-strategy/data/taiwan_stocks.csv \
   $BACKUP_DIR/taiwan_stocks_${DATE}.csv

# 保留最近 30 天的備份
find $BACKUP_DIR -name "*.csv" -mtime +30 -delete
```

新增到 crontab:

```bash
# 每天凌晨 3 點備份
0 3 * * * /usr/local/bin/backup-stock-data.sh
```

## 常見問題

### Q: 資料多久能補齊？

A: 從現在到 2000 年約 26 年，每次補充 1 年，每小時執行一次：
- **理論**: 26 小時
- **實際**: 考量 API 限制和網路，約 2-3 天

### Q: 可以並行執行嗎？

A: 不建議。程式設計為單例執行，多個實例會導致資料衝突。

### Q: 伺服器重啟後會繼續嗎？

A: 會。Timer 設定了 `Persistent=true` 和開機啟動。

### Q: 如何知道資料已補齊？

A: 查看日誌，當出現 "🎉 已完成！資料已涵蓋到 2000-01-01" 即表示完成。

---

**需要協助？** 查看日誌檔案或提交 Issue。
