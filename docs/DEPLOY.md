# Linux 服務器部署指南

快速在 Linux 服務器上部署臺股數據自動獲取服務。

## 系統要求

- **操作系統**: Ubuntu 18.04+ / Debian 10+ / CentOS 7+
- **Python**: 3.7+
- **權限**: root 或 sudo
- **網絡**: 可訪問 FinMind API

## 快速部署

### 1. 上傳項目到服務器

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
sudo bash install_service.sh
```

安裝腳本會自動：
- ✅ 檢查 Python 3 和 pip3
- ✅ 安裝依賴 (FinMind, pandas, requests)
- ✅ 創建日誌文件 `/var/log/stock-fetcher.log`
- ✅ 創建數據目錄 `data/`
- ✅ 配置 systemd service 和 timer
- ✅ 啓動定時任務

### 3. 驗證安裝

```bash
# 查看服務狀態
bash manage.sh status

# 手動運行一次測試
bash manage.sh run

# 查看實時日誌
bash manage.sh logs
```

## 服務說明

### 運行頻率

- **定時**: 每小時運行一次
- **隨機延遲**: 0-5 分鐘（避免同時大量請求）
- **開機啓動**: 系統重啓後自動啓動
- **斷點續傳**: 每次從上次中斷處繼續

### 日誌位置

```bash
# 系統日誌（systemd）
sudo journalctl -u stock-fetcher.service -f

# 應用日誌（程序輸出）
sudo tail -f /var/log/stock-fetcher.log
```

### 數據位置

```
/path/to/stock-strategy/data/taiwan_stocks.csv
```

## 管理命令

### 查看狀態

```bash
# Timer 和 Service 狀態
bash manage.sh status

# 下次運行時間
systemctl list-timers stock-fetcher.timer
```

### 控制服務

```bash
# 啓動定時任務
bash manage.sh start

# 停止定時任務
bash manage.sh stop

# 重啓定時任務
bash manage.sh restart

# 手動運行一次（不影響定時）
bash manage.sh run
```

### 查看日誌

```bash
# 實時日誌
bash manage.sh logs

# 歷史記錄
bash manage.sh history

# 系統日誌（最近 50 條）
sudo journalctl -u stock-fetcher.service -n 50
```

### 數據管理

```bash
# 查看數據統計
bash manage.sh data

# 手動查看 CSV
head -20 data/taiwan_stocks.csv
```

## 配置調整

### 修改運行頻率

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

編輯 `fetch_taiwan_stocks.py` 第 261 行：

```python
api_token = "YOUR_NEW_TOKEN"
```

### 修改請求延遲

編輯 `fetch_taiwan_stocks.py` 第 316 行：

```python
# 600次/小時 = 0.2秒/次（當前）
# 改爲更保守的 0.5 秒
new_df = fetcher.fetch_batch(stock_list, start_date, end_date, delay=0.5)
```

## 故障排查

### 服務未啓動

```bash
# 檢查狀態
sudo systemctl status stock-fetcher.timer
sudo systemctl status stock-fetcher.service

# 查看錯誤日誌
sudo journalctl -u stock-fetcher.service -xe

# 手動啓動
sudo systemctl start stock-fetcher.timer
```

### API 限流錯誤

如果日誌顯示 API 請求過多：

1. 檢查是否配置了 API Token
2. 增加請求延遲（修改 `delay` 參數）
3. 減少運行頻率（修改 timer）

### 數據未更新

```bash
# 檢查上次運行時間
sudo journalctl -u stock-fetcher.service | tail -20

# 檢查數據文件
ls -lh data/taiwan_stocks.csv
tail -20 data/taiwan_stocks.csv

# 手動運行測試
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

## 性能優化

### API Token（必須）

已配置 API Token:
- 每小時限制: 600 次
- 約 1200 支股票
- 需要約 2 小時完成一次全量獲取

### 調整批次大小

如果想更快完成，可以修改每次獲取的時間跨度：

編輯 `fetch_taiwan_stocks.py` 第 80 和 85 行：

```python
# 每次獲取 2 年而不是 1 年
start_date = end_date - timedelta(days=365*2)
```

注意：增加批次會增加單次運行時間。

## 卸載服務

```bash
# 停止並刪除服務
sudo bash uninstall_service.sh

# 刪除項目（可選）
cd ..
rm -rf stock-strategy
```

## 監控建議

### 設置告警

創建監控腳本 `/usr/local/bin/check-stock-fetcher.sh`:

```bash
#!/bin/bash
if ! systemctl is-active --quiet stock-fetcher.timer; then
    echo "Stock fetcher timer is not running!" | mail -s "Alert" admin@example.com
fi
```

添加到 crontab:

```bash
# 每天檢查一次
0 9 * * * /usr/local/bin/check-stock-fetcher.sh
```

### 磁盤空間監控

```bash
# 查看數據文件大小
du -h data/taiwan_stocks.csv

# 預期: 完整 26 年數據約 200-300 MB
```

## 備份建議

### 自動備份腳本

創建 `/usr/local/bin/backup-stock-data.sh`:

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

添加到 crontab:

```bash
# 每天凌晨 3 點備份
0 3 * * * /usr/local/bin/backup-stock-data.sh
```

## 常見問題

### Q: 數據多久能補齊？

A: 從現在到 2000 年約 26 年，每次補充 1 年，每小時運行一次：
- 理論: 26 小時
- 實際: 考慮 API 限制和網絡，約 2-3 天

### Q: 可以並行運行嗎？

A: 不建議。程序設計爲單例運行，多個實例會導致數據衝突。

### Q: 服務器重啓後會繼續嗎？

A: 會。Timer 設置了 `Persistent=true` 和開機啓動。

### Q: 如何知道數據已補齊？

A: 查看日誌，當出現 "🎉 已完成！數據已涵蓋到 2000-01-01" 即表示完成。

---

**需要幫助？** 查看日誌文件或提交 Issue。
