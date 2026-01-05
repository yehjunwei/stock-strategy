# 快速入門指南

## 🚀 Linux 伺服器一鍵部署（推薦）

### 1. 上傳專案到伺服器

```bash
# 使用 scp 上傳
scp -r stock-strategy user@your-server:/home/user/

# 或使用 git
ssh user@your-server
git clone <your-repo-url>
cd stock-strategy
```

### 2. 執行安裝腳本

```bash
sudo bash services/install_service.sh
```

### 3. 完成！

服務已啟動，每小時自動執行一次，自動補齊資料到 2000 年。

---

## 📊 查看狀態

```bash
# 查看服務狀態
bash services/manage.sh status

# 查看即時日誌
bash services/manage.sh logs

# 查看資料資訊
bash services/manage.sh data
```

---

## 🔧 手動執行（本地測試）

如果你想在本地手動執行：

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 執行程式

```bash
python scripts/fetch_stocks.py
```

### 3. 再次執行（補充更多資料）

```bash
python scripts/fetch_stocks.py
```

每次執行會往前補充 1 年資料，重複約 25 次即可補齊到 2000 年。

---

## 📁 資料檔案

獲取的資料儲存在：
```
data/taiwan_stocks.csv
```

格式：
```csv
date,stock_id,open,high,low,close,volume
2025-12-08,2330,1035.0,1050.0,1032.0,1048.0,58234567
```

---

## ⏱️ 預計時間

- **單次執行**: 10-30 分鐘（約 1200 支股票）
- **完整補齊**: 2-3 天（自動執行，每小時一次）
- **資料量**: 約 200-300 MB（2000-2026 年）

---

## 🔑 API Token 已設定

已使用 FinMind API Token:
- 每小時限制: 600 次請求
- 延遲優化: 0.2 秒/次
- 無需額外設定

---

## 📖 更多文件

- **完整說明**: [README.md](README.md)
- **部署指南**: [DEPLOY.md](DEPLOY.md)
- **管理命令**: `bash manage.sh help`

---

## ❓ 常見問題

**Q: 如何知道資料已補齊？**
```bash
bash services/manage.sh data
# 查看日期範圍，當最早日期為 2000-01-01 即完成
```

**Q: 如何停止服務？**
```bash
bash services/manage.sh stop
```

**Q: 如何卸載？**
```bash
sudo bash services/uninstall_service.sh
```

---

**需要協助？** 查看 [README.md](README.md) 或 [DEPLOY.md](DEPLOY.md)
